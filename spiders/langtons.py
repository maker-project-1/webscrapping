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

from ers import all_keywords_aus as keywords, fpath_namer, mh_brands, clean_url, headers
from matcher import BrandMatcher
from ers import COLLECTION_DATE, file_hash, img_path_namer
import shutil
from parse import parse
from custom_browser import CustomDriver


# Init variables and assets
shop_id = 'langtons'
root_url = 'https://www.langtons.com.au'
requests_cache.install_cache(fpath_namer(shop_id, 'requests_cache'))
country = 'AUS'
searches, categories, products = {}, {}, {}
driver = CustomDriver(headless=True)

urls_ctgs_dict = {
    'champagne': 'https://www.langtons.com.au/search?p={page}&IncludeBuyNow=true&varietyIds=384,385',
    'sparkling': 'https://www.langtons.com.au/search?p={page}&IncludeBuyNow=true&varietyIds=390,391,392,393',
    'still_wines': 'https://www.langtons.com.au/search?p={page}&IncludeBuyNow=true&style=2',
    'whisky': 'https://www.langtons.com.au/search?p={page}&IncludeBuyNow=true&varietyIds=507',
    'cognac': 'https://www.langtons.com.au/search?p={page}&IncludeBuyNow=true&varietyIds=485',
    'vodka': 'https://www.langtons.com.au/search?p={page}&IncludeAuction=false&IncludeBuyNow=true&varietyIds=506',
    'gin': 'https://www.langtons.com.au/search?p={page}&IncludeBuyNow=true&varietyIds=487',
    'rum': 'https://www.langtons.com.au/search?p={page}&IncludeBuyNow=true&varietyIds=500',
    'tequila': 'https://www.langtons.com.au/search?p={page}&IncludeBuyNow=true&varietyIds=503',
    'red_wine': 'https://www.langtons.com.au/search?p={page}&IncludeBuyNow=true&style=1',
    'white_wine': 'https://www.langtons.com.au/search?p={page}&IncludeBuyNow=true&style=2',
}


def getprice(pricestr):
    if pricestr == '':
        return pricestr
    pricestr = pricestr.replace(',', '').strip()
    price = parse('${dol:d}.{pence:d}', pricestr)
    if price is None:
        price = parse('${dol:d}', pricestr)
        if price is not None:
            return price.named['dol'] * 100
        else:
            price = parse('{pence:d}p', pricestr)
            return price.named['pence']
    else:
        return price.named['dol'] * 100 + price.named['pence']


# Category Scraping - with selenium - multiple pages per category (hard-coded in url)
for ctg, url in urls_ctgs_dict.items():
    categories[ctg] = []
    number_of_pdcts_in_ctg = 0
    for p in range(100):
        urlp = url.format(page=p+1)
        fpath = fpath_namer(shop_id, 'ctg', ctg, p)
        if not op.exists(fpath):
            driver.get(urlp)
            sleep(2)
            driver.save_page(fpath)
        tree = etree.parse(open(fpath, 'rb'), parser=parser)
        for li in tree.xpath('//*[@id="results"]//li[contains(@ng-repeat, "prod in List.Products")]'):
            produrl = li.xpath('.//a/@href')[0]
            produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
            produrl = clean_url(produrl, root_url)
            products[produrl] = {
                'pdct_name_on_eretailer': li.xpath('.//b[@class="ng-binding"]//text()')[0],
                'raw_price': li.xpath('.//div[@class="current-bid ng-binding"]//text()')[0],
            }
            products[produrl]['price'] = getprice(products[produrl]['raw_price'])
            categories[ctg].append(produrl)

        # Checking if it was the last page
        if len(set(categories[ctg])) == number_of_pdcts_in_ctg:
            break
        else:
            number_of_pdcts_in_ctg = len(set(categories[ctg]))
print([(c, len(categories[c])) for c in categories])


# KW searches Scraping - with selenium - with nb page hard-coded in url - multiple page per search
search_url = "https://www.langtons.com.au/search?p={page}&query={kw}&IncludeBuyNow=true"
for kw in keywords:
    searches[kw] = []
    number_of_pdcts_in_kw_search = 0

    for p in range(10):
        # Storing and extracting infos
        fpath = fpath_namer(shop_id, 'search', kw, p)
        url = search_url.format(kw=kw, page=p+1)
        if not op.exists(fpath):
            driver.get(url)
            driver.wait_for_xpath('//*[@ng-repeat="prod in List.Products"]')
            driver.save_page(fpath, scroll_to_bottom=True)
        tree = etree.parse(open(fpath, 'rb'), parser=parser)
        for li in tree.xpath('//*[@id="results"]//li[contains(@ng-repeat, "prod in List.Products")]'):
            produrl = li.xpath('.//a/@href')[0]
            produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
            produrl = clean_url(produrl, root_url)
            products[produrl] = {
                'pdct_name_on_eretailer': li.xpath('.//b[@class="ng-binding"]//text()')[0],
                'raw_price': li.xpath('.//div[@class="current-bid ng-binding"]//text()')[0],
            }
            products[produrl]['price'] = getprice(products[produrl]['raw_price'])
            searches[kw].append(produrl)
        if len(set(searches[kw])) == number_of_pdcts_in_kw_search:
            break
        else:
            number_of_pdcts_in_kw_search = len(set(searches[kw]))
    print(kw, p, len(searches[kw]))


# Download the pages - with requests
brm = BrandMatcher()
for url in sorted(list(set(products))):
    d = products[url]
    if brm.find_brand(d['pdct_name_on_eretailer'])['brand'] in mh_brands:
        print(d['pdct_name_on_eretailer'])
        url_mod = clean_url(url, root_url=root_url)
        r = requests.get(url_mod, headers)
        with open('/tmp/' + shop_id + ' ' + d['pdct_name_on_eretailer'].replace('/', "-") + '.html', 'wb') as f:
            f.write(r.content)
        tree = etree.parse(BytesIO(r.content), parser=parser)
        products[url].update({
            'volume': d['pdct_name_on_eretailer'],
            'pdct_img_main_url': ''.join(tree.xpath('//div[@class="image-container"]//img/@src')),
            'ctg_denom_txt': ' '.join(' '.join(tree.xpath('//*[@id="bread-crumb"]//text()')).split()),
        })
        print(products[url])
        if not r.from_cache:
            sleep(3)


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
