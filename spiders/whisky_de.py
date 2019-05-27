import os.path as op
from io import BytesIO

from lxml import etree

parser = etree.HTMLParser(encoding='utf-8')
from time import sleep
from urllib.parse import urlsplit, parse_qs
import requests
import requests_cache, imghdr
from validators import validate_raw_files
from create_csvs import create_csvs

from ers import all_keywords_de as keywords, fpath_namer, mh_brands, clean_url, headers
from matcher import BrandMatcher
from ers import COLLECTION_DATE, file_hash, img_path_namer
import shutil
from custom_browser import CustomDriver

# Init variables and assets
shop_id = 'whisky_de'
root_url = 'https://www.whisky.de'
country = 'DE'
requests_cache.install_cache(fpath_namer(shop_id, 'requests_cache'))

searches, categories, products = {}, {}, {}
driver = CustomDriver(headless=True, download_images=False)
import re
from parse import parse


def getprice(pricestr):
    pricestr = re.sub("[^0-9,€EUR]", "", pricestr)
    if pricestr == '':
        return pricestr
    price = parse('{dol:d},{pence:d}EUR', pricestr)
    if price is None:
        price = parse('{dol:d}EUR', pricestr)
        return price.named['dol'] * 100
    else:
        return price.named['dol'] * 100 + price.named['pence']


urls_ctgs_dict = {
    'whisky': 'https://www.whisky.de/shop/Schottland/?_artperpage=30',
    'liquor': 'https://www.whisky.de/shop/Likoere/?_artperpage=30',
}

# Category Scraping - with selenium - one page per category
for ctg, url in urls_ctgs_dict.items():
    categories[ctg] = []
    fpath = fpath_namer(shop_id, 'ctg', ctg, 0)
    if not op.exists(fpath):
        driver.get(url)
        sleep(1)
        driver.save_page(fpath, scroll_to_bottom=True)
    tree = etree.parse(BytesIO(open(fpath, 'rb').read()), parser=parser)
    for li in tree.xpath('//div[@id="productList"]//div[@class="panel-body"]'):
        produrl = li.xpath('.//div[@class="article-title"]/a/@href')[0]
        produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
        produrl = clean_url(produrl, root_url)

        products[produrl] = {
            'pdct_name_on_eretailer': " ".join("".join(li.xpath('.//div[@class="article-title"]/a[1]//text()')).split()),
            'raw_price': ''.join(w for t in li.xpath('.//span[@class="article-price-default"]/text()')[:1] for w in t.split()).strip(),
        }
        print(products[produrl], produrl)
        products[produrl]['price'] = getprice(products[produrl]['raw_price'])
        print(products[produrl])
        categories[ctg].append(produrl)
print([(c, len(categories[c])) for c in categories])



# KW Scraping - with selenium - one page per category
kw_search_url = "https://www.whisky.de/shop/index.php?stoken=ECD6E865&lang=0&cl=search&searchparam={kw}"
for kw in keywords:
    print('Requesting', kw)
    searches[kw] = []
    fpath = fpath_namer(shop_id, 'search', kw, 0)
    if not op.exists(fpath):
        driver.get(kw_search_url.format(kw=kw))
        sleep(1)
        driver.save_page(fpath, scroll_to_bottom=True)
    tree = etree.parse(BytesIO(open(fpath, 'rb').read()), parser=parser)
    for li in tree.xpath('//div[@id="searchList"]//div[@class="panel-body"]'):
        produrl = li.xpath('.//div[@class="article-title"]/a/@href')[0]
        produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
        produrl = clean_url(produrl, root_url)
        products[produrl] = {
            'pdct_name_on_eretailer': " ".join("".join(li.xpath('.//div[@class="article-title"]//text()')).split()),
            'raw_price': ''.join(w for t in li.xpath('.//span[@class="article-price-default"]/text()')[:1] for w in t.split()).strip(),
        }
        print(products[produrl], produrl)
        products[produrl]['price'] = getprice(products[produrl]['raw_price'])
        print(products[produrl])
        searches[kw].append(produrl)
print(searches)


# Download the pages - with requests
brm = BrandMatcher()
for url in sorted(set([k for k, v in products.items()])):
    d = products[url]
    if brm.find_brand(d['pdct_name_on_eretailer'])['brand'] in mh_brands:
        print(d['pdct_name_on_eretailer'])
        url_mod = clean_url(url, root_url=root_url)
        r = requests.get(url_mod, headers)
        with open('/tmp/' + shop_id + ' ' + d['pdct_name_on_eretailer'].replace('/', "-") + '.html', 'wb') as f:
            f.write(r.content)
        tree = etree.parse(BytesIO(r.content), parser=parser)
        products[url].update({
            'volume': ''.join(tree.xpath('//div[@itemtype="http://schema.org/Product"]//div[@class="article-amount"]/span[1]/text()')[:1]),
            'pdct_img_main_url': ''.join(tree.xpath('//div[@itemtype="http://schema.org/Product"]//div[@class="article-image"]//img/@src')[:1]),
            'ctg_denom_txt': ' '.join(' '.join(tree.xpath('//*[@id="breadcrumb"]//text()')).split()) + 'whisky',
        })
        print(products[url])
        if not r.from_cache:
            sleep(3)


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
             print('Warning :', tmp_file_path, imghdr.what(tmp_file_path))


create_csvs(products, categories, searches, shop_id, fpath_namer(shop_id, 'raw_csv'), COLLECTION_DATE)
validate_raw_files(fpath_namer(shop_id, 'raw_csv'))
driver.quit()
