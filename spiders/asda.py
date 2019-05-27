import os.path as op
from io import BytesIO

from lxml import etree

parser = etree.HTMLParser(encoding='utf-8')
from time import sleep
from urllib.parse import urlsplit, parse_qs
import requests
import requests_cache, imghdr
from parse import parse

from validators import validate_raw_files
from create_csvs import create_csvs
from ers import all_keywords_uk as keywords
from ers import fpath_namer, mh_brands, clean_url, headers
from matcher import BrandMatcher
from ers import COLLECTION_DATE, file_hash, img_path_namer
import shutil
from custom_browser import CustomDriver
import re

# Init variables and assets
shop_id = 'asda'
root_url = 'https://groceries.asda.com/'
requests_cache.install_cache(fpath_namer(shop_id, 'requests_cache'))
country = 'UK'
searches, categories, products = {}, {}, {}
driver = CustomDriver(headless=False, download_images=True)


def getprice(pricestr):
    if pricestr == '':
        return pricestr
    pricestr = re.sub("[^0-9.£p]", "", pricestr)
    price = parse('£{pound:d}.{pence:d}', pricestr)
    if price is None:
        price = parse('{pence:d}p', pricestr)
        return price.named['pence']
    else:
        return price.named['pound'] * 100 + price.named['pence']

print(getprice('£40.00'))

# CTG scrapping
urls_ctgs_dict = {
    'champagne': 'https://groceries.asda.com/shelf/champagne/champagne/_/109900213',
    'sparkling': 'https://groceries.asda.com/shelf/prosecco-sparkling-wine/sparkling-wine/_/102525',
    'still_wines': 'https://groceries.asda.com/shelf/white-wine/view-all-white-wine/_/113141/1/shelf%3A0000%3A113141/sortBy/relevance%20desc',
    'whisky': 'https://groceries.asda.com/shelf/spirits/view-all-whisky/_/1579926650/1/shelf%3A0000%3A1579926650/sortBy/relevance%20desc',
    'cognac': 'https://groceries.asda.com/shelf/spirits/brandy-cognac/_/102576',
    'gin':'https://groceries.asda.com/shelf/spirits/gin/_/102583',
    'white_wine':'https://groceries.asda.com/shelf/white-wine/view-all-white-wine/_/113141',
    'red_wine':'https://groceries.asda.com/shelf/red-wine/view-all-red-wine/_/113142',
    'rum':'https://groceries.asda.com/shelf/spirits/rum/_/102574',
    'vodka': 'https://groceries.asda.com/shelf/spirits/vodka/_/102573',
    'liquor': 'https://groceries.asda.com/shelf/spirits/liqueurs/_/102575',
}

# Categories scraping
for ctg, url in urls_ctgs_dict.items():
    print(ctg, url)
    categories[ctg] = []
    number_of_pdcts_in_ctg = 0
    scraping_launched = False

    if not op.exists(fpath_namer(shop_id, 'ctg', ctg, 0)):
        driver.get(url)
        scraping_launched = True

    for p in range(100):
        fpath = fpath_namer(shop_id, 'ctg', ctg, p)
        if not op.exists(fpath):
            sleep(2)
            driver.save_page(fpath, scroll_to_bottom=True)
        tree = etree.parse(BytesIO(open(fpath, 'rb').read()), parser=parser)
        for li in tree.xpath('//div[@data-cid]'):
            produrl = li.xpath('.//span[@class="title productTitle"]/a/@href')[0]
            produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
            categories[ctg].append(produrl)
            products[produrl] = {
                'pdct_name_on_eretailer': " ".join("".join(li.xpath('.//span[@class="title productTitle"]//span//text()')).split()),
                'raw_price': " ".join("".join(li.xpath('.//span[@class="price"]/span[last()]//text()|.//span[@class="wasprice"]/span[2]//text()')[:1]).split()),
            }
            print(products[produrl])
            products[produrl]['price'] = getprice(products[produrl]['raw_price'])
            print(products[produrl])
        if len(set(categories[ctg])) == number_of_pdcts_in_ctg:
            break
        else:
            number_of_pdcts_in_ctg = len(set(categories[ctg]))
            if scraping_launched:
                driver.waitclick('//a[contains(@class, "forward-listing btn")]')
                sleep(1)
print([(c, len(categories[c])) for c in categories])


# Easy case, where you scroll down to get the whole page
search_url = "https://groceries.asda.com/search/{kw}"
for kw in keywords:
    print(kw)
    searches[kw] = []
    # Storing and extracting infos
    fpath = fpath_namer(shop_id, 'search', kw, 0)
    url = search_url.format(kw=kw, page=0)
    if not op.exists(fpath):
        driver.get(url)
        sleep(3)
        driver.save_page(fpath, scroll_to_bottom=True)
        sleep(1)
    tree = etree.parse(BytesIO(open(fpath, 'rb').read()), parser=parser)
    for li in tree.xpath('//div[@data-cid]'):
        produrl = li.xpath('.//span[@class="title productTitle"]/a/@href')[0]
        produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
        searches[kw].append(produrl)
        products[produrl] = {
            'pdct_name_on_eretailer': " ".join(
                "".join(li.xpath('.//span[@class="title productTitle"]//span//text()')).split()),
            'raw_price': " ".join("".join(li.xpath('.//span[@class="price"]/span[last()]//text()')).split()),
        }
        print(products[produrl]['raw_price'])
        products[produrl]['price'] = getprice(products[produrl]['raw_price'])
        print(products[produrl])


# Download the pages
brm = BrandMatcher()
for url in sorted(products):
    d = products[url]
    if brm.find_brand(d['pdct_name_on_eretailer'])['brand'] in mh_brands:
        print(d['pdct_name_on_eretailer'], brm.find_brand(d['pdct_name_on_eretailer'])['brand'], url)
        url_mod = clean_url(url, root_url=root_url)
        fname = fpath_namer(shop_id, 'pdct', d['pdct_name_on_eretailer'], 0)
        if not op.exists(fname):
            driver.get(url_mod)
            sleep(2)
            driver.save_page(fname, scroll_to_bottom=True)
        tree = etree.parse(open(fname), parser=parser)
        products[url] = {
            'pdct_name_on_eretailer': ''.join(tree.xpath('//h1[@class="prod-title"]//text()')),
            'volume': ''.join(tree.xpath('//span[@class="weight"]//text()')),
            'raw_price': ''.join(tree.xpath('//span[@class="prod-price-inner"]//text()|//p[@class="prod-price"]/strike//text()')[-1:]),
            'raw_promo_price': ''.join(tree.xpath('//p[@class="prod-price"]/strike//text()')),
            'pdct_img_main_url': ''.join(tree.xpath('//*[@class="s7staticimage"]//img/@src')[:1]),
            'ctg_denom_txt': ''.join(tree.xpath('//div[@class="breadcrumb breadcrumbHeader"]//text()')),
        }
        print(d['pdct_name_on_eretailer'], products[url])
        products[url]['price'] = getprice(products[url]['raw_price'])
        products[url]['promo_price'] = getprice(products[url]['raw_promo_price'])
        print(d['pdct_name_on_eretailer'], products[url])


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