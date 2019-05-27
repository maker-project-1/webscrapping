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
shop_id = "la_grande_epicerie"
root_url = "https://www.lagrandeepicerie.com/"
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
    "champagne": "https://www.lagrandeepicerie.com/fr/cave/champagne/",
    "still_wines": "https://www.lagrandeepicerie.com/fr/cave/vins-etrangers/",
    "sparkling": "https://www.lagrandeepicerie.com/fr/cave/champagne/",
    "whisky": "https://www.lagrandeepicerie.com/fr/cave/spiritueux/whiskies/",
    "cognac": "https://www.lagrandeepicerie.com/fr/cave/spiritueux/cognac/",
    "vodka": "https://www.lagrandeepicerie.com/fr/cave/spiritueux/vodka/",
    "rum": "https://www.lagrandeepicerie.com/fr/cave/spiritueux/rhums/",
    "gin": "https://www.lagrandeepicerie.com/fr/cave/spiritueux/gin/",
}



# Category Scraping
for ctg, url in urls_ctgs_dict.items():
    categories[ctg] = []

    fpath = fpath_namer(shop_id, 'ctg', ctg, 0)
    if not op.exists(fpath):
        driver.get(url)
        sleep(2)
        driver.waitclick('//*[@id="show-more-product"]', timeout=5)
        # driver.click_to_bottom('//*[@id="show-more-product"]')
        driver.save_page(fpath, scroll_to_bottom=True)
    tree = etree.parse(BytesIO(open(fpath, 'rb').read()), parser=parser)
    print(ctg, fpath)
    for li in tree.xpath('//*[@id="search-result-items"]/div'):
        produrl = li.xpath('.//a[@class="thumb-link"]/@href')[0]
        produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
        produrl = clean_url(produrl, root_url)
        products[produrl] = {
            'pdct_name_on_eretailer': ' '.join(''.join(li.xpath('.//div[@class="product-name"]//text()')).split()).strip(),
            'raw_price': ' '.join(''.join(li.xpath('.//span[@class="box-price"]//text()')).split()).strip(),
            'raw_promo_price': '',
            'volume': ' '.join(''.join(li.xpath('.//span[@itemprop="weight"]//text()')).split()).strip(),
        }
        print(products[produrl], produrl)
        products[produrl]['price'] = getprice(products[produrl]['raw_price'])
        # products[produrl]['promo_price'] = getprice(products[produrl]['raw_promo_price'])
        print(products[produrl])
        categories[ctg].append(produrl)

print([(c, len(categories[c])) for c in categories])


# KW searches Scraping - with selenium - with nb page hard-coded in url - multiple page per search
search_url = "https://www.lagrandeepicerie.com/fr/votre-recherche?q={kw}&lang=fr&simplesearch=Go"
for kw in keywords:
    searches[kw] = []
    number_of_pdcts_in_kw_search = 0

    # Storing and extracting infos
    urlp = search_url.format(kw=kw)
    fpath = fpath_namer(shop_id, 'search', kw, 0)
    if not op.exists(fpath):
        driver.get(urlp)
        driver.save_page(fpath)
    tree = etree.parse(BytesIO(open(fpath, 'rb').read()), parser=parser)

    for li in tree.xpath('//*[@id="search-result-items"]/div'):
        # print(li.xpath('.//text()'))
        if li.xpath('.//a[@class="thumb-link"]/@href'):
            produrl = li.xpath('.//a[@class="thumb-link"]/@href')[0]
            produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
            produrl = clean_url(produrl, root_url)
            products[produrl] = {
                'pdct_name_on_eretailer': ' '.join(''.join(li.xpath('.//div[@class="product-name"]//text()')).split()).strip(),
                'raw_price': ' '.join(''.join(li.xpath('.//span[@class="box-price"]//text()')).split()).strip(),
                'raw_promo_price': '',
                'volume': ' '.join(''.join(li.xpath('.//span[@itemprop="weight"]//text()')).split()).strip(),
            }
            print(products[produrl], produrl)
            products[produrl]['price'] = getprice(products[produrl]['raw_price'])
            products[produrl]['pdct_name_on_eretailer'] = products[produrl]['pdct_name_on_eretailer'].replace('Recette', '').strip()
            # products[produrl]['promo_price'] = getprice(products[produrl]['raw_promo_price'])
            print(products[produrl])

            searches[kw].append(produrl)
    print(kw, 0, len(searches[kw]))


# Download the pages - with selenium
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
            'pdct_img_main_url': clean_url(''.join(tree.xpath('//div[@class="product-primary-image"]//img[@itemprop="image"]/@src')), root_url),
            'ctg_denom_txt': ' '.join(' '.join(tree.xpath('//*[@itemtype="http://schema.org/BreadcrumbList"]//text()')).split()),
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
         print(img_path)
         with open(tmp_file_path, 'wb') as out_file:
             shutil.copyfileobj(response.raw, out_file)
         if imghdr.what(tmp_file_path) is not None:
             img_path = img_path.split('.')[0] + '.' + imghdr.what('/tmp/' + shop_id + 'mhers_tmp_{}.imgtype'.format(abs(hash(pdt['pdct_img_main_url']))))
             shutil.copyfile('/tmp/' + shop_id + 'mhers_tmp_{}.imgtype'.format(abs(hash(pdt['pdct_img_main_url']))), img_path)
             products[url].update({'img_path': img_path, 'img_hash': file_hash(img_path)})

create_csvs(products, categories, searches, shop_id, fpath_namer(shop_id, 'raw_csv'), COLLECTION_DATE)
validate_raw_files(fpath_namer(shop_id, 'raw_csv'))
driver.quit()
