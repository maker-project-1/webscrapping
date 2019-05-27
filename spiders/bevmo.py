import os.path as op
import re
from io import BytesIO

from lxml import etree

parser = etree.HTMLParser(encoding='utf-8')
from time import sleep
from urllib.parse import urlsplit, parse_qs
import requests
import requests_cache, imghdr

from validators import validate_raw_files
from create_csvs import create_csvs
from ers import all_keywords_usa as keywords, fpath_namer, mh_brands, clean_url, headers
#
from matcher import BrandMatcher
from ers import COLLECTION_DATE, file_hash, img_path_namer
import shutil
from custom_browser import CustomDriver
from parse import parse


# Init variables and assets
shop_id = "bevmo"
root_url = "http://shop.bevmo.com/"
requests_cache.install_cache(fpath_namer(shop_id, 'requests_cache'))
country = "USA"


searches, categories, products = {}, {}, {}
# If necessary
driver = CustomDriver(headless=False, download_images=True)


def getprice(pricestr):
    pricestr = re.sub("[^0-9.$]", "", pricestr)
    if pricestr == '':
        return pricestr
    price = parse('${pound:d}.{pence:d}', pricestr)
    if price is None:
        price = parse('{pence:d}p', pricestr)
        return price.named['pence']
    else:
        return price.named['pound'] * 100 + price.named['pence']


def init_bevmo(driver):
    driver.get("https://www.bevmo.com")
    sleep(5)
    driver.wait_for_xpath('//form[@id="storeselect-popup"]//*[@name="twenty_one_option"]')
    button_to_click_xpath = '//*[@name="twenty_one_option"]'
    driver.waitclick(button_to_click_xpath, timeout=10)
    button_to_click_xpath = '//input[@value="ship"]'
    driver.waitclick(button_to_click_xpath, timeout=10)
    button_to_click_xpath = '//select[@name="ship_state"]/option[@value="17"]'
    driver.waitclick(button_to_click_xpath, timeout=10)
    button_to_click_xpath = '//*[@id="storeselect-select"]'
    driver.waitclick(button_to_click_xpath, timeout=10)
    print("Sleeping", sleep(3))

bevmo_was_initialised = False


urls_ctgs_dict = {
    'champagne': 'http://shop.bevmo.com/search?w=champagne&view=list&srt={page}',
    'cognac': 'http://shop.bevmo.com/search?w=cognac&view=list&srt={page}',
    'sparkling': 'http://shop.bevmo.com/search?w=sparkling&view=list&srt={page}',
    'vodka': 'http://shop.bevmo.com/search?w=vodka&view=list&srt={page}',
    'whisky': 'http://shop.bevmo.com/search?w=whiskey&view=list&srt={page}',
    'still_wines': 'http://shop.bevmo.com/search?w=wine&view=list&srt={page}',
    'gin': 'http://shop.bevmo.com/search?w=gin&view=list&srt={page}',
    'red_wine': 'http://shop.bevmo.com/search?w=red%20wine&view=list&srt={page}',
    'white_wine': 'http://shop.bevmo.com/search?w=white%20wine&view=list&srt={page}',
    'tequila': 'http://shop.bevmo.com/search?w=tequila&view=list&srt={page}',
    'rum': 'http://shop.bevmo.com/search?w=rum&view=list&srt={page}',
    'liquor': 'http://shop.bevmo.com/search?format=varietal&lbc=bevmo&method=and&p=Q&ts=custom&uid=644456520&view=list&w=rum&af=varietal%3aliqueur&srt={page}',
}


# Categories scraping
for ctg, url in urls_ctgs_dict.items():
    categories[ctg] = []
    number_of_pdcts_in_ctg = 0
    for p in range(100):
        print(ctg, p)
        fpath = fpath_namer(shop_id, 'ctg', ctg, p)
        if not op.exists(fpath):
            if not bevmo_was_initialised:
                init_bevmo(driver)
                bevmo_was_initialised = True
            print(url.format(page=32*p))
            driver.get(url.format(page=32*p))
            sleep(1)
            driver.save_page(fpath, scroll_to_bottom=True)

        # Parsing
        tree = etree.parse(BytesIO(open(fpath, 'rb').read()), parser=parser)
        for li in tree.xpath('//ul[contains(@class, "products")]//li[@class="item"]'):
            produrl = "".join(li.xpath('.//h2[contains(@class, "product-name")]/a/@href'))
            produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(
                urlsplit(produrl).query) else produrl
            produrl = clean_url(produrl, root_url)
            products[produrl] = {
                'pdct_name_on_eretailer': " ".join(''.join(li.xpath('.//h2[contains(@class, "product-name")]/a//text()')).split()),
                'raw_price': ''.join(w for t in li.xpath('.//span[contains(@id, "product-price")]//text()') for w in t.split()).strip(),
                'raw_promo_price': ''.join(w for t in li.xpath('.//span[contains(@id, "old-price")]//text()') for w in t.split()).strip(),
                'volume': ' '.join(w for t in li.xpath('.//h2[contains(@class, "product-name")]/a//text()') for w in t.split()).strip(),
            }
            print(products[produrl], produrl)
            products[produrl]['price'] = getprice(products[produrl]['raw_price'])
            products[produrl]['promo_price'] = getprice(products[produrl]['raw_promo_price'])
            categories[ctg].append(produrl)

        if len(set(categories[ctg])) == number_of_pdcts_in_ctg:
            break
        else:
            number_of_pdcts_in_ctg = len(set(categories[ctg]))

print([(ctg, len(val)) for ctg, val in categories.items()])


# KW searches Scraping - with selenium - with nb page hard-coded in url - multiple page per search
search_url = "http://shop.bevmo.com/search?w={kw}&view=list&srt={page}"
for kw in keywords:
    searches[kw] = []
    print(kw)
    fpath = fpath_namer(shop_id, 'search', kw, 0)
    if not op.exists(fpath):
        if not bevmo_was_initialised:
            init_bevmo(driver)
            bevmo_was_initialised = True
        driver.get(search_url.format(kw=kw, page=0))
        sleep(1)
        driver.save_page(fpath, scroll_to_bottom=True)

    # Parsing
    tree = etree.parse(BytesIO(open(fpath, 'rb').read()), parser=parser)
    for li in tree.xpath('//ul[contains(@class, "products")]//li[@class="item"]'):
        produrl = "".join(li.xpath('.//h2[contains(@class, "product-name")]/a/@href'))
        produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(
            urlsplit(produrl).query) else produrl
        produrl = clean_url(produrl, root_url)
        products[produrl] = {
            'pdct_name_on_eretailer': " ".join(
                ''.join(li.xpath('.//h2[contains(@class, "product-name")]/a//text()')).split()),
            'raw_price': ''.join(
                w for t in li.xpath('.//span[contains(@id, "product-price")]//text()') for w in t.split()).strip(),
            'raw_promo_price': ''.join(
                w for t in li.xpath('.//span[contains(@id, "old-price")]//text()') for w in t.split()).strip(),
            'volume': ' '.join(w for t in li.xpath('.//h2[contains(@class, "product-name")]/a//text()') for w in
                              t.split()).strip(),
        }
        print(products[produrl], produrl)
        products[produrl]['price'] = getprice(products[produrl]['raw_price'])
        products[produrl]['promo_price'] = getprice(products[produrl]['raw_promo_price'])
        print(products[produrl], produrl)

        searches[kw].append(produrl)
    print(kw, len(searches[kw]))

# Download the pages - with requests
brm = BrandMatcher()
for url in sorted(list(set(products))):
    d = products[url]
    if brm.find_brand(d['pdct_name_on_eretailer'])['brand'] in mh_brands:
        print(d['pdct_name_on_eretailer'])
        url_mod = clean_url(url, root_url=root_url)
        r = requests.get(url_mod, headers)
        with open('/tmp/' + shop_id + ' ' + d['pdct_name_on_eretailer'].replace('/', "-") + '.html', 'wb') as f:
            f.write(r.content)
        tree = etree.parse(BytesIO(r.content), parser=parser)
        products[url].update({
            'pdct_img_main_url': ''.join(tree.xpath('//img[@id="image-main"]/@src')),
            'ctg_denom_txt': ' '.join(' '.join(tree.xpath('//*[@class="productinfo"]//text()')).split()),
        })
        print(products[url])
        if not r.from_cache:
            sleep(3)


# Download images
for url, pdt in products.items():
     if 'pdct_img_main_url' in pdt and pdt['pdct_img_main_url'] and brm.find_brand(pdt['pdct_name_on_eretailer'])['brand'] in mh_brands:
         print(pdt['pdct_name_on_eretailer'] + "." + pdt['pdct_img_main_url'].split('.')[-1])
         response = requests.get(pdt['pdct_img_main_url'], stream=True, verify=False, headers=headers)
         # response.raw.decode_content = True
         tmp_file_path = '/tmp/' + shop_id + 'mhers_tmp_{}.imgtype'.format(abs(hash(pdt['pdct_img_main_url'])))
         img_path = img_path_namer(shop_id, pdt['pdct_name_on_eretailer'])
         with open(tmp_file_path, 'wb') as out_file:
             shutil.copyfileobj(response.raw, out_file)
         if imghdr.what(tmp_file_path) is not None:
             img_path = img_path.split('.')[0] + '.' + imghdr.what('/tmp/' + shop_id + 'mhers_tmp_{}.imgtype'.format(abs(hash(pdt['pdct_img_main_url']))))
             shutil.copyfile('/tmp/' + shop_id + 'mhers_tmp_{}.imgtype'.format(abs(hash(pdt['pdct_img_main_url']))), img_path)
             products[url].update({'img_path': img_path, 'img_hash': file_hash(img_path)})

create_csvs(products, categories, searches, shop_id, fpath_namer(shop_id, 'raw_csv'), COLLECTION_DATE)
validate_raw_files(fpath_namer(shop_id, 'raw_csv'))
driver.quit()
