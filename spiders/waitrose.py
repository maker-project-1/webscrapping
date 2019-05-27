import os.path as op
import re
from io import BytesIO

from lxml import etree

parser = etree.HTMLParser(encoding='utf-8')
from time import sleep
from urllib.parse import urlsplit, parse_qs
import requests
import requests_cache, imghdr
from parse import parse
from validators import validate_raw_files
from create_csvs import create_csvs


from ers import all_keywords_uk as keywords
from ers import fpath_namer, mh_brands, clean_url, headers
from matcher import BrandMatcher
from ers import COLLECTION_DATE, file_hash, img_path_namer
import shutil
from custom_browser import CustomDriver


# Init variables and assets
shop_id = 'waitrose'
root_url = 'https://www.waitrose.com'
requests_cache.install_cache(fpath_namer(shop_id, 'requests_cache'))
country = 'UK'
searches, categories, products = {}, {}, {}
driver = CustomDriver(headless=False, download_images=False)


def getprice(pricestr):
    if pricestr == '':
        return None
    pricestr = pricestr.replace('Itemprice', '')
    pricestr = re.sub("[^0-9.£p]", "", pricestr)
    price = parse('£{pound:d}.{pence:d}', pricestr)
    if price is None:
        price = parse('{pence:d}p', pricestr)
        print("?? price", pricestr)
        return price.named['pence']
    else:
        return price.named['pound'] * 100 + price.named['pence']


urls_ctgs_dict = {
	'champagne' : 'https://www.waitrose.com/ecom/shop/Browse/Groceries/Beer_Wine_and_Spirits/Champagne_and_Sparkling_Wine/Champagne',
	'whisky' : 'https://www.waitrose.com/ecom/shop/browse/groceries/beer_wine_and_spirits/spirits_and_liqueurs/whisky/scottish_whisky/malt_whisky',
	'cognac' : 'https://www.waitrose.com/ecom/shop/browse/groceries/beer_wine_and_spirits/spirits_and_liqueurs/cognac',
	'vodka' : 'https://www.waitrose.com/ecom/shop/browse/groceries/beer_wine_and_spirits/spirits_and_liqueurs/vodka',
	'sparkling' : 'https://www.waitrose.com/ecom/shop/browse/groceries/beer_wine_and_spirits/champagne_and_sparkling_wine/sparkling_wine',
	'still_wines' : 'https://www.waitrose.com/ecom/shop/browse/groceries/beer_wine_and_spirits/wine',
    'red_wine': 'https://www.waitrose.com/ecom/shop/browse/groceries/beer_wine_and_spirits/wine/red_wine',
    'white_wine': 'https://www.waitrose.com/ecom/shop/browse/groceries/beer_wine_and_spirits/wine/white_wine',
    'gin': 'https://www.waitrose.com/ecom/shop/browse/groceries/beer_wine_and_spirits/spirits_and_liqueurs/gin',
    'tequila': 'https://www.waitrose.com/ecom/shop/browse/groceries/beer_wine_and_spirits/spirits_and_liqueurs/tequila',
    'rum': 'https://www.waitrose.com/ecom/shop/browse/groceries/beer_wine_and_spirits/spirits_and_liqueurs/rum',
    'liquor': 'https://www.waitrose.com/ecom/shop/browse/groceries/beer_wine_and_spirits/spirits_and_liqueurs/liqueurs_and_aperitifs',
    'brandy': 'https://www.waitrose.com/ecom/shop/browse/groceries/beer_wine_and_spirits/spirits_and_liqueurs/brandy',
}

# Category Scraping - with selenium - one page per category
for ctg, url in urls_ctgs_dict.items():
    count = 1
    categories[ctg] = []
    fpath = fpath_namer(shop_id, 'ctg', ctg, 0)
    if not op.exists(fpath):
        driver.get(url)
        driver.waitclick('//*[@class="closeNoticeSomethingDifferentPopup"]', timeout=4)
        last_height = driver.driver.execute_script("return document.body.scrollHeight")
        while True:
            sleep(1)
            driver.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            driver.waitclick('//*[@data-actiontype="load"]', timeout=3)
            driver.waitclick('//*[@data-actiontype="load"]', timeout=0.5)
            new_height = driver.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        driver.save_page(fpath, scroll_to_bottom=True)
    tree = etree.parse(BytesIO(open(fpath, 'rb').read()), parser=parser)
    for li in tree.xpath('//article[@data-test="product-pod"]'):
        produrl = clean_url(li.xpath('.//a[h2]/@href')[0], root_url)
        produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(
            urlsplit(produrl).query) else produrl
        products[produrl] = {
            'pdct_name_on_eretailer': ' '.join(li.xpath('.//h2//text()')),
            'raw_price': ''.join(w for t in li.xpath('.//span[@data-test="product-pod-price"]//text()') for w in t.split()).strip(),
            'raw_promo_price': ''.join(w for t in li.xpath('.//em[@data-test="was-price"]/text()')[:1] for w in t.split()).strip(),
            'volume': ''.join(w for t in li.xpath('.//span[contains(@class, "sizeMessage")]//text()')[:1] for w in t.split()).strip(),
        }
        print(products[produrl])
        products[produrl]['price'] = getprice(products[produrl]['raw_price'])
        products[produrl]['promo_price'] = getprice(products[produrl]['raw_promo_price'])
        categories[ctg].append(produrl)
        print(ctg, count, products[produrl], produrl)
        count += 1

print([(c, len(categories[c])) for c in categories])


# KW searches Scraping - with selenium - one page per search
search_url = "https://www.waitrose.com/ecom/shop/search?&searchTerm={kw}"
for kw in keywords:
    searches[kw] = []
    # Storing and extracting infos
    fpath = fpath_namer(shop_id, 'search', kw, 0)
    url = search_url.format(kw=kw, page=0)
    if not op.exists(fpath):
        driver.get(url)
        driver.waitclick('//*[@class="closeNoticeSomethingDifferentPopup"]', timeout=4)
        last_height = driver.driver.execute_script("return document.body.scrollHeight")
        while True:
            sleep(1)
            driver.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            driver.wait_for_xpath('//*[@data-actiontype="load"]', timeout=4, is_enabled=True)
            driver.waitclick('//*[@data-actiontype="load"]', timeout=2)
            new_height = driver.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        driver.save_page(fpath, scroll_to_bottom=True)

    tree = etree.parse(BytesIO(open(fpath, 'rb').read()), parser=parser)
    for li in tree.xpath('//article[@data-test="product-pod"]'):
        produrl = clean_url(li.xpath('.//a[h2]/@href')[0], root_url)
        produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(
            urlsplit(produrl).query) else produrl
        products[produrl] = {
            'pdct_name_on_eretailer': ' '.join(li.xpath('.//h2//text()')),
            'raw_price': ''.join(w for t in li.xpath('.//span[@data-test="product-pod-price"]//text()') for w in t.split()).strip(),
            'raw_promo_price': ''.join(w for t in li.xpath('.//*[@data-test="was-price"]/text()')[:1] for w in t.split()).strip(),
            'volume': ''.join(w for t in li.xpath('.//span[contains(@class, "sizeMessage")]//text()') for w in t.split()).strip(),
        }
        print(products[produrl])
        products[produrl]['price'] = getprice(products[produrl]['raw_price'])
        products[produrl]['promo_price'] = getprice(products[produrl]['raw_promo_price'])
        searches[kw].append(produrl)
    print(kw, len(searches[kw]))


# Download the pages - with selenium
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
            'pdct_img_main_url': ''.join(tree.xpath('//section[contains(@class, "productImage")]//picture//img/@src')),
            'ctg_denom_txt': ' '.join(tree.xpath('//nav[contains(@class, "breadcrumbs")]//text()')),
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
