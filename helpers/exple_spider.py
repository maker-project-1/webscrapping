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
from ers import all_keywords_COUNTRYLOWER as keywords, fpath_namer, mh_brands, clean_url, headers
from ers import TEST_PAGES_FOLDER_PATH
from matcher import BrandMatcher
from custom_browser import CustomDriver
from parse import parse


# Init variables and assets
shop_id = SHOP_ID
root_url = SHOP_URL
country = COUNTRY
searches, categories, products = {}, {}, {}
driver = CustomDriver(headless=False)


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


###################
# # CTG page xpathing #
###################
exple_ctg_page_path = op.join(TEST_PAGES_FOLDER_PATH, SHOP_ID, 'ctg_page_test.html') # TODO : store the file
ctg, test_categories, test_products = '', {'': []}, {}


def ctg_parsing(fpath, ctg, categories, products):  # TODO : modify xpaths
    tree = etree.parse(open(fpath, 'rb'), parser=parser)
    for li in tree.xpath('//xpath'):
        produrl = li.xpath('.//xpath/a/@href')[0]
        produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
        products[produrl] = {
            'pdct_name_on_eretailer': li.xpath('.//xpath//text()'),
            'raw_price': ''.join(w for t in li.xpath('.//xpath/text()') for w in t.split()).strip(),
            'raw_promo_price': ''.join(w for t in li.xpath('.//xpath/text()') for w in t.split()).strip(),
            'volume': ''.join(w for t in li.xpath('.//xpath/text()') for w in t.split()).strip(),
        }
        print(products[produrl], produrl)
        products[produrl]['price'] = getprice(products[produrl]['raw_price'])
        products[produrl]['promo_price'] = getprice(products[produrl]['raw_promo_price'])
        print(products[produrl])
        categories[ctg].append(produrl)
    return categories, products


ctg_parsing(exple_ctg_page_path, ctg, test_categories, test_products)

###################
# # KW page xpathing #
###################

exple_kw_page_path = op.join(TEST_PAGES_FOLDER_PATH, SHOP_ID, 'kw_page_test.html') # TODO : store the file
kw, test_searches, test_products = '', {'': []}, {}


def kw_parsing(fpath, kw, searches, products):  # TODO : modify xpaths
    tree = etree.parse(open(fpath, 'rb'), parser=parser)
    for li in tree.xpath('//xpath'):
        produrl = li.xpath('.//xpath/a/@href')[0]
        produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
        products[produrl] = {
            'pdct_name_on_eretailer': li.xpath('.//xpath//text()'),
            'raw_price': ''.join(w for t in li.xpath('.//xpath/text()') for w in t.split()).strip(),
            'raw_promo_price': ''.join(w for t in li.xpath('.//xpath/text()') for w in t.split()).strip(),
            'volume': ''.join(w for t in li.xpath('.//xpath/text()') for w in t.split()).strip(),
        }
        print(products[produrl], produrl)
        products[produrl]['price'] = getprice(products[produrl]['raw_price'])
        products[produrl]['promo_price'] = getprice(products[produrl]['raw_promo_price'])
        print(products[produrl])
        searches[kw].append(produrl)
    return searches, products


ctg_parsing(exple_ctg_page_path, ctg, test_categories, test_products)



###################
# # PDCT page xpathing #
###################
exple_pdct_page_path = op.join(TEST_PAGES_FOLDER_PATH, SHOP_ID, 'pdct_page_test.html') # TODO: store the file
test_url, test_products = '', {'': {}}


def pdct_parsing(fpath, url, products): # TODO : modify xpaths
    tree = etree.parse(open(fpath), parser=parser)
    products[url].update({
        'volume': ''.join(tree.xpath('//h1[@class="title-page"]//text()')).strip(),
        'pdct_img_main_url': clean_url(''.join(tree.xpath('//img[@id="xzoom"]/@src')[:1]), root_url),
        'ctg_denom_txt': ' '.join(tree.xpath('//div[@id="body"]//text()')),
    })
    return products


pdct_parsing(exple_pdct_page_path, test_url, products)


###################
# # CTG scrapping #
###################

# TODO : complete the urls
urls_ctgs_dict = {
    'champagne': '',
    'sparkling': '',
    'still_wines': '',
    'whisky': '',
    'cognac': '',
    'vodka': '',
    'gin': '',
    'tequila': '',
    'liquor': '',
    'white_wine': '',
    'red_wine': '',
    'bourbon': '',
    'brandy': '',
    'rum': '',
}


# Category Scraping - with selenium - multiple pages per category (click on next page)
for ctg, url in urls_ctgs_dict.items():
    categories[ctg] = []
    number_of_pdcts_in_ctg = 0
    if not op.exists(fpath_namer(shop_id, 'ctg', ctg, 0)):
        driver.get(url)

    for p in range(100):
        fpath = fpath_namer(shop_id, 'ctg', ctg, p)
        if not op.exists(fpath):
            sleep(2)
            driver.smooth_scroll()
            driver.save_page(fpath, scroll_to_bottom=True)
        categories, products = ctg_parsing(fpath, ctg, categories, products)

        # Going to next page if need be
        next_page_click = '//a[@class="resultsNext"]'  # TODO : modify
        if not op.exists(fpath_namer(shop_id, 'ctg', ctg, p+1)):
            if not driver.check_exists_by_xpath(next_page_click):
                break
            else:
                driver.waitclick(next_page_click)
    print(ctg, url, p, len(categories[ctg]))


######################################
# # KW searches scrapping ############
######################################

# KW searches Scraping - with requests - one page per search
kw_search_url = "https://www.harrods.com/en-gb/search?searchTerm={kw}"  # TODO : modify URL
for kw in keywords:
    searches[kw] = []
    number_of_pdcts_in_kw_search = 0
    if not op.exists(fpath_namer(shop_id, 'search', kw, 0)):
        driver.get(kw_search_url.format(kw=kw))

    # search_input_box_xpath = u'//*[@id="SimpleSearchForm_SearchTerm"]'
    # if not op.exists(fpath_namer(shop_id, 'search', kw, 0)):
    #     if not driver.check_exists_by_xpath(search_input_box_xpath):
    #         # Getting back to root if search input box is not found
    #         driver.get(root_url)
    #     driver.text_input(kw, search_input_box_xpath, enter=True)

    for p in range(10):
        fpath = fpath_namer(shop_id, 'search', kw, p)
        if not op.exists(fpath):
            sleep(2)
            driver.smooth_scroll()
            driver.save_page(fpath, scroll_to_bottom=True)

        searches, products = kw_parsing(fpath, kw, searches, products)

        # Going to next page if need be
        next_page_click = '//a[@class="resultsNext"]'  # TODO : modify
        if not op.exists(fpath_namer(shop_id, 'ctg', ctg, p+1)):
            if not driver.check_exists_by_xpath(next_page_click):
                break
            else:
                driver.waitclick(next_page_click)
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
