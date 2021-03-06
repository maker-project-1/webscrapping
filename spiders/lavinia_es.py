import re
from io import BytesIO

from lxml import etree

parser = etree.HTMLParser(encoding='utf-8')
from time import sleep
from urllib.parse import urlsplit, parse_qs
import requests
import requests_cache, imghdr
from ers import all_keywords_es as keywords, fpath_namer, mh_brands, clean_url, headers

from matcher import BrandMatcher
from ers import COLLECTION_DATE, file_hash, img_path_namer
import shutil
from custom_browser import CustomDriver
from parse import parse
from validators import validate_raw_files
from create_csvs import create_csvs

# Init variables and assets
shop_id = "lavinia_es"
root_url = "http://www.lavinia.es"
requests_cache.install_cache(fpath_namer(shop_id, 'requests_cache'))
country = "ES"

searches, categories, products = {}, {}, {}
# If necessary
driver = CustomDriver(headless=False)


def getprice(pricestr):
    if pricestr == '':
        return pricestr
    pricestr = re.sub("[^0-9,€]", "", pricestr)
    price = parse('{pound:d},{pence:d}€', pricestr)
    if price is None:
        price = parse('{pence:d}p', pricestr)
        return price.named['pence']
    else:
        return price.named['pound'] * 100 + price.named['pence']


urls_ctgs_dict = {
    "cognac": "http://www.lavinia.es/es/t/destilados/brandy-cognac-y-armagnac?page={page}&per_page=36",
    "vodka": "http://www.lavinia.es/es/t/destilados/vodka?page={page}&per_page=36",
    "champagne": "http://www.lavinia.es/es/l/grandes-maisons-de-champagne?page={page}&per_page=36",
    "still_wines": "http://www.lavinia.es/es/t/internacionales/francia/bordeaux?page={page}&per_page=36",
    "whisky": "http://www.lavinia.es/es/t/destilados/whisky?page={page}&per_page=36",
    "gin": "https://www.lavinia.es/es/t/destilados/gin?page={page}&per_page=36",
    "rum": "https://www.lavinia.es/es/t/destilados/ron-y-cachaca?page={page}&per_page=36",
}


# Category Scraping - with requests - one page per category
for ctg, url in urls_ctgs_dict.items():
    categories[ctg] = []
    number_of_pdcts_in_ctg = 0
    for p in range(100):
        urlp = url.format(page=p+1)
        r = requests.get(urlp)
        tree = etree.parse(BytesIO(r.content), parser=parser)
        with open('/tmp/test.html', 'wb') as f:
            f.write(r.content)
        for li in tree.xpath('//div[@class="col_sls sfull"]//div[contains(@class, "m-product expandable")]'):
            produrl = li.xpath('.//strong/a/@href')[0]
            produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
            produrl = clean_url(produrl, root_url)
            products[produrl] = {
                'pdct_name_on_eretailer': "".join(li.xpath('.//strong[@itemprop="name"]//text()')),
                'raw_price': ''.join(w for t in li.xpath('.//div[@class="product_prices"]//dl//dd[1]//text()') for w in t.split()).strip(),
                'raw_promo_price':
                    ' '.join(w for t in li.xpath('.//div[@class="product_prices"]//dl//dd[2]//text()') for w in t.split()).strip(),
                # 'raw_promo_price': ''.join(w for t in li.xpath('.//div[@class="full_price_text"]/text()') for w in t.split()).strip(),
            }
            print(products[produrl], produrl)
            products[produrl]['price'] = getprice(products[produrl]['raw_price'])
            products[produrl]['promo_price'] = getprice(products[produrl]['raw_promo_price'])
            print(products[produrl])

            categories[ctg].append(produrl)
        # Checking if it was the last page
        if len(set(categories[ctg])) == number_of_pdcts_in_ctg:
            break
        else:
            number_of_pdcts_in_ctg = len(set(categories[ctg]))

        if not r.from_cache:
            sleep(2)
    print(ctg, len(categories[ctg]))


import json
# kw_search_url = "https://sblavinia.empathybroker.com/sb-lavinia/services/search?filter=&jsonCallback=angular.callbacks._0&lang=fr&q={kw}&rows=100&sort=&start=0"
kw_search_url = "https://sblavinia.empathybroker.com/sb-lavinia/services/search?jsonCallback=angular.callbacks._2&lang=es&q={kw}&rows=100&sort=&start=0"
for kw in keywords:
    searches[kw] = []
    url = kw_search_url.format(kw=kw)
    r = requests.get(url)
    text = r.text.replace('angular.callbacks._2(', '')
    text = text[0:len(text)-1]
    # print(type(json.loads(text)), )
    dicts = json.loads(text)["docs"]
    for d in dicts:
        produrl = d['url']
        products[produrl] = {
            'pdct_name_on_eretailer': d["name"],
            'raw_price': d['formatted_real_price'] + '€',
            'raw_promo_price': d['formatted_price'] + '€',
            # 'raw_promo_price': ''.join(w for t in li.xpath('.//div[@class="full_price_text"]/text()') for w in t.split()).strip(),
        }
        # print(products[produrl], produrl)
        products[produrl]['price'] = getprice(products[produrl]['raw_price'])
        if products[produrl]['raw_price'] != products[produrl]['raw_promo_price']:
            products[produrl]['promo_price'] = getprice(products[produrl]['raw_promo_price'])
        else:
            products[produrl]['promo_price'], products[produrl]['raw_promo_price'] = None, ''
        print(products[produrl])
        searches[kw].append(produrl)
    if not r.from_cache:
        sleep(3)
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
            'volume': ''.join(tree.xpath('//h1/span/text()')).strip(),
            'pdct_img_main_url': clean_url(''.join(tree.xpath('//article/img/@src')), root_url),
            'ctg_denom_txt': ' '.join(tree.xpath('//div[@itemprop="breadcrumbs"]//text()')),
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



