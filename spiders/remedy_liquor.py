import re
from io import BytesIO

from lxml import etree

parser = etree.HTMLParser(encoding='utf-8')
from time import sleep
from urllib.parse import urlsplit, parse_qs
import requests_cache, imghdr
from validators import validate_raw_files
from create_csvs import create_csvs
from ers import all_keywords_usa as keywords, mh_brands, clean_url, headers

from matcher import BrandMatcher
from ers import COLLECTION_DATE, file_hash, img_path_namer, fpath_namer
import shutil
from parse import parse
from helpers.random_user_agent import randomua
import requests

# Init variables and assets
shop_id = "remedy_liquor"
root_url = "https://remedyliquor.com/"
session = requests_cache.CachedSession(fpath_namer(shop_id, 'requests_cache'))
session.headers = {'User-Agent': randomua()}
country = "USA"

searches, categories, products = {}, {}, {}
# If necessary
# driver = CustomDriver(headless=True)


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
    "vodka": "https://remedyliquor.com/spirits/vodka.html?limit=100&p={page}",
    "sparkling": "https://remedyliquor.com/wine/champagne.html?limit=100&p={page}",
    "cognac": "https://remedyliquor.com/spirits/brandy-cognac.html?limit=100&p={page}",
    "champagne": "https://remedyliquor.com/wine/champagne.html?limit=100&p={page}",
    "still_wines": "https://remedyliquor.com/wine.html?limit=100&p={page}",
    "whisky": "https://remedyliquor.com/spirits/whisky.html?limit=100&p={page}",
    "red_wine": "https://remedyliquor.com/wine/red-wine.html?limit=100&p={page}",
    "white_wine": "https://remedyliquor.com/wine/white-wine.html?limit=100&p={page}",
    "gin": "https://remedyliquor.com/spirits/gin.html?limit=100&p={page}",
    "liquor": "https://remedyliquor.com/spirits/liqueurs.html?limit=100&p={page}",
    "rum": "https://remedyliquor.com/spirits/rum.html?limit=100&p={page}",
    "tequila": "https://remedyliquor.com/spirits/tequila.html?limit=100&p={page}",
    "bourbon": "https://remedyliquor.com/spirits/bourbon.html?limit=100&p={page}",
}


# Category Scraping
for ctg, url in urls_ctgs_dict.items():
    categories[ctg] = []
    number_of_pdcts_in_ctg = 0
    for p in range(100):
        urlp = url.format(page=p+1)

        # fpath = fpath_namer(shop_id, 'ctg', ctg, p)
        # if not op.exists(fpath):
        #     driver.get(urlp)
        #     sleep(2)
        #     driver.save_page(fpath)
        # tree = etree.parse(BytesIO(open(fpath, 'rb').read()), parser=parser)

        r = session.get(urlp)
        with open('/tmp/' + shop_id + ' ' + ctg + '.html', 'wb') as f:
            f.write(r.content)
        tree = etree.parse(BytesIO(r.content), parser=parser)
        
        for li in tree.xpath('//div[@class="product-content"]'):
            produrl = li.xpath('.//h2[contains(@class, "product-name")]/a/@href')[0]
            produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
            produrl = clean_url(produrl, root_url)
            products[produrl] = {
                'pdct_name_on_eretailer': ' '.join(''.join(li.xpath('.//h2[contains(@class, "product-name")]/a//text()')).split()).strip(),
                'raw_price': ' '.join(''.join(li.xpath('.//span/span[contains(@class, "price")]//text()')).split()).strip(),
                'raw_promo_price': ' '.join(''.join(li.xpath('.//span/span[contains(@class, "price")]/dsq//text()')).split()).strip(),
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
        if not r.from_cache:
            sleep(2)
print([(c, len(categories[c])) for c in categories])


# KW searches Scraping - with selenium - with nb page hard-coded in url - multiple page per search
search_url = "https://remedyliquor.com/catalogsearch/result/index/?a=all&limit=120&q={kw}&p={page}"
for kw in keywords:
    searches[kw] = []
    number_of_pdcts_in_kw_search = 0
    
    for p in range(10):
        # Storing and extracting infos
        urlp = search_url.format(kw=kw, page=p+1)

        # fpath = fpath_namer(shop_id, 'search', kw, 0)
        # if not op.exists(fpath):
        #     driver.get(urlp)
        #     try:
        #         driver.wait_for_xpath('//*[class="product-box"]', timeout=15)
        #     except:
        #         pass
        #     driver.save_page(fpath)
        # tree = etree.parse(BytesIO(open(fpath, 'rb').read()), parser=parser)

        r = session.get(urlp)
        with open('/tmp/' + shop_id + " " + kw + '.html', 'wb') as f:
            f.write(r.content)
        tree = etree.parse(BytesIO(r.content), parser=parser)
        
        for li in tree.xpath('//div[@class="product-content"]'):
            produrl = li.xpath('.//h2[contains(@class, "product-name")]/a/@href')[0]
            produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
            produrl = clean_url(produrl, root_url)
            products[produrl] = {
                'pdct_name_on_eretailer': ' '.join(''.join(li.xpath('.//h2[contains(@class, "product-name")]/a//text()')).split()).strip(),
                'raw_price': ' '.join(''.join(li.xpath('.//span/span[contains(@class, "price")]//text()')).split()).strip(),
                'raw_promo_price': ' '.join(''.join(li.xpath('.//span/span[contains(@class, "price")]/dsq//text()')).split()).strip(),
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
        if not r.from_cache:
            sleep(2)
    print(kw, p, len(searches[kw]))

# Download the pages - with selenium
brm = BrandMatcher()
for url in sorted(list(set(products))):
    d = products[url]
    if brm.find_brand(d['pdct_name_on_eretailer'])['brand'] in mh_brands:
        print(d['pdct_name_on_eretailer'])
        url_mod = clean_url(url, root_url=root_url)
        r = session.get(url_mod)
        with open('/tmp/' + shop_id + ' ' + d['pdct_name_on_eretailer'].replace('/', "-") + '.html', 'wb') as f:
            f.write(r.content)
        tree = etree.parse(BytesIO(r.content), parser=parser)
        
        products[url].update({
            'volume': ' '.join(''.join(tree.xpath('//div[@class="product-name"]/h1//text()')).split()),
            'pdct_img_main_url': clean_url(''.join(tree.xpath('//*[@id="ma-zoom1"]/@href')), root_url),
            'ctg_denom_txt': ' '.join(' '.join(tree.xpath('//*[@class="breadcrumbs"]//text()')).split()),
        })
        print(products[url])
        if not r.from_cache:
            sleep(2)

# Download images
# from custom_browser import CustomDriver
# driver = CustomDriver()
for url, pdt in products.items():
     if 'pdct_img_main_url' in pdt and pdt['pdct_img_main_url'] and brm.find_brand(pdt['pdct_name_on_eretailer'])['brand'] in mh_brands:
         print(pdt['pdct_name_on_eretailer'] + "." + pdt['pdct_img_main_url'].split('.')[-1])
         response = requests.get(pdt['pdct_img_main_url'], stream=True, verify=False, headers=headers)
         # response.raw.decode_content = True
         tmp_file_path = '/tmp/' + shop_id + 'mhers_tmp_{}.imgtype'.format(abs(hash(pdt['pdct_img_main_url'])))
         img_path = img_path_namer(shop_id, pdt['pdct_name_on_eretailer'])
         # print(img_path, tmp_file_path)
         with open(tmp_file_path, 'wb') as out_file:
             out_file.write(response.content)
             # shutil.copyfileobj(response.raw, out_file)
         if imghdr.what(tmp_file_path) is not None:
             img_path = img_path.split('.')[0] + '.' + imghdr.what('/tmp/' + shop_id + 'mhers_tmp_{}.imgtype'.format(abs(hash(pdt['pdct_img_main_url']))))
             print(img_path, tmp_file_path)
             shutil.copyfile('/tmp/' + shop_id + 'mhers_tmp_{}.imgtype'.format(abs(hash(pdt['pdct_img_main_url']))), img_path)
             products[url].update({'img_path': img_path, 'img_hash': file_hash(img_path)})
         else:
             print("WARNING !", pdt['pdct_img_main_url'], img_path, tmp_file_path)

create_csvs(products, categories, searches, shop_id, fpath_namer(shop_id, 'raw_csv'), COLLECTION_DATE)
validate_raw_files(fpath_namer(shop_id, 'raw_csv'))
# driver.quit()
