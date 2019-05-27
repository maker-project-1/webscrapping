from io import BytesIO

from lxml import etree

parser = etree.HTMLParser()
from urllib.parse import quote_plus
import requests_cache, imghdr
from validators import validate_raw_files
from create_csvs import create_csvs

from ers import all_keywords_aus as keywords, mh_brands
from matcher import BrandMatcher
from ers import COLLECTION_DATE, file_hash, img_path_namer, fpath_namer, headers
import shutil
from helpers.random_user_agent import randomua
import requests

# Init variables and assets
shop_id = 'grayswine'
root_url = 'http://www.grayswine.com.au'
session = requests_cache.CachedSession(fpath_namer(shop_id, 'requests_cache'))
session.headers = {'User-Agent': randomua()}
country = 'UK'
searches, categories, products = {}, {}, {}


from parse import parse


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
    'champagne': 'http://www.grayswine.com.au/wine/wine-type/sparkling-wine-champagne/variety/champagne?page={page}?page-size=100',
    'sparkling': 'http://www.grayswine.com.au/wine/wine-type/sparkling-wine-champagne?variety=prosecco%2csparkling-rose%2cimported-sparkling%2cdomestic-sparkling&page={page}&page-size=100',
    'still_wines': 'http://www.grayswine.com.au/wine/wine-type/white-wine/variety/sauvignon-blanc?wine-type=sparkling-wine-champagne%2cwhite-wine&page-size=100&sort=most-relevant&page={page}&page-size=100',
    'whisky': 'http://www.grayswine.com.au/search.aspx?q=whisky&page={page}?page-size=100',
    'cognac': 'http://www.grayswine.com.au/search.aspx?q=cognac&page={page}?page-size=100',
    'vodka': 'http://www.grayswine.com.au/search.aspx?q=vodka&page={page}?page-size=100',
    'red_wine': 'http://www.grayswine.com.au/wine/wine-type/red-wine&page={page}?page-size=100',
    'white_wine': 'http://www.grayswine.com.au/wine/wine-type/white-wine&page={page}?page-size=100',
}


from pprint import pprint
for cat, url in categories_urls.items():
    categories[cat] = []
    for page in range(1, 30):
        r = session.get(url.format(page=page))
        tree = etree.parse(BytesIO(r.content), parser=parser)
        prices = tree.xpath('//p[@class="unit-price"]/text()')
        names = tree.xpath('//div[@class="s3rw"]/div[@class="s3r"]/div[@class="s3c"]//text()')
        images = tree.xpath('//div[@class="s3rw"]/div[@class="s3r s3r-image"]//img/@data-src')
        purls = tree.xpath('//div[@class="s3rw"]/div[@class="s3r s3r-image"]//a/@href')
        if not purls:
            break
        for price, name, image, purl in zip(prices, names, images, purls):
            data = {
                'url': purl,
                'pdct_name_on_eretailer': name,
                'price': getprice(price),
                'img': image
            }
            categories[cat].append(purl)
            products[purl] = data
    print(cat, len(categories[cat]))


for kw in keywords:
    searches[kw] = []
    for page in range(1, 3):
        r = session.get(
            'http://www.grayswine.com.au/search.aspx?q={kw}&page={page}'.format(page=page, kw=quote_plus(kw)))
        tree = etree.parse(BytesIO(r.content), parser=parser)
        prices = tree.xpath('//p[@class="unit-price"]/text()')
        names = tree.xpath('//div[@class="s3rw"]/div[@class="s3r"]/div[@class="s3c"]//text()')
        images = tree.xpath('//div[@class="s3rw"]/div[@class="s3r s3r-image"]//img/@data-src')
        purls = tree.xpath('//div[@class="s3rw"]/div[@class="s3r s3r-image"]//a/@href')
        if not purls:
            break
        for price, name, image, purl in zip(prices, names, images, purls):
            data = {
                'url': purl,
                'pdct_name_on_eretailer': name,
                'price': getprice(price),
                'img': image
            }
            searches[kw].append(purl)
            products[purl] = data
            pprint(data)

brm = BrandMatcher()
for url, product in products.items():
    if brm.find_brand(product['pdct_name_on_eretailer'])['brand'] in mh_brands:
        print('http://www.grayswine.com.au' + url)
        r = session.get('http://www.grayswine.com.au' + url)
        tree = etree.parse(BytesIO(r.content), parser=parser)
        data = {
            'pdct_img_main_url': tree.xpath('//img[@itemprop="image"]/@src')[0],
            'ctg_denom_txt': tree.xpath('//div[@class="bread-crumbs bread-crumbs-invisible"]//span/text()'),
        }
        product.update(data)


# Download images
for url, pdt in products.items():
     if 'pdct_img_main_url' in pdt and pdt['pdct_img_main_url'] and brm.find_brand(pdt['pdct_name_on_eretailer'])['brand'] in mh_brands:
         print(pdt['pdct_name_on_eretailer'] + "." + pdt['pdct_img_main_url'].split('.')[-1])
         response = requests.get(pdt['pdct_img_main_url'], headers=headers)
         # response.raw.decode_content = True
         tmp_file_path = '/tmp/' + shop_id + 'mhers_tmp_{}.imgtype'.format(abs(hash(pdt['pdct_img_main_url'])))
         img_path = img_path_namer(shop_id, pdt['pdct_name_on_eretailer'])
         with open(tmp_file_path, 'wb') as out_file:
             shutil.copyfileobj(response.content, out_file)
         if imghdr.what(tmp_file_path) is not None:
             img_path = img_path.split('.')[0] + '.' + imghdr.what('/tmp/' + shop_id + 'mhers_tmp_{}.imgtype'.format(abs(hash(pdt['pdct_img_main_url']))))
             shutil.copyfile('/tmp/' + shop_id + 'mhers_tmp_{}.imgtype'.format(abs(hash(pdt['pdct_img_main_url']))), img_path)
             products[url].update({'img_path': img_path, 'img_hash': file_hash(img_path)})

create_csvs(products, categories, searches, shop_id, fpath_namer(shop_id, 'raw_csv'), COLLECTION_DATE)
validate_raw_files(fpath_namer(shop_id, 'raw_csv'))
