import os.path as op

from lxml import etree

parser = etree.HTMLParser(encoding='utf-8')
from time import sleep
from urllib.parse import urlsplit, parse_qs
from ers import COLLECTION_DATE, file_hash, img_path_namer
from validators import validate_raw_files
from create_csvs import create_csvs
from ers import all_keywords_jp as keywords, fpath_namer, mh_brands, clean_url
from ers import TEST_PAGES_FOLDER_PATH
from matcher import BrandMatcher
from custom_browser import CustomDriver
from parse import parse
from ers import clean_xpathd_text
import re

# Init variables and assets
shop_id = "aeon_dewine"
root_url = "https://www.aeondewine.com"
country = "JP"
searches, categories, products = {}, {}, {}
driver = CustomDriver(headless=False)
brm = BrandMatcher()


def getprice(pricestr):
    if pricestr == '':
        return pricestr
    pricestr = re.sub("[^0-9]", "", pricestr)
    price = parse('{pound:d}', pricestr)
    if price:
        return price.named['pound'] * 100


###################
# # CTG page xpathing #
###################
exple_ctg_page_path = op.join(TEST_PAGES_FOLDER_PATH, "aeon_dewine", 'ctg_page_test.html') # TODO : store the file
ctg, test_categories, test_products = '', {'': []}, {}


def ctg_parsing(fpath, ctg, categories, products):  # TODO : modify xpaths
    tree = etree.parse(open(fpath, 'rb'), parser=parser)

    for li in tree.xpath('//ul[@class="goods_p_"]//li'):
        produrl = li.xpath('./a/@href')[0]
        produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
        products[produrl] = {
            'pdct_name_on_eretailer': clean_xpathd_text(li.xpath('.//div[@class="name1_"]//text()'), unicodedata_normalize=True),
            'raw_price': clean_xpathd_text(li.xpath('.//div[@class="price_"][1]/span/span/text()'), unicodedata_normalize=True),
            'raw_promo_price': clean_xpathd_text(li.xpath('.//xpath//text()'), unicodedata_normalize=True),
            'volume': clean_xpathd_text(li.xpath('.//div[@class="name1_"]//text()'), unicodedata_normalize=True),
            'pdct_img_main_url': li.xpath('.//figure[@class="img_"]/img/@src')[0],
            'ctg_denom_txt': "",
        }
        products[produrl]['brnd'] = brm.find_brand(products[produrl]['pdct_name_on_eretailer'])['brand']
        print(products[produrl], produrl)
        products[produrl]['price'] = getprice(products[produrl]['raw_price'])
        products[produrl]['promo_price'] = getprice(products[produrl]['raw_promo_price'])
        products[produrl]['pdct_img_main_url'] = clean_url(products[produrl]['pdct_img_main_url'].replace('/S/', '/L/'), root_url)
        print(products[produrl])

        categories[ctg].append(produrl)
    return categories, products


ctg_parsing(exple_ctg_page_path, ctg, test_categories, test_products)

###################
# # KW page xpathing #
###################

exple_kw_page_path = op.join(TEST_PAGES_FOLDER_PATH, "aeon_dewine", 'kw_page_test.html') # TODO : store the file
kw, test_searches, test_products = '', {'': []}, {}


def kw_parsing(fpath, kw, searches, products):  # TODO : modify xpaths
    tree = etree.parse(open(fpath, 'rb'), parser=parser)

    for li in tree.xpath('//ul[@class="goods_p_"]//li'):
        produrl = li.xpath('./a/@href')[0]
        produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
        products[produrl] = {
            'pdct_name_on_eretailer': clean_xpathd_text(li.xpath('.//div[@class="name1_"]//text()'), unicodedata_normalize=True),
            'raw_price': clean_xpathd_text(li.xpath('.//div[@class="price_"][1]/span/span/text()'), unicodedata_normalize=True),
            'raw_promo_price': clean_xpathd_text(li.xpath('.//xpath//text()'), unicodedata_normalize=True),
            'volume': clean_xpathd_text(li.xpath('.//div[@class="name1_"]//text()'), unicodedata_normalize=True),
            'pdct_img_main_url': li.xpath('.//figure[@class="img_"]/img/@src')[0],
            'ctg_denom_txt': "",
        }
        products[produrl]['brnd'] = brm.find_brand(products[produrl]['pdct_name_on_eretailer'])['brand']
        print(products[produrl], produrl)
        products[produrl]['price'] = getprice(products[produrl]['raw_price'])
        products[produrl]['promo_price'] = getprice(products[produrl]['raw_promo_price'])
        products[produrl]['pdct_img_main_url'] = clean_url(products[produrl]['pdct_img_main_url'].replace('/S/', '/L/'), root_url)
        print(products[produrl])

        searches[kw].append(produrl)
    return searches, products


kw_parsing(exple_kw_page_path, kw, test_searches, test_products)


###################
# # PDCT page xpathing #
###################
exple_pdct_page_path = op.join(TEST_PAGES_FOLDER_PATH, shop_id, 'pdct_page_test.html') # TODO: store the file
# exple_pdct_page_path = "/code/mhers/cache/w_9/isetan/pdct/＜クリュッグ＞ロゼ ハーフサイズ-page0.html"
test_url, test_products = '', {'': {}}


def pdct_parsing(fpath, url, products): # TODO : modify xpaths
    tree = etree.parse(open(fpath), parser=parser)
    products[url].update({
        'volume': clean_xpathd_text(tree.xpath('//ul[@class="ingredients"]//text()')[:3], unicodedata_normalize=True),
        'pdct_img_main_url': clean_url(''.join(tree.xpath('//*[@class="product-img-box"]//a[@id="zoom1"]/@href')[:1]), root_url),
        'ctg_denom_txt': ' '.join(tree.xpath('//div[@class="grid-full breadcrumbs"]//text()')),
    })
    return products

pdct_parsing(exple_pdct_page_path, test_url, test_products)


###################
# # CTG scrapping #
###################

# TODO : complete the urls

urls_ctgs_dict = {
    'champagne': 'https://www.aeondewine.com/shop/category/category.aspx?category=06020103&p={page}',
    'still_wines': 'https://www.aeondewine.com/shop/category/category.aspx?category=060102&p={page}',
    'whisky': 'https://www.aeondewine.com/shop/category/category.aspx?category=060109&p={page}',
    # 'sparkling': '',#no sparkling
    # 'cognac': '',#no cognac
    # 'vodka': '',#no vodka
    # 'gin': '',#no gin
    # 'tequila': '',#no tequila
    # 'liquor': '',#no liquor
    # 'white_wine': 'https://www.aeondewine.com/shop/c/c060102/?l:inkid=aw69_avGM7kHb',
    # 'red_wine': 'https://www.aeondewine.com/shop/c/c060101/?linkid=aw69_Xl3132nk',
    # 'bourbon': '',#no bourbon
    # 'brandy': '',#no brandy
    # 'rum': '',#no rum
}


# Category Scraping - with selenium - multiple pages per category (click on next page)
for ctg, url in urls_ctgs_dict.items():
    categories[ctg] = []
    number_of_pdcts_in_ctg = 0
    print("Beginning ", ctg, url)
    if not op.exists(fpath_namer(shop_id, 'ctg', ctg, 0)):
        driver.get(url)

    # If files exist, don't scrap
    perform_scrapping = not op.exists(fpath_namer(shop_id, 'ctg', ctg, 0))
    for p in range(100):
        fpath = fpath_namer(shop_id, 'ctg', ctg, p)
        if not op.exists(fpath) and perform_scrapping:
            sleep(2)
            driver.save_page(fpath, scroll_to_bottom=True)
        categories, products = ctg_parsing(fpath, ctg, categories, products)
        print(fpath, ctg, p, len(categories[ctg]))

        # Break or change pages
        if number_of_pdcts_in_ctg == len(categories[ctg]):
            print("Finished, because no more new products")
            break

        if not perform_scrapping and not op.exists(fpath_namer(shop_id, 'ctg', ctg, p + 1)):
            print("Finished, because no more new products")
            break

        if perform_scrapping:
            next_page_click = '//span[@class="navipage_next_"]/a'  # TODO : modify
            if not driver.check_exists_by_xpath(next_page_click):
                print("Finished, because no more next button")
                break
            else:
                driver.waitclick(next_page_click)
        number_of_pdcts_in_ctg = len(categories[ctg])
    print(ctg, url, p, len(categories[ctg]))


######################################
# # KW searches scrapping ############
######################################

# KW searches Scraping - with requests - one page per search
driver.get('https://www.aeondewine.com')
for kw in keywords:
    searches[kw] = []
    number_of_pdcts_in_kw_search = 0

    # If files exist, don't scrap
    perform_scrapping = not op.exists(fpath_namer(shop_id, 'search', kw, 0))

    for p in range(5):
        fpath = fpath_namer(shop_id, 'search', kw, p)
        if not op.exists(fpath) and perform_scrapping:
            driver.text_input(kw, '//input[@id="keyword"]', enter=True)
            sleep(2)
            driver.save_page(fpath, scroll_to_bottom=True)

        searches, products = kw_parsing(fpath, kw, searches, products)

        # Break or change pages
        if number_of_pdcts_in_kw_search == len(searches[kw]):
            print("Finished, because no more new products")
            break

        if not perform_scrapping and not op.exists(fpath_namer(shop_id, 'search', kw, p + 1)):
            print("Finished, because no more new products")
            break

        if perform_scrapping:
            next_page_click = '//span[@class="navipage_next_"]/a'  # TODO : modify
            if not driver.check_exists_by_xpath(next_page_click):
                print("Finished, because no more next button")
                break
            else:
                driver.waitclick(next_page_click)
        number_of_pdcts_in_kw_search = len(searches[kw])
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
from ers import download_img

for url, pdt in products.items():
    if 'pdct_img_main_url' in pdt and pdt['pdct_img_main_url'] and brm.find_brand(pdt['pdct_name_on_eretailer'])['brand'] in mh_brands:
        print(pdt['pdct_name_on_eretailer'] + "." + pdt['pdct_img_main_url'].split('.')[-1])
        orig_img_path = img_path_namer(shop_id, pdt['pdct_name_on_eretailer'])
        img_path = download_img(pdt['pdct_img_main_url'], orig_img_path, shop_id=shop_id, decode_content=False, gzipped=False, debug=False)
        if img_path:
            products[url].update({'img_path': img_path, 'img_hash': file_hash(img_path)})


create_csvs(products, categories, searches, shop_id, fpath_namer(shop_id, 'raw_csv'), COLLECTION_DATE, special_country='JP')
validate_raw_files(fpath_namer(shop_id, 'raw_csv'), special_country='JP')
check_products_detection(shop_id, fpath_namer(shop_id, 'raw_csv'), shop_inventory_lw_csv)
driver.quit()
