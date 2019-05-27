
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
from ers import all_keywords_aus as keywords, fpath_namer, mh_brands, clean_url, headers

from matcher import BrandMatcher
from ers import COLLECTION_DATE, file_hash, img_path_namer
import shutil
from custom_browser import CustomDriver
from parse import parse


# Init variables and assets
shop_id = "nicks_wine_merchant"
root_url = "https://www.nicks.com.au/" 
requests_cache.install_cache(fpath_namer(shop_id, 'requests_cache'))
country = "AUS"


searches, categories, products = {}, {}, {}
# If necessary
driver = CustomDriver(headless=True)



def getprice(pricestr):
    if pricestr == '':
        return pricestr
    pricestr = re.sub("[^0-9.$]", "", pricestr)
    price = parse('${pound:d}.{pence:d}', pricestr)
    if price is None:
        price = parse('{pence:d}p', pricestr)
        return price.named['pence']
    else:
        return price.named['pound'] * 100 + price.named['pence']



urls_ctgs_dict = {
    "vodka": "https://www.nicks.com.au/store/spirits-liqueurs/vodka?limit=48&mode=grid&p={page}", 
    "sparkling": "https://www.nicks.com.au/sparklings?limit=48&mode=grid&p={page}", 
    "cognac": "https://www.nicks.com.au/store/spirits-liqueurs/cognac?limit=48&mode=grid&p={page}", 
    "champagne": "https://www.nicks.com.au/sparklings/imported/champagne?limit=48&mode=grid&p={page}", 
    "still_wines": "https://www.nicks.com.au/white-wines?limit=48&mode=grid&p={page}", 
    "whisky": "https://www.nicks.com.au/store/spirits-liqueurs/whiskies?limit=60&mode=grid&p={page}",
    "red_wine": "https://www.nicks.com.au/red-wines?limit=60&mode=grid&p={page}",
    "white_wine": "https://www.nicks.com.au/white-wines?limit=60&mode=grid&p={page}",
    "gin": "https://www.nicks.com.au/store/spirits-liqueurs/gin?limit=60&mode=grid&p={page}",
    "tequila": "https://www.nicks.com.au/store/spirits-liqueurs/tequila-mezcal?limit=60&mode=grid&p={page}",
    "brandy": "https://www.nicks.com.au/store/spirits-liqueurs/other-brandy-eau-de-vie?limit=60&mode=grid&p={page}",
    "liquor": "https://www.nicks.com.au/store/spirits-liqueurs/liqueurs?limit=60&mode=grid&p={page}",
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
        
        for li in tree.xpath('//div[@class="product item"]'):
            produrl = li.xpath('.//div[@class="productblock-title"]/a/@href')[0]
            produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
            produrl = clean_url(produrl, root_url)
            products[produrl] = {
                'pdct_name_on_eretailer': ' '.join(''.join(li.xpath('.//div[@class="productblock-title"]/a//text()')).split()).strip(),
                'raw_price': ' '.join(''.join(li.xpath('.//div[contains(@id, "product-price")]//text()')).split()).strip(),
                'raw_promo_price': ' '.join(''.join(li.xpath('.//span[contains(@id, "old-price")]//text()')).split()).strip(),
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
        # if not r.from_cache:
        #     sleep(2)
print([(c, len(categories[c])) for c in categories])




# KW searches Scraping - with selenium - with nb page hard-coded in url - multiple page per search
search_url = "https://www.nicks.com.au/search?q={kw}&page={page}&limit=48&sort=relevance&mode=grid&type=products"
for kw in keywords:
    searches[kw] = []
    number_of_pdcts_in_kw_search = 0
    
    for p in range(10):
        # Storing and extracting infos
        urlp = search_url.format(kw=kw, page=p+1)
        
        fpath = fpath_namer(shop_id, 'search', kw, p)
        if not op.exists(fpath):
            driver.get(urlp)
            try:driver.wait_for_xpath('//div[@class="product item"]', timeout=15)
            except: pass
            driver.save_page(fpath)
        tree = etree.parse(BytesIO(open(fpath, 'rb').read()), parser=parser)
        
        # r = requests.get(urlp)
        # with open('/tmp/' + shop_id + " " + kw + '.html', 'wb') as f:
        #     f.write(r.content)
        # tree = etree.parse(BytesIO(r.content), parser=parser)
        
        for li in tree.xpath('//div[@class="product item"]'):
            produrl = li.xpath('.//div[@class="productblock-title"]/a/@href')[0]
            produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
            produrl = clean_url(produrl, root_url)
            products[produrl] = {
                'pdct_name_on_eretailer': ' '.join(''.join(li.xpath('.//div[@class="productblock-title"]/a//text()')).split()).strip(),
                'raw_price': ' '.join(''.join(li.xpath('.//div[contains(@id, "product-price")]//text()')).split()).strip(),
                'raw_promo_price': ' '.join(''.join(li.xpath('.//span[contains(@id, "old-price")]//text()')).split()).strip(),
            }
            print(products[produrl], produrl)
            products[produrl]['price'] = getprice(products[produrl]['raw_price'])
            products[produrl]['promo_price'] = getprice(products[produrl]['raw_promo_price'])
            print(products[produrl])
            
            searches[kw].append(produrl)
        if len(set(searches[kw])) == number_of_pdcts_in_kw_search:
            break
        else:
            number_of_pdcts_in_kw_search = len(set(searches[kw]))
        # if not r.from_cache:
        #     sleep(2)
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
        
        # r = requests.get(url_mod, headers)
        # with open('/tmp/' + shop_id + ' ' + d['pdct_name_on_eretailer'].replace('/', "-") + '.html', 'wb') as f:
        #     f.write(r.content)
        # tree = etree.parse(BytesIO(r.content), parser=parser)
        
        products[url].update({
            'volume': ''.join(tree.xpath('//div[@class="product details"]//div[contains(@class, "title")]/h1//text()')).strip(),
            'pdct_img_main_url': clean_url(''.join(tree.xpath('//div[@class="product details"]//div[@class="image"]/img/@src')), root_url),
            'ctg_denom_txt': ' '.join(' '.join(tree.xpath('//div[@class="breadcrumbs"]//text()')).split()),
        })
        print(products[url])
        # if not r.from_cache:
        #     sleep(2)




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
