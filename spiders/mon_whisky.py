from lxml import etree
from io import BytesIO
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
shop_id = 'mon_whisky'
root_url = 'http://www.monwhisky.fr'
requests_cache.install_cache(fpath_namer(shop_id, 'requests_cache'))
country = 'FR'
searches, categories, products = {}, {}, {}
driver = CustomDriver(headless=True, download_images=False)


urls_ctgs_dict = {
            # 'champagne': '',
            # 'sparkling': '',
            # 'still_wines': '',
            'whisky': 'http://www.monwhisky.fr/whiskies.html?mode=list&p={page}/',
            # 'cognac':'',
            'vodka': 'http://www.monwhisky.fr/catalogsearch/result/?q=vodka',
        }


def getprice(pricestr):
    pricestr = pricestr.replace(' ', '')
    if pricestr == '':
        return pricestr
    price = parse('{dol:d},{pence:d}€', pricestr)
    if price is None:
        price = parse('{dol:d}€', pricestr)
        return price.named['dol'] * 100
    else:
        return price.named['dol'] * 100 + price.named['pence']


# Category Scraping - with requests - multiple pages per category
for ctg, url in urls_ctgs_dict.items():
    categories[ctg] = []
    number_of_pdcts_in_ctg = 0
    for p in range(100):
        urlp = url.format(page=p+1)
        print(ctg, p, urlp)
        r = requests.get(urlp)
        tree = etree.parse(BytesIO(r.content), parser=parser)
        for li in tree.xpath('//div[@class="category-products"]/ul/li'):
            produrl = li.xpath('.//div[1]/a/@href')[0]
            produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
            raw_promo_price = ''.join(w for t in li.xpath('.//div[@class="price-box"]//p[2]//text()') for w in t.split()).strip()
            raw_price = ''.join(w for t in li.xpath('.//div[@class="price-box"]//p[1]//text()') for w in t.split()).strip()
            print(raw_promo_price)
            products[produrl] = {
                'pdct_name_on_eretailer': ''.join(li.xpath('.//h2[@class="product-name"]//text()')),
                'raw_price': ''.join(w for t in li.xpath('.//div[@class="price-box"]//text()') for w in t.split()).strip(),
            }
            if raw_promo_price:
                products[produrl]['raw_price'] = raw_price.replace('Prixnormal:', '')
                products[produrl]['raw_promo_price'] = raw_promo_price.replace('SpecialPrice', '')
                products[produrl]['promo_price'] = getprice(products[produrl]['raw_promo_price'])
            print(products[produrl], produrl)
            products[produrl]['price'] = getprice(products[produrl]['raw_price'])
            print(products[produrl])
            categories[ctg].append(produrl)
        assert all(products[produrl][k] for k in products[produrl])

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
kw_search_url = "http://www.monwhisky.fr/catalogsearch/result/?q={kw}"
for kw in keywords:
    print('Requesting', kw)
    searches[kw] = []
    url = kw_search_url.format(kw=kw)
    r = requests.get(url)
    tree = etree.parse(BytesIO(r.content), parser=parser)
    for li in tree.xpath('//div[@class="category-products"]/ul/li'):
        produrl = li.xpath('.//div[1]/a/@href')[0]
        produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
        raw_promo_price = ''.join(
            w for t in li.xpath('.//div[@class="price-box"]//p[2]//text()') for w in t.split()).strip()
        raw_price = ''.join(w for t in li.xpath('.//div[@class="price-box"]//p[1]//text()') for w in t.split()).strip()
        print(raw_promo_price)
        products[produrl] = {
            'pdct_name_on_eretailer': ''.join(li.xpath('.//h2[@class="product-name"]//text()')),
            'raw_price': ''.join(w for t in li.xpath('.//div[@class="price-box"]//text()') for w in t.split()).strip(),
        }
        if raw_promo_price:
            products[produrl]['raw_price'] = raw_price.replace('Prixnormal:', '')
            products[produrl]['raw_promo_price'] = raw_promo_price.replace('SpecialPrice', '')
            products[produrl]['promo_price'] = getprice(products[produrl]['raw_promo_price'])
        print(products[produrl], produrl)
        products[produrl]['price'] = getprice(products[produrl]['raw_price'])
        print(products[produrl])
        searches[kw].append(produrl)
    assert all(products[produrl][k] for k in products[produrl])
    if not r.from_cache:
        sleep(3)
    print(kw, len(searches[kw]))


# Download the pages - with requests
brm = BrandMatcher()
for url in sorted(list(set(products))):
    d = products[url]
    if brm.find_brand(d['pdct_name_on_eretailer'])['brand'] in mh_brands:
        print(d['pdct_name_on_eretailer'])
        url_mod = clean_url(url, root_url=root_url)
        r = requests.get(url_mod, headers)
        with open('/tmp/' + shop_id + ' ' + d['pdct_name_on_eretailer'].replace('/', "-") + '.html', 'wb') as f:
            f.write(r.content)
        tree = etree.parse(BytesIO(r.content), parser=parser)
        products[url].update({
            'volume': ' '.join(' '.join(tree.xpath('//p[@class="legend"]//text()')).split()),
            'pdct_img_main_url': clean_url(''.join(tree.xpath('//a[@id="zoom1"]/@href')), root_url),
            'ctg_denom_txt': ' '.join(' '.join(tree.xpath('//p[@class="legend"]//text()')).split()),
        })
        print(products[url])
        if not r.from_cache:
            sleep(3)


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
