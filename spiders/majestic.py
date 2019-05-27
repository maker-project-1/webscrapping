from lxml import etree
from io import BytesIO
from io import BytesIO

from lxml import etree

parser = etree.HTMLParser(encoding='utf-8')
from time import sleep
from urllib.parse import urlsplit, parse_qs
import requests
import requests_cache, imghdr

from validators import validate_raw_files
from create_csvs import create_csvs

from ers import all_keywords_uk as keywords, fpath_namer, mh_brands, clean_url, headers
from matcher import BrandMatcher
from ers import COLLECTION_DATE, file_hash, img_path_namer
import shutil
from parse import parse

# Init variables and assets
shop_id = 'majestic'
root_url = 'https://www.majestic.co.uk/'
requests_cache.install_cache(fpath_namer(shop_id, 'requests_cache'))
country = 'UK'
searches, categories, products = {}, {}, {}


def getprice(pricestr):
    if pricestr == '':
        return pricestr
    pricestr = pricestr.replace(',', '').strip()
    price = parse('£{pound:d}.{pence:d}', pricestr)
    if price is None:
        price = parse('{pence:d}p', pricestr)
        return price.named['pence']
    else:
        return price.named['pound'] * 100 + price.named['pence']


# CTG scrapping
urls_ctgs_dict = {
    'champagne': 'https://www.majestic.co.uk/champagne?pageNum={page}&pageSize=12',
    'sparkling': 'https://www.majestic.co.uk/sparkling-wine?pageNum={page}&pageSize=12',
    'still_wines': 'https://www.majestic.co.uk/white-wine?pageNum={page}&pageSize=12',
    'whisky': 'https://www.majestic.co.uk/whisky-whiskey?pageNum={page}&pageSize=12',
    'cognac': 'https://www.majestic.co.uk/brandy?pageNum={page}&pageSize=12',
    'vodka': 'https://www.majestic.co.uk/vodka?pageNum={page}&pageSize=12',
    'red_wine': 'https://www.majestic.co.uk/red-wine?pageNum={page}&pageSize=12',
    'white_wine': 'https://www.majestic.co.uk/white-wine?pageNum={page}&pageSize=12',
    'gin': 'https://www.majestic.co.uk/gin?pageNum={page}&pageSize=12',
    'rum': 'https://www.majestic.co.uk/rum?pageNum={page}&pageSize=12',
    'liquor': 'https://www.majestic.co.uk/liqueurs-and-aperitifs?pageNum={page}&pageSize=12',
    'brandy': 'https://www.majestic.co.uk/brandy?pageNum={page}&pageSize=12',
}


# Category Scraping
for ctg, url in urls_ctgs_dict.items():
    categories[ctg] = []
    number_of_pdcts_in_ctg = 0
    for p in range(100):
        urlp = url.format(page=p)
        r = requests.get(urlp)
        tree = etree.parse(BytesIO(r.content), parser=parser)
        for li in tree.xpath('//div[@class="row collapse"]'):
            produrl = li.xpath('.//h3[@class="space-b--none"]/a/@href')[0]
            produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(
                urlsplit(produrl).query) else produrl
            categories[ctg].append(produrl)
            products[produrl] = {
                'pdct_name_on_eretailer': li.xpath('.//h3[@class="space-b--none"]//text()')[0],
                'raw_price': ''.join(w for t in li.xpath('.//span[@class="product-action__price-info"]/text()') for w in t.split()).strip(),
            }
            products[produrl]['price'] = getprice(products[produrl]['raw_price'])
        assert all(products[produrl][k] for k in products[produrl])
        if len(set(categories[ctg])) == number_of_pdcts_in_ctg:
            break
        else:
            number_of_pdcts_in_ctg = len(set(categories[ctg]))
        if not r.from_cache:
            sleep(3)
    print(ctg, len(categories[ctg]))


#  Search scraping
for kw in keywords:
    searches[kw] = []
    kw_search_url = "https://www.majestic.co.uk/search.htm?searchText={kw}&pageSize=40&layoutType=list&pageNum=0"
    r = requests.get(kw_search_url.format(kw=kw))
    with open('/tmp/' + shop_id + ' ' + kw + '.html', 'wb') as f:
        f.write(r.content)
    tree = etree.parse(BytesIO(r.content), parser=parser)
    for li in tree.xpath('//div[@class="row collapse"]'):
        produrl = li.xpath('.//h3[@class="space-b--none"]/a/@href')[0]
        produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
        searches[kw].append(produrl)
        products[produrl] = {
            'pdct_name_on_eretailer': li.xpath('.//h3[@class="space-b--none"]//text()')[0],
            'raw_price': ''.join(w for t in li.xpath('.//span[@class="product-action__price-info"]/text()') for w in t.split()).strip(),
        }
        if not products[produrl]['raw_price']:
            products[produrl]['raw_price'] = ''.join(w for t in li.xpath('.//span[@class="product-action__price-text"]/text()') for w in t.split())
            products[produrl]['raw_price'] = products[produrl]['raw_price'].replace(',', '').replace(')', '')
        print(products[produrl])
        products[produrl]['price'] = getprice(products[produrl]['raw_price'])
        print(products[produrl])
        searches[kw].append(produrl)

    if not tree.xpath('//div[@class="row collapse"]') and tree.xpath('//h1//text()'):
        produrl = kw_search_url.format(kw=kw)
        searches[kw].append(produrl)
        products[produrl] = {
            'pdct_name_on_eretailer': tree.xpath('//h1//text()')[0],
            'raw_price': ''.join(
                w for t in tree.xpath('.//span[@class="product-action__price-info"]/text()') for w in t.split()).strip(),
        }
        if not products[produrl]['raw_price']:
            products[produrl]['raw_price'] = ''.join(
                w for t in tree.xpath('//span[@class="product-action__price-text"]/text()') for w in t.split())
            products[produrl]['raw_price'] = products[produrl]['raw_price'].replace(',', '').replace(')', '')
        print(products[produrl])
        products[produrl]['price'] = getprice(products[produrl]['raw_price'])
        print(products[produrl])
        searches[kw].append(produrl)

    if not r.from_cache:
        sleep(3)
assert sum(len(searches[kw]) for kw in searches) > 100


# Download the pages
brm = BrandMatcher()
for url in sorted(products):
    d = products[url]
    if brm.find_brand(d['pdct_name_on_eretailer'])['brand'] in mh_brands:
        print(d['pdct_name_on_eretailer'])
        url_mod = clean_url(url, root_url=root_url)
        r = requests.get(url_mod, headers)
        with open('/tmp/' + shop_id + ' ' + d['pdct_name_on_eretailer'].replace('/', "-") + '.html', 'wb') as f:
            f.write(r.content)
        tree = etree.parse(BytesIO(r.content), parser=parser)
        products[url] = {
            'pdct_name_on_eretailer': ' '.join(w for t in tree.xpath('//h1[@class="product-info__name"]//text()') for w in t.split()).strip(),
            'volume': ''.join(tree.xpath('(//div[@class="product-info__info"]/div[@class="product-info__symbol"])[1]//text()')).strip(),
            'raw_price': ' '.join(w for t in tree.xpath('//span[@class="product-action__price-info"]//text()') for w in t.split()).replace('per bottle', '').strip(),
            'raw_promo_price': ''.join(tree.xpath('//span[@class="product-action__price-text"]//fdsfdsf//text()')), # No because mix 6
            'pdct_img_main_url': ''.join(tree.xpath('//div/img/@src')),
            # 'ctg_denom_txt': ' '.join(tree.xpath('//div[@class="breadcrumbs small-8 columns"]//text()')),
        }
        print(products[url])

        products[url]['price'] = getprice(products[url]['raw_price'])
        products[url]['promo_price'] = getprice(products[url]['raw_promo_price'])
        print(products[url])
#

from pprint import pprint
pprint(products)

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
