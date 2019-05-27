from io import BytesIO

from lxml import etree

parser = etree.HTMLParser()
import requests_cache, imghdr
from validators import validate_raw_files
from create_csvs import create_csvs

from ers import all_keywords_uk as keywords, mh_brands
from matcher import BrandMatcher
from ers import COLLECTION_DATE, file_hash, img_path_namer, fpath_namer, headers
import requests
import shutil
from helpers.random_user_agent import randomua

# Init variables and assets
shop_id = 'tesco'
root_url = 'https://www.tesco.com/'
session = requests_cache.CachedSession()
session.headers = {'User-Agent': randomua()}
country = 'UK'
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
    'champagne': 'https://www.tesco.com/groceries/en-GB/shop/drinks/all?department=Wine&viewAll=department%2Caisle%2Cshelf&aisle=Champagne%20%26%20Sparkling%20Wine&shelf=Champagne&page={page}',
    'sparkling': 'https://www.tesco.com/groceries/en-GB/shop/drinks/all?department=Wine&viewAll=department%2Caisle%2Cshelf&aisle=Champagne%20%26%20Sparkling%20Wine&shelf=Sparkling%20Wine&page={page}',
    #'still_wines': 'https://www.tesco.com/groceries/en-GB/shop/drinks/all?department=Wine&viewAll=department%2Caisle&aisle=White%20Wine&page={page}',
    'whisky': 'https://www.tesco.com/groceries/en-GB/shop/drinks/spirits/whisky?page={page}',
    'cognac': 'https://www.tesco.com/groceries/en-GB/shop/drinks/spirits/all?aisle=Brandy%20%26%20Cognac&viewAll=aisle%2Cshelf&shelf=Cognac&page={page}',
    'vodka'     : 'https://www.tesco.com/groceries/en-GB/shop/drinks/spirits/all?aisle=Vodka&viewAll=aisle&page={page}',
    'red_wine'  : 'https://www.tesco.com/groceries/en-GB/shop/drinks/wine/red-wine?viewAll=aisle&page={page}',
    'white_wine': 'https://www.tesco.com/groceries/en-GB/shop/drinks/wine/white-wine?viewAll=aisle&page={page}',
    'gin'       : 'https://www.tesco.com/groceries/en-GB/shop/drinks/spirits/gin?viewAll=aisle&page={page}',
    'tequila'   : 'https://www.tesco.com/groceries/en-GB/shop/drinks/spirits/tequila-and-sambuca?viewAll=aisle&page={page}',
    'rum'       : 'https://www.tesco.com/groceries/en-GB/shop/drinks/spirits/rum?viewAll=aisle&page={page}',
    'brandy'    : 'https://www.tesco.com/groceries/en-GB/shop/drinks/spirits/brandy-and-cognac?viewAll=aisle&page={page}',
    'liquor'    : 'https://www.tesco.com/groceries/en-GB/shop/drinks/spirits/liqueurs-and-speciality-spirits?viewAll=aisle&page={page}',
}


def getproduct(a):
    data = {
        'url': a.xpath('.//div[@class="product-details--content"]/a/@href')[0],
        'pdct_name_on_eretailer': a.xpath('.//a[@class="product-tile--title product-tile--browsable"]/text()')[0],
        'volume': a.xpath('.//a[@class="product-tile--title product-tile--browsable"]/text()')[0].split()[-1],
        'price': getprice(''.join(a.xpath('.//div[contains(@class,"price-per-sellable-unit")]//span[@class="value"]/text()'))),
        'img': a.xpath('.//img/@src')[0]
    }
    assert data['price'] or a.xpath('.//p[text()="Sorry, this product is currently unavailable"]')
    assert '/products/' in data['url']
    products[data['url']] = data


for cat, url in categories_urls.items():
    categories[cat] = []
    for page in range(1, 100):
        r = session.get(url.format(page=page))
        tree = etree.parse(BytesIO(r.content), parser=parser)
        articles = tree.xpath('//div[@class="product-tile--wrapper"]')
        aurls = [a.xpath('.//div[@class="product-details--content"]/a/@href')[0]
                 for a in articles]
        if not articles or all(a in categories[cat] for a in aurls) or len(articles) < 24:
            categories[cat] += aurls
            [getproduct(a) for a in articles]
            print(cat,  len(articles), len(categories[cat]))
            break
        print(cat,  len(articles), len(categories[cat]))
        categories[cat] += aurls
        [getproduct(a) for a in articles]

for kw in keywords:
    searches[kw] = []
    for page in range(1, 10):
        r = session.get('https://www.tesco.com/groceries/en-GB/search?query={kw}&page={page}'.format(
            page=page, kw='%20'.join(kw.split())))
        tree = etree.parse(BytesIO(r.content), parser=parser)
        articles = tree.xpath('//div[@class="product-tile--wrapper"]')
        aurls = [a.xpath('.//div[@class="product-details--content"]/a/@href')[0] for a in articles]
        if not articles or all(a in searches[kw] for a in aurls) or len(articles) < 24:
            searches[kw] += aurls
            [getproduct(a) for a in articles]
            print(cat,  len(articles), len(categories[cat]))
            break
        searches[kw] += aurls
        [getproduct(a) for a in articles]
        print(kw,  len(articles), len(searches[kw]))

brm = BrandMatcher()
for url, product in products.items():
    if brm.find_brand(product['pdct_name_on_eretailer'])['brand'] in mh_brands:
        r = session.get('https://www.tesco.com' + url)
        tree = etree.parse(BytesIO(r.content), parser=parser)
        data = {
            'pdct_img_main_url': tree.xpath('//img/@src')[0],
            'ctg_denom_txt': tree.xpath('//span[@class="plp--breadcrumbs--crumb"]/a/text()'),
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
