import os.path as op
import re
import shutil
from urllib.parse import urlsplit, parse_qs

import imghdr
import requests
import requests_cache
from lxml import etree
from parse import parse

from create_csvs import create_csvs
from custom_browser import CustomDriver
from ers import COLLECTION_DATE, file_hash, img_path_namer
from ers import all_keywords_fr as keywords, TEST_PAGES_FOLDER_PATH
from ers import clean_xpathd_text
from ers import fpath_namer, mh_brands, clean_url, headers
from matcher import BrandMatcher
from validators import validate_raw_files

parser = etree.HTMLParser()


# Init variables and assets
shop_id = 'gourmondo'
root_url = 'https://www.gourmondo.de'
requests_cache.install_cache(fpath_namer(shop_id, 'requests_cache'))
country = 'DE'
searches, categories, products = {}, {}, {}
driver = CustomDriver(headless=True, download_images=True)


def getprice(pricestr):
    pricestr = re.sub("[^0-9.€,]", "", pricestr)
    if pricestr.endswith('*'):
        pricestr = pricestr[:-1]
    if not pricestr:
        return
    price = parse('{pound:d}€', pricestr)
    if price:
        return price.named['pound'] * 100
    price = parse('{pound:d},{pence:d}€', pricestr)
    if price:
        return price.named['pound'] * 100 + price.named['pence']
    price = parse('{th:d}.{pound:d}€', pricestr)
    if price:
        return price.named['th'] * 100000 + price.named['pound'] * 100
    price = parse('{th:d}.{pound:d},{pence:d}€', pricestr)
    if price:
        return price.named['th'] * 100000 + price.named['pound'] * 100 + price.named['pence']
    price = parse('{pound:d},{pence:d}', pricestr)
    if price:
        return price.named['pound'] * 100 + price.named['pence']
    print('pb price', pricestr)
    raise Exception


###################
# # CTG page xpathing #
###################
exple_ctg_page_path = op.join(TEST_PAGES_FOLDER_PATH, shop_id, 'ctg_page_test.html')  # TODO : store the file
ctg, test_categories, test_products = '', {'': []}, {}


def ctg_parsing(fpath, ctg, categories, products):  # TODO : modify xpaths
    tree = etree.parse(open(fpath, 'rb'), parser=parser)
    for li in tree.xpath('//div[@class="product"]'):
        if not li.xpath('(./div/a/@href)[1]'):
            continue
        produrl = li.xpath('(./div/a/@href)[1]')[0]
        produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
        products[produrl] = {
            'pdct_name_on_eretailer': clean_xpathd_text(li.xpath('.//h4/@title')),
            'raw_price': clean_xpathd_text(li.xpath('.//div[@class="price"]/p[2]//text()')),
            'raw_promo_price': clean_xpathd_text(li.xpath('.//div[@class="price"]/p[1]//text()')),
            'volume': clean_xpathd_text(li.xpath('.//span[@class="total-weight"]//text()')),
            'pdct_img_main_url': "".join(li.xpath('.//img[@itemprop="contentUrl"]/@src')[:1]),
        }
        print(products[produrl], produrl)
        products[produrl]['price'] = getprice(products[produrl]['raw_price'])
        products[produrl]['promo_price'] = getprice(products[produrl]['raw_promo_price'])
        products[produrl]['pdct_img_main_url'] = clean_url(products[produrl]['pdct_img_main_url'].replace('w_107/h_125', 'w_305/h_376'), root_url)
        print(products[produrl])

        categories[ctg].append(produrl)
    return categories, products


ctg_parsing(exple_ctg_page_path, ctg, test_categories, test_products)

###################
# # KW page xpathing #
###################

exple_kw_page_path = op.join(TEST_PAGES_FOLDER_PATH, shop_id, 'kw_page_test.html') # TODO : store the file
kw, test_searches, test_products = '', {'': []}, {}


def kw_parsing(fpath, kw, searches, products):  # TODO : modify xpaths
    tree = etree.parse(open(fpath, 'rb'), parser=parser)
    for li in tree.xpath('//div[@class="product"]'):
        if not li.xpath('(./div/a/@href)[1]'):
            continue
        produrl = li.xpath('(./div/a/@href)[1]')[0]
        produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
        products[produrl] = {
            'pdct_name_on_eretailer': clean_xpathd_text(li.xpath('.//h4/@title')),
            'raw_price': clean_xpathd_text(li.xpath('.//div[@class="price"]/p[2]//text()')),
            'raw_promo_price': clean_xpathd_text(li.xpath('.//div[@class="price"]/p[1]//text()')),
            'volume': clean_xpathd_text(li.xpath('.//span[@class="total-weight"]//text()')),
            'pdct_img_main_url': "".join(li.xpath('.//img[@itemprop="contentUrl"]/@src')[:1]),
        }
        print(products[produrl], produrl)
        products[produrl]['price'] = getprice(products[produrl]['raw_price'])
        products[produrl]['promo_price'] = getprice(products[produrl]['raw_promo_price'])
        products[produrl]['pdct_img_main_url'] = clean_url(products[produrl]['pdct_img_main_url'].replace('w_107/h_125', 'w_305/h_376'), root_url)
        print(products[produrl])

        searches[kw].append(produrl)
    return searches, products


kw_parsing(exple_kw_page_path, kw, test_searches, test_products)


###################
# # CTG scrapping #
###################

urls_ctgs_dict = {
    'champagne': 'https://www.gourmondo.de/champagner-schaumwein/champagner#pageNumber={page}&sortOption=topseller&pageSize=100',
    'cognac': 'https://www.gourmondo.de/spirituosen/cognac-brandy#pageNumber={page}&sortOption=topseller&pageSize=100',
    'sparkling': 'https://www.gourmondo.de/champagner-schaumwein/champagner#pageNumber={page}&sortOption=topseller&pageSize=100',
    'vodka': 'https://www.gourmondo.de/spirituosen/wodka#pageNumber={page}&sortOption=topseller&pageSize=100',
    'whisky': 'https://www.gourmondo.de/spirituosen/whisky#pageNumber={page}&sortOption=topseller&pageSize=100',
    'still_wines': 'https://www.gourmondo.de/wein/weisswein#pageNumber={page}&sortOption=topseller&pageSize=100',
    'white_wine': 'https://www.gourmondo.de/wein/weisswein#pageNumber={page}&sortOption=topseller&pageSize=100',
    'red_wine': 'https://www.gourmondo.de/wein/rotwein#pageNumber={page}&sortOption=topseller&pageSize=100',
    'gin': 'https://www.gourmondo.de/spirituosen/gin#pageNumber={page}&sortOption=topseller&pageSize=100',
    'rum': 'https://www.gourmondo.de/spirituosen/rum#pageNumber={page}&sortOption=topseller&pageSize=100',
    'tequila': 'https://www.gourmondo.de/spirituosen/tequila-mezcal#pageNumber={page}&sortOption=topseller&pageSize=100',
    'liquor': 'https://www.gourmondo.de/spirituosen/likoere#pageNumber={page}&sortOption=topseller&pageSize=100',
}


# Category Scraping
for ctg, url in urls_ctgs_dict.items():
    categories[ctg] = []
    number_of_pdcts_in_ctg = 0

    for p in range(100):
        fpath = fpath_namer(shop_id, 'ctg', ctg, p)

        if not op.exists(fpath):
            driver.get(url.format(page=p+1))
            driver.smooth_scroll()
            driver.save_page(fpath)
        categories, products = ctg_parsing(fpath, ctg, categories, products)

        if len(set(categories[ctg])) == number_of_pdcts_in_ctg:
            break
        else:
            number_of_pdcts_in_ctg = len(set(categories[ctg]))
    print(ctg, url, p, len(categories[ctg]))


######################################
# # KW searches scrapping ############
######################################

# KW searches Scraping - with requests - one page per search
kw_search_url = "https://www.gourmondo.de/search/?text={kw}#pageNumber=1&sortOption=topseller&pageSize=100"  # TODO : modify URL
for kw in keywords:
    searches[kw] = []
    fpath = fpath_namer(shop_id, 'search', kw, 0)
    if not op.exists(fpath):
        driver.get(kw_search_url.format(kw=kw))
        driver.smooth_scroll()
        driver.save_page(fpath, scroll_to_bottom=True)
    searches, products = kw_parsing(fpath, kw, searches, products)
    print(kw, len(searches[kw]))


######################################
# # Download images        ###########
######################################
brm = BrandMatcher()
for url, pdt in products.items():
    if 'pdct_img_main_url' in pdt and pdt['pdct_img_main_url'] and \
            brm.find_brand(pdt['pdct_name_on_eretailer'], special_country='JP')['brand'] in mh_brands:
        print(pdt['pdct_name_on_eretailer'] + "." + pdt['pdct_img_main_url'].split('.')[-1])
        print(pdt['pdct_img_main_url'])
        response = requests.get(pdt['pdct_img_main_url'], stream=True, verify=False, headers=headers)
        # response.raw.decode_content = True
        tmp_file_path = '/tmp/' + shop_id + 'mhers_tmp_{}.imgtype'.format(abs(hash(pdt['pdct_img_main_url'])))
        img_path = img_path_namer(shop_id, pdt['pdct_name_on_eretailer'])
        print("img_path", img_path)
        with open(tmp_file_path, 'wb') as out_file:
            shutil.copyfileobj(response.raw, out_file)
        if imghdr.what(tmp_file_path) is not None:
            img_path = img_path.split('.')[0] + '.' + imghdr.what(
                '/tmp/' + shop_id + 'mhers_tmp_{}.imgtype'.format(abs(hash(pdt['pdct_img_main_url']))))
            shutil.copyfile('/tmp/' + shop_id + 'mhers_tmp_{}.imgtype'.format(abs(hash(pdt['pdct_img_main_url']))),
                            img_path)
            products[url].update({'img_path': img_path, 'img_hash': file_hash(img_path)})
        else:
             print("WARNING : ", tmp_file_path, pdt['pdct_img_main_url'], imghdr.what(tmp_file_path))

create_csvs(products, categories, searches, shop_id, fpath_namer(shop_id, 'raw_csv'), COLLECTION_DATE, special_country='JP')
validate_raw_files(fpath_namer(shop_id, 'raw_csv'), special_country='JP')
driver.quit()
