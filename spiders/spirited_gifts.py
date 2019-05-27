import json
from io import BytesIO

from lxml import etree

parser = etree.HTMLParser()
from urllib.parse import quote_plus
import requests_cache, imghdr
from validators import validate_raw_files
from create_csvs import create_csvs

from ers import all_keywords_usa as keywords, mh_brands
from matcher import BrandMatcher
from ers import COLLECTION_DATE, file_hash, img_path_namer, fpath_namer, headers
import requests
import shutil

# Init variables and assets
shop_id = 'spirited_gifts'
root_url = 'https://spiritedgifts.com'
requests_cache.install_cache(fpath_namer(shop_id, 'requests_cache'))
country = 'USA'
searches, categories, products = {}, {}, {}


from parse import parse


def getprice(pricestr):
    if not pricestr:
        return
    price = parse('${pound:d}.{pence:d}', pricestr)
    if not price:
        price = parse('${th:d},{pound:d}.{pence:d}', pricestr)
        return price.named['th'] * 100000 + price.named['pound'] * 100 + price.named['pence']
    return price.named['pound'] * 100 + price.named['pence']


categories_urls = {
    'champagne': 'https://spiritedgifts.com/champagne?p={page}',
    'sparkling': 'https://spiritedgifts.com/catalogsearch/result/?q=sparkling&p={page}',
    'still_wines': 'https://spiritedgifts.com/wine?p={page}',
    'whisky': 'https://spiritedgifts.com/scotch-whisky?p={page}',
    'cognac': 'https://spiritedgifts.com/cognac-brandy?p={page}',
    'vodka': 'https://spiritedgifts.com/vodka?p={page}',
    'red_wine': 'https://spiritedgifts.com/red-wine-gifts?p={page}',
    'white_wine': 'https://spiritedgifts.com/white-wine-gifts?p={page}',
    'gin': 'https://spiritedgifts.com/gin?p={page}',
    'rum': 'https://spiritedgifts.com/rum?p={page}',
    'brandy': 'https://spiritedgifts.com/cordials?p={page}',
    'tequila': 'https://spiritedgifts.com/tequila?p={page}',
    'bourbon': 'https://spiritedgifts.com/bourbon-and-whiskey-gifts?p={page}',
    'liquor': 'https://spiritedgifts.com/cordials?p={page}',
}

for cat, url in categories_urls.items():
    categories[cat] = []
    for page in range(1, 100):
        r = requests.get(url.format(page=page), headers={'x-requested-with': 'XMLHttpRequest'})
        data = json.loads(r.content.decode('utf8'))
        tree = etree.parse(BytesIO(data['listing'].encode()), parser=parser)
        #print(etree.tostring(tree, pretty_print=True).decode())
        articles = tree.xpath('//div[@class="col-lg-4 col-md-4 col-sm-6 col-xs-6"]')
        aurls = [a.xpath('.//a[1]/@href')[0] for a in articles]
        if not articles or all(a in categories[cat] for a in aurls):
            break
        categories[cat] += aurls
        for a in articles:
            data = {
                'url': a.xpath('.//a[1]/@href')[0],
                'img': a.xpath('.//img[@class="product-img"]/@src')[0],
                'pdct_name_on_eretailer': a.xpath('.//div[@class="product-item-name"]/text()')[0],
                'price': getprice(a.xpath('.//span[@class="price"]/text()')[0].replace(',', '').strip())
            }
            products[data['url']] = data
        print(cat,  len(articles), len(categories[cat]))

for kw in keywords:
    searches[kw] = []
    for page in range(1, 100):
        r = requests.get('https://spiritedgifts.com/catalogsearch/result/?q={kw}&p={page}'.format(
            page=page, kw=quote_plus(kw)), headers={'x-requested-with': 'XMLHttpRequest'})
        data = json.loads(r.content.decode('utf8'))
        tree = etree.parse(BytesIO(data['listing'].encode()), parser=parser)
        #print(etree.tostring(tree, pretty_print=True).decode())
        articles = tree.xpath('//div[@class="col-lg-4 col-md-4 col-sm-6 col-xs-6"]')
        aurls = [a.xpath('.//a[1]/@href')[0] for a in articles]
        if not articles or all(a in searches[kw] for a in aurls):
            break
        searches[kw] += aurls
        for a in articles:
            data = {
                'url': a.xpath('.//a[1]/@href')[0],
                'img': a.xpath('.//img[@class="product-img"]/@src')[0],
                'pdct_name_on_eretailer': a.xpath('.//div[@class="product-item-name"]/text()')[0],
                'price': getprice(a.xpath('.//span[@class="price"]/text()')[0].replace(',', '').strip())
            }
            products[data['url']] = data
        print(kw,  len(articles), len(searches[kw]))

brm = BrandMatcher()
for url, product in products.items():
    if brm.find_brand(product['pdct_name_on_eretailer'])['brand'] in mh_brands:
        r = requests.get(url)
        with open('/tmp/' + shop_id + ' ' + product['pdct_name_on_eretailer'].replace('/', "-") + '.html', 'wb') as f:
            f.write(r.content)
        tree = etree.parse(BytesIO(r.content), parser=parser)
        data = {
            'volume': " ".join(tree.xpath('//a[contains(@href,"bottle-size")]/text()')[:1]).strip(),
            'pdct_img_main_url': tree.xpath('//img[@id="image-main"]/@src')[0],
            'ctg_denom_txt': [t.strip() for t in tree.xpath('//ul[@class="breadcrumb"]/li//text()') if t.strip()],
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
