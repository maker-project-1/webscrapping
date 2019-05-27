
import os.path as op
import re
from io import BytesIO

from lxml import etree

parser = etree.HTMLParser(encoding='utf-8')
from time import sleep
from urllib.parse import urlsplit, parse_qs
import requests
import requests_cache, imghdr
from validators import validate_raw_files
from create_csvs import create_csvs
from ers import all_keywords_fr as keywords, fpath_namer, mh_brands, clean_url, headers
from matcher import BrandMatcher
from ers import COLLECTION_DATE, file_hash, img_path_namer
import shutil
from custom_browser import CustomDriver
from parse import parse


# Init variables and assets
shop_id = "plusdebulles"
root_url = "https://www.plus-de-bulles.com/" 
requests_cache.install_cache(fpath_namer(shop_id, 'requests_cache'))
country = "FR"


searches, categories, products = {}, {}, {}
# If necessary
driver = CustomDriver(headless=True)


def getprice(pricestr):
    if pricestr == '':
        return pricestr
    pricestr = re.sub("[^0-9,€]", "", pricestr)
    price = parse('{pound:d},{pence:d}€', pricestr)
    if price is None:
        price = parse('{pence:d}p', pricestr)
        return price.named['pence']
    else:
        return price.named['pound'] * 100 + price.named['pence']


urls_ctgs_dict = {
    "champagne": "https://www.plus-de-bulles.com/fr/recherche?q=&hPP=24&idx=prod_product_catalogue_DEFAULT_price_asc&p={page}&dFR%5Bformat%5D%5B0%5D=Bouteille%2075CL&nR%5Bprice_absolute%5D%5B%3E%3D%5D%5B0%5D=106&is_v=1"
}


# Category Scraping
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
        tree = etree.parse(BytesIO(open(fpath, 'rb').read()), parser=parser)

        for li in tree.xpath('//div[@class="product-box"]'):
            produrl = li.xpath('./a/@href')[0]
            produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
            produrl = clean_url(produrl, root_url)
            products[produrl] = {
                'pdct_name_on_eretailer': ' '.join(''.join(li.xpath('.//div[@class="group-first"]//text()')).split()).strip(),
                'raw_price': ' '.join(''.join(li.xpath('.//*[contains(@class,"price-box")]//span/text()')).split()).strip().split("€")[0] + '€',
                'raw_promo_price': ' '.join(''.join(li.xpath('.//span[@class="crossed"]//text()')).split()).strip(),
            }
            print(products[produrl], produrl)
            products[produrl]['price'] = getprice(products[produrl]['raw_price'])
            products[produrl]['promo_price'] = getprice(products[produrl]['raw_promo_price'])
            print(products[produrl])
            
            categories[ctg].append(produrl)

        # Checking if it was the last page
        if len(set(categories[ctg])) == number_of_pdcts_in_ctg:
            break
        else:
            number_of_pdcts_in_ctg = len(set(categories[ctg]))
print([(c, len(categories[c])) for c in categories])


# KW searches Scraping - with selenium - with nb page hard-coded in url - multiple page per search
search_url = "https://www.plus-de-bulles.com/browse/?q={kw}&search_param=all"
for kw in keywords:
    searches[kw] = []
    number_of_pdcts_in_kw_search = 0

    # Storing and extracting infos
    urlp = search_url.format(kw=kw)
    fpath = fpath_namer(shop_id, 'search', kw, 0)
    if not op.exists(fpath):
        driver.get(urlp)
        try: driver.wait_for_xpath('//*[class="product-box"]', timeout=15)
        except: pass
        driver.save_page(fpath)
    tree = etree.parse(BytesIO(open(fpath, 'rb').read()), parser=parser)

    for li in tree.xpath('//div[@class="product-box"]'):
        produrl = li.xpath('./a/@href')[0]
        produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
        produrl = clean_url(produrl, root_url)
        products[produrl] = {
            'pdct_name_on_eretailer': ' '.join(''.join(li.xpath('.//div[@class="group-first"]//text()')).split()).strip(),
            'raw_price': ' '.join(''.join(li.xpath('.//*[contains(@class,"price-box")]//span/text()')).split()).strip().split("€")[0] + '€',
            'raw_promo_price': ' '.join(''.join(li.xpath('.//span[@class="crossed"]//text()')).split()).strip(),
        }
        print(products[produrl], produrl)
        products[produrl]['price'] = getprice(products[produrl]['raw_price'])
        products[produrl]['promo_price'] = getprice(products[produrl]['raw_promo_price'])
        print(products[produrl])

        searches[kw].append(produrl)
    print(kw, p, len(searches[kw]))


# Download the pages - with selenium
brm = BrandMatcher()
for url in sorted(list(set(products))):
    d = products[url]
    if brm.find_brand(d['pdct_name_on_eretailer'])['brand'] in mh_brands:
        print(d['pdct_name_on_eretailer'])
        url_mod = clean_url(url, root_url=root_url)
        
        fname = fpath_namer(shop_id, 'pdct', d['pdct_name_on_eretailer'], 0)
        if not op.exists(fname):
            driver.get(url_mod)
            sleep(2)
            driver.save_page(fname, scroll_to_bottom=True)
        tree = etree.parse(open(fname), parser=parser)

        products[url].update({
            'volume': ' '.join(''.join(tree.xpath('//div[contains(@class, "hidden-md")]//div[@class="product-title"]//text()')).split()),
            'pdct_img_main_url': clean_url(''.join(tree.xpath('//*[contains(@class, "product-image")]//img/@src')), root_url),
            'ctg_denom_txt': ' '.join(' '.join(tree.xpath('//ol[contains(@class, "breadcrumb")]//text()')).split()),
        })
        print(products[url])


# Download images
for url, pdt in products.items():
     if 'pdct_img_main_url' in pdt and pdt['pdct_img_main_url'] and brm.find_brand(pdt['pdct_name_on_eretailer'])['brand'] in mh_brands:
         print(pdt['pdct_name_on_eretailer'] + "." + pdt['pdct_img_main_url'].split('.')[-1])
         response = requests.get(pdt['pdct_img_main_url'], stream=True, verify=False, headers=headers)
         # response.raw.decode_content = True
         tmp_file_path = '/tmp/mhers_tmp_{}.imgtypetype'.format(abs(hash(pdt['pdct_img_main_url'])))
         img_path = img_path_namer(shop_id, pdt['pdct_name_on_eretailer'])
         with open(tmp_file_path, 'wb') as out_file:
             shutil.copyfileobj(response.raw, out_file)
         if imghdr.what(tmp_file_path) is not None:
             img_path = img_path.split('.')[0] + '.' + imghdr.what('/tmp/mhers_tmp_{}.imgtypetype'.format(abs(hash(pdt['pdct_img_main_url']))))
             shutil.copyfile('/tmp/mhers_tmp_{}.imgtypetype'.format(abs(hash(pdt['pdct_img_main_url']))), img_path)
             products[url].update({'img_path': img_path, 'img_hash': file_hash(img_path)})

create_csvs(products, categories, searches, shop_id, fpath_namer(shop_id, 'raw_csv'), COLLECTION_DATE)
validate_raw_files(fpath_namer(shop_id, 'raw_csv'))
driver.quit()
