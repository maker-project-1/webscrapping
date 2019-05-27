import os.path as op
from io import BytesIO

from lxml import etree

parser = etree.HTMLParser(encoding='utf-8')
from time import sleep
from urllib.parse import urlsplit, parse_qs
import re
import requests
import requests_cache, imghdr

from validators import validate_raw_files
from create_csvs import create_csvs

from ers import all_keywords_fr as keywords, fpath_namer, mh_brands, clean_url, headers
from matcher import BrandMatcher
from ers import COLLECTION_DATE, file_hash, img_path_namer
import shutil
from custom_browser import CustomDriver
from parse import parse


# Init variables and assets
shop_id = 'millesima'
root_url = 'https://www.millesima.fr/'
requests_cache.install_cache(fpath_namer(shop_id, 'requests_cache'))
country = 'FR'
searches, categories, products = {}, {}, {}
driver = CustomDriver(headless=True, download_images=False)
urls_ctgs_dict = {'champagne': "https://www.millesima.fr/tous-nos-vins/france/champagne.html?#facet:&productBeginIndex:0&facetLimit:&orderBy:&pageView:list&minPrice:&maxPrice:&pageSize:500&"}


def getprice(pricestr):
    pricestr = pricestr.replace(' ', '')
    if pricestr == '':
        return pricestr
    price = parse('{dol:d},{pence:d}€', pricestr)
    if price is None:
        price = parse('{pence:d}p', pricestr)
        return price.named['pence']
    else:
        return price.named['dol'] * 100 + price.named['pence']


# Category Scraping - with requests - one page per category
for ctg, url in urls_ctgs_dict.items():
    categories[ctg] = []
    fpath = fpath_namer(shop_id, 'ctg', ctg, 0)
    if not op.exists(fpath):
        driver.get(url)
        sleep(60)
        driver.save_page(fpath, scroll_to_bottom=True)
    tree = etree.parse(BytesIO(open(fpath, 'rb').read()), parser=parser)
    for li in tree.xpath('//div[@class="product_listing_container"]/ul/li'):
        produrl = li.xpath('.//a/@href')[0]
        produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
        products[produrl] = {
            'pdct_name_on_eretailer': ' '.join(''.join(li.xpath('.//*[@itemprop="name"]//text()')).split()),
            'raw_price': ''.join(w for t in li.xpath('.//span[contains(@id, "unitPrice")]/text()') for w in t.split()).strip(),
            'raw_promo_price': ''.join(w for t in li.xpath('.//xpath/text()') for w in t.split()).strip(),
        }
        if products[produrl]['raw_price'] == '':
            products[produrl]['raw_price'] = ''.join(w for t in li.xpath('.//span[contains(@id, "offerPrice_")]//text()') for w in t.split()).strip()

        raw_price = re.sub("[^0-9,€]", "", products[produrl]['raw_price'])
        products[produrl]['price'] = getprice(raw_price)
        products[produrl]['promo_price'] = None
        print(products[produrl])
        categories[ctg].append(produrl)
    print(ctg, len(categories[ctg]))


# KW searches Scraping - with selenium - one page per search
search_url = "https://www.millesima.fr/SearchDisplay?categoryId=&storeId=11652&catalogId=10554&langId=-2&sType=SimpleSearch&resultCatEntryType=2&showResultsPage=true&searchSource=Q&pageView=&beginIndex=0&pageSize=12&searchTerm={kw}&#facet:&productBeginIndex:0&facetLimit:&orderBy:&pageView:list&minPrice:&maxPrice:&pageSize:100&"
for kw in keywords:
    searches[kw] = []
    # Storing and extracting infos
    fpath = fpath_namer(shop_id, 'search', kw, 0)
    if not op.exists(fpath):
        driver.get(search_url.format(kw=kw))
        sleep(15)
        driver.save_page(fpath, scroll_to_bottom=True)
    tree = etree.parse(BytesIO(open(fpath, 'rb').read()), parser=parser)
    for li in tree.xpath('//div[@class="product_listing_container"]/ul/li'):
        produrl = li.xpath('.//a/@href')[0]
        produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
        products[produrl] = {
            'pdct_name_on_eretailer': ' '.join(''.join(li.xpath('.//*[@itemprop="name"]//text()')).split()),
            'raw_price': ''.join(w for t in li.xpath('.//span[contains(@id, "unitPrice")]/text()') for w in t.split()).strip(),
            'raw_promo_price':  ''.join(w for t in li.xpath('.//xpath/text()') for w in t.split()).strip(),
        }
        if products[produrl]['raw_price'] == '':
            products[produrl]['raw_price'] = ''.join(w for t in li.xpath('.//span[contains(@id, "offerPrice_")]//text()') for w in t.split()).strip()
        raw_price = re.sub("[^0-9,€]", "", products[produrl]['raw_price'])
        products[produrl]['price'] = getprice(raw_price)
        products[produrl]['promo_price'] = None
        print(products[produrl])
        searches[kw].append(produrl)
    print(kw, len(searches[kw]))


# Download the pages - with requests
brm = BrandMatcher()
for url in sorted(list(set(products))):
    d = products[url]
    if brm.find_brand(d['pdct_name_on_eretailer'])['brand'] in mh_brands:
        print(d['pdct_name_on_eretailer'])
        url_mod = clean_url(url, root_url=root_url)
        r = requests.get(url_mod, headers)
        with open('/tmp/' + shop_id + ' ' + d['pdct_name_on_eretailer'].replace('/', "-") + '.html', 'wb') as f:
            f.write(r.content)
        tree = etree.parse(BytesIO(r.content), parser=parser)
        products[url].update({
            'pdct_img_main_url': clean_url(''.join(tree.xpath('//img[@id="productMainImage"]/@src')), root_url),
            'ctg_denom_txt': ' '.join(' '.join(tree.xpath('//*[@id="widget_breadcrumb"]//text()')).split()),
            'volume': ' '.join(' '.join(tree.xpath('//*[contains(@id, "product_shortdescription")]//text()')).split()),
        })
        print(products[url])
        if not r.from_cache:
            sleep(3)


# Download images
for url, pdt in products.items():
     if 'pdct_img_main_url' in pdt and pdt['pdct_img_main_url'] and brm.find_brand(pdt['pdct_name_on_eretailer'])['brand'] in mh_brands:
         print(pdt['pdct_name_on_eretailer'] + "." + pdt['pdct_img_main_url'].split('.')[-1])
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
