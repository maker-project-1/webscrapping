import os
import os.path as op

from lxml import etree

parser = etree.HTMLParser(encoding='utf-8')
from time import sleep
from urllib.parse import urlsplit, parse_qs
import requests
import requests_cache, imghdr

from validators import validate_raw_files
from create_csvs import create_csvs
from ers import all_keywords_uk as keywords, fpath_namer, mh_brands, clean_url, headers

from matcher import BrandMatcher
from ers import COLLECTION_DATE, file_hash, img_path_namer, TEST_PAGES_FOLDER_PATH
import shutil
from custom_browser import CustomDriver
from parse import parse
from ers import clean_xpathd_text


# Init variables and assets
shop_id = 'the_champagne_company'
root_url = 'https://thechampagnecompany.com'
country = 'UK'
requests_cache.install_cache(fpath_namer(shop_id, 'requests_cache'))
driver = CustomDriver(headless=True)
brm = BrandMatcher()
searches, categories, products = {}, {}, {}


# If necessary
def getprice(pricestr):
    if pricestr == '':
        return pricestr
    pricestr = pricestr.replace(',', '').strip()
    price = parse('£{pound:d}.{pence:d}', pricestr)
    if price is None:
        price = parse('{pence:d}p', pricestr)
        return price.named['pence']
    else:
        return price.named['pound'] * 100 + price.named['pence']



# ##################
# # CTG page xpathing #
# ##################
ctg_page_test_url = 'https://thechampagnecompany.com/champagne'
exple_ctg_page_path = op.join(TEST_PAGES_FOLDER_PATH, shop_id, 'ctg_page_test.html')  # TODO : store the file
os.makedirs(op.dirname(exple_ctg_page_path), exist_ok=True)
ctg, test_categories, test_products = '', {'': []}, {}

# driver.get(ctg_page_test_url)
# driver.save_page(exple_ctg_page_path, scroll_to_bottom=True)


def ctg_parsing(fpath, ctg, categories, products):  # TODO : modify xpaths
    tree = etree.parse(open(fpath, 'rb'), parser=parser)
    for li in tree.xpath('//ol/li[@class="item product product-item"]'):
        if not li.xpath('(.//a/@href)[1]'):
            continue
        produrl = li.xpath('(.//a/@href)[1]')[0]
        produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
        products[produrl] = {
            'pdct_name_on_eretailer': clean_xpathd_text(li.xpath('.//*[@class="product name product-item-name"]//text()')),
            'volume': clean_xpathd_text(li.xpath('.//*[@class="product name product-item-name"]//text()')),
            'raw_price': clean_xpathd_text(li.xpath('.//span[contains(@id,"product-price")]/span//text()')),
            'raw_promo_price': clean_xpathd_text(li.xpath('.//span[@data-price-type="oldPrice"]/span//text()')),
        }
        products[produrl]['brnd'] = brm.find_brand(products[produrl]['pdct_name_on_eretailer'])['brand']
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
search_page_test_url = 'https://thechampagnecompany.com/catalogsearch/result/?q={kw}?product_list_limit=48&p={page}'
exple_kw_page_path = op.join(TEST_PAGES_FOLDER_PATH, shop_id, 'kw_page_test.html') # TODO : store the file
os.makedirs(op.dirname(exple_ctg_page_path), exist_ok=True)
kw_test, test_searches, test_products = 'champagne', {"champagne": []}, {}

# driver.get(search_page_test_url.format(kw=kw_test,page=1))
# driver.save_page(exple_kw_page_path, scroll_to_bottom=True)


def kw_parsing(fpath, kw, searches, products):  # TODO : modify xpaths
    tree = etree.parse(open(fpath, 'rb'), parser=parser)
    for li in tree.xpath('//ol/li[@class="item product product-item"]'):
        if not li.xpath('(.//a/@href)[1]'):
            continue
        produrl = li.xpath('(.//a/@href)[1]')[0]
        produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
        products[produrl] = {
            'pdct_name_on_eretailer': clean_xpathd_text(li.xpath('.//*[@class="product name product-item-name"]//text()')),
            'volume': clean_xpathd_text(li.xpath('.//*[@class="product name product-item-name"]//text()')),
            'raw_price': clean_xpathd_text(li.xpath('.//span[contains(@id, "product-price")]/span//text()')),
            'raw_promo_price': clean_xpathd_text(li.xpath('.//span[@data-price-type="oldPrice"]/span//text()')),
        }
        products[produrl]['brnd'] = brm.find_brand(products[produrl]['pdct_name_on_eretailer'])['brand']
        print(products[produrl], produrl)
        products[produrl]['price'] = getprice(products[produrl]['raw_price'])
        products[produrl]['promo_price'] = getprice(products[produrl]['raw_promo_price'])
        print(products[produrl])

        searches[kw].append(produrl)
    return searches, products


kw_parsing(exple_kw_page_path, kw_test, test_searches, test_products)



###################
# # PDCT page xpathing #
###################
pdct_page_test_url = 'https://thechampagnecompany.com/moet-chandon-rose-champagne-mini-champagne-truffles-gift-set'
exple_pdct_page_path = op.join(TEST_PAGES_FOLDER_PATH, shop_id, 'pdct_page_test.html') # TODO: store the file
test_url, test_products = '', {'': {}}
os.makedirs(op.dirname(exple_pdct_page_path), exist_ok=True)
test_products = {pdct_page_test_url: {}}

# driver.get(pdct_page_test_url)
# driver.save_page(exple_pdct_page_path, scroll_to_bottom=True)


def pdct_parsing(fpath, url, products): # TODO : modify xpaths
    tree = etree.parse(open(fpath), parser=parser)
    products[url].update({
        'pdct_img_main_url': clean_url(''.join(tree.xpath('//img[contains(@class, "fotorama__img")]/@src')[:1]), root_url),
    })
    print(products[url])
    return products


pdct_parsing(exple_pdct_page_path, pdct_page_test_url, test_products)


###################
# # CTG scrapping #
###################


urls_ctgs_dict = {
    'champagne': 'https://thechampagnecompany.com/champagne?product_list_limit=48&p={page}',
    'sparkling': 'https://thechampagnecompany.com/search?query=sparkling%20wine&product_list_limit=48&p={page}',
    'still_wines': 'https://thechampagnecompany.com/wine/wine-type/fine-wine/colour/white?product_list_limit=48&p={page}',
    'whisky': 'https://thechampagnecompany.com/premium-spirits/type/whisky-whiskey?product_list_limit=48&p={page}',
    'cognac': 'https://thechampagnecompany.com/premium-spirits/type/cognac-brandy?product_list_limit=48&p={page}',
    'vodka': 'https://thechampagnecompany.com/premium-spirits/type/vodka?product_list_limit=48&p={page}',
    'red_wine': 'https://thechampagnecompany.com/wine/colour/red?product_list_limit=48&p={page}',
    'white_wine': 'https://thechampagnecompany.com/wine/colour/white?product_list_limit=48&p={page}',
    'gin': 'https://thechampagnecompany.com/premium-spirits/type/gin?product_list_limit=48&p={page}',
    'liquor': 'https://thechampagnecompany.com/premium-spirits/type/liqueurs?product_list_limit=48&p={page}',
    'tequila': 'https://thechampagnecompany.com/premium-spirits/type/tequila?product_list_limit=48&p={page}',
    'rum': 'https://thechampagnecompany.com/premium-spirits/type/rum?product_list_limit=48&p={page}',
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
kw_search_url = "https://thechampagnecompany.com/catalogsearch/result/?q={kw}&product_list_limit=48"  # TODO : modify URL
for kw in keywords:
    searches[kw] = []
    number_of_pdcts_in_kw_search = 0
    if not op.exists(fpath_namer(shop_id, 'search', kw, 0)):
        driver.get(kw_search_url.format(kw=kw))

    for p in range(1):
        fpath = fpath_namer(shop_id, 'search', kw, p)
        if not op.exists(fpath):
            sleep(2)
            driver.smooth_scroll()
            driver.save_page(fpath, scroll_to_bottom=True)
        searches, products = kw_parsing(fpath, kw, searches, products)

    print(kw, len(searches[kw]))


######################################
# # Product pages scraping ###########
######################################

# Download the pages - with selenium
l = []
for url in sorted(list(set(products))):
    d = products[url]
    if d['brnd'] in mh_brands and d['pdct_name_on_eretailer'] not in l:
        l.append(d['pdct_name_on_eretailer'])
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
    if 'pdct_img_main_url' in pdt and pdt['pdct_img_main_url'] and pdt['brnd'] in mh_brands:
        print(pdt['pdct_name_on_eretailer'] + "." + pdt['pdct_img_main_url'].split('.')[-1])
        print(pdt['pdct_img_main_url'], )
        response = requests.get(pdt['pdct_img_main_url'], stream=True, verify=False, headers=headers)
        # # response.raw.decode_content = True
        tmp_file_path = '/tmp/' + shop_id + 'mhers_tmp_{}.imgtype'.format(abs(hash(pdt['pdct_img_main_url'])))
        img_path = img_path_namer(shop_id, pdt['pdct_name_on_eretailer'])
        print(img_path)
        # driver.get(pdt['pdct_img_main_url'])
        # driver.save_page(tmp_file_path)
        with open(tmp_file_path, 'wb') as out_file:
            out_file.write(response.content)
        if imghdr.what(tmp_file_path) is not None:
            img_path = img_path.split('.')[0] + '.' + imghdr.what(
                '/tmp/' + shop_id + 'mhers_tmp_{}.imgtype'.format(abs(hash(pdt['pdct_img_main_url']))))
            shutil.copyfile('/tmp/' + shop_id + 'mhers_tmp_{}.imgtype'.format(abs(hash(pdt['pdct_img_main_url']))), img_path)
            products[url].update({'img_path': img_path, 'img_hash': file_hash(img_path)})
        else:
            print('Warning :', tmp_file_path, imghdr.what(tmp_file_path))


create_csvs(products, categories, searches, shop_id, fpath_namer(shop_id, 'raw_csv'), COLLECTION_DATE)
validate_raw_files(fpath_namer(shop_id, 'raw_csv'))
driver.quit()
