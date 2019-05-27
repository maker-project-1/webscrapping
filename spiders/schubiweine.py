
import os.path as op
import re
from io import BytesIO

from lxml import etree

parser = etree.HTMLParser(encoding='iso-8859-1')
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
shop_id = "schubiweine"
root_url = "https://www.schubiweine.ch/"
requests_cache.install_cache(fpath_namer(shop_id, 'requests_cache'))
country = "CH"


searches, categories, products = {}, {}, {}
# If necessary
driver = CustomDriver(headless=False)


def getprice(pricestr):
    if pricestr == '':
        return pricestr
    pricestr = re.sub("[^0-9.]", "", pricestr.lower())
    price = parse('{pound:d}.{pence:d}', pricestr)
    if price is None:
        price = parse('{pence:d}p', pricestr)
        return price.named['pence']
    else:
        return price.named['pound'] * 100 + price.named['pence']

urls_ctgs_dict = {
    "vodka": "https://www.schubiweine.ch/andere-spirituosen/vodka.html?shop_recpage={page}",
    "sparkling": "https://www.schubiweine.ch/de/schaumweine/italien/{page}/", 
    "cognac": "https://www.schubiweine.ch/de/cognac-brandy/{page}/", 
    "champagne": "https://www.schubiweine.ch/de/champagner/{page}/", 
    "still_wines": "https://www.schubiweine.ch/de/weissweine/{page}/", 
    "whisky": "https://www.schubiweine.ch/de/whisky/{page}/",
    "red_wine": "https://www.schubiweine.ch/rotwein.html/{page}/",
    "white_wine": "https://www.schubiweine.ch/weisswein.html/{page}/",
    "rum": "https://www.schubiweine.ch/rum.html/{page}/",
    "gin": "https://www.schubiweine.ch/andere-spirituosen/gin.html/{page}/",
    "brandy": "https://www.schubiweine.ch/andere-spirituosen/cognac-brandy.html/{page}/"
}


# Category Scraping
for ctg, url in urls_ctgs_dict.items():
    categories[ctg] = []
    number_of_pdcts_in_ctg = 0
    for p in range(100):
        urlp = url.format(page=p+1)

        fpath = fpath_namer(shop_id, 'ctg', ctg, p)
        if not op.exists(fpath):
            driver.get(url)
            sleep(1)
            driver.save_page(fpath, scroll_to_bottom=True)
        tree = etree.parse(BytesIO(open(fpath, 'rb').read()), parser=parser)
        
        for li in tree.xpath('//section[@itemprop="itemListElement"]'):
            produrl = li.xpath('.//a/@href')[0]
            produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
            produrl = clean_url(produrl, root_url)
            products[produrl] = {
                'pdct_name_on_eretailer': ' '.join(''.join(li.xpath('.//*[@class="product__title"]//text()')).split()) + " " + ' '.join(''.join(li.xpath('.//*[@class="product__vintage"]//text()')).split()),
                'ctg_denom_txt': ' '.join(''.join(li.xpath('.//h3//text()')).split()),
                'raw_price': ' '.join(''.join(li.xpath('.//span[@class="productdetail__price-norm"]//text()')).split()),
                'volume': ' '.join(''.join(li.xpath('.//*[@class="tmpl--gamma js-matchheight"]//text()')).split()),
                'raw_promo_price': ' '.join(''.join(li.xpath('.//yuio//text()')).split()),
                'pdct_img_main_url': clean_url(''.join(li.xpath('.//img[@class="product__image"]/@src')), root_url),
            }
            print(products[produrl], produrl)
            products[produrl]['pdct_name_on_eretailer'] = products[produrl]['pdct_name_on_eretailer'].strip()
            products[produrl]['pdct_img_main_url'] = products[produrl]['pdct_img_main_url'].replace("/7/1/1", '/7/1/3')
            products[produrl]['pdct_img_main_url'] = products[produrl]['pdct_img_main_url'].replace('https://schubiweine-webtuningag.netdna-ssl.com/',
                                                                                                    "https://www.schubiweine.ch/")
            products[produrl]['volume'] = products[produrl]['volume'].split('(')[0]
            products[produrl]['price'] = getprice(products[produrl]['raw_price'])
            products[produrl]['promo_price'] = getprice(products[produrl]['raw_promo_price'])
            print(products[produrl])
            
            categories[ctg].append(produrl)

        # Checking if it was the last page
        if len(set(categories[ctg])) == number_of_pdcts_in_ctg:
            break
        else:
            number_of_pdcts_in_ctg = len(set(categories[ctg]))
print(categories)

# KW searches Scraping - with selenium - with nb page hard-coded in url - multiple page per search
search_url = "https://www.schubiweine.ch/search.html?searchtext={kw}"
for kw in keywords:
    searches[kw] = []
    number_of_pdcts_in_kw_search = 0
    
    # Storing and extracting infos
    urlp = search_url.format(kw=kw, page=0)
    fpath = fpath_namer(shop_id, 'search', kw, 0)

    if not op.exists(fpath_namer(shop_id, 'search', kw, 0)):
        driver.get(urlp)
        sleep(2)
        driver.save_page(fpath, scroll_to_bottom=True)

    tree = etree.parse(BytesIO(open(fpath, 'rb').read()), parser=parser)
    for li in tree.xpath('//section[@itemprop="itemListElement"]'):
        produrl = li.xpath('.//a/@href')[0]
        produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
        produrl = clean_url(produrl, root_url)
        products[produrl] = {
            'pdct_name_on_eretailer': ' '.join(
                ''.join(li.xpath('.//*[@class="product__title"]//text()')).split()) + " " + ' '.join(
                ''.join(li.xpath('.//*[@class="product__vintage"]//text()')).split()),
            'ctg_denom_txt': ' '.join(''.join(li.xpath('.//h3//text()')).split()),
            'raw_price': ' '.join(''.join(li.xpath('.//span[@class="productdetail__price-norm"]//text()')).split()),
            'volume': ' '.join(''.join(li.xpath('.//*[@class="tmpl--gamma js-matchheight"]//text()')).split()),
            'raw_promo_price': ' '.join(''.join(li.xpath('.//yuio//text()')).split()),
            'pdct_img_main_url': clean_url(''.join(li.xpath('.//img[@class="product__image"]/@src')), root_url),
        }
        print(products[produrl], produrl)
        products[produrl]['pdct_name_on_eretailer'] = products[produrl]['pdct_name_on_eretailer'].strip()
        products[produrl]['pdct_img_main_url'] = products[produrl]['pdct_img_main_url'].replace("/7/1/1", '/7/1/3')
        products[produrl]['pdct_img_main_url'] = products[produrl]['pdct_img_main_url'].replace('https://schubiweine-webtuningag.netdna-ssl.com/',
                                                                                                "https://www.schubiweine.ch/")
        products[produrl]['volume'] = products[produrl]['volume'].split('(')[0]

        print(products[produrl], produrl)
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


