from io import BytesIO

from lxml import etree

parser = etree.HTMLParser()
from urllib.parse import quote_plus
import requests_cache, imghdr
from validators import validate_raw_files
from create_csvs import create_csvs

from ers import all_keywords_de as keywords, mh_brands, headers
from matcher import BrandMatcher
from ers import COLLECTION_DATE, file_hash, img_path_namer, fpath_namer
import shutil
import requests
from helpers.random_user_agent import randomua

# Init variables and assets
shop_id = 'galeria'
root_url = 'https://www.galeria-kaufhof.de'
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
    'whisky': 'https://www.galeria-kaufhof.de/wein-gourmet/spirituosen/whisky/?page={page}',
    'champagne': 'https://www.galeria-kaufhof.de/wein-gourmet/wein-sekt/champagner/?page={page}',
    'cognac': 'https://www.galeria-kaufhof.de/search?q=Cognac&page={page}',
    'vodka': 'https://www.galeria-kaufhof.de/wein-gourmet/spirituosen/wodka-tequila/?page={page}',
    'sparkling': 'https://www.galeria-kaufhof.de/wein-gourmet/wein-sekt/sekt-prosecco/?page={page}',
    'still_wines': 'https://www.galeria-kaufhof.de/wein-gourmet/wein-sekt/weisswein/?page={page}',
    'gin': 'https://www.galeria-kaufhof.de/wein-gourmet/spirituosen/gin/?page={page}',
    'rum': 'https://www.galeria-kaufhof.de/wein-gourmet/spirituosen/rum/?page={page}',
    'liquor': 'https://www.galeria-kaufhof.de/wein-gourmet/spirituosen/likoere/?page={page}',
}


def getproduct(a):
    data = {
        'url': a.xpath('.//a[@class="gk-article__link"]/@href')[0],
        'pdct_name_on_eretailer': " ".join(" ".join(a.xpath('.//span[@class="gk-article__description"]//text()')).split()),
        'ctg_denom_txt': a.xpath('.//span[@class="gk-article__description"]//text()')[0],
        'price': getprice((a.xpath('.//div[@class="gk-price"]/text()') or a.xpath('.//ins[@class="gk-price-new"]/text()'))[0]),
        'pdct_img_main_url': (a.xpath('.//img[@itemprop="image"]/@data-src') or
                a.xpath('.//img[@itemprop="image"]/@src'))[0]
    }
    # from pprint import pprint
    # pprint(data)
    assert data['pdct_name_on_eretailer']
    products[data['url']] = data


for cat, url in categories_urls.items():
    categories[cat] = []
    for page in range(1, 100):
        r = session.get(url.format(page=page))
        tree = etree.parse(BytesIO(r.content), parser=parser)
        articles = tree.xpath('//div[@class="gk-article gk-article--big"]')
        aurls = [a.xpath('.//a[@class="gk-article__link"]/@href')[0] for a in articles]
        if not articles or all(a in categories[cat] for a in aurls):
            break
        print(cat,  len(articles), len(categories[cat]))
        categories[cat] += aurls
        [getproduct(a) for a in articles]


for kw in keywords:
    searches[kw] = []
    for page in range(1, 10):
        r = session.get('https://www.galeria-kaufhof.de/search?q={kw}&page={page}'.format(
            page=page, kw=quote_plus(kw)))
        tree = etree.parse(BytesIO(r.content), parser=parser)
        articles = tree.xpath('//div[@class="gk-article gk-article--big"]')
        aurls = [a.xpath('.//a[@class="gk-article__link"]/@href')[0] for a in articles]
        if not articles or all(a in searches[kw] for a in aurls):
            break
        searches[kw] += aurls
        [getproduct(a) for a in articles]
        print(kw,  len(articles), len(searches[kw]))

brm = BrandMatcher()
# for url, product in products.items():
#     if brm.find_brand(product['pdct_name_on_eretailer'])['brand'] in mh_brands:
#         r = session.get('https://www.galeria-kaufhof.de' + url)
#         print('https://www.galeria-kaufhof.de' + url)
#         tree = etree.parse(BytesIO(r.content), parser=parser)
#         data = {
#             'ctg_denom_txt': tree.xpath('//div[@class="ev-page__breadcrumb"]//a/span/text()'),
#             'pdct_img_main_url': tree.xpath('//div[@class="ev-images__main__imagewrap"]/img/@src')[0],
#         }
#         print(data)
#         product.update(data)


# Download images
for url, pdt in products.items():
    # print(pdt['pdct_img_main_url'], pdt['pdct_name_on_eretailer'], brm.find_brand(pdt['pdct_name_on_eretailer'])['brand'])
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

create_csvs(products, categories, searches, shop_id, fpath_namer(shop_id, 'raw_csv'), COLLECTION_DATE)
validate_raw_files(fpath_namer(shop_id, 'raw_csv'))
