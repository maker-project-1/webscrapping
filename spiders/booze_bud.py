import json
from lxml import etree
import json

from lxml import etree

parser = etree.HTMLParser()
from urllib.parse import quote_plus
import requests
import requests_cache, imghdr


from validators import validate_raw_files
from create_csvs import create_csvs
from ers import all_keywords_aus as keywords, fpath_namer, mh_brands, headers
from matcher import BrandMatcher
from ers import COLLECTION_DATE, file_hash, img_path_namer
import shutil

from pprint import pprint
# Init variables and assets
shop_id = 'booze_bud'
root_url = 'https://boozebud.com'
requests_cache.install_cache(fpath_namer(shop_id, 'requests_cache'))
country = 'AUS'
searches, categories, products = {}, {}, {}

categories_urls = {
    'champagne': 'https://boozebud.com/a/products?btype=wine&page=1&style=champagne&pagesize=100&page={page}',
    'sparkling': 'https://boozebud.com/a/products?t=sparklingwine&page={page}&pagesize=100',
    'still_wines': 'https://boozebud.com/a/products?t=wine&page={page}&pagesize=100',
    'red_wine': 'https://boozebud.com/a/products?t=redwine&page={page}&pagesize=100',
    'white_wine': 'https://boozebud.com/a/products?t=wine&page={page}&pagesize=100',
    'whisky': 'https://boozebud.com/a/products?style=whisky&page={page}&pagesize=100',
    'cognac': 'https://boozebud.com/a/products?subregion=cognac&page={page}&pagesize=100',
    'vodka': 'https://boozebud.com/a/products?style=vodka&page={page}&pagesize=100',
    'gin': 'https://boozebud.com/a/products?style=gin&page={page}&pagesize=100',
    'tequila': 'https://boozebud.com/a/products?style=tequila&page={page}&pagesize=100',
    'rum': 'https://boozebud.com/a/products?style=rum&page={page}&pagesize=100',
    'liquor': 'https://boozebud.com/a/products?style=liqueurs&page={page}&pagesize=100',
}

for cat, url in categories_urls.items():
    categories[cat] = []
    print(cat)
    for page in range(1, 100):
        r = requests.get(url.format(page=page))
        data = json.loads(r.content.decode('utf8'))
        categories[cat] += [p['url'] for p in data['results'] if not " mix" in p['name'].lower()]
        for p in data['results']:
            qt, price = min((v['qty'], v['price']) for v in p['variants'])
            if (not " mix" in p['name'].lower()):
                products[p['url']] = {
                    'url': p['url'],
                    'pdct_name_on_eretailer': p['brandName'] + ' ' + p['name'],
                    'volume': str(p['bottleVolume'] if 'bottleVolume' in p else None),
                    'price': price / qt,
                    'raw_price': "$" + str(price / qt),
                    'pdct_img_main_url': p['largeImage']
                }
                pprint(products[p['url']])
        if len(categories[cat]) >= data['totalAvailable']:
            break

searchesall = {}
for kw in keywords:
    searchesall[kw] = []
    searches[kw] = []
    for page in range(1, 100):
        url = 'https://boozebud.com/a/search?page={kw}&pagesize=100&searchterm={kw}'.format(
            page=page, kw=quote_plus(kw))
        r = requests.get(url)
        data = json.loads(r.content.decode('utf8'))
        searchesall[kw] += [p['path'] for p in data['results']]
        for p in data['results']:
            if (p['type'] == 'product') and (not " mix" in p['title'].lower()):
                if p['path'] not in products:
                    print('fromsearch')
                    products[p['path']] = {
                        'url': p['path'],
                        'pdct_name_on_eretailer': p['title'],
                        'img': p['image'],
                        'fromsearch': True
                    }
                searches[kw].append(p['path'])
        if len(searchesall[kw]) >= data['totalAvailable']:
            break

for url, p in products.items():
    if 'fromsearch' in p:
        print(url)
        r = requests.get('https://boozebud.com/a/producturl' + url)
        p = json.loads(r.content)
        qt, price = min((v['qty'], v['price']) for v in p['variants'])
        products[p['url']] = {
            'url': p['url'],
            'pdct_name_on_eretailer': p['brandName'] + ' ' + p['name'],
            'volume': str(p['bottleVolume'] if 'bottleVolume' in p else None),
            'price': price / qt,
            'raw_price': "$" + str(price / qt),
        }
        if 'largeImage' in p:
            products[p['url']]['pdct_img_main_url'] = p['largeImage']


# Download images
brm = BrandMatcher()
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
