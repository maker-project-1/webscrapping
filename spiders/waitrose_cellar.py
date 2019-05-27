import os.path as op

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
shop_id = 'waitrose_cellar'
root_url = 'http://www.waitrosecellar.com'
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
            'champagne': 'http://www.waitrosecellar.com/champagne-and-sparkling/type/champagne',
            'sparkling': 'http://www.waitrosecellar.com/champagne-and-sparkling/type/sparkling-wine',
            'still_wines': 'http://www.waitrosecellar.com/white-fine-wines',
            'whisky': 'http://www.waitrosecellar.com/spirits/spirit-type/whisky',
            'cognac': 'http://www.waitrosecellar.com/spirits/spirit-type/cognac',
            'vodka': 'http://www.waitrosecellar.com/spirits/spirit-type/vodka',
            'red_wine': 'http://www.waitrosecellar.com/all-wines/wine-type/red-wine',
            'white_wine': 'http://www.waitrosecellar.com/all-wines/wine-type/white-wine',
            'gin': 'http://www.waitrosecellar.com/gin',
            'rum': 'http://www.waitrosecellar.com/rum',
            'tequila': 'http://www.waitrosecellar.com/tequila',
            'liquor': 'http://www.waitrosecellar.com/liqueurs',
        }

# Difficult case, where you should click a button to get on next page and send the request via the search bar
for ctg, url in urls_ctgs_dict.items():
    categories[ctg] = []
    number_of_pdcts_in_ctg = 0
    if not op.exists(fpath_namer(shop_id, 'ctg', ctg, 0)):
        # Getting back to root if search input box is not found
        driver.get(url)
    for p in range(100):
        # Storing and extracting infos
        fpath = fpath_namer(shop_id, 'ctg', ctg, p)
        if not op.exists(fpath):
            driver.save_page(fpath)
            sleep(2)
        tree = etree.parse(open(fpath, 'rb'), parser=parser)
        for li in tree.xpath('//div[@class="productCard"]'):
            produrl = li.xpath('.//div[@class="productName"]/a/@href')[0]
            produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
            categories[ctg].append(produrl)
            products[produrl] = {
                'pdct_name_on_eretailer': li.xpath('.//div[@class="productName"]//text()')[0].strip(),
                'raw_price': "".join(li.xpath('.//div[@class="productCurrentPrice"]//text()')).replace('Now',''),
            }
            # print(products[produrl])
            products[produrl]['price'] = getprice(products[produrl]['raw_price'])
            # print(products[produrl])
        # Going to next page if need be
        next_page_click = '//a[@class="resultsNext"]'
        if not op.exists(fpath_namer(shop_id, 'ctg', ctg, p+1)):
            if not driver.check_exists_by_xpath(next_page_click):
                break
            else:
                driver.waitclick(next_page_click)
    print(ctg, url, p, len(categories[ctg]))


# Difficult case, where you should click a button to get on next page and send the request via the search bar
for kw in keywords:
    searches[kw] = []
    number_of_pdcts_in_kw_search = 0
    search_input_box_xpath = u'//*[@id="SimpleSearchForm_SearchTerm"]'
    if not op.exists(fpath_namer(shop_id, 'search', kw, 0)):
        if not driver.check_exists_by_xpath(search_input_box_xpath):
            # Getting back to root if search input box is not found
            driver.get(root_url)
        driver.text_input(kw, search_input_box_xpath, enter=True)
    for p in range(10):
        # Storing and extracting infos
        fpath = fpath_namer(shop_id, 'search', kw, p)
        if not op.exists(fpath):
            driver.save_page(fpath)
            sleep(2)
        tree = etree.parse(open(fpath, 'rb'), parser=parser)
        for li in tree.xpath('//div[@class="productCard"]'):
            produrl = li.xpath('.//div[@class="productName"]/a/@href')[0]
            produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
            searches[kw].append(produrl)
            products[produrl] = {
                'pdct_name_on_eretailer': li.xpath('.//div[@class="productName"]//text()')[0].strip(),
                'raw_price': "".join(li.xpath('.//div[@class="productCurrentPrice"]//text()')).replace('Now',''),
            }
            # print(products[produrl])
            products[produrl]['price'] = getprice(products[produrl]['raw_price'])
        # Going to next page if need be
        next_page_click = '//a[@class="resultsNext"]'
        if not op.exists(fpath_namer(shop_id, 'search', kw, p+1)):
            if not driver.check_exists_by_xpath(next_page_click):
                break
            else:
                driver.waitclick(next_page_click)
    print(kw, p, len(searches[kw]))


# Download the pages
brm = BrandMatcher()
for url in sorted(list(set(products))):
    d = products[url]
    if brm.find_brand(d['pdct_name_on_eretailer'])['brand'] in mh_brands:
        fname = fpath_namer(shop_id, 'pdct', d['pdct_name_on_eretailer'], 0)
        if not op.exists(fname):
            driver.get(url)
            sleep(2)
            driver.save_page(fname, scroll_to_bottom=True)
        tree = etree.parse(open(fname), parser=parser)
        products[url] = {
            'pdct_name_on_eretailer': ''.join(tree.xpath('//h1[@class="productName"]//text()')).strip(),
            'volume': ''.join(tree.xpath('.//div[@class="infomation"]/ul[@class="rowOne"]/li[2]//text()')).replace('Size:', '').strip(),
            'raw_price': ''.join(tree.xpath('//*[@id="mainContent"]//div[@class="detailsLeft"]//div[@class="productCurrentPrice"]//text()')).replace('Now', '').strip(),
            'raw_promo_price': ''.join(tree.xpath('//*[@id="mainContent"]//div[@class="detailsLeft"]//div[@class="productPreviousPrice"]//text()')).replace('Was', '').strip(),
            'pdct_img_main_url': clean_url(''.join(tree.xpath('//div[@class="mainImage"]/img/@src')), root_url),
            'ctg_denom_txt': ''.join(tree.xpath('//h1[@class="productName"]//text()')).strip(),
        }
        products[url]['price'] = getprice(products[url]['raw_price'])
        products[url]['promo_price'] = getprice(products[url]['raw_promo_price'])
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
