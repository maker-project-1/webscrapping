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
from ers import all_keywords_de as keywords, fpath_namer, mh_brands, clean_url, headers

from matcher import BrandMatcher
from ers import COLLECTION_DATE, file_hash, img_path_namer
import shutil
from custom_browser import CustomDriver
from parse import parse

# Init variables and assets
shop_id = "belvini"
root_url = "https://www.belvini.de/"
requests_cache.install_cache(fpath_namer(shop_id, 'requests_cache'))
country = "DE"

searches, categories, products = {}, {}, {}
# If necessary
driver = CustomDriver(headless=True)


def getprice(pricestr):
    if pricestr == '':
        return pricestr
    pricestr = re.sub("[^0-9€, EUR]", "", pricestr)
    price = parse('{pound:d}.{pence:d} €', pricestr)
    print(pricestr)
    if price is None:
        print(price)
        try:
            price = parse('{pound:d},{pence:d} EUR', pricestr)
            return price.named['pound'] * 100 + price.named['pence']
        except:
            pass
        try:
            price = parse('{pound:d} €', pricestr)
            return price.named['pound'] * 100
        except:
            pass
    else:
        return price.named['pound'] * 100 + price.named['pence']



urls_ctgs_dict = {'vodka': 'https://www.belvini.de/index.php/page/{page}/cID/2009.html',
                  'sparkling': 'https://www.belvini.de/filter.php/page/{page}/cID/20/categories_id/20/inc_subcat/1.html',
                  'cognac': 'https://www.belvini.de/index.php/page/{page}/cID/30.html',
                  'champagne': 'https://www.belvini.de/filter.php/page/{page}/cID/20/country/frankreich_champagne.66/categories_id/20/inc_subcat/1.html',
                  'still_wines': 'https://www.belvini.de/index.php/page/{page}/cID/12.html',
                  'whisky': 'https://www.belvini.de/index.php/page/{page}/cID/2008.html',
                  'gin': 'https://www.belvini.de/spirituosen/gin?page={page}',
                  'tequila': 'https://www.belvini.de/spirituosen/tequila?page={page}',
                  'red_wine': 'https://www.belvini.de/rotweine?page={page}',
                  'white_wine': 'https://www.belvini.de/weisswein?page={page}',
                  'rum': 'https://www.belvini.de/spirituosen/rum?page={page}',
                  'brandy': 'https://www.belvini.de/spirituosen/brandy?page={page}',
                  'liquor': 'https://www.belvini.de/spirituosen/likoer?page={page}',
                  }

#  Get price list

d = {}
for kw in keywords:
    fpath = fpath_namer(shop_id, 'other', kw)
    url = "https://www.belvini.de/"
    if not op.exists(fpath):
        driver.get(url)
        driver.text_input(kw, '//input[@name="keywords"]')
        sleep(1.5)
        driver.save_page(fpath)
    tree = etree.parse(BytesIO(open(fpath, 'rb').read()), parser=parser)
    for li in tree.xpath('//*[not(contains(@id, "Help")) and @class="suggRow"]/*[@class="suggItem"]'):
        pdct_name_on_eretailer = ' '.join(''.join(li.xpath('.//*[@class="suggProduct"]//text()')).split()).strip()
        d[pdct_name_on_eretailer] = {
            'raw_price': ' '.join(''.join(li.xpath('.//*[@class="suggCat"]//text()')).split()).strip(),
            'raw_promo_price' ""
            'promo_price': '',
            }
        d[pdct_name_on_eretailer]['price'] = getprice(d[pdct_name_on_eretailer]['raw_price'])

print(len(d.keys()))


# Category Scraping
for ctg, url in urls_ctgs_dict.items():
    print(ctg)
    categories[ctg] = []
    number_of_pdcts_in_ctg = 0
    for p in range(100):
        urlp = url.format(page=p + 1)

        fpath = fpath_namer(shop_id, 'ctg', ctg, p)
        if not op.exists(fpath):
            driver.get(urlp)
            sleep(2)
            driver.save_page(fpath)
        tree = etree.parse(BytesIO(open(fpath, 'rb').read()), parser=parser)

        for li in tree.xpath('//*[contains(@id, "product_id_")]'):
            produrl = li.xpath('.//td/a/@href')[0]
            produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(
                urlsplit(produrl).query) else produrl
            produrl = clean_url(produrl, root_url)
            products[produrl] = {
                'pdct_name_on_eretailer': ' '.join(
                    ''.join(li.xpath('.//a[@class="contentpagetitle"]//text()')).split()).strip(),
                # 'raw_price': ' '.join(''.join(li.xpath('//div[@class="spell"]//text()')).split()).strip(),
                # 'raw_promo_price': ' '.join(''.join(li.xpath('.//sdfdsfdsf//text()')).split()).strip(),
            }
            if products[produrl]['pdct_name_on_eretailer'] in d:
                products[produrl].update(d[products[produrl]['pdct_name_on_eretailer']])
            categories[ctg].append(produrl)
            # print(products[produrl], produrl)

        # Checking if it was the last page
        if len(set(categories[ctg])) == number_of_pdcts_in_ctg:
            break
        else:
            number_of_pdcts_in_ctg = len(set(categories[ctg]))
print([(c, len(categories[c])) for c in categories])

# KW searches Scraping - with selenium - with nb page hard-coded in url - multiple page per search
search_url = "https://www.belvini.de/advanced_search_result.php/page/{page}/keywords/{kw}.html"
for kw in keywords:
    searches[kw] = []
    number_of_pdcts_in_kw_search = 0

    for p in range(10):
        # Storing and extracting infos
        urlp = search_url.format(kw=kw, page=p)

        fpath = fpath_namer(shop_id, 'search', kw, p)
        if not op.exists(fpath):
            driver.get(urlp)
            sleep(2)
            driver.save_page(fpath)
        tree = etree.parse(BytesIO(open(fpath, 'rb').read()), parser=parser)

        # r = requests.get(urlp)
        # tree = etree.parse(BytesIO(r.content), parser=parser)

        for li in tree.xpath('//*[contains(@id, "product_id_")]'):
            produrl = li.xpath('.//td/a/@href')[0]
            produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(
                urlsplit(produrl).query) else produrl
            produrl = clean_url(produrl, root_url)
            products[produrl] = {
                'pdct_name_on_eretailer': ' '.join(
                    ''.join(li.xpath('.//a[@class="contentpagetitle"]//text()')).split()).strip(),
            }
            if products[produrl]['pdct_name_on_eretailer'] in d:
                products[produrl].update(d[products[produrl]['pdct_name_on_eretailer']])
            searches[kw].append(produrl)
        if len(set(searches[kw])) == number_of_pdcts_in_kw_search:
            break
        else:
            number_of_pdcts_in_kw_search = len(set(searches[kw]))
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
            'volume': products[url]['pdct_name_on_eretailer'],
            'pdct_img_main_url': clean_url(''.join(tree.xpath('//td/a[@id="info_image"]/img/@src')), root_url),
            'ctg_denom_txt': ' '.join(tree.xpath('//h2[@class="contentpagetitle"]//text()')),
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
