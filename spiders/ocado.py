
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
from ers import all_keywords_uk as keywords, fpath_namer, mh_brands, clean_url, headers

from matcher import BrandMatcher
from ers import COLLECTION_DATE, file_hash, img_path_namer
import shutil
from custom_browser import CustomDriver
from parse import parse


# Init variables and assets
shop_id = "ocado"
root_url = "http://www.ocado.com" 
requests_cache.install_cache(fpath_namer(shop_id, 'requests_cache'))
country = "UK"


searches, categories, products = {}, {}, {}
# If necessary
driver = CustomDriver(headless=True)


def getprice(pricestr):
    if pricestr == '':
        return pricestr
    pricestr = re.sub("[^0-9.£p]", "", pricestr)
    price = parse('£{pound:d}.{pence:d}', pricestr)
    if price is None:
        price = parse('{pence:d}p', pricestr)
        return price.named['pence']
    else:
        return price.named['pound'] * 100 + price.named['pence']



urls_ctgs_dict = {
    "vodka": "https://www.ocado.com/webshop/getCategories.do?tags=%7C20000%7C43510%7C43519%7C43649&Asidebar=2", 
        "sparkling": "https://www.ocado.com/webshop/getCategories.do?tags=%7C20000%7C43510%7C43516%7C43601&Asidebar=2",
    "cognac": "https://www.ocado.com/webshop/getSearchProducts.do?clearTabs=yes&isFreshSearch=true&chosenSuggestionPosition=0&entry=cognac", 
    "champagne": "https://www.ocado.com/webshop/getWines.do?tags=%7C20000%7C19980%7C45491&viewAllProducts=true&Awine=2&dnr=y", 
    "still_wines": "https://www.ocado.com/webshop/getCategories.do?tags=%7C20000%7C43510%7C135827&Asidebar=1", 
    "whisky": "https://www.ocado.com/webshop/getCategories.do?tags=%7C20000%7C43510%7C43519%7C43651&Asidebar=1",
    "red_wine": "https://www.ocado.com/webshop/getCategories.do?tags=%7C20000%7C43510%7C135827%7C45710&Asidebar=2",
    "white_wine": "https://www.ocado.com/webshop/getCategories.do?tags=%7C20000%7C43510%7C135827%7C45743&Asidebar=1",
    "gin": "https://www.ocado.com/webshop/getCategories.do?tags=%7C20000%7C43510%7C43519%7C43648&Asidebar=2",
    "tequila": "https://www.ocado.com/webshop/getCategories.do?tags=%7C20000%7C43510%7C43519%7C43648&Asidebar=2",
    "rum": "https://www.ocado.com/webshop/getCategories.do?tags=%7C20000%7C43510%7C43519%7C203897&Asidebar=1",
    "liquor": "https://www.ocado.com/webshop/getCategories.do?tags=%7C20000%7C43510%7C43519%7C203906&Asidebar=1",
    "brandy": "https://www.ocado.com/webshop/getCategories.do?tags=%7C20000%7C43510%7C43519%7C203901%7C203899&Asidebar=1",
}


# Category Scraping
for ctg, url in urls_ctgs_dict.items():
    categories[ctg] = []
    number_of_pdcts_in_ctg = 0

        
    fpath = fpath_namer(shop_id, 'ctg', ctg, 0)
    if not op.exists(fpath):
        driver.get(url)
        sleep(2)
        driver.save_page(fpath, scroll_to_bottom=True)
    tree = etree.parse(BytesIO(open(fpath, 'rb').read()), parser=parser)

    for li in tree.xpath('//div[@class="fop-item"]'):
        if not li.xpath('.//a/@href'):
            continue
        produrl = li.xpath('.//a/@href')[0]
        produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
        produrl = clean_url(produrl, root_url)
        products[produrl] = {
            'pdct_name_on_eretailer': ' '.join(''.join(li.xpath('.//h4[@class="fop-title"]//text()')).split()).strip(),
            'raw_price': ' '.join(''.join(li.xpath('.//*[contains(@class, "fop-price")]//text()')).split()).strip(),
            'raw_promo_price': ' '.join(''.join(li.xpath('.//*[@class="fop-old-price"]//text()')).split()).strip(),
        }
        print(products[produrl], produrl)
        if products[produrl]['raw_price'].lower() != 'out of stock':
            products[produrl]['price'] = getprice(products[produrl]['raw_price'].split("per")[0])
        products[produrl]['promo_price'] = getprice(products[produrl]['raw_promo_price'].split("per")[0])
        print(products[produrl])

        categories[ctg].append(produrl)
print([(c, len(categories[c])) for c in categories])


# KW searches Scraping - with selenium - with nb page hard-coded in url - multiple page per search
search_url = "https://www.ocado.com/webshop/getSearchProducts.do?clearTabs=yes&isFreshSearch=true&chosenSuggestionPosition=0&entry={kw}&viewAllProducts=true"
for kw in keywords:
    searches[kw] = []

    # Storing and extracting infos
    urlp = search_url.format(kw=kw)

    fpath = fpath_namer(shop_id, 'search', kw, 0)
    if not op.exists(fpath):
        driver.get(urlp)
        sleep(2)
        driver.save_page(fpath)
    tree = etree.parse(BytesIO(open(fpath, 'rb').read()), parser=parser)

    for li in tree.xpath('//div[@class="fop-item"]'):
        if not li.xpath('.//a/@href'):
            continue
        produrl = li.xpath('.//a/@href')[0]
        produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
        produrl = clean_url(produrl, root_url)
        products[produrl] = {
            'pdct_name_on_eretailer': ' '.join(''.join(li.xpath('.//h4[@class="fop-title"]//text()')).split()).strip(),
            'raw_price': ' '.join(''.join(li.xpath('.//*[contains(@class, "fop-price")]//text()')).split()).strip(),
            'raw_promo_price': ' '.join(''.join(li.xpath('.//*[@class="fop-old-price"]//text()')).split()).strip(),
        }
        print(products[produrl], produrl)
        if products[produrl]['raw_price'].lower() != 'out of stock':
            products[produrl]['price'] = getprice(products[produrl]['raw_price'].split("per")[0])
        products[produrl]['promo_price'] = getprice(products[produrl]['raw_promo_price'].split("per")[0])
        print(products[produrl])

        searches[kw].append(produrl)
    print(kw, 0, len(searches[kw]))


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
            'volume': ' '.join(''.join(tree.xpath('//h1[contains(@class, "productTitle")]//text()')).strip().split()),
            'pdct_img_main_url': clean_url(''.join(tree.xpath('//*[@id="zoomedImage"]/div/img/@src')), root_url),
            'ctg_denom_txt': ' '.join(' '.join(tree.xpath('//ul[@class="categories"]//text()')).split()),
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
