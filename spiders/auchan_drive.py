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
shop_id = 'auchan_drive'
root_url = 'https://www.auchandrive.fr'
requests_cache.install_cache(fpath_namer(shop_id, 'requests_cache'))
country = 'FR'
searches, categories, products = {}, {}, {}
driver = CustomDriver(headless=True, download_images=True)


def getprice(pricestr):
    if not pricestr:
        return None
    pricestr = re.sub("[^0-9,€]", "", pricestr)
    price = parse('{euro:d},{cent:d}€', pricestr)
    if price is not None:
        return price.named['euro'] * 100 + price.named['cent']


###################
# # CTG page xpathing #
###################
exple_ctg_page_path = op.join(TEST_PAGES_FOLDER_PATH, "auchan_drive", 'ctg_page_test.html') # TODO : store the file
ctg, test_categories, test_products = '', {'': []}, {}


def ctg_parsing(fpath, ctg, categories, products):  # TODO : modify xpaths
    tree = etree.parse(open(fpath, 'rb'), parser=parser)
    for li in tree.xpath('//article[@class="product-item"]'):
        if not li.xpath('(./a/@href)[1]'):
            continue
        produrl = li.xpath('(./a/@href)[1]')[0]
        produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
        products[produrl] = {
            'pdct_name_on_eretailer': clean_xpathd_text(li.xpath('./@data-name')),
            'raw_price': clean_xpathd_text(li.xpath('./@data-price')) + "€",
            'raw_promo_price': clean_xpathd_text(li.xpath('.//xpath/text()')),
            'volume': clean_xpathd_text(li.xpath('./@data-name')),
            'pdct_img_main_url': "".join(li.xpath('.//picture//img/@src')[0]),
        }
        print(products[produrl], produrl)
        products[produrl]['price'] = getprice(products[produrl]['raw_price'])
        products[produrl]['promo_price'] = getprice(products[produrl]['raw_promo_price'])
        products[produrl]['pdct_img_main_url'] = clean_url(products[produrl]['pdct_img_main_url'].replace('_165x165', '_460x460'), root_url)
        print(products[produrl])

        categories[ctg].append(produrl)
    return categories, products


ctg_parsing(exple_ctg_page_path, ctg, test_categories, test_products)

###################
# # KW page xpathing #
###################

exple_kw_page_path = op.join(TEST_PAGES_FOLDER_PATH, "askul", 'kw_page_test.html') # TODO : store the file
kw, test_searches, test_products = '', {'': []}, {}


def kw_parsing(fpath, kw, searches, products):  # TODO : modify xpaths
    tree = etree.parse(open(fpath, 'rb'), parser=parser)
    for li in tree.xpath('//article[@class="product-item"]'):
        produrl = li.xpath('(./a/@href)[1]')[0]
        produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
        products[produrl] = {
            'pdct_name_on_eretailer': clean_xpathd_text(li.xpath('./@data-name')),
            'raw_price': clean_xpathd_text(li.xpath('./@data-price')) + "€",
            'raw_promo_price': clean_xpathd_text(li.xpath('.//xpath/text()')),
            'volume': clean_xpathd_text(li.xpath('./@data-name')),
            'pdct_img_main_url': "".join(li.xpath('.//picture//img/@src')[0]),
        }
        print(products[produrl], produrl)
        products[produrl]['price'] = getprice(products[produrl]['raw_price'])
        products[produrl]['promo_price'] = getprice(products[produrl]['raw_promo_price'])
        products[produrl]['pdct_img_main_url'] = clean_url(products[produrl]['pdct_img_main_url'].replace('_165x165', '_460x460'), root_url)
        print(products[produrl])

        searches[kw].append(produrl)
    return searches, products


kw_parsing(exple_kw_page_path, kw, test_searches, test_products)


# Init the drive
def init_auchan_drive(driver):
    print("Initing init_auchan_drive")
    driver.get("https://www.auchandrive.fr")
    driver.waitclick('//a[@href="https://www.auchandrive.fr/drive/nos-drives/p/dieppe-894"]')
    driver.waitclick('//a[@href="https://www.auchandrive.fr/drive/mag/Dieppe-894/"]')
    print("Finished initing init_auchan_drive")

auchan_drive_was_initialised = False

###################
# # CTG scrapping #
###################

# TODO : complete the urls
urls_ctgs_dict = {
    'champagne': 'https://www.auchandrive.fr/drive/Dieppe-894//Boissons-R3686969/Vins-champagnes-3686339/',
    'sparkling': 'https://www.auchandrive.fr/drive/Dieppe-894/Boissons-R3686969/Vins-champagnes-3686339/',
    'still_wines': 'https://www.auchandrive.fr/drive/Dieppe-894/Boissons-R3686969/Vins-champagnes-3686339/',
    'whisky': 'https://www.auchandrive.fr/drive/Dieppe-894/Boissons-R3686969/Whiskies-3702918/',
    'cognac': 'https://www.auchandrive.fr/drive/recherche/cognac/AUTOCOMPLETION_KEYWORD',
    'vodka': 'https://www.auchandrive.fr/catalog/boissons-3686969/bieres-alcools-3686338/vodka-gin-tequila-R3702926',
    'rum': 'https://www.auchandrive.fr/catalog/boissons-3686969/bieres-alcools-3686338/rhums-R3702929',
    'liquor': 'https://www.auchandrive.fr/catalog/boissons-3686969/bieres-alcools-3686338/aperitifs-anises-R3702917',
}

# Category Scraping
for ctg, url in urls_ctgs_dict.items():
    print('Beginning,', ctg, url)
    categories[ctg] = []
    fpath = fpath_namer(shop_id, 'ctg', ctg, 0)
    if not op.exists(fpath):
        if not auchan_drive_was_initialised:
            init_auchan_drive(driver)
            auchan_drive_was_initialised = True
        driver.get(url)
        driver.smooth_scroll()
        driver.save_page(fpath, scroll_to_bottom=True)
    categories, products = ctg_parsing(fpath, ctg, categories, products)
    print(ctg, url, len(categories[ctg]))


######################################
# # KW searches scrapping ############
######################################

# KW searches Scraping - with requests - one page per search
kw_search_url = "https://www.auchandrive.fr/recherche/{kw}"  # TODO : modify URL
for kw in keywords:
    searches[kw] = []
    fpath = fpath_namer(shop_id, 'search', kw, 0)
    if not op.exists(fpath):
        if not auchan_drive_was_initialised:
            init_auchan_drive(driver)
            auchan_drive_was_initialised = True
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
