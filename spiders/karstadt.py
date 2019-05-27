import os.path as op
from io import BytesIO

from lxml import etree

parser = etree.HTMLParser(encoding='utf-8')
from time import sleep
from urllib.parse import urlsplit, parse_qs
import requests_cache, imghdr
from validators import validate_raw_files
from create_csvs import create_csvs
import requests

from ers import all_keywords_de as keywords, fpath_namer, mh_brands
from matcher import BrandMatcher
from ers import COLLECTION_DATE, file_hash, img_path_namer
import shutil
from helpers.random_user_agent import randomua
from custom_browser import CustomDriver

# Init variables and assets
shop_id = 'karstadt'
root_url = 'http://www.karstadt.de/'
session = requests_cache.CachedSession(fpath_namer(shop_id, 'requests_cache'))
session.headers = {'User-Agent': randomua()}
country = 'DE'
searches, categories, products = {}, {}, {}
driver = CustomDriver(headless=False)


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


urls_ctgs_dict = {
    'champagne': 'http://www.karstadt.de/Champagner-und-Sekt/6194/?sz=60&start={page}',
    'cognac': 'http://www.karstadt.de/Spirituosen/6195/?prefn1=Produkttyp&prefv1=Cognac&sz=60&start={page}',
    'sparkling': 'http://www.karstadt.de/Champagner-und-Sekt/6194/#sz=60&start={page}',
    'vodka': 'http://www.karstadt.de/Spirituosen/6195/?prefn1=Produkttyp&prefv1=Wodka&sz=60&start={page}',
    'whisky': 'http://www.karstadt.de/Spirituosen/6195/?prefn1=Produkttyp&prefv1=Whisky&sz=60&start={page}',
    'still_wines': 'http://www.karstadt.de/weine/KDE_121/#sz=60&start={page}',
    'red_wine': 'http://www.karstadt.de/rotwein/6193/#sz=60&start={page}',
    'white_wine': 'http://www.karstadt.de/weisswein/904515/#sz=60&start={page}',
    'gin': 'http://www.karstadt.de/Spirituosen/6195/?prefn1=Produkttyp&prefv1=Gin&sz=36&sz=60&start={page}',
    'rum': 'http://www.karstadt.de/Spirituosen/6195/?prefn1=Produkttyp&prefv1=Rum&sz=60&start={page}',
    'liquor': 'http://www.karstadt.de/Spirituosen/6195/?prefn1=Produkttyp&prefv1=Lik%C3%B6r&sz=36&sz=60&start={page}'
}

# Category Scraping - with requests - multiple pages per category
for ctg, url in urls_ctgs_dict.items():
    categories[ctg] = []
    number_of_pdcts_in_ctg = 0
    for p in range(100):
        urlp = url.format(page=p*60)
        print(urlp)

        fpath = fpath_namer(shop_id, 'ctg', ctg, p)
        if not op.exists(fpath):
            driver.get(urlp)
            sleep(2)
            driver.save_page(fpath, scroll_to_bottom=True)
        tree = etree.parse(open(fpath, 'rb'), parser=parser)
        for li in tree.xpath('//ul[contains(@class, "tiles-container")]/li'):
            if not li.xpath('.//a[img]/@href'):
                continue
            produrl = li.xpath('.//a[img]/@href')[0]
            produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(
                urlsplit(produrl).query) else produrl
            products[produrl] = {
                'pdct_name_on_eretailer': "".join(li.xpath('.//span[@class="product-name"]/text()')),
                'price': int(float(li.xpath('.//div[contains(@class,"price-sales")]/@data-baseprice')[0]) * 100),
                'volume': ''.join(li.xpath('.//div[contains(@class, "price-sales")]/span[last()]/text()')),
            }
            if li.xpath('.//div[@class="price"]/@data-baseprice'):
                products[produrl]['promo_price'] = int(
                    float(li.xpath('.//div[@class="price"]/@data-baseprice')[0]) * 100),

            print(products[produrl], produrl)
            categories[ctg].append(produrl)
            assert all(products[produrl][k] for k in products[produrl])

        # Checking if it was the last page
        if len(set(categories[ctg])) == number_of_pdcts_in_ctg:
            break
        else:
            number_of_pdcts_in_ctg = len(set(categories[ctg]))

    print(ctg, len(categories[ctg]))
print([(c, len(categories[c])) for c in categories])


for kw in keywords:
    searches[kw] = []
    number_of_pdcts_in_kw_search = 0

    for p in range(10):
        urlp = url.format(page=p*36)
        print(urlp)
        # r = session.get(urlp)
        # tree = etree.parse(BytesIO(r.content), parser=parser)

        fpath = fpath_namer(shop_id, 'ctg', ctg, p)
        if not op.exists(fpath):
            driver.get(urlp)
            sleep(2)
            driver.save_page(fpath, scroll_to_bottom=True)
        tree = etree.parse(open(fpath, 'rb'), parser=parser)
        for li in tree.xpath('//ul[contains(@class, "tiles-container")]/li'):
            if not li.xpath('.//a[img]/@href'):
                continue
            produrl = li.xpath('.//a[img]/@href')[0]
            produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(
                urlsplit(produrl).query) else produrl
            products[produrl] = {
                'pdct_name_on_eretailer': "".join(li.xpath('.//span[@class="product-name"]/text()')),
                'price': int(float(li.xpath('.//div[contains(@class,"price-sales")]/@data-baseprice')[0]) * 100),
                'volume': ''.join(li.xpath('.//div[contains(@class, "price-sales")]/span[last()]/text()')),
            }
            if li.xpath('.//div[@class="price"]/@data-baseprice'):
                products[produrl]['promo_price'] = int(float(li.xpath('.//div[@class="price"]/@data-baseprice')[0]) * 100),

            print(products[produrl], produrl)
            searches[kw].append(produrl)

        # Checking if it was the last page
        if len(set(searches[kw])) == number_of_pdcts_in_kw_search:
            break
        else:
            number_of_pdcts_in_kw_search = len(set(searches[kw]))
    print(kw, p, len(searches[kw]))

brm = BrandMatcher()
for url, product in products.items():
    if brm.find_brand(product['pdct_name_on_eretailer'])['brand'] in mh_brands:
        r = session.get(url)
        tree = etree.parse(BytesIO(r.content), parser=parser)
        data = {
            'ctg_denom_txt': ' '.join(''.join(tree.xpath('//ol[@class="breadcrumb"]//a/text()')).split()),
            'pdct_img_main_url': tree.xpath('//img[@class="primary-image"]/@src')[0],
        }
        product.update(data)
        print(product)

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
driver.quit()
