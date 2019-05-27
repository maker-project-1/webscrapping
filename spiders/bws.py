import os.path as op
from io import BytesIO

from lxml import etree

parser = etree.HTMLParser()
from time import sleep
from urllib.parse import urlsplit, parse_qs
import re
import requests
import requests_cache, imghdr

from validators import validate_raw_files
from create_csvs import create_csvs
from ers import all_keywords_aus as keywords, fpath_namer, mh_brands, clean_url, headers
from custom_browser import CustomDriver
from matcher import BrandMatcher
from ers import COLLECTION_DATE, file_hash, img_path_namer
import shutil

from parse import parse

# Init variables and assets
shop_id = 'bws'
root_url = 'https://bws.com.au'
requests_cache.install_cache(fpath_namer(shop_id, 'requests_cache'))
country = 'AUS'
searches, categories, products = {}, {}, {}
driver = CustomDriver(headless=True)


def getprice(pricestr):
    pricestr = re.sub("[^0-9.$]", "", pricestr)
    if pricestr == '':
        return pricestr
    price = parse('${pound:d}', pricestr)
    return price.named['pound'] * 100


# Download categories
urls_ctgs_dict = {
    'champagne': 'https://bws.com.au/wine/champagne-sparkling/champagne',
    'sparkling': 'https://bws.com.au/wine/champagne-sparkling/sparkling-wine/sparkling-whites',
    'still_wines': 'https://bws.com.au/wine/white-wine',
    'whisky': 'https://bws.com.au/spirits/whisky',
    'cognac': 'https://bws.com.au/spirits/brandy-cognac',
    'vodka': 'https://bws.com.au/spirits/vodka',
    'gin': 'https://bws.com.au/spirits/gin',
    'tequila': 'https://bws.com.au/spirits/tequila',
    'white_wine': 'https://bws.com.au/wine/white-wine',
    'red_wine': 'https://bws.com.au/wine/red-wine',
    'rum': 'https://bws.com.au/spirits/rum',
    'bourbon': 'https://bws.com.au/spirits/bourbon',
    'liquor': 'https://bws.com.au/spirits/liqueurs',
}

# Simple case, where the page is hard-coded in the url
for ctg, url in urls_ctgs_dict.items():
    categories[ctg] = []
    fpath = fpath_namer(shop_id, 'ctg', ctg, 0)
    if not op.exists(fpath):
        driver.get(url)
        sleep(2)
        driver.save_page(fpath, scroll_to_bottom=True)
    tree = etree.parse(BytesIO(open(fpath, 'rb').read()), parser=parser)
    for li in tree.xpath('id("center-panel")//bws-category//wow-card-list//div[contains(@class,"card-list-item") and not(.//wow-inspiration-card)]'):
        produrl = li.xpath('.//a/@href')[0]
        print(produrl)
        produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
        categories[ctg].append(produrl)
        products[produrl] = {
            'pdct_name_on_eretailer':  " ".join("".join(li.xpath('.//*[@class="productTile_brandAndName"]//text()')).split()),
            'raw_price':  "$" + " ".join("".join(li.xpath('.//*[contains(@class, "productTile_priceDollars")]//text()')).split()),
        }
        products[produrl]['price'] = getprice(products[produrl]['raw_price'])
print([(c, len(categories[c])) for c in categories])

# Easy case, where you scroll down to get the whole page
search_url = "https://bws.com.au/search?searchTerm={kw}&pageNumber={page}"
for kw in keywords:
    print(kw)
    searches[kw] = []
    # Storing and extracting infos
    fpath = fpath_namer(shop_id, 'search', kw, 0)
    url = search_url.format(kw=kw, page=0)
    if not op.exists(fpath):
        driver.get(url)
        sleep(2)
        driver.save_page(fpath, scroll_to_bottom=True)
    tree = etree.parse(BytesIO(open(fpath, 'rb').read()), parser=parser)
    for li in tree.xpath('id("center-panel")//wow-card[not(.//wow-inspiration-card)]'):
        produrl = li.xpath('.//a/@href')[0]
        print(produrl)
        produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
        searches[kw].append(produrl)
        products[produrl] = {
            'pdct_name_on_eretailer':  " ".join("".join(li.xpath('.//*[@class="productTile_brandAndName"]//text()')).split()),
            'raw_price':  "$" + " ".join("".join(li.xpath('.//*[contains(@class, "productTile_priceDollars")]//text()')).split()),
        }
        print(products[produrl])
        products[produrl]['price'] = getprice(products[produrl]['raw_price'])
        print(products[produrl])

# Download the pages
brm = BrandMatcher()
for url in sorted(products):
    d = products[url]
    # print(url, find_brand(d['pdct_name_on_eretailer'])['brand'])
    if brm.find_brand(d['pdct_name_on_eretailer'])['brand'] in mh_brands:
        url_mod = clean_url(url, root_url=root_url)
        fpath = fpath_namer(shop_id, 'pdct', d['pdct_name_on_eretailer'], 0)
        if not op.exists(fpath):
            driver.get(url_mod)
            sleep(3)
            driver.save_page(fpath)
        tree = etree.parse(BytesIO(open(fpath, 'rb').read()), parser=parser)
        products[url].update({
            'volume': " ".join(''.join(tree.xpath('//li[@class="list--details_item clearfix ng-scope" and contains(strong, "Liquor Size")]/span/text()')).split()),
            'raw_promo_price': ''.join(tree.xpath('//div[@class="prices"]/s//text()')),
            'pdct_img_main_url': ''.join(tree.xpath('//img[@class="product-image"]/@src')),
            'ctg_denom_txt': " ".join(''.join(tree.xpath('//div[@expandable-content="product-additional-details"]//text()')).split()),
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

create_csvs(products, categories, searches, shop_id, fpath_namer(shop_id, 'raw_csv'), COLLECTION_DATE)
validate_raw_files(fpath_namer(shop_id, 'raw_csv'))
driver.quit()