from lxml import etree
from io import BytesIO
from io import BytesIO

from lxml import etree

parser = etree.HTMLParser(encoding='utf-8')
from time import sleep
from urllib.parse import urlsplit, parse_qs
import requests
import requests_cache, imghdr

from validators import validate_raw_files
from create_csvs import create_csvs

from ers import all_keywords_aus as keywords, fpath_namer, mh_brands, clean_url, headers
from matcher import BrandMatcher
from ers import COLLECTION_DATE, file_hash, img_path_namer
import shutil
from parse import parse
import re

# Init variables and assets
shop_id = 'shortys_liquor'
root_url = 'http://shortysliquor.com.au'
requests_cache.install_cache(fpath_namer(shop_id, 'requests_cache'))
country = 'UK'
searches, categories, products = {}, {}, {}

# Adaptable
def getprice(pricestr):
    if pricestr == '':
        return None
    pricestr = re.sub("[^0-9.$]", "", pricestr)
    pricestr = pricestr.replace(',', '').strip()
    price = parse('${dol:d}.{pence:d}', pricestr)
    if price is None:
        price = parse('{${dol:d}', pricestr)
        return price.named['dol']
    else:
        return price.named['dol'] * 100 + price.named['pence']


# CTG scrapping
urls_ctgs_dict = {
    'champagne': 'http://shortysliquor.com.au/champagne-sparkling?limit=all&variety=3777',
    'sparkling': 'http://shortysliquor.com.au/champagne-sparkling/sparkling-variety/imported-sparkling?limit=all',
    'still_wines': 'http://shortysliquor.com.au/white-wine?limit=all',
    'whisky': 'http://shortysliquor.com.au/spirits-fortified/spirit-variety/malts-whisky?limit=all',
    'cognac': 'http://shortysliquor.com.au/spirits-fortified/spirit-variety/cognac-brandy?limit=all',
    'vodka': 'http://shortysliquor.com.au/spirits-fortified/spirit-variety/vodka?limit=all',
    'white_wine': 'http://shortysliquor.com.au/white-wine?limit=all',
    'red_wine': 'http://shortysliquor.com.au/red-wine?limit=all',
    'brandy': 'http://shortysliquor.com.au/spirits-fortified/spirit-variety/cognac-brandy?limit=all',
    'liquor': 'http://shortysliquor.com.au/spirits-fortified/spirit-variety/liqueurs?limit=all',
    'rum': 'http://shortysliquor.com.au/spirits-fortified/spirit-variety/rum?limit=all',
    'gin': 'http://shortysliquor.com.au/spirits-fortified/spirit-variety/gin-1/rum?limit=all',
}


# Category Scraping - One page per category
for ctg, url in urls_ctgs_dict.items():
    categories[ctg] = []
    r = requests.get(url)
    tree = etree.parse(BytesIO(r.content), parser=parser)
    for li in tree.xpath('//html[1]//ul[contains(@class, "products-grid")]/li'):
        produrl = li.xpath('.//h2/a/@href')[0]
        produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(
            urlsplit(produrl).query) else produrl
        categories[ctg].append(produrl)
        products[produrl] = {
            'pdct_name_on_eretailer': " ".join(li.xpath('.//h2//text()')),
            'raw_price': ''.join(w for t in li.xpath('.//span[@class="bx-price"]/span/text()') for w in t.split()).strip(),
        }
        print(products[produrl], produrl)
        products[produrl]['price'] = getprice(products[produrl]['raw_price'])
        print(products[produrl])
    if not r.from_cache:
        sleep(3)
    print(ctg, len(categories[ctg]))


# KW searches Scraping - with requests - one page per search
kw_search_url = "http://shortysliquor.com.au/catalogsearch/result/?q={kw}&limit=all"
for kw in keywords:
    searches[kw] = []
    url = kw_search_url.format(kw=kw)
    r = requests.get(url)
    tree = etree.parse(BytesIO(r.content), parser=parser)
    for li in tree.xpath('//html[1]//ul[contains(@class, "products-grid")]/li'):
        produrl = li.xpath('.//h2/a/@href')[0]
        produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
        products[produrl] = {
            'pdct_name_on_eretailer': " ".join(li.xpath('.//h2//text()')),
            'raw_price': ''.join(w for t in li.xpath('.//span[@class="bx-price"]/span/text()') for w in t.split()).strip(),
        }
        products[produrl]['price'] = getprice(products[produrl]['raw_price'])
        print(products[produrl])
        searches[kw].append(produrl)
    assert all(products[produrl][k] for k in products[produrl])
    if not r.from_cache:
        sleep(3)
    print(kw, len(searches[kw]))


# Download the pages - with requests
brm = BrandMatcher()
for url in sorted(products):
    d = products[url]
    if brm.find_brand(d['pdct_name_on_eretailer'])['brand'] in mh_brands:
        print(d['pdct_name_on_eretailer'])
        url_mod = clean_url(url, root_url=root_url)
        r = requests.get(url_mod, headers)
        with open('/tmp/' + shop_id + ' ' + d['pdct_name_on_eretailer'].replace('/', "-") + '.html', 'wb') as f:
            f.write(r.content)
        tree = etree.parse(BytesIO(r.content), parser=parser)
        products[url] = {
            'pdct_name_on_eretailer': ' '.join(w for t in tree.xpath('//div[@class="product-name"]/h1//text()') for w in t.split()).strip(),
            'volume': ' '.join(w for t in tree.xpath('//div[@class="product-name"]/h1//text()') for w in t.split()).strip(),
            'raw_price': ''.join(w for t in tree.xpath('//div[@class="product-shop"]//span[@class="regular-price"]//span[@class="bx-price"]//text()') for w in t.split()),
            'raw_promo_price': ''.join(tree.xpath('//xpath//text()')),
            'pdct_img_main_url': ''.join(tree.xpath('//a[@id="main-image"]/@href')),
            'ctg_denom_txt': ' '.join(w for t in tree.xpath('//div[@class="product-name"]/h1//text()') for w in t.split()).strip(),
        }
        print(products[url])
        products[url]['price'] = getprice(products[url]['raw_price'])
        products[url]['promo_price'] = getprice(products[url]['raw_promo_price'])
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
