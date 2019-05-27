import os.path as op
from io import BytesIO

from lxml import etree

parser = etree.HTMLParser(encoding='utf-8')
from time import sleep
from urllib.parse import urlsplit, parse_qs
import requests
import requests_cache, imghdr

from validators import validate_raw_files
from create_csvs import create_csvs
from ers import all_keywords_usa as keywords, fpath_namer, mh_brands, clean_url, headers

from matcher import BrandMatcher
from ers import COLLECTION_DATE, file_hash, img_path_namer
import shutil
from custom_browser import CustomDriver
from parse import parse

# Init variables and assets
shop_id = "argonaut"
requests_cache.install_cache(fpath_namer(shop_id, 'requests_cache'))
root_url = "https://www.argonautliquor.com/"
country = "USA"

searches, categories, products = {}, {}, {}
# If necessary
driver = CustomDriver(headless=True, download_images=True)


def getprice(pricestr):
    if pricestr == '':
        return pricestr
    price = parse('${pound:d}.{pence:d}', pricestr)

    if price is None:
        price = parse('{pence:d}p', pricestr)
        return price.named['pence']
    else:
        return price.named['pound'] * 100 + price.named['pence']


urls_ctgs_dict = {'vodka': 'https://www.argonautliquor.com/search/result_size/96/categories/Vodka/page/{page}',
                  'sparkling': 'https://www.argonautliquor.com/search/result_size/96/categories/Sparkling%20Wine/page/{page}',
                  'cognac': 'https://www.argonautliquor.com/search/categories/Cognac/result_size/96',
                  'champagne': 'https://www.argonautliquor.com/search/term/champagne/result_size/96',
                  'still_wines': 'https://www.argonautliquor.com/search/categories/White%20Wine/result_size/96/page/{page}',
                  'whisky': 'https://www.argonautliquor.com/search/result_size/96/categories/Whiskey/page/{page}',
                  'gin': 'https://www.argonautliquor.com/search/categories/Gin/result_size/96/page/{page}',
                  'tequila': 'https://www.argonautliquor.com/search/categories/Tequila/result_size/96/page/{page}',
                  'red_wine': 'https://www.argonautliquor.com/search/categories/Red%20Wine/result_size/96/page/{page}',
                  'white_wine': 'https://www.argonautliquor.com/search/categories/White%20Wine/result_size/96/page/{page}',
                  'rum': 'https://www.argonautliquor.com/search/categories/Rum/result_size/96/page/{page}',
                  'liquor': 'https://www.argonautliquor.com/search/categories/Liqueur/result_size/96/page/{page}',
                  'brandy': 'https://www.argonautliquor.com/search/categories/Brandy/result_size/96/page/{page}',
                  'mezcal': 'https://www.argonautliquor.com/search/categories/Mezcal/result_size/96/page/{page}',
                  }

# Category Scraping
for ctg, url in urls_ctgs_dict.items():
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

        # r = requests.get(urlp)
        # tree = etree.parse(BytesIO(r.content), parser=parser)

        for li in tree.xpath('//div[@id="product-list"]//div[@class="grid-item"]'):
            produrl = li.xpath('.//a[@class="product-link"]/@href')[0]
            produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(
                urlsplit(produrl).query) else produrl
            produrl = clean_url(produrl, root_url)
            products[produrl] = {
                'pdct_name_on_eretailer': ' '.join(
                    ''.join(li.xpath('.//div[@class="product-name"]//text()')).split()).strip(),
                'raw_price': ' '.join(''.join(
                    li.xpath('.//s[@class="regular-price"]//text() | .//span[@class="price"]//text()')).split()).strip(),
                'raw_promo_price': ' '.join(''.join(li.xpath('.//span[@class="sale-price"]//text()')).split()).strip(),
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
search_url = "https://www.argonautliquor.com/search/term/{kw}/result_size/96/page/{page}"
for kw in keywords:
    searches[kw] = []
    number_of_pdcts_in_kw_search = 0

    for p in range(10):
        # Storing and extracting infos
        urlp = search_url.format(kw=kw, page=p+1)

        fpath = fpath_namer(shop_id, 'search', kw, p)
        if not op.exists(fpath):
            driver.get(urlp)
            sleep(2)
            driver.save_page(fpath)
        tree = etree.parse(BytesIO(open(fpath, 'rb').read()), parser=parser)

        for li in tree.xpath('//div[@id="product-list"]//div[@class="grid-item"]'):
            produrl = li.xpath('.//a[@class="product-link"]/@href')[0]
            produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(
                urlsplit(produrl).query) else produrl
            produrl = clean_url(produrl, root_url)
            products[produrl] = {
                'pdct_name_on_eretailer': ' '.join(
                    ''.join(li.xpath('.//div[@class="product-name"]//text()')).split()).strip(),
                'raw_price': ' '.join(''.join(
                    li.xpath('.//s[@class="regular-price"]//text() | .//span[@class="price"]//text()')).split()).strip(),
                'raw_promo_price': ' '.join(''.join(li.xpath('.//span[@class="sale-price"]//text()')).split()).strip(),
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
        with open('/tmp/' + shop_id + ' ' + d['pdct_name_on_eretailer'].replace('/', "-") + '.html', 'wb') as f:
            f.write(r.content)
        tree = etree.parse(BytesIO(r.content), parser=parser)

        products[url].update({
            'volume': ''.join(tree.xpath('//p[@class="text-muted small size-container"]//text()')).strip(),
            'pdct_img_main_url': clean_url(''.join(tree.xpath('//*[@id="product-detail"]//*[@class="product-image"]//img/@data-src')), root_url),
            'ctg_denom_txt': ' '.join(tree.xpath('//table[@class="table"]//text()')).split("?")[0],
        })
        print(products[url])
        if not r.from_cache:
            print("Waiting")
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

