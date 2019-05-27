import os.path as op
from io import BytesIO

from lxml import etree

parser = etree.HTMLParser()
from urllib.parse import quote_plus
import requests_cache, imghdr
from validators import validate_raw_files
from create_csvs import create_csvs

from ers import all_keywords_aus as keywords, mh_brands, headers
from matcher import BrandMatcher
from ers import COLLECTION_DATE, file_hash, img_path_namer, fpath_namer
import shutil
from helpers.random_user_agent import randomua
import requests
from custom_browser import CustomDriver
from time import sleep


# Init variables and assets
shop_id = 'my_bottle_shop'
root_url = 'https://www.mybottleshop.com.au'
session = requests_cache.CachedSession(fpath_namer(shop_id, 'requests_cache'))
session.headers = {'User-Agent': randomua()}
driver = CustomDriver(headless=False, download_images=True)
with session.cache_disabled():
    session.get('https://www.mybottleshop.com.au/directory/currency/switch/currency/AUD/uenc/')
# print(session.cookies)
country = 'AUS'
searches, categories, products = {}, {}, {}
from parse import parse


def getprice(pricestr):
    if not pricestr:
        return
    price = parse('{pound:d}', pricestr)
    if price:
        return price.named['pound'] * 100
    price = parse('{pound:d}.{pence:d}', pricestr)
    if price:
        return price.named['pound'] * 100 + price.named['pence']
    price = parse('{th:d},{pound:d}', pricestr)
    if price:
        return price.named['th'] * 100000 + price.named['pound'] * 100
    price = parse('{th:d},{pound:d}.{pence:d}', pricestr)
    if price:
        return price.named['th'] * 100000 + price.named['pound'] * 100 + price.named['pence']
    raise Exception


categories_urls = {
    'champagne': 'https://www.mybottleshop.com.au/champagne/?p={page}',
    'sparkling': 'https://www.crackawines.com.au/collections/champagne-sparkling-wines#filter:tags_varietal:Champagne/filter:tags_varietal:Sparkling/page:{page}',
    'still_wines': 'https://www.crackawines.com.au/collections/white-wines#page:{page}',
    'whisky': 'https://www.mybottleshop.com.au/spirits/buy-whiskey-online/?p={page}',
    'cognac': 'https://www.mybottleshop.com.au/spirits/cognac-and-brandy/?p={page}',
    'vodka': 'https://www.mybottleshop.com.au/spirits/vodka/?p={page}',
    'gin': 'https://www.mybottleshop.com.au/spirits/gin/?p={page}',
    'tequila': 'https://www.mybottleshop.com.au/spirits/tequila-and-mezcal/?p={page}',
    'rum': 'https://www.mybottleshop.com.au/spirits/rum/?p={page}',
}


def getproduct(a):
    data = {
        'url': a.xpath('.//h2[@itemprop="name"]/a/@href')[0],
        'pdct_name_on_eretailer': a.xpath('.//h2[@itemprop="name" and @class="active-mobile product-name   "]//text()')[0].strip(),
        'price': int(float(a.xpath('.//span[@itemprop="price"]/@content')[0]) * 100),
        'img': a.xpath('.//img[@width="430"]/@data-original')[0]
    }
    # pprint(data['pdct_name_on_eretailer'])
    # print(data)
    # assert data['price'] > 50000 or a.xpath(
    #    './/span[@itemprop="price"]/span[1]/text()')[0] == 'AUD $'
    # assert '/products/' in data['url']
    products[data['url']] = data


for cat, url in categories_urls.items():
    categories[cat] = []
    for page in range(1, 100):
        r = session.get(url.format(page=page))
        tree = etree.parse(BytesIO(r.content), parser=parser)
        articles = tree.xpath('id("em-grid-mode")/ul[1]/li')
        aurls = [a.xpath('.//h2[@itemprop="name"]/a/@href')[0]
                 for a in articles]
        if not articles or all(a in categories[cat] for a in aurls):
            break
        print(cat,  len(articles), len(categories[cat]))
        categories[cat] += aurls
        [getproduct(a) for a in articles]


for kw in keywords:
    searches[kw] = []
    for page in range(1, 10):
        r = session.get('https://www.mybottleshop.com.au/catalogsearch/result/?p={page}&q={kw}'.format(
            page=page, kw=quote_plus(kw)))
        tree = etree.parse(BytesIO(r.content), parser=parser)
        articles = tree.xpath('id("em-grid-mode")/ul[1]/li')
        aurls = [a.xpath('.//h2[@itemprop="name"]/a/@href')[0] for a in articles]
        if not articles or all(a in searches[kw] for a in aurls):
            break
        searches[kw] += aurls
        [getproduct(a) for a in articles]
        print(kw,  len(articles), len(searches[kw]))

brm = BrandMatcher()
for url, product in products.items():
    if brm.find_brand(product['pdct_name_on_eretailer'])['brand'] in mh_brands:
        print(url)
        fname = fpath_namer(shop_id, 'pdct', product['pdct_name_on_eretailer'], 0)
        if not op.exists(fname):
            driver.get(url)
            sleep(2)
            driver.save_page(fname, scroll_to_bottom=True)
        tree = etree.parse(open(fname), parser=parser)
        data = {
            'pdct_img_main_url': tree.xpath('//meta[@property="og:image"]/@content')[0],
        }
        product.update(data)

# Download images
for url, pdt in products.items():
     if 'pdct_img_main_url' in pdt and pdt['pdct_img_main_url'] and brm.find_brand(pdt['pdct_name_on_eretailer'])['brand'] in mh_brands:
         print(pdt['pdct_name_on_eretailer'] + "." + pdt['pdct_img_main_url'].split('.')[-1])
         print(pdt['pdct_img_main_url'])
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
         else:
             print("WARNING : ", tmp_file_path, pdt['pdct_img_main_url'], imghdr.what(tmp_file_path))

create_csvs(products, categories, searches, shop_id, fpath_namer(shop_id, 'raw_csv'), COLLECTION_DATE)
validate_raw_files(fpath_namer(shop_id, 'raw_csv'))
driver.quit()
