import os
import os.path as op

from lxml import etree

parser = etree.HTMLParser(encoding='utf-8')
from time import sleep
from urllib.parse import urlsplit, parse_qs
import requests_cache

from validators import validate_raw_files, check_products_detection
from create_csvs import create_csvs
from ers import all_keywords_usa as keywords, fpath_namer, mh_brands, clean_url, shop_inventory_lw_csv

from matcher import BrandMatcher
from ers import COLLECTION_DATE, file_hash, img_path_namer, TEST_PAGES_FOLDER_PATH
from custom_browser import CustomDriver
from parse import parse
from ers import clean_xpathd_text


# Init variables and assets
shop_id = 'goodygoody'
root_url = 'https://www.goodygoody.com/'
requests_cache.install_cache(fpath_namer(shop_id, 'requests_cache'))
country = 'AUS'

searches, categories, products = {}, {}, {}
driver = CustomDriver(headless=True)
brm = BrandMatcher()


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

def init_goodygoody(driver):
    driver.get("https://www.goodygoody.com/Products/Products?searchTerm=champagne&category=&type=0&orderBy=name&minprice=&maxprice=")
    sleep(1)
    driver.waitclick('//*[@id="applyStoreButton"]')

goodygoody_was_initialised = False

# ##################
# # CTG page xpathing #
# ##################
ctg_page_test_url = 'https://www.goodygoody.com/Products/Products?searchTerm=&category=4RDE&type=0&orderBy=name&minprice=&maxprice='
exple_ctg_page_path = op.join(TEST_PAGES_FOLDER_PATH, shop_id, 'ctg_page_test.html')  # TODO : store the file
os.makedirs(op.dirname(exple_ctg_page_path), exist_ok=True)
ctg, test_categories, test_products = '', {'': []}, {}

# driver.get(ctg_page_test_url)
# driver.save_page(exple_ctg_page_path, scroll_to_bottom=True)


def ctg_parsing(fpath, ctg, categories, products):  # TODO : modify xpaths
    tree = etree.parse(open(fpath, 'rb'), parser=parser)
    for li in tree.xpath('//div[@class="row productRow"]//div[@class="row"]'):
        if not li.xpath('./zzzzzz'):
            continue
        produrl = li.xpath('')
        produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
        products[produrl] = {
            'pdct_name_on_eretailer': clean_xpathd_text(li.xpath('./div[2]/p[1]//text()')),
            'volume': clean_xpathd_text(li.xpath('./div[2]/br[1]/preceding-sibling::text()[1]')),
            'raw_price': clean_xpathd_text(li.xpath('./div[2]/br[1]/following-sibling::text()[1]')),
            'raw_promo_price': clean_xpathd_text(li.xpath('./zzzzzzzzzz')),
            'pdct_img_main_url': "".join(li.xpath('.//img[@class="img-thumbnail"]/@src')),
        }
        products[produrl]['brnd'] = brm.find_brand(products[produrl]['pdct_name_on_eretailer'])['brand']
        print(products[produrl], produrl)
        products[produrl]['price'] = getprice(products[produrl]['raw_price'])
        products[produrl]['promo_price'] = getprice(products[produrl]['raw_promo_price'])
        products[produrl]['pdct_img_main_url'] = clean_url(products[produrl]['pdct_img_main_url'], root_url)
        print(products[produrl])

        categories[ctg].append(produrl)
    return categories, products


ctg_parsing(exple_ctg_page_path, ctg, test_categories, test_products)

###################
# # KW page xpathing #
###################
search_page_test_url = 'https://www.goodygoody.com/Products/Products?searchTerm=champagne&category=&type=0&orderBy=name&minprice=&maxprice='
exple_kw_page_path = op.join(TEST_PAGES_FOLDER_PATH, shop_id, 'kw_page_test.html') # TODO : store the file
os.makedirs(op.dirname(exple_ctg_page_path), exist_ok=True)
kw_test, test_searches, test_products = '', {"": []}, {}

# driver.get(search_page_test_url.format(kw=kw_test))
# driver.save_page(exple_kw_page_path, scroll_to_bottom=True)


def kw_parsing(fpath, kw, searches, products):  # TODO : modify xpaths
    tree = etree.parse(open(fpath, 'rb'), parser=parser)
    for li in tree.xpath('//div[@class="row productRow"]//div[@class="row"]'):
        if not li.xpath('./zzzzzzz'):
            continue
        produrl = li.xpath('')
        produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
        products[produrl] = {
            'pdct_name_on_eretailer': clean_xpathd_text(li.xpath('./div[2]/br[1]/following-sibling::text()[1]')),
            'volume': clean_xpathd_text(li.xpath('./div[2]/br[1]/preceding-sibling::text()[1]')),
            'raw_price': clean_xpathd_text(li.xpath('./div[2]/br[1]/following-sibling::text()[1]')),
            'raw_promo_price': clean_xpathd_text(li.xpath('./zzzzzzzzz')),
            'pdct_img_main_url': "".join(li.xpath('.//img[@class="img-thumbnail"]/@src')),
        }
        products[produrl]['brnd'] = brm.find_brand(products[produrl]['pdct_name_on_eretailer'])['brand']
        print(products[produrl], produrl)
        products[produrl]['price'] = getprice(products[produrl]['raw_price'])
        products[produrl]['promo_price'] = getprice(products[produrl]['raw_promo_price'])
        products[produrl]['pdct_img_main_url'] = clean_url(products[produrl]['pdct_img_main_url'], root_url)
        print(products[produrl])
        print(products[produrl])

        searches[kw].append(produrl)
    return searches, products


kw_parsing(exple_kw_page_path, kw_test, test_searches, test_products)


###################
# # CTG scrapping #
###################

urls_ctgs_dict = {
    'champagne': 'https://www.goodygoody.com/Products/Products?searchTerm=&category=4RDE&type=0&orderBy=name&minprice=&maxprice=',
    'sparkling': 'https://www.goodygoody.com/Products/Products?searchTerm=&category=4RDE&type=0&orderBy=name&minprice=&maxprice=',
    'still_wines': 'https://www.goodygoody.com/Products/Products?searchTerm=&category=4RAE&type=0&orderBy=name&minprice=&maxprice=',
    'whisky': 'https://www.goodygoody.com/Products/Products?searchTerm=&category=1ASC&type=0&orderBy=name&minprice=&maxprice=',
    'cognac': 'https://www.goodygoody.com/Products/Products?searchTerm=&category=1ACG&type=0&orderBy=name&minprice=&maxprice=',
    'vodka': 'https://www.goodygoody.com/Products/Products?searchTerm=&category=1AVK&type=0&orderBy=name&minprice=&maxprice=',
    'gin': 'https://www.goodygoody.com/Products/Products?searchTerm=&category=1AGN&type=0&orderBy=name&minprice=&maxprice=',
    'tequila': 'https://www.goodygoody.com/Products/Products?searchTerm=&category=1ATQ&type=0&orderBy=name&minprice=&maxprice=',
    'rum': 'https://www.goodygoody.com/Products/Products?searchTerm=&category=1ARM&type=0&orderBy=name&minprice=&maxprice=',
    'brandy': 'https://www.goodygoody.com/Products/Products?searchTerm=&category=1ABR&type=0&orderBy=name&minprice=&maxprice=',
    'bourbon': 'https://www.goodygoody.com/Products/Products?searchTerm=&category=1ABN&type=0&orderBy=name&minprice=&maxprice=',
}


# Category Scraping - with selenium - multiple pages per category (click on next page)
for ctg, url in urls_ctgs_dict.items():
    categories[ctg] = []
    number_of_pdcts_in_ctg = 0

    for p in range(100):
        fpath = fpath_namer(shop_id, 'ctg', ctg, p)

        if not op.exists(fpath):
            if not goodygoody_was_initialised:
                init_goodygoody(driver)
                goodygoody_was_initialised = True

            driver.get(url.format(page=p+1))
            sleep(2)
            driver.save_page(fpath, scroll_to_bottom=True)
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
kw_search_url = "https://www.goodygoody.com/Products/Products?searchTerm={kw}&category=&type=0&orderBy=name&minprice=&maxprice="  # TODO : modify URL
for kw in keywords:
    searches[kw] = []
    number_of_pdcts_in_kw_search = 0
    if not op.exists(fpath_namer(shop_id, 'search', kw, 0)):
        if not goodygoody_was_initialised:
            init_goodygoody(driver)
            goodygoody_was_initialised = True

        driver.get(kw_search_url.format(kw=kw))

    for p in range(1):
        fpath = fpath_namer(shop_id, 'search', kw, p)
        if not op.exists(fpath):
            if not goodygoody_was_initialised:
                init_goodygoody(driver)
                goodygoody_was_initialised = True

            sleep(2)
            driver.smooth_scroll()
            driver.save_page(fpath, scroll_to_bottom=True)
        searches, products = kw_parsing(fpath, kw, searches, products)

    print(kw, len(searches[kw]))


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
