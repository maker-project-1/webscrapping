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
from ers import all_keywords_usa as keywords, fpath_namer, mh_brands, clean_url, headers
from matcher import BrandMatcher
from ers import COLLECTION_DATE, file_hash, img_path_namer
import shutil
from custom_browser import CustomDriver
from parse import parse


# Init variables and assets
shop_id = 'ludwigs'
root_url = 'https://ludwigsfinewine.com/'
requests_cache.install_cache(fpath_namer(shop_id, 'requests_cache'))
country = 'USA'
searches, categories, products = {}, {}, {}
driver = CustomDriver(headless=True, download_images=False)

urls_ctgs_dict = {
    'champagne': 'https://ludwigsfinewine.com/collections/champagne/champagne?page={page}',
    'sparkling': 'https://ludwigsfinewine.com/collections/champagne/sparkling-wine',
    'still_wines': 'https://ludwigsfinewine.com/collections/wine?page={page}',
    'whisky': 'https://ludwigsfinewine.com/search?page={page}&q=whisky&type=product',
    'cognac': 'https://ludwigsfinewine.com/collections/cognac-1?page={page}',
    'vodka': 'https://ludwigsfinewine.com/collections/vodka?page={page}',
    'gin': 'https://ludwigsfinewine.com/collections/gin?page={page}',
    'tequila': 'https://ludwigsfinewine.com/collections/tequila?page={page}',
    'bourbon': 'https://ludwigsfinewine.com/collections/bourbon?page={page}',
    'rum': 'https://ludwigsfinewine.com/collections/rum?page={page}',
    'liquor': 'https://ludwigsfinewine.com/collections/liqueur?page={page}',
}


def getprice(pricestr):
    if not pricestr:
        return ''
    price = parse('${pound:d}.{pence:d}', pricestr)
    if not price:
        price = parse('${th:d},{pound:d}.{pence:d}', pricestr)
        return price.named['th'] * 100000 + price.named['pound'] * 100 + price.named['pence']
    return price.named['pound'] * 100 + price.named['pence']


# Category Scraping - with requests - multiple pages per category
for ctg, url in urls_ctgs_dict.items():
    categories[ctg] = []
    number_of_pdcts_in_ctg = 0
    for p in range(100):
        urlp = url.format(page=p+1)

        r = requests.get(urlp)

        with open('/tmp/' + shop_id + "_" + ctg + str(p) + ".html", 'wb') as f:
            f.write(r.content)

        tree = etree.parse(BytesIO(r.content), parser=parser)
        for li in tree.xpath('//div[contains(@id, "product-")]'):
            if not li.xpath('.//a/@href') or not ''.join(li.xpath('.//h3//text()')):
                continue
            produrl = li.xpath('.//a/@href')[0]
            produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(
                urlsplit(produrl).query) else produrl
            produrl = clean_url(produrl, root_url)
            products[produrl] = {
                'pdct_name_on_eretailer': ''.join(li.xpath('.//h3//text()')),
                'volume': ''.join(li.xpath('.//h3//text()')),
                'raw_promo_price': ''.join(w for t in li.xpath('.//span[@class="was_price"]//text()') for w in t.split()).strip(),
                'raw_price': ''.join(w for t in li.xpath('.//span[@class="current_price "]//text()') for w in t.split()).strip(),

            }
            # print(products[produrl], produrl)
            products[produrl]['price'] = getprice(products[produrl]['raw_price'].replace('SoldOut', ''))
            products[produrl]['promo_price'] = getprice(products[produrl]['raw_promo_price'])
            print(products[produrl])

            categories[ctg].append(produrl)

        # Checking if it was the last page
        if len(set(categories[ctg])) == number_of_pdcts_in_ctg:
            break
        else:
            number_of_pdcts_in_ctg = len(set(categories[ctg]))

        # Handling cache
        if not r.from_cache:
            sleep(3)
    print(ctg, len(categories[ctg]))


# KW searches Scraping - with requests - one page per search
kw_search_url = "https://ludwigsfinewine.com/pages/search-results-page?q={kw}"
for kw in keywords:
    searches[kw] = []
    url = kw_search_url.format(kw=kw)
    fpath = fpath_namer(shop_id, 'search', kw, 0)
    if not op.exists(fpath):
        driver.get(url)
        sleep(2)
        driver.save_page(fpath, scroll_to_bottom=True)

    tree = etree.parse(open(fpath, 'rb'), parser=parser)
    for li in tree.xpath('//ul//li[@class="snize-product"]'):
        if not li.xpath('.//a/@href') or not ''.join(li.xpath('.//span[@class="snize-title"]//text()')):
            continue
        produrl = li.xpath('.//a/@href')[0]
        produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(
            urlsplit(produrl).query) else produrl
        produrl = clean_url(produrl, root_url)
        products[produrl] = {
            'pdct_name_on_eretailer': ''.join(li.xpath('.//span[@class="snize-title"]//text()')),
            'volume': ''.join(li.xpath('.//span[@class="snize-title"]//text()')),
            'raw_promo_price': ''.join(
                w for t in li.xpath('.//span[@class="was_price"]//text()') for w in t.split()).strip(),
            'raw_price': ''.join(
                w for t in li.xpath('.//span[@class="snize-price "]//text()') for w in t.split()).strip(),

        }
        # print(products[produrl], produrl)
        products[produrl]['price'] = getprice(products[produrl]['raw_price'].replace('SoldOut', ''))
        products[produrl]['promo_price'] = getprice(products[produrl]['raw_promo_price'])
        print(products[produrl])

        searches[kw].append(produrl)
    print(kw, len(searches[kw]))


# Download the pages - with requests
brm = BrandMatcher()
for url in sorted(list(set(products))):
    d = products[url]
    if brm.find_brand(d['pdct_name_on_eretailer'])['brand'] in mh_brands:
        print(d['pdct_name_on_eretailer'])
        fname = fpath_namer(shop_id, 'pdct', d['pdct_name_on_eretailer'], 0)
        if not op.exists(fname):
            driver.get(url)
            sleep(2)
            driver.save_page(fname, scroll_to_bottom=True)
        tree = etree.parse(open(fname), parser=parser)
        products[url].update({
            'pdct_img_main_url': clean_url(''.join(tree.xpath('(//img[@class="cloudzoom featured_image"]/@src)[1]')), root_url),
            'ctg_denom_txt': ' '.join(' '.join(tree.xpath('//div[@class="breadcrumb_text"]//text()')).split()),
        })
        print(products[url])


import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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
