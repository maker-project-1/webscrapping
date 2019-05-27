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
from custom_browser import CustomDriver
from ers import all_keywords_uk as keywords, fpath_namer, mh_brands, clean_url, headers
from matcher import BrandMatcher
from ers import COLLECTION_DATE, file_hash, img_path_namer
import shutil
from parse import parse

# Init variables and assets
shop_id = 'harrods'
root_url = 'https://www.harrods.com/'
requests_cache.install_cache(fpath_namer(shop_id, 'requests_cache'))
country = 'UK'
searches, categories, products = {}, {}, {}
driver = CustomDriver(headless=True, firefox=True, download_images=True)

urls_ctgs_dict = {
    'champagne': 'https://www.harrods.com/en-gb/food-and-wine/wine-and-spirits/champagne-and-sparkling?view=Product&list=List&viewAll=False&pageNumber={page}',
    'sparkling': 'https://www.harrods.com/en-gb/food-and-wine/wine-and-spirits/champagne-and-sparkling?view=Product&list=List&viewAll=False&pageNumber={page}',
    'still_wines': 'https://www.harrods.com/en-gb/food-and-wine/wine-and-spirits/white-wine?view=Product&list=List&viewAll=False&pageNumber={page}',
    'whisky': 'https://www.harrods.com/en-gb/food-and-wine/wine-and-spirits/spirits?view=Product&list=List&viewAll=False&pageNumber={page}&categoryFilterIds=34605',
    'cognac':'https://www.harrods.com/en-gb/food-and-wine/wine-and-spirits/spirits?view=Product&list=List&viewAll=False&pageNumber={page}&categoryFilterIds=23692',
    'vodka': 'https://www.harrods.com/en-gb/food-and-wine/wine-and-spirits/spirits?view=Product&list=List&viewAll=False&pageNumber={page}&categoryFilterIds=23688',
    'white_wine': 'https://www.harrods.com/en-gb/food-and-wine/wine-and-spirits/white-wine?icid=foodandwine_quadruple-slot_module-17_element-3_white-wine&view=Product&list=List&viewAll=False&pageNumber={page}',
    'red_wine': 'https://www.harrods.com/en-gb/food-and-wine/wine-and-spirits/red-wine?icid=foodandwine_boxes_module-23_element-1_red-wine&view=Product&list=List&viewAll=False&pageNumber={page}',
    'gin': 'https://www.harrods.com/en-gb/food-and-wine/wine-and-spirits/spirits?view=Product&list=List&viewAll=False&pageNumber={page}&categoryFilterIds=23693',
    'brandy': 'https://www.harrods.com/en-gb/food-and-wine/wine-and-spirits/spirits?view=Product&list=List&viewAll=False&pageNumber={page}&categoryFilterIds=23692',
    'rum': 'https://www.harrods.com/en-gb/food-and-wine/wine-and-spirits/spirits?view=Product&list=List&viewAll=False&pageNumber={page}&categoryFilterIds=23690',
    'liquor': 'https://www.harrods.com/en-gb/food-and-wine/wine-and-spirits/spirits?icid=foodandwine_boxes_module-23_element-4_spirits-liqueurs&view=Product&list=List&viewAll=False&pageNumber={page}',
}

cookies = {'ctry': 'UK', 'curr': 'GBP'}


def getprice(pricestr):
    if pricestr == '' or pricestr == '£':
        return ''
    pricestr = pricestr.replace(',', '').strip()
    price = parse('£{pound:d}.{pence:d}', pricestr)
    if price is None:
        price = parse('£{pound:d}', pricestr)
        return price.named['pound'] * 100
    else:
        return price.named['pound'] * 100 + price.named['pence']


# Category Scraping
for ctg, url in urls_ctgs_dict.items():
    categories[ctg] = []
    number_of_pdcts_in_ctg = 0
    for page in range(10):

        fpath = fpath_namer(shop_id, 'ctg', ctg, page)
        if not op.exists(fpath):
            print(url.format(page=page+1))
            driver.respawn()
            driver.get(url.format(page=page+1))
            driver.save_page(fpath, scroll_to_bottom=True)

        tree = etree.parse(open(fpath, 'rb'), parser=parser)
        for li in tree.xpath('//li[@class="product-grid_item"]'):
            produrl = li.xpath('.//a[contains(@class, "product-card_link")]/@href')[0]
            produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
            produrl = clean_url(produrl, root_url)
            categories[ctg].append(produrl)
            products[produrl] = {
                'pdct_name_on_eretailer': ' '.join([li.xpath('.//span[@class="product-card_brand"]//text()')[0],
                                           li.xpath('.//span[@class="product-card_name"]//text()')[0]]),
                'raw_price': '£' + ''.join(w for t in li.xpath('.//span[@class="price_amount"]/@content') for w in t.split()).strip(),
            }
            print(products[produrl], produrl)
            products[produrl]['price'] = getprice(products[produrl]['raw_price'])
            assert all(products[produrl][k] for k in products[produrl])

        # Checking if it was the last page
        if len(set(categories[ctg])) == number_of_pdcts_in_ctg:
            break
        else:
            number_of_pdcts_in_ctg = len(set(categories[ctg]))
            
        print(ctg, len(categories[ctg]))


# Keywords scraping
for kw in keywords:
    searches[kw] = []
    kw_search_url = "https://www.harrods.com/en-gb/search?searchTerm={kw}"
    fpath = fpath_namer(shop_id, 'search', kw, 0)
    print("\n\n ------------------", kw, fpath)

    if not op.exists(fpath):
        print(kw_search_url.format(kw=kw))
        driver.respawn(lazyload=False)
        driver.driver.execute_script("window.location.href='{url}'".format(url=kw_search_url.format(kw=kw)))
        sleep(2)
        try:
            driver.save_page(fpath, scroll_to_bottom=True)
        except Exception:
            print('Missing', kw)
    tree = etree.parse(open(fpath, 'rb'), parser=parser)
    for li in tree.xpath('//li[@class="product-grid_item"]'):
        produrl = li.xpath('.//a[contains(@class, "product-card_link")]/@href')[0]
        produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
        produrl = clean_url(produrl, root_url)
        searches[kw].append(produrl)
        products[produrl] = {
            'pdct_name_on_eretailer': ' '.join([li.xpath('.//span[@class="product-card_brand"]//text()')[0],
                                       li.xpath('.//span[@class="product-card_name"]//text()')[0]]),
            'raw_price': '£' + ''.join(w for t in li.xpath('.//span[@class="price_amount"]/@content') for w in t.split()).strip(),
        }
        print(kw, products[produrl])
        products[produrl]['price'] = getprice(products[produrl]['raw_price'])
        print(kw, products[produrl])
    print(kw, len(searches[kw]))


# Download the pages
brm = BrandMatcher()
for url in sorted(products):
    d = products[url]
    if brm.find_brand(d['pdct_name_on_eretailer'])['brand'] in mh_brands:
        print(d['pdct_name_on_eretailer'], url)
        fpath = fpath_namer(shop_id, 'pdct', d['pdct_name_on_eretailer'], 0)

        if not op.exists(fpath):
            print(url)
            for i in range(5):
                try :
                    driver.respawn(lazyload=False)
                    driver.driver.execute_script("window.location.href='{url}'".format(url=url))
                    sleep(5)
                    driver.save_page(fpath, scroll_to_bottom=True)
                    break
                except:
                    driver.respawn(lazyload=False)
                    driver.driver.execute_script("window.location.href='{url}'".format(url=url))
                    sleep(5)
                    driver.save_page(fpath, scroll_to_bottom=True)

        tree = etree.parse(BytesIO(open(fpath, 'rb').read()), parser=parser)
        products[url].update({
            # 'pdct_name_on_eretailer': ' '.join(w for t in tree.xpath('//h1[@class="buying-controls_title"]//text()') for w in t.split()).strip(),
            # 'volume': ''.join(tree.xpath('//span[contains(@id, "productSize")]//text()')).strip(),
            # 'raw_price': ' '.join(w for t in tree.xpath('//section[@class="pdp_buying-controls"]//div[@class="price"]//text()') for w in t.split()).strip(),
            # 'raw_promo_price': ''.join(tree.xpath('//span[@class="product-action__price-text"]//fdsfdsf//text()')), # No because mix 6
            'pdct_img_main_url': clean_url(''.join(tree.xpath('//section[@class="pdp_images"]//img/@src')), root_url),
            'ctg_denom_txt': ' '.join(' '.join(tree.xpath('//section[@class="breadcrumb"]//text()')).split()),
        })
        # products[url]['price'] = getprice(products[url]['raw_price'])
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
