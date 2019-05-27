import re
from io import BytesIO

from lxml import etree

parser = etree.HTMLParser(encoding='utf-8')
from time import sleep
from urllib.parse import urlsplit, parse_qs
import requests
import requests_cache, imghdr
from ers import all_keywords_es as keywords, fpath_namer, mh_brands, clean_url, headers

from matcher import BrandMatcher
from ers import COLLECTION_DATE, file_hash, img_path_namer
import shutil
from parse import parse
from validators import validate_raw_files
from create_csvs import create_csvs

# Init variables and assets
shop_id = "elcorteingles_supermercado"
root_url = "https://www.elcorteingles.es/"
requests_cache.install_cache(fpath_namer(shop_id, 'requests_cache'))
country = "ES"


searches, categories, products = {}, {}, {}
# If necessary
# driver = CustomDriver(headless=False)


def getprice(pricestr):
    if pricestr == '':
        return pricestr
    pricestr = re.sub("[^0-9,€]", "", pricestr)
    price = parse('{pound:d},{pence:d}€', pricestr)
    if price is None:
        price = parse('{pence:d}p', pricestr)
        return price.named['pence']
    else:
        return price.named['pound'] * 100 + price.named['pence']


urls_ctgs_dict = {
            'champagne': 'https://www.elcorteingles.es/supermercado/bebidas/vinos/cavas-champagne-y-espumosos/champagne/{page}/',
            'sparkling': 'https://www.elcorteingles.es/supermercado/bebidas/vinos/cavas-champagne-y-espumosos/vinos-espumosos/',
            'still_wines': 'https://www.elcorteingles.es/supermercado/bebidas/vinos/vino-blanco/{page}/',
            'whisky': 'https://www.elcorteingles.es/supermercado/bebidas/licores-y-alcoholes/whisky/{page}/',
            'cognac': 'https://www.elcorteingles.es/supermercado/bebidas/licores-y-alcoholes/brandy-y-conac/conac/',
            'vodka': 'https://www.elcorteingles.es/supermercado/bebidas/licores-y-alcoholes/vodka/{page}/',
            'gin': 'https://www.elcorteingles.es/supermercado/bebidas/licores-y-alcoholes/ginebra/{page}/',
            'rum': 'https://www.elcorteingles.es/supermercado/bebidas/licores-y-alcoholes/ron/{page}/',
            'tequila': 'https://www.elcorteingles.es/supermercado/bebidas/licores-y-alcoholes/tequila/{page}/',
            'white_wine': 'https://www.elcorteingles.es/supermercado/bebidas/vinos/vino-blanco/{page}/',
            'red_wine': 'https://www.elcorteingles.es/supermercado/bebidas/vinos/vino-tinto/{page}/',
            'brandy': 'https://www.elcorteingles.es/supermercado/bebidas/licores-y-alcoholes/brandy-y-conac/brandy/{page}/',
        }

# Category Scraping
for ctg, url in urls_ctgs_dict.items():
    categories[ctg] = []
    number_of_pdcts_in_ctg = 0
    for p in range(100):
        urlp = url.format(page=p + 1)
        print(ctg, p)
        r = requests.get(urlp)
        with open('/tmp/' + ctg + str(p) + '.html', 'wb') as f:
            f.write(r.content)
        tree = etree.parse(BytesIO(r.content), parser=parser)

        for li in tree.xpath('//div[@data-scope="product"]'):
            produrl = li.xpath('.//h3/a/@href')[0]
            produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(
                urlsplit(produrl).query) else produrl
            produrl = clean_url(produrl, root_url)
            products[produrl] = {
                'pdct_name_on_eretailer': ' '.join(''.join(li.xpath('.//h3/a/@title')).split()),
                'raw_price': ' '.join(
                    ''.join(li.xpath('.//div[contains(@class,"prices-price _curren")]//text()')).split()),
                'raw_promo_price': '',
            }
            if not products[produrl]['raw_price']:
                products[produrl].update({
                    'raw_price': ' '.join(''.join(li.xpath('.//span[@class="current   sale"]//text()')).split()),
                    'raw_promo_price': ' '.join(''.join(li.xpath('.//span[@class="former stroked"]//text()')).split()),
                })
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
print(categories)

# KW searches Scraping - with selenium - with nb page hard-coded in url - multiple page per search
search_url = "https://www.elcorteingles.es/supermercado/buscar/{page}/?term={kw}"
for kw in keywords:
    searches[kw] = []
    number_of_pdcts_in_kw_search = 0

    for p in range(2):
        # Storing and extracting infos
        urlp = search_url.format(kw=kw, page=p + 1)

        # fpath = fpath_namer(shop_id, 'search', kw, p)
        # if not op.exists(fpath):
        #     driver.get(urlp)
        #     sleep(2)
        #     driver.save_page(fpath)
        # tree = etree.parse(BytesIO(open(fpath, 'rb').read()), parser=parser)

        r = requests.get(urlp)
        with open('/tmp/' + kw + str(p) + '.html', 'wb') as f:
            f.write(r.content)
        tree = etree.parse(BytesIO(r.content), parser=parser)

        for li in tree.xpath('//div[@data-scope="product"]'):
            produrl = li.xpath('.//h3/a/@href')[0]
            produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(
                urlsplit(produrl).query) else produrl
            produrl = clean_url(produrl, root_url)
            products[produrl] = {
                'pdct_name_on_eretailer': ' '.join(''.join(li.xpath('.//h3/a/@title')).split()),
                'raw_price': ' '.join(
                    ''.join(li.xpath('.//div[contains(@class,"prices-price _curren")]//text()')).split()),
                'raw_promo_price': '',
            }
            if not products[produrl]['raw_price']:
                print(products[produrl]['pdct_name_on_eretailer'])
                products[produrl].update({
                    'raw_price': ' '.join(''.join(li.xpath('.//span[@class="current   sale"]//text()')).split()),
                    'raw_promo_price': ' '.join(''.join(li.xpath('.//span[@class="former stroked"]//text()')).split()),
                })
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

        # fname = fpath_namer(shop_id, 'pdct', d['pdct_name_on_eretailer'], 0)
        # if not op.exists(fname):
        #     driver.get(url_mod)
        #     sleep(2)
        #     driver.save_page(fname, scroll_to_bottom=True)
        # tree = etree.parse(open(fname), parser=parser)

        r = requests.get(url_mod, headers)
        with open('/tmp/' + d['pdct_name_on_eretailer'].replace('/', "-") + '.html', 'wb') as f:
            f.write(r.content)
        tree = etree.parse(BytesIO(r.content), parser=parser)

        products[url].update({
            'volume': ' '.join(''.join(tree.xpath('//div[contains(@class, "pack_composition")]//text()')).split()),
            'pdct_img_main_url': clean_url(''.join(tree.xpath('//img[@id="product-image-placer"]/@src')), root_url),
            'ctg_denom_txt': ' '.join(' '.join(tree.xpath('//*[@id="breadcrumbs"]//text()')).split()),
        })
        products[url]['volume'] = products[url]['volume'].split('2 sobre')[0].split('botella')[-1]
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

