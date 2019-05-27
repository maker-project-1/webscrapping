

import os.path as op
import re
from io import BytesIO

from lxml import etree

parser = etree.HTMLParser(encoding='utf-8')
from time import sleep
from urllib.parse import urlsplit, parse_qs
import requests
from validators import validate_raw_files
from create_csvs import create_csvs
import requests_cache, imghdr
from ers import all_keywords_usa as keywords, fpath_namer, mh_brands, clean_url, headers

from matcher import BrandMatcher
from ers import COLLECTION_DATE, file_hash, img_path_namer
import shutil
from custom_browser import CustomDriver
from parse import parse


# Init variables and assets
shop_id = "mission_liquor"
root_url = "https://www.missionliquor.com/" 
requests_cache.install_cache(fpath_namer(shop_id, 'requests_cache'))
country = "USA"


searches, categories, products = {}, {}, {}
# If necessary
driver = CustomDriver(headless=True)


def getprice(pricestr):
    if pricestr == '':
        return pricestr
    pricestr = re.sub("[^0-9.$]", "", pricestr)
    price = parse('${pound:d}.{pence:d}', pricestr)
    if price is None:
        price = parse('{pence:d}p', pricestr)
        return price.named['pence']
    else:
        return price.named['pound'] * 100 + price.named['pence']


urls_ctgs_dict = {
    "vodka": "https://www.missionliquor.com/category/vodka/1384?reset_filter_option=1&page_limit=all&order=best_seller&method=asc",
    "sparkling": "https://www.missionliquor.com/category/wines/1000?add_filter_option=1017&page_limit=all&order=best_seller&method=asc",
    "cognac": "https://www.missionliquor.com/category/cognac/1376?reset_filter_option=1&page_limit=all&order=best_seller&method=asc",
    "champagne": "https://www.missionliquor.com/category/wines/1000?add_filter_option=1262&page_limit=all&order=best_seller&method=asc",
    "still_wines": "https://www.missionliquor.com/category/1000/wines?page_limit=all&order=best_seller&method=asc",
    "whisky": "https://www.missionliquor.com/category/whiskey/1385?reset_filter_option=1&page_limit=all&order=best_seller&method=asc",
    "gin": "https://www.missionliquor.com/category/gin/1377?reset_filter_option=1&page_limit=all&order=best_seller&method=asc",
    "tequila": "https://www.missionliquor.com/category/tequila/1383?reset_filter_option=1&page_limit=all&order=best_seller&method=asc",
    "rum": "https://www.missionliquor.com/category/rum/1382?reset_filter_option=1&page_limit=all&order=best_seller&method=asc",
    "brandy": "https://www.missionliquor.com/category/brandy/1938?reset_filter_option=1&page_limit=all&order=best_seller&method=asc",
    "red_wine": "https://www.missionliquor.com/category/wines/1000?reset_filter_option=1&page_limit=all&order=best_seller&method=asc",
    "white_wine": "https://www.missionliquor.com/category/wines/1000?reset_filter_option=1&page_limit=all&order=best_seller&method=asc",
}


# Category Scraping
for ctg, url in urls_ctgs_dict.items():
    categories[ctg] = []
    number_of_pdcts_in_ctg = 0
    for p in range(1):
        fpath = fpath_namer(shop_id, 'ctg', ctg, p)
        if not op.exists(fpath):
            driver.get(url)
            sleep(2)
            driver.save_page(fpath)
        tree = etree.parse(BytesIO(open(fpath, 'rb').read()), parser=parser)

        for li in tree.xpath('//*[@id="catalog_category"]//div[@class="main-prd-box"]'):
            produrl = li.xpath('.//center/a/@href')[0]
            produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
            produrl = clean_url(produrl, root_url)
            products[produrl] = {
                'pdct_name_on_eretailer': ' '.join(''.join(li.xpath('.//div[@id="catalog_item_title"]//text()')).split()).strip(),
                'raw_price': ' '.join(''.join(li.xpath('.//span[contains(@class, "price")]//text()')).split()).strip(),
                'raw_promo_price': ' '.join(''.join(li.xpath('.//span[contains(@class, "price")]/dsd//text()')).split()).strip(),
            }
            print(products[produrl], produrl)
            products[produrl]['price'] = getprice(products[produrl]['raw_price'])
            products[produrl]['promo_price'] = getprice(products[produrl]['raw_promo_price'])
            print(products[produrl])
            
            categories[ctg].append(produrl)

        # # Checking if it was the last page
        # if len(set(categories[ctg])) == number_of_pdcts_in_ctg:
        #     break
        # else:
        #     number_of_pdcts_in_ctg = len(set(categories[ctg]))
print([(c, len(categories[c])) for c in categories])




# KW searches Scraping - with selenium - with nb page hard-coded in url - multiple page per search
search_url = "https://www.missionliquor.com/search?q={kw}&page_limit=100&order=best_seller&method=asc"
for kw in keywords:
    print("KW = ", kw)
    searches[kw] = []
    number_of_pdcts_in_kw_search = 0
    
    for p in range(10):
        # Storing and extracting infos
        urlp = search_url.format(kw=kw,page=p)
        
        fpath = fpath_namer(shop_id, 'search', kw, p)
        if not op.exists(fpath):
            driver.get(urlp)
            sleep(2)
            driver.save_page(fpath)
        tree = etree.parse(BytesIO(open(fpath, 'rb').read()), parser=parser)

        for li in tree.xpath('//*[@id="catalog_category"]//div[@class="main-prd-box"]'):
            produrl = li.xpath('.//center/a/@href')[0]
            produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
            produrl = clean_url(produrl, root_url)
            products[produrl] = {
                'pdct_name_on_eretailer': ' '.join(''.join(li.xpath('.//div[@id="catalog_item_title"]//text()')).split()).strip(),
                'raw_price': ' '.join(''.join(li.xpath('.//span[contains(@class, "price")]//text()')).split()).strip(),
                'raw_promo_price': ' '.join(''.join(li.xpath('.//span[contains(@class, "price")]/dsd//text()')).split()).strip(),
            }
            print(products[produrl], produrl)
            products[produrl]['price'] = getprice(products[produrl]['raw_price'])
            products[produrl]['promo_price'] = getprice(products[produrl]['raw_promo_price'])
            print(products[produrl])
            
            searches[kw].append(produrl)
        if len(set(searches[kw])) == number_of_pdcts_in_kw_search:
            break
        else:
            number_of_pdcts_in_kw_search = len(set(searches[kw]))
    print(kw, p, len(searches[kw]))


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
            'volume': ''.join(tree.xpath('//*[@id="product_page_title"]/h1//text()')).strip(),
            'pdct_img_main_url': clean_url(''.join(tree.xpath('//*[@id="Main_image_file"]/@src')), root_url),
            'ctg_denom_txt': ' '.join(' '.join(tree.xpath('//*[@id="breadcrumb"]//text()')).split()),
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
