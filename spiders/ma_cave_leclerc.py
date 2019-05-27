import os.path as op
from io import BytesIO

from lxml import etree

parser = etree.HTMLParser(encoding='utf-8')
from time import sleep
from urllib.parse import urlsplit, parse_qs
import requests
import requests_cache, imghdr
import re
from validators import validate_raw_files
from create_csvs import create_csvs

from ers import all_keywords_fr as keywords, fpath_namer, mh_brands, clean_url, headers
from matcher import BrandMatcher
from ers import COLLECTION_DATE, file_hash, img_path_namer
import shutil
from custom_browser import CustomDriver
from parse import parse


# Init variables and assets
shop_id = 'ma_cave_leclerc'
root_url = 'https://www.macave.leclerc'
requests_cache.install_cache(fpath_namer(shop_id, 'requests_cache'))
country = 'FR'
searches, categories, products = {}, {}, {}
driver = CustomDriver(headless=True, download_images=False)


urls_ctgs_dict = {
            'champagne': 'https://www.macave.leclerc/champagnes',
            # 'cognac': '',
            'sparkling': 'https://www.macave.leclerc/champagnes',
            # 'vodka': '',
            # 'whisky': '',
            'still_wines': 'https://www.macave.leclerc/vins-blanc',
            'red_wine': 'https://www.macave.leclerc/vins-rouge',
            'white_wine': 'https://www.macave.leclerc/vins-blanc',
            'rum': 'https://www.macave.leclerc/rhums-spiritueux',
            'gin': 'https://www.macave.leclerc/gin-spiritueux',
        }


def getprice(pricestr):
    pricestr = re.sub("[^0-9,€]", "", pricestr)
    if pricestr == '':
        return pricestr
    price = parse('{dol:d},{pence:d}€', pricestr)
    if price is None:
        price = parse('{dol:d}€', pricestr)
        return price.named['dol'] * 100
    else:
        return price.named['dol'] * 100 + price.named['pence']


# Category Scraping - with selenium - one page per category
for ctg, url in urls_ctgs_dict.items():
    categories[ctg] = []
    number_of_pdcts_in_ctg = 0

    if not op.exists(fpath_namer(shop_id, 'ctg', ctg, 0)):
        driver.get(url)

    for p in range(100):
        fpath = fpath_namer(shop_id, 'ctg', ctg, p)
        if not op.exists(fpath_namer(shop_id, 'ctg', ctg, p)):
            driver.save_page(fpath, scroll_to_bottom=True)
        tree = etree.parse(BytesIO(open(fpath, 'rb').read()), parser=parser)
        for li in tree.xpath('//ul[contains(@class, "products-grid")]/li[contains(@class, "item")]'):
            produrl = li.xpath('.//a/@href')[0]
            produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
            produrl = clean_url(produrl, root_url)
            products[produrl] = {
                'pdct_name_on_eretailer': "".join(li.xpath('.//a//text()')[:1]).strip(),
                'raw_price': ''.join(w for t in li.xpath('.//*[@class="thumbnail-price "]//text()')[:3] for w in t.split()).strip(),
                'raw_promo_price': ''.join(w for t in li.xpath('.//*[@class="thumbnail-priceOld"]//text()')[:3] for w in t.split()).strip(),
            }
            print(products[produrl], produrl)
            if products[produrl]['raw_price'].count('$') >= 2:
                products[produrl]['raw_price'] = ''.join(w for t in li.xpath('.//*[@class="thumbnail-price promo"]//text()')[:3] for w in t.split()).strip()
            products[produrl]['price'] = getprice(products[produrl]['raw_price'])
            products[produrl]['promo_price'] = getprice(products[produrl]['raw_promo_price'])
            print(products[produrl])
            categories[ctg].append(produrl)

        # Checking if it was the last page
        if len(set(categories[ctg])) == number_of_pdcts_in_ctg:
            break
        else:
            number_of_pdcts_in_ctg = len(set(categories[ctg]))
            driver.waitclick('//*[class="glyphicon glyphicon-menu-right"]')

print([(c, len(categories[c])) for c in categories])


# KW searches Scraping - with requests - one page per search
kw_search_url = "https://www.macave.leclerc/catalogsearch/result/?q={kw}"
for kw in keywords:
    print('Requesting', kw)
    searches[kw] = []
    fpath = fpath_namer(shop_id, 'search', kw, 0)
    if not op.exists(fpath):
        driver.get(kw_search_url.format(kw=kw))
        driver.waitclick('//div[@class="limiter"]/span[last()]')
        sleep(2)
        driver.save_page(fpath, scroll_to_bottom=True)
    tree = etree.parse(BytesIO(open(fpath, 'rb').read()), parser=parser)
    for li in tree.xpath('//ul[contains(@class, "products-grid")]/li[contains(@class, "item")]'):
        produrl = li.xpath('./a/@href')[0]
        produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
        produrl = clean_url(produrl, root_url)
        products[produrl] = {
            'pdct_name_on_eretailer': "".join(li.xpath('.//div[@class="ns-product-domain"]//text()')),
            'raw_price': ''.join(w for t in li.xpath('.//*[contains(@id, "product-price")]//text()')[:3] for w in t.split()).strip(),
            'raw_promo_price': ''.join(w for t in li.xpath('.//*[contains(@id, "old-price")]//text()')[:3] for w in t.split()).strip(),
        }
        print(products[produrl], produrl)
        products[produrl]['price'] = getprice(products[produrl]['raw_price'])
        products[produrl]['promo_price'] = getprice(products[produrl]['raw_promo_price'])
        print(products[produrl])
        searches[kw].append(produrl)
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
            'pdct_name_on_eretailer': " ".join(" ".join(tree.xpath('//*[@class="product-name"]//text()')).split()),
            'volume': ' '.join(' '.join(tree.xpath('//*[@class="mc-product-bottle"]//text()')).split()),
            'pdct_img_main_url': clean_url(''.join(tree.xpath('//img[@id="image-main"]/@src')), root_url),
            'ctg_denom_txt': ' '.join(' '.join(tree.xpath('//div[@class="breadcrumbs"]//text()')).split()),
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
