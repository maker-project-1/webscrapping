
import os.path as op

from lxml import etree

parser = etree.HTMLParser(encoding='utf-8')
from time import sleep
from urllib.parse import urlsplit, parse_qs
import requests
import requests_cache, imghdr
from ers import all_keywords_ch as keywords, fpath_namer, mh_brands, clean_url, headers

from matcher import BrandMatcher
from ers import COLLECTION_DATE, file_hash, img_path_namer
import shutil
from custom_browser import CustomDriver
from parse import parse
from validators import validate_raw_files
from create_csvs import create_csvs

# Init variables and assets
shop_id = "denner_wineshop_ch"
root_url = "http://denner-wineshop.ch"
requests_cache.install_cache(fpath_namer(shop_id, 'requests_cache'))
country = "CH"


searches, categories, products = {}, {}, {}
# If necessary
driver = CustomDriver(headless=False)


def getprice(pricestr):
    if pricestr == '':
        return pricestr
    pricestr = re.sub("[^0-9.fr]", "", pricestr.lower())
    price = parse('fr.{pound:d}.{pence:d}', pricestr)
    if price is None:
        print("Problem in price")
        price = parse('{pence:d}p', pricestr)
        return price.named['pence']
    else:
        return price.named['pound'] * 100 + price.named['pence']

urls_ctgs_dict = {
    "sparkling": "https://www.denner.ch/de/shop/wein/pre/search/result/?wine_type=261&p={page}",
    "champagne": "https://www.denner.ch/de/shop/wein/pre/search/result/?wine_type=261&p={page}",
    "red_wine": "https://www.denner.ch/de/shop/wein/pre/search/result/?wine_type=42&p={page}",
    "white_wine": "https://www.denner.ch/de/shop/wein/pre/search/result/?wine_type=41&p={page}",
    "still_wines": "https://www.denner.ch/de/shop/wein/pre/search/result/?wine_type=41&p={page}",
}

import re


def get_pricestr(s):
    regex_price = 'Einzelflasche\: (Fr\. \d*\.\d*)'
    # s = 'Einzelflasche: Fr. 36.95 Karton à 6 x 75 cl'
    reobj = re.search(regex_price, s)
    if reobj:
        return reobj.group(1)
    return ''


def get_promopricestr(s):
    regex_price = 'statt (Fr\. \d*\.\d*)'
    # s = 'Einzelflasche: Fr. 36.95 Karton à 6 x 75 cl'
    reobj = re.search(regex_price, s)
    if reobj:
        return reobj.group(1)
    return ''


# Category Scraping
for ctg, url in urls_ctgs_dict.items():
    categories[ctg] = []
    number_of_pdcts_in_ctg = 0
    for p in range(50):
        print(ctg, p)
        urlp = url.format(page=p + 1)
        fpath = fpath_namer(shop_id, 'ctg', ctg, p)
        if not op.exists(fpath):
            driver.get(urlp)
            driver.save_page(fpath)
            sleep(2)
        tree = etree.parse(open(fpath, 'rb'), parser=parser)
        for li in tree.xpath('//li[@class="item product product-item denner-tile"]'):
            produrl = li.xpath('.//a[@class="product photo denner-tile__link"]/@href')[0]
            produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(
                urlsplit(produrl).query) else produrl
            produrl = clean_url(produrl, root_url)
            products[produrl] = {
                'pdct_name_on_eretailer': ' '.join(
                    ''.join(li.xpath('.//div[@class="denner-tile__title"]/h2//text()')).split()),
                'raw_price': ' '.join(''.join(li.xpath('.//div[@class="denner-price__additional"]//text()')).split()),
                'raw_promo_price': ' '.join(''.join(li.xpath('.//div[@class="denner-price__additional"]//text()')).split()),
            }
            print(products[produrl], produrl)
            products[produrl]['raw_price'] = get_pricestr(products[produrl]['raw_price'])
            products[produrl]['raw_promo_price'] = get_promopricestr(products[produrl]['raw_promo_price'])
            products[produrl]['price'] = getprice(products[produrl]['raw_price'].replace('Flasche', ''))
            products[produrl]['promo_price'] = getprice(products[produrl]['raw_promo_price'])
            print(products[produrl])

            categories[ctg].append(produrl)

        # Checking if it was the last page
        if len(set(categories[ctg])) == number_of_pdcts_in_ctg:
            break
        else:
            number_of_pdcts_in_ctg = len(set(categories[ctg]))

print(categories)


# KW searches Scraping - with selenium - with nb page hard-coded in url - multiple page per search
search_url = "https://www.denner.ch/de/shop/wein/pre/search/result/?p=1&q={kw}"
for kw in keywords:
    print(kw)
    searches[kw] = []
    # Storing and extracting infos
    urlp = search_url.format(kw=kw)

    fpath = fpath_namer(shop_id, 'search', kw, 0)
    if not op.exists(fpath):
        driver.get(urlp)
        driver.save_page(fpath)
    tree = etree.parse(open(fpath, 'rb'), parser=parser)
    for li in tree.xpath('//li[@class="item product product-item denner-tile"]'):
        produrl = li.xpath('.//a[@class="product photo denner-tile__link"]/@href')[0]
        produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(
            urlsplit(produrl).query) else produrl
        produrl = clean_url(produrl, root_url)
        products[produrl] = {
            'pdct_name_on_eretailer': ' '.join(
                ''.join(li.xpath('.//div[@class="denner-tile__title"]/h2//text()')).split()),
            'raw_price': ' '.join(''.join(li.xpath('.//div[@class="denner-price__additional"]//text()')).split()),
            'raw_promo_price': ' '.join(''.join(li.xpath('.//div[@class="denner-price__additional"]//text()')).split()),
        }
        print(products[produrl], produrl)
        products[produrl]['raw_price'] = get_pricestr(products[produrl]['raw_price'])
        products[produrl]['raw_promo_price'] = get_promopricestr(products[produrl]['raw_promo_price'])
        products[produrl]['price'] = getprice(products[produrl]['raw_price'].replace('Flasche', ''))
        products[produrl]['promo_price'] = getprice(products[produrl]['raw_promo_price'])
        print(products[produrl])

        searches[kw].append(produrl)
    print(kw, 0, len(searches[kw]))


# Download the pages - with selenium
brm = BrandMatcher()
for url in sorted(list(set(products))):
    d = products[url]
    if brm.find_brand(d['pdct_name_on_eretailer'])['brand'] in mh_brands:
        print(d['pdct_name_on_eretailer'])
        url_mod = clean_url(url, root_url=root_url)
        fpath = fpath_namer(shop_id, 'pdct', d['pdct_name_on_eretailer'])
        if not op.exists(fpath):
            driver.get(url_mod)
            driver.save_page(fpath)
        tree = etree.parse(open(fpath, 'rb'), parser=parser)
        products[url].update({
            'volume': ' '.join(''.join(tree.xpath('//div[@class="head"]/p/text()')).split()),
            'pdct_img_main_url': clean_url(''.join(tree.xpath('//img[contains(@class, "fotorama__img")]/@src')), root_url),
            'ctg_denom_txt': ' '.join(' '.join(tree.xpath('//div[@class="head"]/p//text()')).split()),
        })
        print(products[url])


# Download images
for url, pdt in products.items():
     if 'pdct_img_main_url' in pdt and pdt['pdct_img_main_url'] and brm.find_brand(pdt['pdct_name_on_eretailer'])['brand'] in mh_brands:
         print(pdt['pdct_name_on_eretailer'] + "." + pdt['pdct_img_main_url'].split('.')[-1], pdt['pdct_img_main_url'].split('.'))
         response = requests.get(pdt['pdct_img_main_url'], stream=True, verify=False, headers=headers)
         # response.raw.decode_content = True
         tmp_file_path = '/tmp/' + shop_id + 'mhers_tmp_{}.imgtype'.format(abs(hash(pdt['pdct_img_main_url'])))
         img_path = img_path_namer(shop_id, pdt['pdct_name_on_eretailer'])
         with open(tmp_file_path, 'wb') as out_file:
             shutil.copyfileobj(response.raw, out_file)
         if imghdr.what(tmp_file_path) is not None:
             img_path = img_path.split('.')[0] + '.' + imghdr.what('/tmp/' + shop_id + 'mhers_tmp_{}.imgtype'.format(abs(hash(pdt['pdct_img_main_url']))))
             shutil.copyfile('/tmp/' + shop_id + 'mhers_tmp_{}.imgtype'.format(abs(hash(pdt['pdct_img_main_url']))), img_path)
             products[url].update({'img_path': img_path, 'img_hash': file_hash(img_path)})

create_csvs(products, categories, searches, shop_id, fpath_namer(shop_id, 'raw_csv'), COLLECTION_DATE)
validate_raw_files(fpath_namer(shop_id, 'raw_csv'))
driver.quit()