import os.path as op

from lxml import etree

parser = etree.HTMLParser(encoding='utf-8')
from time import sleep
from urllib.parse import urlsplit, parse_qs
import requests
from ers import COLLECTION_DATE, file_hash, img_path_namer
import shutil, imghdr
from validators import validate_raw_files
from create_csvs import create_csvs
from ers import all_keywords_jp as keywords, fpath_namer, mh_brands, clean_url, headers
from ers import TEST_PAGES_FOLDER_PATH
from matcher import BrandMatcher
from custom_browser import CustomDriver
from parse import parse
import re
from ers import clean_xpathd_text

# Init variables and assets
shop_id = "isetan"
root_url = "https://isetan.mistore.jp/"
country = "JP"
searches, categories, products = {}, {}, {}
driver = CustomDriver(headless=False)


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
exple_ctg_page_path = op.join(TEST_PAGES_FOLDER_PATH, "isetan", 'ctg_page_test.html') # TODO : store the file
ctg, test_categories, test_products = '', {'': []}, {}


def ctg_parsing(fpath, ctg, categories, products):  # TODO : modify xpaths
    tree = etree.parse(open(fpath, 'rb'), parser=parser)
    for li in tree.xpath('//div[@class="content"]/ul/li[@class="col"]'):
        produrl = li.xpath('.//a/@href')[0]
        produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
        products[produrl] = {
            'pdct_name_on_eretailer': clean_xpathd_text(li.xpath('.//p[@class="text"]//a//text()', unicodedata_normalize=True)[0]),
            'raw_price': clean_xpathd_text(li.xpath('.//p[@class="text"]/a//span//text()'), unicodedata_normalize=True),
            'raw_promo_price': clean_xpathd_text(li.xpath('.//xpath/text()'), unicodedata_normalize=True),
            'volume': clean_xpathd_text(li.xpath('.//p[@class="text"]/a/font//text()'), unicodedata_normalize=True),
            'pdct_img_main_url': clean_url(li.xpath('.//p[@class="image"]//img/@src')[0], root_url),
        }

        print(products[produrl], produrl)
        products[produrl]['price'] = getprice(products[produrl]['raw_price'])
        products[produrl]['promo_price'] = getprice(products[produrl]['raw_promo_price'])
        products[produrl]['pdct_img_main_url'] = products[produrl]['pdct_img_main_url'].split('?')[0] + "?$VC_LL$"
        print(products[produrl])

        categories[ctg].append(produrl)
    return categories, products


ctg_parsing(exple_ctg_page_path, ctg, test_categories, test_products)


###################
# # KW page xpathing #
###################

exple_kw_page_path = op.join(TEST_PAGES_FOLDER_PATH, "isetan", 'kw_page_test.html') # TODO : store the file
kw, test_searches, test_products = '', {'': []}, {}


def kw_parsing(fpath, kw, searches, products):  # TODO : modify xpaths
    tree = etree.parse(open(fpath, 'rb'), parser=parser)
    for li in tree.xpath('//div[@class="content"]/ul/li[@class="col"]'):
        produrl = li.xpath('.//a/@href')[0]
        produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
        products[produrl] = {
            'pdct_name_on_eretailer': clean_xpathd_text(li.xpath('.//p[@class="text"]//a//text()', unicodedata_normalize=True)[0]),
            'raw_price': clean_xpathd_text(li.xpath('.//p[@class="text"]/a//span//text()'), unicodedata_normalize=True),
            'raw_promo_price': clean_xpathd_text(li.xpath('.//xpath/text()'), unicodedata_normalize=True),
            'volume': clean_xpathd_text(li.xpath('.//p[@class="text"]/a/font//text()'), unicodedata_normalize=True),
            'pdct_img_main_url': clean_url(li.xpath('.//p[@class="image"]//img/@src')[0], root_url),
        }

        print(products[produrl], produrl)
        products[produrl]['price'] = getprice(products[produrl]['raw_price'])
        products[produrl]['promo_price'] = getprice(products[produrl]['raw_promo_price'])
        products[produrl]['pdct_img_main_url'] = products[produrl]['pdct_img_main_url'].split('?')[0] + "?$VC_LL$"
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
        'volume': clean_xpathd_text(tree.xpath('.//*[@class="item-info"]//tr//td//text()')[:3], unicodedata_normalize=True),
        # 'pdct_img_main_url': clean_url(''.join(tree.xpath('//a[@class="fade"]/img/@src')[:1]), root_url),
        'ctg_denom_txt': ' '.join(tree.xpath('//div[@id="body"]//text()')),
    })
    return products


pdct_parsing(exple_pdct_page_path, test_url, test_products)


###################
# # CTG scrapping #
###################

# TODO : complete the urls
urls_ctgs_dict = {
    'champagne': 'https://isetan.mistore.jp/onlinestore/foods/list?pageNo={page}&itemPerPage=100&order=1&categoryId=01_070503&slPsblCntUmuFlg=1&sitePath=onlinestore',
    'sparkling': 'https://isetan.mistore.jp/onlinestore/foods/list?pageNo={page}&itemPerPage=100&order=1&categoryId=01_070517&slPsblCntUmuFlg=1&sitePath=onlinestore',
    'still_wines': 'https://isetan.mistore.jp/onlinestore/foods/list?pageNo={page}&itemPerPage=100&categoryId=01_070500&rid=1f9d8efd36f84d648d1168c7c90a1283',
    'whisky': 'https://isetan.mistore.jp/onlinestore/foods/list?pageNo={page}&itemPerPage=100&categoryId=01_070600&rid=4312db3d3a4b4619903e981b3af58f24',
    'cognac': 'https://isetan.mistore.jp/onlinestore/foods/list?pageNo={page}&itemPerPage=100&order=1&categoryId=01_070604&slPsblCntUmuFlg=1&sitePath=onlinestore',
    # 'vodka': '',#na
    # 'gin': '',#na
    # 'tequila': '',#na
    'liquor': 'https://isetan.mistore.jp/onlinestore/foods/list?pageNo={page}&itemPerPage=100&order=1&categoryId=01_070605&slPsblCntUmuFlg=1&sitePath=onlinestore',
    # 'white_wine': '',#na
    # 'red_wine': '',#na
    # 'bourbon': '',#na
    # 'brandy': '',#na
    # 'rum': '',#na
}


# Category Scraping - with selenium - multiple pages per category (click on next page)
for ctg, url in urls_ctgs_dict.items():
    categories[ctg] = []
    number_of_pdcts_in_ctg = 0

    for p in range(100):
        fpath = fpath_namer(shop_id, 'ctg', ctg, p)

        if not op.exists(fpath):
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
kw_search_url = "https://isetan.mistore.jp/onlinestore/search?searchAttribute={kw}&searchAction=true&itemPerPage=100"  # TODO : modify URL
for kw in keywords:
    searches[kw] = []
    number_of_pdcts_in_kw_search = 0
    if not op.exists(fpath_namer(shop_id, 'search', kw, 0)):
        driver.get(kw_search_url.format(kw=kw))

    for p in range(1):
        fpath = fpath_namer(shop_id, 'search', kw, p)
        if not op.exists(fpath):
            sleep(2)
            driver.save_page(fpath, scroll_to_bottom=True)

        searches, products = kw_parsing(fpath, kw, searches, products)

    print(kw, len(searches[kw]))

######################################
# # Product pages scraping ###########
######################################

# Download the pages - with selenium
brm = BrandMatcher()
for url in sorted(list(set(products))):
    d = products[url]
    if brm.find_brand(d['pdct_name_on_eretailer'], special_country='JP')['brand'] in mh_brands:
        print(d['pdct_name_on_eretailer'])
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
