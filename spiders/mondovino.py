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
shop_id = "mondovino"
root_url = "https://www.mondovino.ch"
requests_cache.install_cache(fpath_namer(shop_id, 'requests_cache'))
country = "CH"

searches, categories, products = {}, {}, {}


# If necessary
driver = CustomDriver(headless=False, download_images=True)



def getprice(pricestr):
    if pricestr == '':
        return pricestr
    pricestr = re.sub("[^0-9.chf]", "", pricestr.lower())
    price = parse('chf{pound:d}.{pence:d}', pricestr)
    if price is None:
        price = parse('{pence:d}p', pricestr)
        return price.named['pence']
    else:
        return price.named['pound'] * 100 + price.named['pence']


urls_ctgs_dict = {
    'champagne': 'https://www.mondovino.ch/catalogue/typedevin/Champagne',
    'vodka': 'https://www.mondovino.ch/selections/spiritueux/Cfr',
    'cognac': 'https://www.mondovino.ch/selections/spiritueux/Cfr',
    'whisky': 'https://www.mondovino.ch/selections/spiritueux/Cfr',
    'still_wines': 'https://www.mondovino.ch/catalogue/typedevin/Vin+blanc',
    'white_wine': 'https://www.mondovino.ch/catalogue/typedevin/Vin+blanc',
    'red_wine': 'https://www.mondovino.ch/catalogue/typedevin/Vin+rouge',
}

# Category Scraping
for ctg, url in urls_ctgs_dict.items():
    categories[ctg] = []
    fpath = fpath_namer(shop_id, 'ctg', ctg, 0)
    if not op.exists(fpath):
        driver.get(url)
        # Get scroll height
        last_height = driver.driver.execute_script("return document.body.scrollHeight")
        while True:
            # Scroll down to bottom
            driver.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            try:
                driver.waitclick('//div[@class="mod_product_list__more"]/a', timeout=5, silent=True)
            except:
                pass
            # Wait to load page
            sleep(2)

            # Calculate new scroll height and compare with last scroll height
            new_height = driver.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        driver.save_page(fpath)

    tree = etree.parse(BytesIO(open(fpath, 'rb').read()), parser=parser)

    for li in tree.xpath('//li[@class="mod_product_list__item"]'):
        produrl = li.xpath('.//h3/a/@href')[0]
        produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(
            urlsplit(produrl).query) else produrl
        produrl = clean_url(produrl, root_url)
        products[produrl] = {
            'pdct_name_on_eretailer': ' '.join(''.join(li.xpath('.//h3/a//text()')).split()),
            'ctg_denom_txt': ' '.join(''.join(li.xpath('.//h3/a//text()')).split()),
            'raw_price': ' '.join(''.join(li.xpath('.//span[@class="mod_product_teaser__wrapper_price"]/span[position() <=2]//text()')).split()),
            'volume': ' '.join(''.join(li.xpath('.//span[@class="mod_product_teaser__wrapper_price"]/span[position() > 2]//text()')).split()),
            'raw_promo_price': ' '.join(''.join(li.xpath('.//yuio//text()')).split()),
            'pdct_img_main_url': clean_url(''.join(li.xpath('.//span[@class="mod_product_teaser__teaser_img"]//img/@src')), root_url),
        }
        print(products[produrl], produrl)
        products[produrl]['pdct_img_main_url'] = re.sub(r"front\/.*\/", "front/1000/", products[produrl]['pdct_img_main_url'])
        products[produrl]['volume'] = products[produrl]['volume'].split('(')[0]
        products[produrl]['price'] = getprice(products[produrl]['raw_price'])
        products[produrl]['promo_price'] = getprice(products[produrl]['raw_promo_price'])
        print(products[produrl])

        categories[ctg].append(produrl)
print(categories)

# KW searches Scraping - with selenium - with nb page hard-coded in url - multiple page per search
search_url = "https://www.mondovino.ch/recherche/{kw}"
for kw in keywords:
    searches[kw] = []

    fpath = fpath_namer(shop_id, 'search', kw, 0)
    if not op.exists(fpath):
        driver.get(search_url.format(kw=kw))
        # Get scroll height
        last_height = driver.driver.execute_script("return document.body.scrollHeight")
        while True:
            # Scroll down to bottom
            driver.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            try:
                driver.waitclick('//div[@class="mod_product_list__more"]/a', timeout=3, silent=True)
            except:
                pass
            # Wait to load page
            sleep(2)

            # Calculate new scroll height and compare with last scroll height
            new_height = driver.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        driver.save_page(fpath)

    tree = etree.parse(BytesIO(open(fpath, 'rb').read()), parser=parser)

    for li in tree.xpath('//li[@class="mod_product_list__item"]'):
        produrl = li.xpath('.//h3/a/@href')[0]
        produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(
            urlsplit(produrl).query) else produrl
        produrl = clean_url(produrl, root_url)
        products[produrl] = {
            'pdct_name_on_eretailer': ' '.join(''.join(li.xpath('.//h3/a//text()')).split()),
            'ctg_denom_txt': ' '.join(''.join(li.xpath('.//h3/a//text()')).split()),
            'raw_price': ' '.join(''.join(
                li.xpath('.//span[@class="mod_product_teaser__wrapper_price"]/span[position() <=2]//text()')).split()),
            'volume': ' '.join(''.join(
                li.xpath('.//span[@class="mod_product_teaser__wrapper_price"]/span[position() > 2]//text()')).split()),
            'raw_promo_price': ' '.join(''.join(li.xpath('.//yuio//text()')).split()),
            'pdct_img_main_url': clean_url(
                ''.join(li.xpath('.//span[@class="mod_product_teaser__teaser_img"]//img/@src')), root_url),
        }
        print(products[produrl], produrl)
        products[produrl]['pdct_img_main_url'] = re.sub(r"front\/.*\/", "front/1000/",
                                                        products[produrl]['pdct_img_main_url'])
        products[produrl]['volume'] = products[produrl]['volume'].split('(')[0]
        products[produrl]['price'] = getprice(products[produrl]['raw_price'])
        products[produrl]['promo_price'] = getprice(products[produrl]['raw_promo_price'])
        print(products[produrl])
        searches[kw].append(produrl)

    print(kw, 0, len(searches[kw]))

# Download images
brm = BrandMatcher()
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
