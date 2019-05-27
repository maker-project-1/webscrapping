import os.path as op

from lxml import etree

parser = etree.HTMLParser(encoding='utf-8')
import requests
import requests_cache, imghdr

from validators import validate_raw_files
from create_csvs import create_csvs

from ers import all_keywords_usa as keywords, fpath_namer, mh_brands
from matcher import BrandMatcher
from ers import COLLECTION_DATE, file_hash, img_path_namer
import shutil
from custom_browser import CustomDriver
from parse import parse


# Init variables and assets
shop_id = 'kroger'
root_url = 'https://www.kroger.com/'
requests_cache.install_cache(fpath_namer(shop_id, 'requests_cache'))
country = 'USA'
searches, categories, products = {}, {}, {}
driver = CustomDriver(headless=False, download_images=True, firefox=True)
brm = BrandMatcher()

urls_ctgs_dict = {
            'champagne': 'https://www.kroger.com/pl/champagne/0818000004?page={page}&tab=0',
            'sparkling': 'https://www.kroger.com/pl/sparkling-wine/0818000003?page={page}&tab=0',
            'still_wines': 'https://www.kroger.com/pl/white-wine/08122?page={page}&tab=0',
            'whisky': 'https://www.kroger.com/pl/scotch-whiskey/0812100579?page={page}&tab=0',
            'cognac': 'https://www.kroger.com/pl/brandy-cognac/0812100572?page={page}&tab=0',
            'vodka': 'https://www.kroger.com/pl/vodka/0812100582?page={page}&tab=0',
            'red_wine': 'https://www.kroger.com/pl/red-wine/08120?page={page}&tab=0',
            'white_wine': 'https://www.kroger.com/pl/white-wine/08122?page={page}&tab=0',
            'gin': 'https://www.kroger.com/pl/gin/0812100575?page={page}&tab=0',
            'tequila': 'https://www.kroger.com/pl/tequila/0812100581?page={page}&tab=0',
            'brandy': 'https://www.kroger.com/pl/brandy-cognac/0812100572?page={page}&tab=0',
            'rum': 'https://www.kroger.com/pl/rum/0812100578?page={page}&tab=0',
            'liquor': 'https://www.kroger.com/pl/scotch-whiskey/0812100579?page={page}&tab=0',
        }

headers = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en-US,en;q=0.8,fr-FR;q=0.6,fr;q=0.4",
    "Connection": "keep-alive",
    "content-length": "0",
    "Host": "www.kroger.com",
    "Upgrade-insecure-requests": "1",
    # "referer": "https://www.kroger.com/search?query=" + search_params + "",
    'content-encoding' :'gzip',
    "user-agent": "Toto",
}

headers2 = {
    'origin': 'https://www.kroger.com',
    # 'x-xsrf-token': '392ad84b-c96f-4163-829a-db9fe6c90c8f',
    'accept-language': 'en-US,en;q=0.9',
    'content-type': 'application/json;charset=UTF-8',
    'accept': 'application/json, text/plain, */*',
    'referer': 'https://www.kroger.com/pl/scotch-whiskey/0812100579',
    'authority': 'www.kroger.com',
    'accept-encoding': 'gzip, deflate, br',
    "user-agent": "Toto",
}


def getprice(pricestr):
    pricestr = pricestr.replace(' ', '')
    if pricestr == '':
        return pricestr
    price = parse('${dol:d}.{pence:d}', pricestr)
    if price is None:
        price = parse('{pence:d}p', pricestr)
        return price.named['pence']
    else:
        return price.named['dol'] * 100 + price.named['pence']


# Category Scraping - with requests - multiple pages per category
for ctg, url in urls_ctgs_dict.items():
    categories[ctg] = []
    number_of_pdcts_in_ctg = 0
    for p in range(100):
        urlp = url.format(page=p+1)
        fpath = fpath_namer(shop_id, 'ctg', ctg, p)
        taxoId = url.split('?')[0].split('/')[-1]
        url_p = "https://www.kroger.com/search/api/searchAll?start={start}&count=24&tab=0&taxonomyId={taxoId}&monet=true".format(start=24*p, taxoId=taxoId)
        # Scrap1
        if not op.exists(fpath.replace('.html', '-1.json')):
            r1 = requests.post(url_p, headers=headers)
            print("Calling", url_p)
            with open(fpath.replace('.html', '-1.json'), 'wb') as f:
                f.write(r1.content)
        import json
        with open(fpath.replace('.html', '-1.json'), 'rb') as f:
            d1 = json.load(f)
        if not d1['upcs']:
            break
        post_data2 = json.dumps({'upcs': d1['upcs'], "filterBadProducts": True})
        # Scrap2
        if not op.exists(fpath.replace('.html', '-2.json')):
            r2 = requests.post('https://www.kroger.com/products/api/products/details', headers=headers2, data=post_data2)
            print("Calling", url_p)
            with open(fpath.replace('.html', '-2.json'), 'wb') as f:
                f.write(r2.content)
        with open(fpath.replace('.html', '-2.json'), 'rb') as f:
            d2 = json.load(f)
        for d in d2['products']:
            produrl = d['upc']
            categories[ctg].append(produrl)
            products[produrl] = {}
            products[produrl]['pdct_name_on_eretailer'] = d['description']
            products[produrl]['volume'] = d['customerFacingSize']
            images = [x for x in d['images'] if x['perspective'] == "front" and x['size'] == 'large']
            if images:
                products[produrl]['pdct_img_main_url'] = images[0]['url']


# Category Scraping - with requests - multiple pages per category
for kw in keywords:
    searches[kw] = []
    number_of_pdcts_in_kw_search = 0
    for p in range(100):
        fpath = fpath_namer(shop_id, 'search', kw, p)
        url_p = "https://www.kroger.com/search/api/searchAll?start={start}&count=24&tab=0&query={kw}&monet=true".format(start=24*p, kw=kw)
        # Scrap1
        if not op.exists(fpath.replace('.html', '-1.json')):
            r1 = requests.post(url_p, headers=headers)
            print("Calling", url_p)
            with open(fpath.replace('.html', '-1.json'), 'wb') as f:
                f.write(r1.content)
        import json
        with open(fpath.replace('.html', '-1.json'), 'rb') as f:
            d1 = json.load(f)
        if not d1['upcs']:
            break
        post_data2 = json.dumps({'upcs': d1['upcs'], "filterBadProducts": True})
        # Scrap2
        if not op.exists(fpath.replace('.html', '-2.json')):
            r2 = requests.post('https://www.kroger.com/products/api/products/details', headers=headers2, data=post_data2)
            print("Calling", url_p)
            with open(fpath.replace('.html', '-2.json'), 'wb') as f:
                f.write(r2.content)
        with open(fpath.replace('.html', '-2.json'), 'rb') as f:
            d2 = json.load(f)
        for d in d2['products']:
            produrl = d['upc']
            searches[kw].append(produrl)
            products[produrl] = {}
            products[produrl]['pdct_name_on_eretailer'] = d['description']
            products[produrl]['volume'] = d['customerFacingSize']
            images = [x for x in d['images'] if x['perspective'] == "front" and x['size'] == 'large']
            if images:
                products[produrl]['pdct_img_main_url'] = images[0]['url']

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



