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
from custom_browser import CustomDriver


# Init variables and assets
shop_id = 'minibar_delivery'
root_url = "https://minibardelivery.com"
requests_cache.install_cache(fpath_namer(shop_id, 'requests_cache'))
country = 'USA'
searches, categories, products = {}, {}, {}
driver = CustomDriver(headless=False, download_images=True)


def getprice(pricestr):
    if pricestr == '':
        return pricestr
    pricestr = pricestr.replace(',', '').strip()
    price = parse('${dol:d}.{pence:d}', pricestr)
    if price is None:
        price = parse('{pence:d}p', pricestr)
        return price.named['pence']
    else:
        return price.named['dol'] * 100 + price.named['pence']


urls_ctgs_dict = {
    'champagne': 'https://minibardelivery.com/store/category/wine/wine-sparkling',
    'sparkling': 'https://minibardelivery.com/store/category/wine/wine-sparkling',
    'still_wines': 'https://minibardelivery.com/store/category/wine/wine-white',
    'whisky': 'https://minibardelivery.com/store/category/liquor/liquor-scotch',
    'cognac': 'https://minibardelivery.com/store/category/liquor/liquor-brandy',
    'vodka': 'https://minibardelivery.com/store/category/liquor/liquor-vodka',
    'white_wine': 'https://minibardelivery.com/store/category/wine/wine-white',
    'red_wine': 'https://minibardelivery.com/store/category/wine/wine-red',
    'gin': 'https://minibardelivery.com/store/category/liquor/liquor-gin',
    'tequila': 'https://minibardelivery.com/store/category/liquor/liquor-tequila',
    'rum': 'https://minibardelivery.com/store/category/liquor/liquor-rum',
    'brandy': 'https://minibardelivery.com/store/category/liquor/liquor-brandy',
}

def init_minibardelivery(driver):
    print("Initing Minibar")
    driver.get("https://minibardelivery.com/")
    sleep(1)
    driver.waitclick('//*[@id="close_button"]', timeout=15)
    driver.waitclick('//input[@name="addres-input"]')
    driver.text_input('1557 5th Avenue, New York, NY, United States', '//input[@id="addres-input"]', enter=True)
    sleep(1)
    driver.waitclick('//li[@class="cm-ae-dropdown__option"][1]')
    sleep(2)
# init_minibardelivery(driver)
minibardelivery_was_initialised = False

# Categories scraping
for ctg, url in urls_ctgs_dict.items():
    categories[ctg] = []
    fpath = fpath_namer(shop_id, 'ctg', ctg, 0)
    if not op.exists(fpath):
        if not minibardelivery_was_initialised:
            init_minibardelivery(driver)
            minibardelivery_was_initialised = True
        driver.get(url)
        # Get scroll height
        last_height = driver.driver.execute_script("return document.body.scrollHeight")

        while True:
            # Scroll down to bottom
            driver.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            try:
                driver.waitclick('//*[contains(@class, "product-list-load-more")]', timeout=6)
            except: pass
            # Wait to load page
            sleep(2)

            # Calculate new scroll height and compare with last scroll height
            new_height = driver.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        driver.save_page(fpath)
    # Parsing
    tree = etree.parse(BytesIO(open(fpath, 'rb').read()), parser=parser)
    # print(tree.xpath('//text()'))
    for li in tree.xpath('//ul[@id="products"]//li'):
        produrl = "".join(li.xpath('.//a/@href'))
        produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(
            urlsplit(produrl).query) else produrl
        produrl = clean_url(produrl, root_url)
        products[produrl] = {
            'pdct_name_on_eretailer': ''.join(li.xpath('.//h4[contains(@class, "property--name")]//text()')),
            'raw_price': ''.join(w for t in li.xpath('.//h4[@class="grid-product__property grid-product__property--price"]/text()') for w in t.split()).strip(),
            'raw_promo_price': ''.join(w for t in li.xpath('.//*[@class="grid-product__property grid-product__property--discount"]/text()') for w in t.split()).strip(),
            'volume': ''.join(w for t in li.xpath('.//*[@class="grid-product__property--volume__value"]//text()') for w in t.split()).strip(),
        }
        print(products[produrl], produrl)
        products[produrl]['price'] = getprice(products[produrl]['raw_price'])
        products[produrl]['promo_price'] = getprice(products[produrl]['raw_promo_price'])
        print(products[produrl])
        categories[ctg].append(produrl)
print([(ctg, len(val)) for ctg, val in categories.items()])


# KW searches Scraping - with selenium - one page per search
search_url = "https://minibardelivery.com/store/search/{kw}"
for kw in keywords:
    searches[kw] = []
    # Storing and extracting infos
    fpath = fpath_namer(shop_id, 'search', kw, 0)
    if not op.exists(fpath):
        if not minibardelivery_was_initialised:
            init_minibardelivery(driver)
            minibardelivery_was_initialised = True
        driver.get(search_url.format(kw=kw))
        # Get scroll height
        last_height = driver.driver.execute_script("return document.body.scrollHeight")

        while True:
            # Scroll down to bottom
            driver.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            try:driver.waitclick('//a[@id="list-more"]', timeout=3)
            except: pass
            # Wait to load page
            sleep(2)

            # Calculate new scroll height and compare with last scroll height
            new_height = driver.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        driver.save_page(fpath)
    # Parsing
    tree = etree.parse(BytesIO(open(fpath, 'rb').read()), parser=parser)
    # print(tree.xpath('//text()'))
    for li in tree.xpath('//ul[@id="products"]//li'):
        produrl = "".join(li.xpath('.//a/@href'))
        print(produrl)
        produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(
            urlsplit(produrl).query) else produrl
        produrl = clean_url(produrl, root_url)
        products[produrl] = {
            'pdct_name_on_eretailer': ''.join(li.xpath('.//h4[contains(@class, "property--name")]//text()')),
            'raw_price': ''.join(w for t in li.xpath('.//h4[@class="grid-product__property grid-product__property--price"]/text()') for w in t.split()).strip(),
            'raw_promo_price': ''.join(w for t in li.xpath('.//*[@class="grid-product__property grid-product__property--discount"]/text()') for w in t.split()).strip(),
            'volume': ''.join(w for t in li.xpath('.//*[@class="grid-product__property--volume__value"]//text()') for w in t.split()).strip(),
        }
        print(products[produrl], produrl)
        products[produrl]['price'] = getprice(products[produrl]['raw_price'])
        products[produrl]['promo_price'] = getprice(products[produrl]['raw_promo_price'])
        print(products[produrl])
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
            driver.get(url_mod)
            sleep(2)
            driver.save_page(fname, scroll_to_bottom=True)
        tree = etree.parse(open(fname), parser=parser)
        products[url].update({
            'volume': ''.join(tree.xpath('//div[@class="product__description"]//text()')[-1:]).strip(),
            'pdct_img_main_url': ''.join(tree.xpath('//div[contains(@class, "product-image")]//img/@src')),
            'ctg_denom_txt': '',
        })
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
         else:
             print("WARNING : ", tmp_file_path, pdt['pdct_img_main_url'], imghdr.what(tmp_file_path))

create_csvs(products, categories, searches, shop_id, fpath_namer(shop_id, 'raw_csv'), COLLECTION_DATE)
validate_raw_files(fpath_namer(shop_id, 'raw_csv'))
driver.quit()
