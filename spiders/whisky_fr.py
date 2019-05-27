
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
from ers import all_keywords_fr as keywords, fpath_namer, mh_brands, clean_url, headers

from matcher import BrandMatcher
from ers import COLLECTION_DATE, file_hash, img_path_namer
import shutil
from custom_browser import CustomDriver
from parse import parse


# Init variables and assets
shop_id = "whisky_fr"
root_url = "http://www.whisky.fr/" 
requests_cache.install_cache(fpath_namer(shop_id, 'requests_cache'))
country = "FR"


searches, categories, products = {}, {}, {}
# If necessary
driver = CustomDriver(headless=True)


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
    'champagne': 'https://www.whisky.fr/achat/alcool/spiritueux/champagne-vins-mousseux/champagne.html#limit=60&gan_data=true',
    'sparkling': 'https://www.whisky.fr/achat/alcool/spiritueux/champagne-vins-mousseux/champagne.html#limit=60&gan_data=true',
    "vodka": "http://www.whisky.fr/achat/alcool/spiritueux/vodka-akuavit.html",
    "cognac": "http://www.whisky.fr/achat/alcool/spiritueux/cognac-armagnac-eau-de-vie-de-vin/cognac.html", 
    "still_wines": "http://www.whisky.fr/achat/alcool/spiritueux/vin.html",
    "whisky": "https://www.whisky.fr/achat/alcool/whiskies/types/malt-whisky/single-malt.html#limit=60&p={page}&gan_data=true",
    "gin": "https://www.whisky.fr/achat/alcool/spiritueux/gin-genievre-pecket.html#limit=60&p={page}&gan_data=true",
    "tequila": "https://www.whisky.fr/achat/alcool/spiritueux/tequila-mezcal-sotol/tequila-1.html#limit=60&p={page}&gan_data=true",
    "rum": "https://www.whisky.fr/achat/alcool/spiritueux/rhum-cachaca.html#limit=60&p={page}&gan_data=true",
    "liquor": "https://www.whisky.fr/achat/alcool/spiritueux/liqueur-creme.html#limit=60&p={page}&gan_data=true",
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

        for li in tree.xpath('//ul[contains(@class, "products-grid")]/li[contains(@class, "item")]'):
            produrl = li.xpath('./a/@href')[0]
            produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
            produrl = clean_url(produrl, root_url)
            products[produrl] = {
                'pdct_name_on_eretailer': ' '.join(''.join(li.xpath('.//h2[@class="product-name"]//text()')).split()),
                'raw_price': ' '.join(''.join(li.xpath('.//span[contains(@id, "product-price")]//text()')).split()),
                'raw_promo_price': ' '.join(''.join(li.xpath('.//span[contains(@id, "old-price")]//text()')).split()),
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

print([(c, len(categories[c])) for c in categories])




# KW searches Scraping - with selenium - with nb page hard-coded in url - multiple page per search
search_url = "https://www.whisky.fr/catalogsearch/result/?q={kw}"
for kw in keywords:
    searches[kw] = []
    number_of_pdcts_in_kw_search = 0
    print('\n\nkw', kw, '\n')
    for p in range(10):
        # Storing and extracting infos
        urlp = search_url.format(kw=kw, page=p)
        
        fpath = fpath_namer(shop_id, 'search', kw, p)
        print(fpath)
        if not op.exists(fpath):
            driver.get(urlp)
            sleep(2)
            driver.save_page(fpath)
        tree = etree.parse(BytesIO(open(fpath, 'rb').read()), parser=parser)
        
        # r = requests.get(urlp)
        # with open('/tmp/' + shop_id + '_' + kw + '.html', 'wb') as f:
        #     f.write(r.content)
        # tree = etree.parse(BytesIO(r.content), parser=parser)

        for li in tree.xpath('//div[@class="ais-hits--item"]'):
            produrl = li.xpath('.//a/@href')[0]
            produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
            produrl = clean_url(produrl, root_url)
            products[produrl] = {
                'pdct_name_on_eretailer': ' '.join(''.join(li.xpath('.//a[@class="result-title text-ellipsis"]//text()')).split()),
                'raw_price': ' '.join(''.join(li.xpath('.//span[contains(@class, "after_special ")]//text()')).split()),
                'raw_promo_price': ' '.join(''.join(li.xpath('.//span[@class="before_special"]//text()')).split()),
            }
            print(products[produrl], produrl)
            products[produrl]['price'] = getprice(products[produrl]['raw_price'])
            # products[produrl]['promo_price'] = getprice(products[produrl]['raw_promo_price'])
            print(products[produrl])

            searches[kw].append(produrl)
        if not searches[kw]:
            for li in tree.xpath('//ul[contains(@class, "products-grid")]/li'):
                produrl = li.xpath('.//a/@href')[0]
                produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
                produrl = clean_url(produrl, root_url)
                products[produrl] = {
                    'pdct_name_on_eretailer': ' '.join(''.join(li.xpath('.//*[@class="product-name"]//text()')).split()),
                    'raw_price': ' '.join(''.join(li.xpath('.//*[@class="price"]//text()')).split())[:0],
                    'raw_promo_price': ' '.join(''.join(li.xpath('.//*[@class="product-namedqsds"]//text()')).split()),
                }
                print(products[produrl], produrl)
                products[produrl]['price'] = getprice(products[produrl]['raw_price'])
                # products[produrl]['promo_price'] = getprice(products[produrl]['raw_promo_price'])
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
            'volume': ' '.join(''.join(tree.xpath('//h2[@class="product-ref"]//text()')).split()),
            'pdct_img_main_url': clean_url(''.join(tree.xpath('//a[@class="imageZoom"]/@href')), root_url),
            'ctg_denom_txt': ' '.join(' '.join(tree.xpath('//div[@class="breadcrumbs"]//text()')).split()),
        })
        print(products[url])
        if not r.from_cache:
            sleep(2)



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
