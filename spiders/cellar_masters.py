from io import BytesIO
import shutil
from io import BytesIO
from urllib.parse import urlparse, parse_qs, quote_plus

import imghdr
import requests
import requests_cache
from lxml import etree
from parse import parse

from create_csvs import create_csvs
from ers import COLLECTION_DATE, file_hash, img_path_namer, fpath_namer
from ers import all_keywords_aus as keywords, mh_brands, clean_url
from ers import headers
from helpers.random_user_agent import randomua
from matcher import BrandMatcher
from validators import validate_raw_files

parser = etree.HTMLParser()

# Init variables and assets
shop_id = 'cellar_masters'
root_url = 'https://www.cellarmasters.com.au'
session = requests_cache.CachedSession(fpath_namer(shop_id, 'requests_cache'))
session.headers = {'User-Agent': randomua()}
country = 'AUS'
searches, categories, products = {}, {}, {}
tmp_searches, tmp_categories = {}, {}


def getprice(pricestr):
    if not pricestr:
        return
    price = parse('${pound:d}', pricestr)
    if price:
        return price.named['pound'] * 100
    price = parse('${pound:d}.{pence:d}', pricestr)
    if price:
        return price.named['pound'] * 100 + price.named['pence']
    price = parse('${th:d},{pound:d}', pricestr)
    if price:
        return price.named['th'] * 100000 + price.named['pound'] * 100
    price = parse('${th:d},{pound:d}.{pence:d}', pricestr)
    if price:
        return price.named['th'] * 100000 + price.named['pound'] * 100 + price.named['pence']
    raise Exception


categories_urls = {
    'champagne': 'https://www.cellarmasters.com.au/sparkling/champagne',
    'sparkling': 'https://www.cellarmasters.com.au/sparkling',
    'still_wines': 'https://www.cellarmasters.com.au/red-wine?style=white-wine&sort=score&ps=100&page={page}',
}


def getproduct(a, type_get, cat_or_search_id):
    try:
        data = {
            'url': a.xpath('.//div[@class="bottle listing"]/a/@href')[0],
            'pdct_name_on_eretailer': a.xpath('.//a[@class="productlink straight resultsTemplate_Title"]/text()')[0].strip(),
            'price':  int(float(a.xpath('.//span[@class="bottle-now in-listing"]//text()')[1]) * 100),
            'img':  'https://www.cellarmasters.com.au' + a.xpath('.//img[@class="resultsTemplate_img"]/@src')[0].replace('_175.png', '_670.png')
        }
    except:
        data = {
            'url': a.xpath('.//div[@class="bottle listing"]/a/@href')[0],
            'pdct_name_on_eretailer': a.xpath('.//a[@class="productlink straight resultsTemplate_Title"]/text()')[0].strip(),
            'price':  getprice(a.xpath('.//h2[@class="now-price"]/span/text()')[0]),
            'img':  'https://www.cellarmasters.com.au' + a.xpath('.//img[@class="resultsTemplate_img"]/@src')[0].replace('_175.png', '_670.png')
        }

    data['url'] = parse_qs(urlparse(data['url']).query)['url'][0]
    if type_get == 'category':
        categories[cat_or_search_id].append(data['url'])

    if type_get == 'search':
        if data['url'] == 'h':
            print("WARNING: ", data)
        searches[cat_or_search_id].append(data['url'])

    products[data['url']] = data


for cat, url in categories_urls.items():
    categories[cat] = []
    tmp_categories[cat] = []
    for page in range(1, 100):
        r = session.get(url.format(page=page))
        tree = etree.parse(BytesIO(r.content), parser=parser)
        articles = tree.xpath('//div[@class="row listing straight"]')
        aurls = [a.xpath('.//div[@class="bottle listing"]/a/@href')[0]
                 for a in articles]
        if not articles or all(a in tmp_categories[cat] for a in aurls):
            break
        print(cat,  len(articles), len(categories[cat]))
        print(aurls)
        tmp_categories[cat].extend(aurls)
        [getproduct(a, 'category', cat) for a in articles]


for kw in keywords:
    searches[kw] = []
    tmp_searches[kw] = []
    for page in range(1, 10):
        r = session.get('https://www.cellarmasters.com.au/?w={kw}&sort=score&ps=100&page={page}'.format(
            page=page, kw=quote_plus(kw)))
        tree = etree.parse(BytesIO(r.content), parser=parser)
        articles = tree.xpath('//div[@class="row listing straight"]')
        aurls = [a.xpath('.//div[@class="bottle listing"]/a/@href')[0] for a in articles]
        if not articles or all(a in tmp_searches[kw] for a in aurls):
            break
        tmp_searches[kw].extend(aurls)
        [getproduct(a, 'search', kw) for a in articles]
        print(kw,  len(articles), len(searches[kw]))

brm = BrandMatcher()
for url, product in products.items():
    if brm.find_brand(product['pdct_name_on_eretailer'])['brand'] in mh_brands:
        r = session.get(url)
        with open('/tmp/cellar.html', 'wb') as fd:
            fd.write(r.content)
        tree = etree.parse(BytesIO(r.content), parser=parser)
        data = {
            'ctg_denom_txt': " ".join(tree.xpath('//div[@class="breadcrumb-nav"]//li/a/text()')),
            'pdct_img_main_url': clean_url(tree.xpath('//img[@itemprop="image"]/@src')[0], root_url)
        }
        product.update(data)
        print(product['pdct_img_main_url'])


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
