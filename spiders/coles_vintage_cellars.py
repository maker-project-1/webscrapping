from io import BytesIO

from lxml import etree

parser = etree.HTMLParser()
from urllib.parse import quote_plus
import requests
import requests_cache, imghdr
from validators import validate_raw_files
from create_csvs import create_csvs
from ers import all_keywords_aus as keywords, mh_brands, clean_url
from matcher import BrandMatcher
from ers import COLLECTION_DATE, file_hash, img_path_namer, fpath_namer, headers
import shutil

# Init variables and assets
shop_id = 'coles_vintage_cellars'
root_url = 'https://www.vintagecellars.com.au/'
requests_cache.install_cache(fpath_namer(shop_id, 'requests_cache'))
country = 'AUS'
searches, categories, products = {}, {}, {}

from parse import parse


def getprice(pricestr):
    if not pricestr:
        return
    price = parse(u'{pound:d}.{pence:d}', pricestr)
    if not price:
        price = parse(u'Reg.\xa0${th:d},{pound:d}.{pence:d}', pricestr)
        return price.named['th'] * 100000 + price.named['pound'] * 100 + price.named['pence']
    return price.named['pound'] * 100 + price.named['pence']


categories_ids = {
    'whisky': 'https://www.vintagecellars.com.au/Spirits?show=50&facets=spiritproducttype%3dMalt+Scotch+Whisky&page={page}',
    'champagne': 'https://www.vintagecellars.com.au/Sparkling?show=100&facets=region%3dChampagne',
    'cognac': 'https://www.vintagecellars.com.au/Search?q=cognac&show=100',
    'sparkling': 'https://www.vintagecellars.com.au/Sparkling?show=100&page={page}',
    'vodka': 'https://www.vintagecellars.com.au/Spirits?show=100&facets=spiritproducttype%3dVodka&page={page}',
    'still_wines': 'https://www.vintagecellars.com.au/White%20Wine?page={page}',
    'gin': 'https://www.vintagecellars.com.au/Spirits?facets=spiritproducttype%3dGin&show=50&page={page}',
    'tequila': 'https://www.vintagecellars.com.au/Spirits?facets=spiritproducttype%3dTequila&show=50&page={page}',
    'red_wine': 'https://www.vintagecellars.com.au/Red%20Wine?show=50&page={page}',
    'white_wine': 'https://www.vintagecellars.com.au/White%20Wine&page={page}',
    'rum': 'https://www.vintagecellars.com.au/Spirits?facets=spiritproducttype%3dRum+-+White&page={page}',
    'bourbon': 'https://www.vintagecellars.com.au/Spirits?facets=spiritproducttype%3dBourbon&page={page}',
    'brandy': 'https://www.vintagecellars.com.au/Spirits?facets=spiritproducttype%3dBrandy&page={page}',
    'liquor': 'https://www.vintagecellars.com.au/Spirits?facets=spiritproducttype%3dImported+Liqueurs&page={page}'
}


def getproduct(a):
    data = {
        'url': a.xpath('.//a[contains(@id, "ProductThumbnailLink")]/@href')[0],
        'pdct_name_on_eretailer': a.xpath('.//a[contains(@id, "ProductTitleLink")]/text()')[0].strip(),
        'volume': a.xpath('.//a[contains(@id, "ProductTitleLink")]//text()')[0].strip().split()[-1],
        'promo_price': a.xpath('.//span[contains(@class, "price sqd")]'),
        'price': getprice(a.xpath('.//span[@class="currency"]')[0].tail + a.xpath('.//span[@class="cents"]/text()')[0]),
        'img': a.xpath('.//a[contains(@id, "ProductThumbnailLink")]//img/@src')[0]
    }
    if data['volume']:
        data['volume'] = data['volume'][0]
    else:
        print('NOVOLUME', data['pdct_name_on_eretailer'])
        del data['volume']

    assert(data['price'])
    products[data['url']] = data


for cat, url in categories_ids.items():
    categories[cat] = []
    for p in range(1, 1000):
        r = requests.get(url.format(page=p))
        tree = etree.parse(BytesIO(r.content), parser=parser)
        articles = tree.xpath('//ul[@class="productList"]/li')
        aurls = [a.xpath('.//a[contains(@id, "ProductThumbnailLink")]/@href')[0] for a in articles]
        if not aurls or all(u in categories[cat] for u in aurls):
            break
        categories[cat] += aurls
        [getproduct(a) for a in articles]
        print(cat, p, r, len(r.content), len(articles), len(categories[cat]))


for kw in keywords:
    print(kw)
    searches[kw] = []
    for page in range(1, 1000):
        r = requests.get('https://www.vintagecellars.com.au/Search?q={kw}&show=100&page={page}'.format(
            page=page, kw=quote_plus(kw)))
        with open('/tmp/' + shop_id + ' ' + kw + '.html', 'wb') as f:
            f.write(r.content)
        tree = etree.parse(BytesIO(r.content), parser=parser)
        articles = tree.xpath('//ul[@class="productList"]/li')
        aurls = [a.xpath('.//a[contains(@id, "ProductThumbnailLink")]/@href')[0] for a in articles]
        print(aurls)
        if not aurls or all(u in searches[kw] for u in aurls):
            break
        searches[kw] += aurls
        [getproduct(a) for a in articles]
        print(kw, p, r, len(r.content), len(articles), len(searches[kw]))

brm = BrandMatcher()
for url, product in products.items():
    if brm.find_brand(product['pdct_name_on_eretailer'])['brand'] in mh_brands:
        r = requests.get('https://www.vintagecellars.com.au' + url)
        tree = etree.parse(BytesIO(r.content), parser=parser)
        data = {
            'pdct_img_main_url': clean_url(tree.xpath('//div[@class="fullImg"]//img/@src')[0], root_url),
            'ctg_denom_txt': tree.xpath('//ul[@class="breadcrumbs"]/li/a/text()'),
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

