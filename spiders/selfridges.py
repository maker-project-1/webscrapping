
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
from ers import all_keywords_uk as keywords, fpath_namer, mh_brands, clean_url, headers

from matcher import BrandMatcher
from ers import COLLECTION_DATE, file_hash, img_path_namer
import shutil
from custom_browser import CustomDriver
from parse import parse


# Init variables and assets
shop_id = "selfridges"
root_url = "http://www.selfridges.com/GB/en/"
requests_cache.install_cache(fpath_namer(shop_id, 'requests_cache'))
country = "UK"


searches, categories, products = {}, {}, {}
# If necessary
driver = CustomDriver(headless=False)


def getprice(pricestr):
    if pricestr == '':
        return pricestr
    pricestr = re.sub("[^0-9.£]", "", pricestr)
    price = parse('£{pound:d}.{pence:d}', pricestr)
    if price is None:
        price = parse('{pence:d}p', pricestr)
        return price.named['pence']
    else:
        return price.named['pound'] * 100 + price.named['pence']


urls_ctgs_dict = {
    "vodka": "http://www.selfridges.com/GB/en/cat/foodhall/wines-spirits/spirits/vodka/?llc=sn&browsing_country=GB&currency=",
    "sparkling": "http://www.selfridges.com/GB/en/cat/foodhall/wines-spirits/champagne/sparkling-wine/?llc=sn&browsing_country=GB&currency=",
    "cognac": "http://www.selfridges.com/GB/en/cat/foodhall/wines-spirits/spirits/armagnac-cognac/cognac/?llc=sn&browsing_country=GB&currency=",
    "champagne": "http://www.selfridges.com/GB/en/cat/foodhall/wines-spirits/champagne/?browsing_country=GB&currency=&ic=548444&language=en&pn={page}&ppp=180",
    "still_wines": "http://www.selfridges.com/GB/en/cat/foodhall/wines-spirits/wine/?browsing_country=GB&currency=&ic=548450&language=en&pn={page}&ppp=180",
    "whisky": "http://www.selfridges.com/GB/en/cat/foodhall/wines-spirits/spirits/whiskey/?browsing_country=GB&currency=GBP&ic=600494&language=en&pn={page}&ppp=180",
    "red_wine": "http://www.selfridges.com/GB/en/cat/foodhall/wines-spirits/wine/red/?llc=sn?browsing_country=GB&currency=GBP&ic=600494&language=en&pn={page}&ppp=180",
    "white_wine": "http://www.selfridges.com/GB/en/cat/foodhall/wines-spirits/wine/white/?llc=sn?browsing_country=GB&currency=GBP&ic=600494&language=en&pn={page}&ppp=180",
    "gin": "http://www.selfridges.com/GB/en/cat/foodhall/wines-spirits/spirits/gin/?llc=sn?browsing_country=GB&currency=GBP&ic=600494&language=en&pn={page}&ppp=180",
    "liquor": "http://www.selfridges.com/GB/en/cat/foodhall/wines-spirits/spirits/liqueurs/?llc=sn?browsing_country=GB&currency=GBP&ic=600494&language=en&pn={page}&ppp=180",
    "rum": "http://www.selfridges.com/GB/en/cat/foodhall/wines-spirits/spirits/rum/?llc=sn?browsing_country=GB&currency=GBP&ic=600494&language=en&pn={page}&ppp=180",
    "tequila": "http://www.selfridges.com/GB/en/cat/foodhall/wines-spirits/spirits/tequila-mezcal/?llc=sn?browsing_country=GB&currency=GBP&ic=600494&language=en&pn={page}&ppp=180",
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
        
        # r = requests.get(urlp)
        # with open('/tmp/' + shop_id + '_' + ctg + '.html', 'wb') as f:
        #     f.write(r.content)
        # tree = etree.parse(BytesIO(r.content), parser=parser)
        
        for li in tree.xpath('//div[@class="productsInner"]/div[not(@class="productContainerOrphan")]'):
            produrl = str(li.xpath('.//a/@href')[0])
            produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
            produrl = clean_url(produrl, root_url)
            products[produrl] = {
                'pdct_name_on_eretailer': ' '.join(' '.join(li.xpath('.//div[@class="productContainerDesc"]/a//text()')).split()).strip(),
                'raw_price': ' '.join(''.join(li.xpath('.//p[contains(@class, "price")]//text()')).split()).strip(),
                'raw_promo_price': ' '.join(''.join(li.xpath('.//sdfhgf//text()')).split()).strip(),
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


# KW searches Scraping - with selenium - with search string - multiple page per search
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
search_url = "http://www.selfridges.com/GB/en/cat/foodhall/wines-spirits/"
for kw in keywords:
    print("Searching", kw)
    searches[kw] = []
    fpath = fpath_namer(shop_id, 'search', kw, 0)
    if not op.exists(fpath):
        driver.get(search_url)
        driver.waitclick('//*[@title="Search Selfridges..."]')
        # driver.waitclick('//*[@class="searchSubmit"]')
        actions = ActionChains(driver.driver)
        actions.send_keys(kw)
        actions.send_keys(Keys.ENTER)
        actions.perform()
        driver.save_page(fpath, scroll_to_bottom=True)

    tree = etree.parse(open(fpath, 'rb'), parser=parser)
    for li in tree.xpath('//div[@class="productsInner"]/div[not(@class="productContainerOrphan")]'):
        produrl = str(li.xpath('.//a/@href')[0])
        produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(
            urlsplit(produrl).query) else produrl
        produrl = clean_url(produrl, root_url)
        products[produrl] = {
            'pdct_name_on_eretailer': ' '.join(' '.join(li.xpath('.//div[@class="productContainerDesc"]/a//text()')).split()).strip(),
            'raw_price': ' '.join(''.join(li.xpath('.//p[contains(@class, "price")]//text()')).split()).strip(),
            'raw_promo_price': ' '.join(''.join(li.xpath('.//sdfhgf//text()')).split()).strip(),
        }
        print(products[produrl], produrl)
        products[produrl]['price'] = getprice(products[produrl]['raw_price'])
        products[produrl]['promo_price'] = getprice(products[produrl]['raw_promo_price'])
        print(products[produrl])
        searches[kw].append(produrl)

    print(kw, len(searches[kw]))


# Download the pages - with selenium
brm = BrandMatcher()
for url in sorted(list(set(products))):
    print(url, type(url))
    d = products[url]
    if brm.find_brand(d['pdct_name_on_eretailer'])['brand'] in mh_brands:
        print(d['pdct_name_on_eretailer'], url)
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
            'volume': ' '.join(''.join(tree.xpath('.//span[@class="description"]//text()')).split()),
            'pdct_img_main_url': clean_url(''.join(tree.xpath('//div[@id="preloadZoomImage"]/img/@src')), root_url),
            'ctg_denom_txt': ' '.join(' '.join(tree.xpath('//ul[@itemprop="breadcrumb"]//text()')).split()),
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
