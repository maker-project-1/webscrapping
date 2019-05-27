import os.path as op
import re
from io import BytesIO

from lxml import etree

parser = etree.HTMLParser(encoding='utf-8')
from time import sleep
from urllib.parse import urlsplit, parse_qs
import requests
import requests_cache, imghdr
from parse import parse
from validators import validate_raw_files
from create_csvs import create_csvs


from ers import all_keywords_uk as keywords
from ers import fpath_namer, mh_brands, clean_url, headers
from matcher import BrandMatcher
from ers import COLLECTION_DATE, file_hash, img_path_namer
import shutil
from custom_browser import CustomDriver


# Init variables and assets
shop_id = 'laithwaites'
root_url = 'https://www.laithwaites.co.uk'
requests_cache.install_cache(fpath_namer(shop_id, 'requests_cache'))
country = 'UK'
searches, categories, products = {}, {}, {}
driver = CustomDriver(headless=True, download_images=False)


def getprice(pricestr):
    if pricestr == '':
        return pricestr
    pricestr = pricestr.replace(',', '').strip()
    price = parse('£{pound:d}.{pence:d}', pricestr)
    if price is None:
        price = parse('{pence:d}p', pricestr)
        return price.named['pence']
    else:
        return price.named['pound'] * 100 + price.named['pence']


urls_ctgs_dict = {
    'champagne': 'https://www.laithwaites.co.uk/wines/Champagne/_/N-1z141ue?Nrpp=50&Ns=product.popularity%7C1&icamp=nav-browse-white&No=50#page-{page}',
    'sparkling': 'https://www.laithwaites.co.uk/wines/Sparkling/_/N-1z141ud?Nrpp=50&Ns=product.popularity%7C1&icamp=nav-browse-white&No=50#page-{page}',
    'still_wines': 'https://www.laithwaites.co.uk/wines/White-Wine/_/N-1z141yk?Nrpp=50&Ns=product.popularity%7C1&icamp=nav-browse-white&No=50#page-{page}',
    # 'whisky': '',
    'cognac': 'https://www.laithwaites.co.uk/wines?Ntt=cognac',
    # 'vodka': '',
    'red_wine': 'https://www.laithwaites.co.uk/wines/Red-Wine/_/N-1z141we?Ns=product.popularity%7C1&icamp=nav-browse-red&Nrpp=50&No=0#page-{page}',
    'white_wine': 'https://www.laithwaites.co.uk/wines/White-Wine/_/N-1z141yk?Nrpp=50&Ns=product.popularity%7C1&icamp=nav-fw-white&No=50#page-{page}',
}

# Simple case, where the page is hard-coded in the url
for ctg, url in urls_ctgs_dict.items():
    categories[ctg] = []
    number_of_pdcts_in_ctg = 0

    for p in range(100):
        urlp = url.format(page=p+1)
        fpath = fpath_namer(shop_id, 'ctg', ctg, p)
        if not op.exists(fpath):
            driver.get(urlp)
            driver.smooth_scroll(8)
            driver.save_page(fpath)
        tree = etree.parse(BytesIO(open(fpath, 'rb').read()), parser=parser)
        for li in tree.xpath('//div[@class="product-wrapper"]'):
            produrl = li.xpath('.//h3/a/@href')[0]
            produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
            produrl = clean_url(produrl, root_url)
            regex_produrl = re.compile('&;jsessionid=(.*?)#45;', re.IGNORECASE)
            produrl = re.sub(regex_produrl, '', produrl)
            categories[ctg].append(produrl)
            raw_price = li.xpath('.//span[@class="price-per-bottle"]/text()')
            raw_price = "".join(raw_price[0]) if raw_price else ""
            products[produrl] = {
                'pdct_name_on_eretailer': " ".join("".join(li.xpath('.//h3/a//text()')).split()),
                'raw_price': " ".join(raw_price.split()),
            }
            products[produrl]['price'] = getprice(products[produrl]['raw_price'])
            print(products[produrl])
            categories[ctg].append(produrl)

        # Go to next page if necessary
        if len(set(categories[ctg])) == number_of_pdcts_in_ctg:
            break
        else:
            number_of_pdcts_in_ctg = len(set(categories[ctg]))
print([(c, len(categories[c])) for c in categories])

# Easy case, where you scroll down to get the whole page
search_url = "https://www.laithwaites.co.uk/wines?Ntt={kw}"
for kw in keywords:
    print(kw)
    searches[kw] = []
    # Storing and extracting infos
    fpath = fpath_namer(shop_id, 'search', kw, 0)
    url = search_url.format(kw=kw, page=0)
    if not op.exists(fpath):
        driver.get(url)
        sleep(3)
        driver.save_page(fpath, scroll_to_bottom=True)
        sleep(1)
    tree = etree.parse(BytesIO(open(fpath, 'rb').read()), parser=parser)
    for li in tree.xpath('//div[@class="product-wrapper"]'):
        produrl = li.xpath('.//h3/a/@href')[0]
        produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
        produrl = clean_url(produrl, root_url)
        regex_produrl = re.compile('&;jsessionid=(.*?)#45;', re.IGNORECASE)
        produrl = re.sub(regex_produrl, '', produrl)
        searches[kw].append(produrl)
        raw_price = li.xpath('.//span[@class="price-per-bottle"]/text()')
        raw_price = "".join(raw_price[0]) if raw_price else ""
        products[produrl] = {
            'pdct_name_on_eretailer': " ".join("".join(li.xpath('.//h3/a//text()')).split()),
            'raw_price': " ".join(raw_price.split()),
        }
        products[produrl]['price'] = getprice(products[produrl]['raw_price'])
        print(products[produrl])

# Download the pages
brm = BrandMatcher()
for url in sorted(products):
    d = products[url]
    if brm.find_brand(d['pdct_name_on_eretailer'])['brand'] in mh_brands:
        url_mod = clean_url(url, root_url=root_url)
        fname = fpath_namer(shop_id, 'pdct', d['pdct_name_on_eretailer'], 0)
        print(fname)
        if not op.exists(fname):
            driver.get(url_mod)
            sleep(2)
            driver.save_page(fname, scroll_to_bottom=True)
        # print(d['pdct_name_on_eretailer'], fname)
        tree = etree.parse(open(fname), parser=parser)
        products[url] = {
            'pdct_name_on_eretailer': ' '.join(w for t in tree.xpath('//h1//text()') for w in t.split()).strip(),
            # 'volume': ''.join(tree.xpath('//*[@class="table wine-facts"]//text()')),
            'raw_price': ''.join(w for t in tree.xpath('//*[id="detail-single-wine"]//span[@class="price-per-bottle"]//text()') for w in t.split()).strip(),
            'raw_promo_price': ''.join(tree.xpath('//div[@class="js-op-vpp-a"]//small//text()')[:1]).replace("(Was", '').replace("a bottle)", ''),
            'pdct_img_main_url': clean_url(''.join(tree.xpath('//img[@id="bottle-image"]/@src')[:1]), root_url),
            'ctg_denom_txt': ' '.join(tree.xpath('//*[id="detail-single-wine"]//h3//text()')),
        }
        products[url]['price'] = getprice(products[url]['raw_price'])
        products[url]['promo_price'] = getprice(products[url]['raw_promo_price'])
        print(products[url])


# Download images
for url, pdt in products.items():
     if 'pdct_img_main_url' in pdt and pdt['pdct_img_main_url'] and brm.find_brand(pdt['pdct_name_on_eretailer'])['brand'] in mh_brands:
         print(pdt['pdct_name_on_eretailer'] + "." + pdt['pdct_img_main_url'].split('.')[-1])
         print(pdt['pdct_img_main_url'])
         response = requests.get(pdt['pdct_img_main_url'], stream=True, verify=False, headers=headers)
         # response.raw.decode_content = True
         tmp_file_path = '/tmp/' + shop_id + 'mhers_tmp_{}.imgtype'.format(abs(hash(pdt['pdct_img_main_url'])))
         img_path = img_path_namer(shop_id, pdt['pdct_name_on_eretailer'])
         with open(tmp_file_path, 'wb') as out_file:
             out_file.write(response.content)
         if imghdr.what(tmp_file_path) is not None:
             img_path = img_path.split('.')[0] + '.' + imghdr.what('/tmp/' + shop_id + 'mhers_tmp_{}.imgtype'.format(abs(hash(pdt['pdct_img_main_url']))))
             shutil.copyfile('/tmp/' + shop_id + 'mhers_tmp_{}.imgtype'.format(abs(hash(pdt['pdct_img_main_url']))), img_path)
             products[url].update({'img_path': img_path, 'img_hash': file_hash(img_path)})
         else:
             print('Warning :', tmp_file_path, imghdr.what(tmp_file_path))



create_csvs(products, categories, searches, shop_id, fpath_namer(shop_id, 'raw_csv'), COLLECTION_DATE)
validate_raw_files(fpath_namer(shop_id, 'raw_csv'))
driver.quit()
