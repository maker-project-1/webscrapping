from io import BytesIO

from lxml import etree

parser = etree.HTMLParser()
from urllib.parse import quote_plus
import requests_cache, imghdr
from validators import validate_raw_files
from create_csvs import create_csvs

from ers import all_keywords_de as keywords, mh_brands
from matcher import BrandMatcher
from ers import COLLECTION_DATE, file_hash, img_path_namer, fpath_namer, headers
import shutil
from helpers.random_user_agent import randomua
import requests

# Init variables and assets
shop_id = 'tesdorpf'
root_url = 'https://www.tesdorpf.de'
session = requests_cache.CachedSession(fpath_namer(shop_id, 'requests_cache'))
session.headers = {'User-Agent': randomua()}
country = 'DE'
searches, categories, products = {}, {}, {}


from parse import parse


def getprice(pricestr):
    if pricestr.startswith('ab '):
        pricestr = pricestr[3:]
    if not pricestr:
        return
    price = parse('{pound:d} €', pricestr)
    if price:
        return price.named['pound'] * 100
    price = parse('{pound:d},{pence:d} €', pricestr)
    if price:
        return price.named['pound'] * 100 + price.named['pence']
    price = parse('{th:d}.{pound:d} €', pricestr)
    if price:
        return price.named['th'] * 100000 + price.named['pound'] * 100
    price = parse('{th:d}.{pound:d},{pence:d} €', pricestr)
    if price:
        return price.named['th'] * 100000 + price.named['pound'] * 100 + price.named['pence']
    print('pb price', pricestr)
    raise Exception


categories_urls = {
    'champagne': 'https://www.tesdorpf.de/sortiment/franzoesische-weine/champagne?page={page}',
    'cognac': 'https://www.tesdorpf.de/suche?term=cognac&page={page}',
    # 'sparkling': '',
    # 'vodka': '',
    'whisky': 'https://www.tesdorpf.de/suche?term=whisky&page={page}',
    'still_wines': 'http://www.totalwine.com/wine/c/c0020?viewall=true&pagesize=100&page={page}'
}


def getproduct(a):
    data = {
        'url': a.xpath('.//div[@class="product-info-title"]/a/@href')[0],
        'pdct_name_on_eretailer': a.xpath('.//div[@class="product-info-title"]/a/text()')[0].strip(),
        'price': getprice(a.xpath('.//div[contains(@class, "product-info-price-current")]/text()')[0]),
        'img': a.xpath('.//div/a/img/@src')[0]
    }
    assert data['price']
    products[data['url']] = data


for cat, url in categories_urls.items():
    categories[cat] = []
    for page in range(1, 100):
        r = session.get(url.format(page=page))
        tree = etree.parse(BytesIO(r.content), parser=parser)
        articles = tree.xpath('//li/div[@class="product-grid-item-inset"]')
        aurls = [a.xpath('.//div[@class="product-info-title"]/a/@href')[0] for a in articles]
        if not articles or all(a in categories[cat] for a in aurls):
            break
        print(cat,  len(articles), len(categories[cat]))
        categories[cat] += aurls
        [getproduct(a) for a in articles]


for kw in keywords:
    searches[kw] = []
    for page in range(1, 10):
        r = session.get('https://www.tesdorpf.de/suche?term={kw}&page={page}'.format(
            page=page, kw=quote_plus(kw)))
        tree = etree.parse(BytesIO(r.content), parser=parser)
        articles = tree.xpath('//li/div[@class="product-grid-item-inset"]')
        aurls = [a.xpath('.//div[@class="product-info-title"]/a/@href')[0] for a in articles]
        if not articles or all(a in searches[kw] for a in aurls):
            break
        searches[kw] += aurls
        [getproduct(a) for a in articles]
        print(kw,  len(articles), len(searches[kw]))


brm = BrandMatcher()
for url, product in products.items():
    if brm.find_brand(product['pdct_name_on_eretailer'])['brand'] in mh_brands:
        r = session.get('https://www.tesdorpf.de' + url)
        print("IMAGE", 'https://www.tesdorpf.de' + url, '/tmp/' + shop_id + ' ' + product['pdct_name_on_eretailer'].replace('/', "-") + '.html')
        with open('/tmp/' + shop_id + ' ' + product['pdct_name_on_eretailer'].replace('/', "-") + '.html', 'wb') as f:
            f.write(r.content)
        tree = etree.parse(BytesIO(r.content), parser=parser)
        data = {
            'pdct_img_main_url': 'https://www.tesdorpf.de' + "".join(tree.xpath('//img[@itemprop="image"]/@src')[:1]),
        }
        product.update(data)


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