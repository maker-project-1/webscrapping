
import os.path as op
import re
from io import BytesIO

from lxml import etree

parser = etree.HTMLParser(encoding='utf-8')
from time import sleep
from urllib.parse import urlsplit, parse_qs
import requests
import requests_cache, imghdr
from ers import all_keywords_ch as keywords, fpath_namer, mh_brands, clean_url, headers

from matcher import BrandMatcher
from ers import COLLECTION_DATE, file_hash, img_path_namer
import shutil
from custom_browser import CustomDriver
from parse import parse
from validators import validate_raw_files
from create_csvs import create_csvs

# Init variables and assets
shop_id = "leshop"
root_url = "https://www.leshop.ch/"
requests_cache.install_cache(fpath_namer(shop_id, 'requests_cache'))
country = "CH"


searches, categories, products = {}, {}, {}
# If necessary
driver = CustomDriver(headless=False, download_images=True)


def getprice(pricestr):
    if pricestr == '':
        return pricestr
    pricestr = re.sub("[^0-9.]", "", pricestr.lower())
    if pricestr.startswith('.'):
        pricestr = pricestr[1:]
    price = parse('{pound:d}.{pence:d}', pricestr)
    if price is None:
        price = parse('{pence:d}p', pricestr)
        return price.named['pence']
    else:
        return price.named['pound'] * 100 + price.named['pence']



urls_ctgs_dict = {
    "vodka": "https://www.leshop.ch/en/supermarket/spirits/spirits/vodka-and-gin/vodka", 
    "sparkling": "https://www.leshop.ch/en/supermarket/wines-champagne/wines-champagnes/champagnes-sparkling-wines/sparkling-wines", 
    "cognac": "https://www.leshop.ch/en/supermarket/spirits/spirits/digestives/brandy-cognac", 
    "champagne": "https://www.leshop.ch/en/supermarket/wines-champagne/wines-champagnes/champagnes-sparkling-wines/champagne", 
    "still_wines": "https://www.leshop.ch/en/supermarket/wines-champagne/wines-champagnes/foreign-white-wines", 
    "whisky": "https://www.leshop.ch/en/supermarket/spirits/spirits/whisky",
    "tequila": "https://www.leshop.ch/en/supermarket/drinks-alcohol/aperitifs-digestifs/rum-tequila",
    "rum": "https://www.leshop.ch/en/supermarket/drinks-alcohol/aperitifs-digestifs/rum-tequila",
    "gin": "https://www.leshop.ch/en/supermarket/drinks-alcohol/aperitifs-digestifs/vodka-gin",
}


# Category Scraping
for ctg, url in urls_ctgs_dict.items():
    categories[ctg] = []
    fpath = fpath_namer(shop_id, 'ctg', ctg, 0)
    if not op.exists(fpath):
        driver.get(url)
        sleep(2)
        driver.save_page(fpath, scroll_to_bottom=True)
    tree = etree.parse(BytesIO(open(fpath, 'rb').read()), parser=parser)

    for li in tree.xpath('//ul[@class="subcat"]/li'):
        produrl = li.xpath('.//a/@href')[0]
        produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
        produrl = clean_url(produrl, root_url)
        products[produrl] = {
            'pdct_name_on_eretailer': ' '.join(''.join(li.xpath('.//span[@class="name"]//text()')).split()),
            'raw_price': ' '.join(''.join(li.xpath('.//*[contains(@id, "original-price")]//text()')).split()),
            'raw_promo_price': ' '.join(''.join(li.xpath('.//*[contains(@id, "current-price")]//text()')).split()),
            'volume': ' '.join(''.join(li.xpath('.//span[contains(@id, "weight")]/span/text()')).split()),
            'pdct_img_main_url': clean_url(''.join(li.xpath('.//*[@class="productImage"]/img/@src')), root_url),
            'ctg_denom_txt': ctg,
        }
        if products[produrl]['pdct_img_main_url'] == 'https://www.leshop.ch/':
            products[produrl]['pdct_img_main_url'] = clean_url(''.join(li.xpath('.//*[@class="productImage"]/img/@data-src')), root_url)

        products[produrl]['pdct_img_main_url'] = re.sub(r"w_.{3},h_.{3}", "w_500,h_500", products[produrl]['pdct_img_main_url'])

        if not products[produrl]['raw_promo_price']:
            products[produrl]['raw_price'] = ' '.join(''.join(li.xpath('.//span[@class="price"]//text()')).split())

        products[produrl]['price'] = getprice(products[produrl]['raw_price'])
        products[produrl]['promo_price'] = getprice(products[produrl]['raw_promo_price'])
        print(products[produrl])

        categories[ctg].append(produrl)
print([(c, len(categories[c])) for c in categories])


# KW searches Scraping - with selenium - with nb page hard-coded in url - multiple page per search
search_url = "https://www.leshop.ch/en/search?query={kw}"
for kw in keywords:
    searches[kw] = []

    # Storing and extracting infos
    urlp = search_url.format(kw=kw)

    fpath = fpath_namer(shop_id, 'search', kw, 0)
    if not op.exists(fpath):
        driver.get(urlp)
        sleep(2)
        driver.save_page(fpath, scroll_to_bottom=True)
    tree = etree.parse(BytesIO(open(fpath, 'rb').read()), parser=parser)

    for li in tree.xpath('//ul[@class="subcat"]/li'):
        produrl = li.xpath('.//a/@href')[0]
        produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(
            urlsplit(produrl).query) else produrl
        produrl = clean_url(produrl, root_url)
        products[produrl] = {
            'pdct_name_on_eretailer': ' '.join(''.join(li.xpath('.//span[@class="name"]//text()')).split()),
            'raw_price': ' '.join(''.join(li.xpath('.//*[contains(@id, "original-price")]//text()')).split()),
            'raw_promo_price': ' '.join(''.join(li.xpath('.//*[contains(@id, "current-price")]//text()')).split()),
            'volume': ' '.join(''.join(li.xpath('.//span[contains(@id, "weight")]/span/text()')).split()),
            'pdct_img_main_url': clean_url(''.join(li.xpath('.//*[@class="productImage"]/img/@src')), root_url),
            'ctg_denom_txt': '',
        }
        if products[produrl]['pdct_img_main_url'] == 'https://www.leshop.ch/':
            products[produrl]['pdct_img_main_url'] = clean_url(''.join(li.xpath('.//*[@class="productImage"]/img/@data-src')), root_url)
        products[produrl]['pdct_img_main_url'] = re.sub(r"w_.{3},h_.{3}", "w_500,h_500", products[produrl]['pdct_img_main_url'])
        if not products[produrl]['raw_promo_price']:
            products[produrl]['raw_price'] = ' '.join(''.join(li.xpath('.//span[@class="price"]//text()')).split())
        products[produrl]['price'] = getprice(products[produrl]['raw_price'])
        products[produrl]['promo_price'] = getprice(products[produrl]['raw_promo_price'])
        print(products[produrl])
        searches[kw].append(produrl)
    print(kw, len(searches[kw]))


# Download images
brm = BrandMatcher()
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

create_csvs(products, categories, searches, shop_id, fpath_namer(shop_id, 'raw_csv'), COLLECTION_DATE)
validate_raw_files(fpath_namer(shop_id, 'raw_csv'))
driver.quit()