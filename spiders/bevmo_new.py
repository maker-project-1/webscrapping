import os
import os.path as op
import re

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
shop_id = "bevmo"
root_url = "http://shop.bevmo.com/"
requests_cache.install_cache(fpath_namer(shop_id, 'requests_cache'))
country = 'USA'

searches, categories, products = {}, {}, {}
driver = CustomDriver(headless=False)
brm = BrandMatcher()


def getprice(pricestr):
    pricestr = re.sub("[^0-9.$]", "", pricestr)
    if pricestr == '':
        return pricestr
    price = parse('${pound:d}.{pence:d}', pricestr)
    if price is None:
        price = parse('{pence:d}p', pricestr)
        return price.named['pence']
    else:
        return price.named['pound'] * 100 + price.named['pence']


def init_bevmo(driver):
    driver.get("https://www.bevmo.com")
    sleep(5)
    driver.wait_for_xpath('//form[@id="storeselect-popup"]//*[@name="twenty_one_option"]')
    button_to_click_xpath = '//*[@name="twenty_one_option"]'
    driver.waitclick(button_to_click_xpath, timeout=10)
    button_to_click_xpath = '//input[@value="ship"]'
    driver.waitclick(button_to_click_xpath, timeout=10)
    button_to_click_xpath = '//select[@name="ship_state"]/option[@value="17"]'
    driver.waitclick(button_to_click_xpath, timeout=10)
    button_to_click_xpath = '//*[@id="storeselect-select"]'
    driver.waitclick(button_to_click_xpath, timeout=10)
    print("Sleeping", sleep(3))


bevmo_was_initialised = False


# ##################
# # CTG page xpathing #
# ##################
ctg_page_test_url = 'http://www.bevmo.com/spirits.html'
exple_ctg_page_path = op.join(TEST_PAGES_FOLDER_PATH, shop_id, 'ctg_page_test.html')  # TODO : store the file
os.makedirs(op.dirname(exple_ctg_page_path), exist_ok=True)
ctg, test_categories, test_products = '', {'': []}, {}

# driver.get(ctg_page_test_url)
# driver.save_page(exple_ctg_page_path, scroll_to_bottom=True)


def ctg_parsing(fpath, ctg, categories, products):  # TODO : modify xpaths
    tree = etree.parse(open(fpath, 'rb'), parser=parser)
    for li in tree.xpath('//ul[contains(@class, "products-grid")]/li[contains(@class,"item")]'):
        if not li.xpath('.//h2[contains(@class, "product-name")]/a/@href'):
            continue
        produrl = li.xpath('.//h2[contains(@class, "product-name")]/a/@href')[0]
 #       produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
        products[produrl] = {
            'pdct_name_on_eretailer': clean_xpathd_text(li.xpath('.//h2[contains(@class, "product-name")]/a//text()')),
            'volume': clean_xpathd_text(li.xpath('.//h2[contains(@class, "product-name")]/a//text()')),
            'raw_price': clean_xpathd_text(li.xpath('.//span[contains(@id, "product-price")]//text()')),
            'raw_promo_price': clean_xpathd_text(li.xpath('.//span[contains(@id, "old-price")]//text()')),
            'pdct_img_main_url': "".join(li.xpath('./zzzzzzzzzz')[:1]),
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
search_page_test_url = 'https://specsonline.com/?s={kw}&post_type=product'
exple_kw_page_path = op.join(TEST_PAGES_FOLDER_PATH, shop_id, 'kw_page_test.html') # TODO : store the file
os.makedirs(op.dirname(exple_ctg_page_path), exist_ok=True)
kw_test, test_searches, test_products = '', {"": []}, {}

# driver.get(search_page_test_url.format(kw=kw_test))
# driver.save_page(exple_kw_page_path, scroll_to_bottom=True)


def kw_parsing(fpath, kw, searches, products):  # TODO : modify xpaths
    tree = etree.parse(open(fpath, 'rb'), parser=parser)
    for li in tree.xpath('//ul[contains(@class, "products")]//li[@class="item"]'):
        if not li.xpath('.//h2[contains(@class, "product-name")]/a/@href'):
            continue
        produrl = li.xpath('.//h2[contains(@class, "product-name")]/a/@href')[0]
        produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
        products[produrl] = {
            'pdct_name_on_eretailer': clean_xpathd_text(li.xpath('.//h2[contains(@class, "product-name")]/a//text()')),
            'volume': clean_xpathd_text(li.xpath('.//h2[contains(@class, "product-name")]/a//text()')),
            'raw_price': clean_xpathd_text(li.xpath('.//span[contains(@id, "product-price")]//text()')),
            'raw_promo_price': clean_xpathd_text(li.xpath('.//span[contains(@id, "old-price")]//text()')),
            'pdct_img_main_url': "".join(li.xpath('./zzzzzzzzz')[:1]),
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
# # PDCT page xpathing #
###################
exple_pdct_page_path = op.join(TEST_PAGES_FOLDER_PATH, shop_id, 'pdct_page_test.html') # TODO: store the file
# exple_pdct_page_path = "/code/mhers/cache/w_9/isetan/pdct/＜クリュッグ＞ロゼ ハーフサイズ-page0.html"
test_url, test_products = '', {'': {}}


def pdct_parsing(fpath, url, products): # TODO : modify xpaths
    tree = etree.parse(open(fpath), parser=parser)
    products[url].update({
        # 'volume': clean_xpathd_text(tree.xpath('.//*[@class="item-info"]//tr//td//text()')[:3], unicodedata_normalize=True),
        'pdct_img_main_url': clean_url(''.join(tree.xpath('//img[@id="image-main"]/@src')[:1]), root_url),
        'ctg_denom_txt': ' '.join(tree.xpath('//div[@class="breadcrumbs"]//text()')),
    })
    return products

pdct_parsing(exple_pdct_page_path, test_url, test_products)

###################
# # CTG scrapping #
###################

urls_ctgs_dict = {
    'champagne': 'http://www.bevmo.com/wine/champagne-sparkling.html?p={page}',
    'cognac': 'http://www.bevmo.com/spirits/brandy.html?p={page}',
    'sparkling': 'http://www.bevmo.com/wine/champagne-sparkling.html?p={page}',
    'vodka': 'http://www.bevmo.com/spirits/vodka.html?p={page}',
    'whisky': 'http://www.bevmo.com/spirits/whiskey.html?p={page}',
    'still_wines': 'http://www.bevmo.com/wine/white-wine.html?p={page}',
    'gin': 'http://www.bevmo.com/spirits/gin.html?p={page}',
    'red_wine': 'http://www.bevmo.com/wine/red-wine.html?p={page}',
    'white_wine': 'http://www.bevmo.com/wine/white-wine.html?p={page}',
    'tequila': 'http://www.bevmo.com/spirits/tequila.html?p={page}',
    'rum': 'http://www.bevmo.com/spirits/rum.html?p={page}',
    'liquor': 'http://www.bevmo.com/spirits/liqueur.html?p={page}',
}


# Category Scraping - with selenium - multiple pages per category (click on next page)
for ctg, url in urls_ctgs_dict.items():
    categories[ctg] = []
    number_of_pdcts_in_ctg = 0

    for p in range(100):
        fpath = fpath_namer(shop_id, 'ctg', ctg, p)
        print(fpath)
        print(url.format(page=p+1))
        if not op.exists(fpath):
            if not bevmo_was_initialised:
                init_bevmo(driver)
                bevmo_was_initialised = True
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
kw_search_url = "http://shop.bevmo.com/search?w={kw}&view=list&srt={page}"  # TODO : modify URL
for kw in keywords:
    searches[kw] = []
    number_of_pdcts_in_kw_search = 0
    if not op.exists(fpath_namer(shop_id, 'search', kw, 0)):
        driver.get(kw_search_url.format(kw=kw, page=1))

    for p in range(1):
        fpath = fpath_namer(shop_id, 'search', kw, p)
        if not op.exists(fpath):
            if not bevmo_was_initialised:
                init_bevmo(driver)
                bevmo_was_initialised = True
            sleep(2)
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
            if not bevmo_was_initialised:
                init_bevmo(driver)
                bevmo_was_initialised = True
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
