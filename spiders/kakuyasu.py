import os.path as op

from lxml import etree

parser = etree.HTMLParser(encoding='utf8')
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
shop_id = "kakuyasu"
root_url = "http://www.kakuyasu.co.jp/"
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
exple_ctg_page_path = op.join(TEST_PAGES_FOLDER_PATH, "kakuyasu", 'ctg_page_test.html') # TODO : store the file
exple_ctg_page_path = "/code/mhers/cache/w_8/kakuyasu/ctg/champagne-page0.html" # TODO : store the file
ctg, test_categories, test_products = '', {'': []}, {}


def ctg_parsing(fpath, ctg, categories, products):  # TODO : modify xpaths
    tree = etree.parse(open(fpath, 'rb'), parser=parser)
    for li in tree.xpath('//ul//li//div[@class="item"]'):
        produrl = li.xpath('.//a/@href')[0]
        produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
        products[produrl] = {
            'pdct_name_on_eretailer': clean_xpathd_text(li.xpath('.//dt[@class="noflag"]//a//text()'), unicodedata_normalize=True),
            'raw_price': clean_xpathd_text(li.xpath('(.//td[@class="price"]/span[1]//text())[1]'), unicodedata_normalize=True),
            'raw_promo_price': clean_xpathd_text(li.xpath('.//xpath/text()'), unicodedata_normalize=True),
            'volume': clean_xpathd_text(li.xpath('./dl[1]/dd[4]//text()'), unicodedata_normalize=True),
            'pdct_img_main_url': clean_url(li.xpath('.//dd[@class="photo"]//img/@src')[0].replace('../', './ec/'), root_url),
        }

        print(products[produrl], produrl)
        products[produrl]['price'] = getprice(products[produrl]['raw_price'])
        products[produrl]['promo_price'] = getprice(products[produrl]['raw_promo_price'])
        products[produrl]['pdct_img_main_url'] = products[produrl]['pdct_img_main_url'].replace('-m', '-b')
        print(products[produrl])

        categories[ctg].append(produrl)
    return categories, products


ctg_parsing(exple_ctg_page_path, ctg, test_categories, test_products)

###################
# # KW page xpathing #
###################

exple_kw_page_path = op.join(TEST_PAGES_FOLDER_PATH, "kakuyasu", 'kw_page_test.html') # TODO : store the file
kw, test_searches, test_products = '', {'': []}, {}


def kw_parsing(fpath, kw, searches, products):  # TODO : modify xpaths
    tree = etree.parse(open(fpath, 'rb'), parser=parser)
    for li in tree.xpath('//div[contains(@class, "itemListArea")]//ul/li/div[@class="item"]'):
        produrl = li.xpath('.//a/@href')[0]
        produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
        products[produrl] = {
            'pdct_name_on_eretailer': clean_xpathd_text(li.xpath('.//dt[@class="noflag"]//a//text()'), unicodedata_normalize=True),
            'raw_price': clean_xpathd_text(li.xpath('(.//td[@class="price"]/span[1]//text())[1]'), unicodedata_normalize=True),
            'raw_promo_price': clean_xpathd_text(li.xpath('.//xpath/text()'), unicodedata_normalize=True),
            'volume': clean_xpathd_text(li.xpath('./dl[1]/dd[4]//text()'), unicodedata_normalize=True),
            'pdct_img_main_url': clean_url(li.xpath('.//dd[@class="photo"]//img/@src')[0], root_url),
        }

        print(products[produrl], produrl)
        products[produrl]['price'] = getprice(products[produrl]['raw_price'])
        products[produrl]['promo_price'] = getprice(products[produrl]['raw_promo_price'])
        products[produrl]['pdct_img_main_url'] = products[produrl]['pdct_img_main_url'].replace('-m', '-b')
        print(products[produrl])
        searches[kw].append(produrl)
    return searches, products


kw_parsing(exple_kw_page_path, kw, test_searches, test_products)

###################
# # CTG scrapping #
###################

# TODO : complete the urls

urls_ctgs_dict = {
    'champagne': 'http://www.kakuyasu.co.jp/ec/disp/CSfDispListPage_001.jsp?dispNo=001018003&q=&j=&min=&max=&ys=&yl=&yoryotanni=&allSearch=&type=01&sort=01&page={page}',
    'sparkling': 'http://www.kakuyasu.co.jp/ec/disp/CSfDispListPage_001.jsp?dispNo=001018&q=&j=&min=&max=&ys=&yl=&yoryotanni=&allSearch=&type=01&sort=01&page={page}',
    'still_wines': 'http://www.kakuyasu.co.jp/ec/disp/CSfDispListPage_001.jsp?dispNo=001005&q=&j=&min=&max=&ys=&yl=&yoryotanni=&allSearch=&type=01&sort=01&page={page}',
    'whisky': 'http://www.kakuyasu.co.jp/ec/disp/CSfDispListPage_001.jsp?dispNo=001008&q=&j=&min=&max=&ys=&yl=&yoryotanni=&allSearch=&type=01&sort=01&page={page}',
    'cognac': 'http://www.kakuyasu.co.jp/ec/disp/CSfDispListPage_001.jsp?dispNo=001014002&q=&j=&min=&max=&ys=&yl=&yoryotanni=&allSearch=&type=01&sort=01&page={page}',
    'vodka': 'http://www.kakuyasu.co.jp/ec/disp/CSfDispListPage_001.jsp?dispNo=001075003&q=&j=&min=&max=&ys=&yl=&yoryotanni=&allSearch=&type=01&sort=01&page={page}',
    'gin': 'http://www.kakuyasu.co.jp/ec/disp/CSfDispListPage_001.jsp?dispNo=001075001&q=&j=&min=&max=&ys=&yl=&yoryotanni=&allSearch=&type=01&sort=01&page={page}',
    'tequila': 'http://www.kakuyasu.co.jp/ec/disp/CSfDispListPage_001.jsp?dispNo=001075004&q=&j=&min=&max=&ys=&yl=&yoryotanni=&allSearch=&type=01&sort=01&page={page}',
    'liquor': 'http://www.kakuyasu.co.jp/ec/disp/CSfDispListPage_001.jsp?dispNo=001006&q=&j=&min=&max=&ys=&yl=&yoryotanni=&allSearch=&type=01&sort=01&page={page}',
    'white_wine': 'http://www.kakuyasu.co.jp/ec/disp/CSfDispListPage_001.jsp?dispNo=001005024&q=&j=&min=&max=&ys=&yl=&yoryotanni=&allSearch=&type=01&sort=01&page={page}',
    'red_wine': 'http://www.kakuyasu.co.jp/ec/disp/CSfDispListPage_001.jsp?dispNo=001005001&q=&j=&min=&max=&ys=&yl=&yoryotanni=&allSearch=&type=01&sort=01&page={page}',
    # 'bourbon': '',#na
    'brandy': 'http://www.kakuyasu.co.jp/ec/disp/CSfDispListPage_001.jsp?dispNo=001014&q=&j=&min=&max=&ys=&yl=&yoryotanni=&allSearch=&type=01&sort=01&page={page}',
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
            print("Finishing with :", len(set(categories[ctg])), "products")
            break
        else:
            number_of_pdcts_in_ctg = len(set(categories[ctg]))
    print(ctg, url, p, len(categories[ctg]))

######################################
# # KW searches scrapping ############
######################################

# KW searches Scraping - with requests - one page per search
kw_search_url = "http://www.kakuyasu.co.jp/ec/disp/CSfDispListPage_001.jsp?action=search&searchwordview=&dispNo=001&q={kw}"  # TODO : modify URL
for kw in keywords:
    searches[kw] = []
    number_of_pdcts_in_kw_search = 0
    print(kw_search_url.format(kw=kw))
    fpath = fpath_namer(shop_id, 'search', kw, p)
    if not op.exists(fpath):
        # driver.get(kw_search_url.format(kw=kw))
        driver.get("http://www.kakuyasu.co.jp/index.html")
        driver.text_input(kw, '//input[@id="searchinput"]', enter=True)
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


