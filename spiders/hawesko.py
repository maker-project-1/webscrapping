import os.path as op
from io import BytesIO

from lxml import etree

parser = etree.HTMLParser(encoding='utf-8')
from time import sleep
from urllib.parse import urlsplit, parse_qs
import requests_cache, imghdr
from validators import validate_raw_files
from create_csvs import create_csvs

from ers import all_keywords_de as keywords, fpath_namer, mh_brands, clean_url, headers
from matcher import BrandMatcher
from ers import COLLECTION_DATE, file_hash, img_path_namer
import shutil
from custom_browser import CustomDriver
import requests

# Init variables and assets
shop_id = 'hawesko'
root_url = 'https://www.hawesko.de'
country = 'DE'
requests_cache.install_cache(fpath_namer(shop_id, 'requests_cache'))

searches, categories, products = {}, {}, {}
driver = CustomDriver(headless=True, download_images=False)

from parse import parse


def getprice(pricestr):
    if not pricestr:
        return
    price = parse('{poundandcent:d}', pricestr)
    return price.named['poundandcent'] * 100


def getpromoprice(pricestr):
    pricestr = pricestr.replace(' ', '')
    if pricestr == '':
        return pricestr
    price = parse('€{dol:d},{pence:d}', pricestr)
    if price is None:
        price = parse('€{dol:d}', pricestr)
        return price.named['dol'] * 100
    else:
        return price.named['dol'] * 100 + price.named['pence']


urls_ctgs_dict = {
            'champagne': 'https://www.hawesko.de/prosecco-champagner',
            'sparkling': 'https://www.hawesko.de/weisswein',
            'vodka': 'https://www.hawesko.de/suche/?q=vodka',
            'whisky': 'https://www.hawesko.de/suche/?q=whisky',
            'still_wines': 'https://www.hawesko.de/weisswein',
            'cognac': 'https://www.hawesko.de/spirituosen',
            'red_wine': 'https://www.hawesko.de/rotwein',
            'white_wine': 'https://www.hawesko.de/weisswein',
        }


# Category Scraping - with selenium - one page per category
for ctg, url in urls_ctgs_dict.items():
    categories[ctg] = []
    fpath = fpath_namer(shop_id, 'ctg', ctg, 0)
    if not op.exists(fpath):
        driver.get(url)
        for k in range(20):
            sleep(1.5)
            if driver.check_exists_by_xpath('//div[@class="article list loader"]//*[@class="button loading loaderbutton"]'):
                driver.waitclick('//div[@class="article list loader"]//*[@class="button loading loaderbutton"]')
                sleep(1)
            else:
                break
        driver.save_page(fpath)
    tree = etree.parse(BytesIO(open(fpath, 'rb').read()), parser=parser)
    for li in tree.xpath('//div[@data-module="article"]'):
        if not li.xpath('.//div/a/@href'):
            break
        produrl = li.xpath('.//div/a/@href')[0]

        produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
        produrl = clean_url(produrl, root_url)
        products[produrl] = {
            'pdct_name_on_eretailer': " ".join("".join(li.xpath('.//span[@class="name text-uppercase"]//text()')).split()),
            'raw_promo_price': ''.join(w for t in li.xpath('.//div[@class="price-deprecated"]/span[@class="value"]//text()') for w in t.split()).strip(),
            'raw_price': ''.join(w for t in li.xpath('.//div[@class="price"]//span[@class="bulk-price"]/text()')[:1] for w in t.split()).strip(),
        }
        print(products[produrl], produrl)
        products[produrl]['price'] = getprice(products[produrl]['raw_price'])
        products[produrl]['promo_price'] = getpromoprice(products[produrl]['raw_promo_price'])
        print(products[produrl])
        categories[ctg].append(produrl)
print([(c, len(categories[c])) for c in categories])



# KW Scraping - with selenium - one page per category
kw_search_url = u'https://www.hawesko.de/suche/?q={kw}'
for kw in keywords:
    print('Requesting', kw)
    searches[kw] = []
    fpath = fpath_namer(shop_id, 'search', kw, 0)
    if not op.exists(fpath):
        driver.get(kw_search_url.format(kw=kw))
        for k in range(20):
            sleep(1.5)
            if driver.check_exists_by_xpath('//div[@class="article list loader"]//*[@class="button loading loaderbutton"]'):
                driver.waitclick('//div[@class="article list loader"]//*[@class="button loading loaderbutton"]')
                sleep(1)
            else:
                break
        driver.save_page(fpath)
    tree = etree.parse(BytesIO(open(fpath, 'rb').read()), parser=parser)
    for li in tree.xpath('//div[@data-module="article"]'):
        if not li.xpath('.//div/a/@href'):
            break
        produrl = li.xpath('.//div/a/@href')[0]

        produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
        produrl = clean_url(produrl, root_url)
        products[produrl] = {
            'pdct_name_on_eretailer': " ".join("".join(li.xpath('.//span[@class="name text-uppercase"]//text()')).split()),
            'raw_promo_price': ''.join(w for t in li.xpath('.//div[@class="price-deprecated"]/span[@class="value"]//text()') for w in t.split()).strip(),
            'raw_price': ''.join(w for t in li.xpath('.//div[@class="price"]//span[@class="bulk-price"]/text()')[:1] for w in t.split()).strip(),
        }
        print(products[produrl], produrl)
        products[produrl]['price'] = getprice(products[produrl]['raw_price'].replace('.', ''))
        products[produrl]['promo_price'] = getpromoprice(products[produrl]['raw_promo_price'])
        print(products[produrl])
        searches[kw].append(produrl)
print(searches)


# Download the pages - with requests
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
            'volume': " ".join(tree.xpath('//div[@class="characteristics accordion"]//div[@class="description-row" and contains(div, "Füllmenge")]/div[@class="description-value"]//text()')[:1]).strip(),
            'pdct_img_main_url': clean_url(''.join(tree.xpath('//div[contains(@class, "article") and @data-fragment]//picture//img/@src')[:1]), root_url),
            'ctg_denom_txt': ' '.join(' '.join(tree.xpath('//div[@class="breadcrumb"]//text()')).split()),
        })
        print(products[url])


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
