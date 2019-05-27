import os.path as op
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
from matcher import BrandMatcher
from ers import COLLECTION_DATE, file_hash, img_path_namer
import shutil
from parse import parse
import re
from custom_browser import CustomDriver
from selenium.webdriver.common.keys import Keys

# Init variables and assets
shop_id = 'saucey'
root_url = "https://www.saucey.com/"
requests_cache.install_cache(fpath_namer(shop_id, 'requests_cache'))
country = 'USA'
searches, categories, products = {}, {}, {}
driver = CustomDriver(headless=True, download_images=True)


def getprice(pricestr):
    if "$" not in pricestr:
        return ''
    pricestr = re.sub("[^0-9.$]", "", pricestr.lower())
    price = parse('${dol:d}.{pence:d}', pricestr)
    print(pricestr)
    if price is None:
        price = parse('{pence:d}p', pricestr)
        return price.named['pence']
    else:
        return price.named['dol'] * 100 + price.named['pence']


urls_ctgs_dict = {
    'champagne': 'https://www.saucey.com/champagne-sparkling?skip={page}',
    'sparkling': 'https://www.saucey.com/champagne-sparkling?skip={page}',
    'still_wines': 'https://www.saucey.com/white-wine?varietal=sauvignon%20blanc&skip={page}',
    'whisky': 'https://www.saucey.com/whiskey?skip={page}',
    'cognac': 'https://www.saucey.com/cordials?style=brandy&skip={page}',
    'vodka': 'https://www.saucey.com/vodka?skip={page}',
    'gin': 'https://www.saucey.com/gin?skip={page}',
    'red_wine': 'https://www.saucey.com/red-wine?skip={page}',
    'white_wine': 'https://www.saucey.com/white-wine?skip={page}',
    'tequila': 'https://www.saucey.com/tequila?skip={page}',
    'rum': 'https://www.saucey.com/rum?skip={page}',
    'bourbon': 'https://www.saucey.com/bourbon-whiskey?skip={page}'

}

def init_saucey(driver):
    driver.get("https://www.saucey.com/")
    sleep(1)
    driver.text_input('1557 5th Avenue, New York, NY, United States', '//input[@id="address-input"]', enter=False)
    driver.driver.find_element_by_xpath('//input[@id="address-input"]').send_keys(Keys.ARROW_DOWN)
    sleep(1)
    driver.text_input('', '//input[@id="address-input"]', enter=True)
    sleep(2)

saucey_was_initialised = False


# Categories scraping
for ctg, url in urls_ctgs_dict.items():
    categories[ctg] = []
    number_of_pdcts_in_ctg = 0
    for p in range(10):
        print(ctg, p)
        fpath = fpath_namer(shop_id, 'ctg', ctg, p)
        if not op.exists(fpath):
            if not saucey_was_initialised:
                init_saucey(driver)
                saucey_was_initialised = True
            driver.get(url.format(page=p*60))
            driver.wait_for_xpath('//*[@itemtype="http://schema.org/Product"]', timeout=10)
            driver.smooth_scroll(sleep_time=0.3)
            driver.save_page(fpath, scroll_to_bottom=True)
        # Parsing
        tree = etree.parse(BytesIO(open(fpath, 'rb').read()), parser=parser)
        for li in tree.xpath('//*[@itemtype="http://schema.org/Product"]'):
            produrl = "".join(li.xpath('.//a[@itemprop="url"]/@href'))
            produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(
                urlsplit(produrl).query) else produrl
            produrl = clean_url(produrl, root_url)
            products[produrl] = {
                'pdct_name_on_eretailer': " ".join(''.join(li.xpath('.//*[@itemprop="name"]//text()')).split()),
                'raw_price': ' '.join(w for t in li.xpath('.//*[@class="text-overflow"]//text()') for w in t.split()),
                'volume': ' '.join(w for t in li.xpath('.//*[@class="text-overflow"]//text()') for w in t.split()).strip(),
            }
            print(products[produrl], produrl)
            products[produrl]['price'] = getprice("".join(products[produrl]['raw_price'].split('|')[1:]))
            products[produrl]['pdct_name_on_eretailer'] += ''.join(products[produrl]['volume'].split('|')[:1])
            print(products[produrl], produrl)
            categories[ctg].append(produrl)
        if len(set(categories[ctg])) == number_of_pdcts_in_ctg:
            break
        else:
            number_of_pdcts_in_ctg = len(set(categories[ctg]))
print([(ctg, len(val)) for ctg, val in categories.items()])


# KW searches Scraping - with selenium - with nb page hard-coded in url - multiple page per search
search_url = "https://www.saucey.com/search/{kw}"
for kw in keywords:
    searches[kw] = []
    number_of_pdcts_in_kw_search = 0
    print(kw)
    fpath = fpath_namer(shop_id, 'search', kw, 0)
    if not op.exists(fpath):
        if not saucey_was_initialised:
            init_saucey(driver)
            saucey_was_initialised = True
        driver.get(search_url.format(kw=kw))
        driver.wait_for_xpath('//*[@itemtype="http://schema.org/Product"]', timeout=10)
        driver.smooth_scroll(sleep_time=0.3)
        driver.save_page(fpath, scroll_to_bottom=True)
    # Parsing
    tree = etree.parse(BytesIO(open(fpath, 'rb').read()), parser=parser)
    for li in tree.xpath('//*[@itemtype="http://schema.org/Product"]'):
        produrl = "".join(li.xpath('.//a[@itemprop="url"]/@href'))
        produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(
            urlsplit(produrl).query) else produrl
        produrl = clean_url(produrl, root_url)
        products[produrl] = {
            'pdct_name_on_eretailer': " ".join(''.join(li.xpath('.//*[@itemprop="name"]//text()')).split()),
            'raw_price': ' '.join(w for t in li.xpath('.//*[@class="text-overflow"]//text()') for w in t.split()),
            'volume': ' '.join(w for t in li.xpath('.//*[@class="text-overflow"]//text()') for w in t.split()).strip(),
        }
        print(products[produrl], produrl)
        products[produrl]['price'] = getprice("".join(products[produrl]['raw_price'].split('|')[1:]))
        products[produrl]['pdct_name_on_eretailer'] += ''.join(products[produrl]['volume'].split('|')[:1])
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
        fname = fpath_namer(shop_id, 'pdct', d['pdct_name_on_eretailer'], 0)
        if not op.exists(fname):
            if not saucey_was_initialised:
                init_saucey(driver)
                saucey_was_initialised = True
            driver.get(url_mod)
            sleep(1)
            driver.save_page(fname, scroll_to_bottom=True)
        tree = etree.parse(open(fname), parser=parser)
        products[url].update({
            # 'raw_price': ' '.join(w for t in tree.xpath('//div[@class="radio-list"]/div[1]//div[@class="radio-list__label"]/span[last()]//text()') for w in t.split()),
            'raw_promo_price': ''.join(tree.xpath('//div[@class="radio-list"]/div[1]//*[@class="text-light strikethrough"]//text()')),
            'pdct_img_main_url': ''.join(tree.xpath('//img[@class="product-page__img"]/@src')),
            'ctg_denom_txt': d['pdct_name_on_eretailer'],
        })
        print(products[url])
        products[produrl]['price'] = getprice("".join(products[produrl]['raw_price'].split('|')[1:]))
        products[url]['promo_price'] = getprice(products[url]['raw_promo_price'])
        print(products[url])


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
