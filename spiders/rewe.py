from io import BytesIO

from lxml import etree

parser = etree.HTMLParser(encoding='utf-8')
from time import sleep
from urllib.parse import urlsplit, parse_qs
from validators import validate_raw_files
from create_csvs import create_csvs
import requests_cache, imghdr

from ers import all_keywords_de as keywords, mh_brands, clean_url
from matcher import BrandMatcher
from ers import COLLECTION_DATE, file_hash, img_path_namer, fpath_namer
import requests
import shutil
from helpers.random_user_agent import randomua
from parse import parse

# Init variables and assets
shop_id = 'rewe'
root_url = 'https://shop.rewe.de'
session = requests_cache.CachedSession(fpath_namer(shop_id, 'requests_cache'))
session.headers = {'User-Agent': randomua()}
country = 'DE'
searches, categories, products = {}, {}, {}


def getprice(pricestr):
    pricestr = pricestr.replace(' ', '')
    if pricestr == '':
        return pricestr
    price = parse('{dol:d},{pence:d}€', pricestr)
    if price is None:
        price = parse('{dol:d}€', pricestr)
        return price.named['dol'] * 100
    else:
        return price.named['dol'] * 100 + price.named['pence']


urls_ctgs_dict = {
    'champagne': 'https://shop.rewe.de/c/wein-spirituosen-tabak-wein-fruchtwein-mischgetraenke-sekt-champagner-schaumwein-champagner/?objectsPerPage=200',
    'whisky': 'https://shop.rewe.de/c/wein-spirituosen-tabak-spirituosen-mischgetraenke-whiskey/?objectsPerPage=200',
    'cognac': 'https://shop.rewe.de/c/wein-spirituosen-tabak-spirituosen-mischgetraenke-cognac-weinbrand/?objectsPerPage=200',
    'vodka': 'https://shop.rewe.de/c/wein-spirituosen-tabak-spirituosen-mischgetraenke-vodka/?objectsPerPage=200',
    'still_wines': 'https://shop.rewe.de/c/wein-spirituosen-tabak-wein-fruchtwein-mischgetraenke-weisswein/?objectsPerPage=200',
    'white_wine': 'https://shop.rewe.de/c/wein-spirituosen-tabak-wein-fruchtwein-mischgetraenke-weisswein/?objectsPerPage=200',
    'red_wine': 'https://shop.rewe.de/c/wein-spirituosen-tabak-wein-fruchtwein-mischgetraenke-rotwein/?objectsPerPage=200',
    'gin': 'https://shop.rewe.de/c/wein-spirituosen-tabak-spirituosen-mischgetraenke-gin-genever-wacholder/?objectsPerPage=200',
    'rum': 'https://shop.rewe.de/c/wein-spirituosen-tabak-spirituosen-mischgetraenke-rum/?objectsPerPage=200',
    'liquor': 'https://shop.rewe.de/c/wein-spirituosen-tabak-spirituosen-mischgetraenke-likoere-punsche/?objectsPerPage=200',
}

# Category Scraping - with requests - one page per category
for ctg, url in urls_ctgs_dict.items():
    categories[ctg] = []
    r = session.get(url)
    with open('/tmp/' + shop_id + ' ' + ctg.replace('/', "-") + '.html', 'wb') as f:
        f.write(r.content)
    tree = etree.parse(BytesIO(r.content), parser=parser)
    for li in tree.xpath('//*[@class="search-service-ProductTileWrapper"]'):
        produrl = li.xpath('.//a/@href')[0]
        produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
        produrl = clean_url(produrl, root_url)
        products[produrl] = {
            'pdct_name_on_eretailer': "".join(li.xpath('.//a/@title')),
            'raw_price': ''.join(
                w for t in li.xpath('.//mark[@itemprop="price"]//text()') for w in
                t.split()).strip(),
            'raw_promo_price': ''.join(
                w for t in li.xpath('.//mark[@class="MainTypeCompAtomsPrevProductPricePrevious"]//text()')[:1] for w in
                t.split()).replace('bisher', '').strip(),
        }
        print(products[produrl], produrl)
        products[produrl]['price'] = getprice(products[produrl]['raw_price'])
        products[produrl]['promo_price'] = getprice(products[produrl]['raw_promo_price'])
        print(products[produrl])

        categories[ctg].append(produrl)
    if not r.from_cache:
        sleep(3)
    print(ctg, len(categories[ctg]))

# KW searches Scraping - with requests - one page per search
kw_search_url = "https://shop.rewe.de/productList?search={kw}&objectsPerPage=200"
for kw in keywords:
    searches[kw] = []
    url = kw_search_url.format(kw=kw)
    r = session.get(url)
    tree = etree.parse(BytesIO(r.content), parser=parser)
    for li in tree.xpath('//*[@class="search-service-ProductTileWrapper"]'):
        produrl = li.xpath('.//a/@href')[0]
        produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
        produrl = clean_url(produrl, root_url)
        products[produrl] = {
            'pdct_name_on_eretailer': "".join(li.xpath('.//a/@title')),
            'volume': "".join(li.xpath('.//a/@title')),
            'raw_price': ''.join(
                w for t in li.xpath('.//mark[@itemprop="price"]//text()') for w in
                t.split()).strip(),
            'raw_promo_price': ''.join(
                w for t in li.xpath('.//mark[@class="MainTypeCompAtomsPrevProductPricePrevious"]//text()')[:1] for w in
                t.split()).replace('bisher', '').strip(),
        }
        print(products[produrl], produrl)
        products[produrl]['price'] = getprice(products[produrl]['raw_price'])
        products[produrl]['promo_price'] = getprice(products[produrl]['raw_promo_price'])
        print(products[produrl])
        searches[kw].append(produrl)

    if not r.from_cache:
        sleep(3)
    print(kw, len(searches[kw]))

# Download the pages - with requests
brm = BrandMatcher()
for url in sorted(list(set(products))):
    d = products[url]
    if brm.find_brand(d['pdct_name_on_eretailer'])['brand'] in mh_brands:
        print(d['pdct_name_on_eretailer'], )
        url_mod = clean_url(url, root_url=root_url)
        r = session.get(url_mod)
        with open('/tmp/' + shop_id + ' ' + d['pdct_name_on_eretailer'].replace('/', "-") + '.html', 'wb') as f:
            f.write(r.content)
        tree = etree.parse(BytesIO(r.content), parser=parser)
        products[url].update({
            'pdct_img_main_url': ''.join(tree.xpath('//div[@class="pd-ProductDetails-Image"]//img/@src')),
            'ctg_denom_txt': ' '.join(' '.join(tree.xpath('//*[@class="lr-breadcrumbs"]//text()')).split()) + 'whisky',
        })
        print(products[url])
        if not r.from_cache:
            sleep(3)


# Download images
for url, pdt in products.items():
     if 'pdct_img_main_url' in pdt and pdt['pdct_img_main_url'] and brm.find_brand(pdt['pdct_name_on_eretailer'])['brand'] in mh_brands:
         print(pdt['pdct_name_on_eretailer'] + "." + pdt['pdct_img_main_url'].split('.')[-1])
         response = requests.get(pdt['pdct_img_main_url'])
         # response.raw.decode_content = True
         tmp_file_path = '/tmp/' + shop_id + 'mhers_tmp_{}.imgtype'.format(abs(hash(pdt['pdct_img_main_url'])))
         img_path = img_path_namer(shop_id, pdt['pdct_name_on_eretailer'])
         with open(tmp_file_path, 'wb') as out_file:
             out_file.write(response.content)
         if imghdr.what(tmp_file_path) is not None:
             img_path = img_path.split('.')[0] + '.' + imghdr.what('/tmp/' + shop_id + 'mhers_tmp_{}.imgtype'.format(abs(hash(pdt['pdct_img_main_url']))))
             shutil.copyfile('/tmp/' + shop_id + 'mhers_tmp_{}.imgtype'.format(abs(hash(pdt['pdct_img_main_url']))), img_path)
             products[url].update({'img_path': img_path, 'img_hash': file_hash(img_path)})

create_csvs(products, categories, searches, shop_id, fpath_namer(shop_id, 'raw_csv'), COLLECTION_DATE)
validate_raw_files(fpath_namer(shop_id, 'raw_csv'))
