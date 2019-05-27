import os.path as op
from io import BytesIO

from lxml import etree

parser = etree.HTMLParser()
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
import re
shop_id = 'vicampo'
root_url = 'https://www.vicampo.de'
requests_cache.install_cache(allowable_methods=('GET'))
country = 'DE'
searches, categories, products = {}, {}, {}
driver = CustomDriver(firefox=True)
from parse import parse


def getprice(pricestr):
    pricestr = re.sub("[^0-9,€]", "", pricestr)
    if pricestr == '':
        return None
    print(pricestr)
    price = parse('€{dol:d},{pence:d}', pricestr)
    if price is None:
        price = parse('{pence:d}p', pricestr)
        return price.named['pence']
    else:
        return price.named['dol'] * 100 + price.named['pence']


urls_ctgs_dict = {
    'champagne': 'https://www.vicampo.de/weine/subart/Champagner',
    'sparkling': 'https://www.vicampo.de/weine/subart/Sekt',
    'still_wines': 'https://www.vicampo.de/weine/art/Wei%C3%9Fwein',
    'white_wine': 'https://www.vicampo.de/weine/art/Wei%C3%9Fwein',
    'red_wine': 'https://www.vicampo.de/weine/subart/Rotwein',
}


# Category Scraping - with selenium - multiple pages per category (click on next page)
for ctg, url in urls_ctgs_dict.items():
    categories[ctg] = []
    number_of_pdcts_in_ctg = 0
    if not op.exists(fpath_namer(shop_id, 'ctg', ctg, 0)):
        driver.get(url)
    for p in range(100):
        fpath = fpath_namer(shop_id, 'ctg', ctg, p)
        if not op.exists(fpath):
            sleep(2)
            driver.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            sleep(2)
            driver.waitclick('//button[@data-dismiss="modal"]', timeout=7)
            driver.save_page(fpath, scroll_to_bottom=False)
        tree = etree.parse(open(fpath, 'rb'), parser=parser)
        for li in tree.xpath('//article[@data-entity-type="product"]'):
            produrl = li.xpath('.//a[@data-ec-linklabel="Product Text"]/@href')[0]
            produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
            products[produrl] = {
                'pdct_name_on_eretailer': " ".join("".join(li.xpath('.//h1//text()')).split()),
                'volume': " ".join("".join(li.xpath('.//h1//text()')).split()),
                'raw_price': ''.join(w for t in li.xpath('.//*[starts-with(@class, "price") and not(contains(@class, "crossed"))]//text()') for w in t.split()).strip().split('*')[0],
                'raw_promo_price': ''.join(w for t in li.xpath('.//*[starts-with(@class, "price") and contains(@class, "crossed")]//text()') for w in t.split()).strip(),
            }
            print(products[produrl], produrl)
            tmp_price_str = products[produrl]['raw_price'].split("€")[1]
            print(tmp_price_str, "€" + tmp_price_str[:-2] + ',' + tmp_price_str[-2:])
            products[produrl]['price'] = getprice("€" + tmp_price_str[:-2] + ',' + tmp_price_str[-2:])
            print(products[produrl]['price'])
            tmp_promo_price_str = "".join(products[produrl]['raw_promo_price'].split("€")[:1]).replace('UVP', '')
            if tmp_promo_price_str:
                products[produrl]['promo_price'] = getprice("€" + tmp_promo_price_str[:-2] + ',' + tmp_promo_price_str[-2:])
            print(products[produrl])
            categories[ctg].append(produrl)
        next_page_click = '//li/a[contains(descendant::*/text(), "nächste Seite")]'
        if not driver.check_exists_by_xpath(next_page_click):
            break
        else:
            driver.waitclick(next_page_click)
        # Going to next page if need be
    print(ctg, url, p, len(categories[ctg]))


# KW searches Scraping - with selenium - with search string - multiple page per search
search_url = "https://www.vicampo.de/search?q={kw}"
for kw in keywords:
    searches[kw] = []
    fpath = fpath_namer(shop_id, 'search', kw, p)
    if not op.exists(fpath):
        driver.get(search_url.format(kw=kw))
        driver.save_page(fpath,scroll_to_bottom=True)
    tree = etree.parse(open(fpath, 'rb'), parser=parser)
    for li in tree.xpath('//article[@data-entity-type="product"]'):
        produrl = li.xpath('.//a[@data-ec-linklabel="Product Text"]/@href')[0]
        produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
        products[produrl] = {
            'pdct_name_on_eretailer': " ".join("".join(li.xpath('.//h1//text()')).split()),
            'volume': " ".join("".join(li.xpath('.//h1//text()')).split()),
            'raw_price': ''.join(
                w for t in li.xpath('.//*[starts-with(@class, "price") and not(contains(@class, "crossed"))]//text()')
                for w in t.split()).strip().split('*')[0],
            'raw_promo_price': ''.join(
                w for t in li.xpath('.//*[starts-with(@class, "price") and contains(@class, "crossed")]//text()') for w
                in t.split()).strip(),
        }
        print(products[produrl], produrl)
        tmp_price_str = products[produrl]['raw_price'].split("€")[1]
        print(tmp_price_str, "€" + tmp_price_str[:-2] + ',' + tmp_price_str[-2:])
        products[produrl]['price'] = getprice("€" + tmp_price_str[:-2] + ',' + tmp_price_str[-2:])
        print(products[produrl]['price'])
        tmp_promo_price_str = "".join(products[produrl]['raw_promo_price'].split("€")[:1]).replace('UVP', '')
        if tmp_promo_price_str:
            products[produrl]['promo_price'] = getprice("€" + tmp_promo_price_str[:-2] + ',' + tmp_promo_price_str[-2:])
        print(products[produrl])
        searches[kw].append(produrl)
    print(kw, p, len(searches[kw]))


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
            'pdct_img_main_url': clean_url(''.join(tree.xpath('//img[@itemprop="image"]/@src')), root_url),
            'ctg_denom_txt': ' '.join(' '.join(tree.xpath('//div[@class="tags hidden-xs hidden-sxs"]//text()')).split()),
        })
        print(products[url])
        if not r.from_cache:
            sleep(3)


('/moet-chandon-ice-imperial-demi-sec',
    {'pdct_name_on_eretailer': 'Moët & Chandon Ice Impérial Demi Sec', 'volume': 'Moët & Chandon Ice Impérial Demi Sec',
     'raw_price': '€5410', 'raw_promo_price': '', 'price': 5410,
     'pdct_img_main_url': 'https://assets3.static-vicampo.net/media/cache/10000/image/1000x1000/crop_bottom/x500/b818d075a7/6/2/6294-flasche.png',
     'ctg_denom_txt': 'Schaumwein brut Frankreich',
     'img_path': '/code/mhers/data/w_8/vicampo/images/Moët & Chandon Ice Impérial Demi Sec.png',
     'img_hash': '7dbb907756b1ac0d9ff31ef191e46825dd35aa36e9078b6094ca35fd552b6dc7'})

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
