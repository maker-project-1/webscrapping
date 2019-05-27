import os.path as op
import re
from time import sleep
from urllib.parse import urlsplit, parse_qs

import requests_cache
from lxml import etree
from parse import parse

from create_csvs import create_csvs
from custom_browser import CustomDriver
from ers import COLLECTION_DATE, file_hash, img_path_namer, TEST_PAGES_FOLDER_PATH, shop_inventory_lw_csv
from ers import all_keywords_fr as keywords
from ers import clean_xpathd_text
from ers import fpath_namer, mh_brands, clean_url
from matcher import BrandMatcher
from validators import validate_raw_files, check_products_detection

parser = etree.HTMLParser()


# Init variables and assets
shop_id = 'auchan_drive'
root_url = 'https://www.auchandrive.fr'
requests_cache.install_cache(fpath_namer(shop_id, 'requests_cache'))
country = 'FR'

searches, categories, products = {}, {}, {}
driver = CustomDriver(headless=True, download_images=True)
brm = BrandMatcher()

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
        products[produrl]['brnd'] = brm.find_brand(products[produrl]['pdct_name_on_eretailer'])['brand']
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
        produrl = li.xpath('.//a/@href')[0]
        produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
        products[produrl] = {
            'pdct_name_on_eretailer': clean_xpathd_text(li.xpath('./@data-name')),
            'raw_price': clean_xpathd_text(li.xpath('./@data-price')) + "€",
            'raw_promo_price': clean_xpathd_text(li.xpath('.//xpath/text()')),
            'volume': clean_xpathd_text(li.xpath('./@data-name')),
            'pdct_img_main_url': "".join(li.xpath('.//picture//img/@src')[0]),
        }
        products[produrl]['brnd'] = brm.find_brand(products[produrl]['pdct_name_on_eretailer'])['brand']
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
# # PDCT page xpathing #
###################
exple_pdct_page_path = op.join(TEST_PAGES_FOLDER_PATH, shop_id, 'pdct_page_test.html') # TODO: store the file
# exple_pdct_page_path = "/code/mhers/cache/w_9/isetan/pdct/＜クリュッグ＞ロゼ ハーフサイズ-page0.html"
test_url, test_products = '', {'': {}}


def pdct_parsing(fpath, url, products): # TODO : modify xpaths
    tree = etree.parse(open(fpath), parser=parser)
    products[url].update({
        'volume': clean_xpathd_text(tree.xpath('//span[@class="weight"]//text()')[:3], unicodedata_normalize=True),
        'pdct_img_main_url': clean_url(''.join(tree.xpath('//*[@class="s7staticimage"]//img/@src')[:1]), root_url),
        'ctg_denom_txt': ' '.join(tree.xpath('//div[@class="breadcrumb breadcrumbHeader"]//text()')),
    })
    return products

pdct_parsing(exple_pdct_page_path, test_url, test_products)

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
# # Product pages scraping ###########
######################################

# Download the pages - with selenium
for url in sorted(list(set(products))):
    d = products[url]
    if d['brnd'] in mh_brands:
        print(d['pdct_name_on_eretailer'], d['volume'])
        url_mod = clean_url(url, root_url=root_url)

        fpath = fpath_namer(shop_id, 'pdct', d['pdct_name_on_eretailer'], 0)
        if not op.exists(fpath):
            driver.get(url_mod)
            sleep(2)
            driver.save_page(fpath, scroll_to_bottom=True)
        products = pdct_parsing(fpath, url, products)
        print(products[url])


######################################
# # Download images        ###########
######################################
# Download images
from ers import download_img

for url, pdt in products.items():
    if 'pdct_img_main_url' in pdt and pdt['pdct_img_main_url'] and brm.find_brand(pdt['pdct_name_on_eretailer'])['brand'] in mh_brands:
        print(pdt['pdct_name_on_eretailer'] + "." + pdt['pdct_img_main_url'].split('.')[-1])
        orig_img_path = img_path_namer(shop_id, pdt['pdct_name_on_eretailer'])
        img_path = download_img(pdt['pdct_img_main_url'], orig_img_path, shop_id=shop_id, decode_content=False, gzipped=False, debug=False)
        if img_path:
            products[url].update({'img_path': img_path, 'img_hash': file_hash(img_path)})

create_csvs(products, categories, searches, shop_id, fpath_namer(shop_id, 'raw_csv'), COLLECTION_DATE)
validate_raw_files(fpath_namer(shop_id, 'raw_csv'))
check_products_detection(shop_id, fpath_namer(shop_id, 'raw_csv'), shop_inventory_lw_csv)
driver.quit()
