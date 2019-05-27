import os.path as op

from lxml import etree

parser = etree.HTMLParser(encoding='utf-8')
from time import sleep
import requests
import requests_cache, imghdr

from validators import validate_raw_files
from create_csvs import create_csvs

from ers import all_keywords_aus as keywords, fpath_namer, mh_brands, clean_url, headers
from matcher import BrandMatcher
from ers import COLLECTION_DATE, file_hash, img_path_namer
import shutil
from parse import parse
from custom_browser import CustomDriver


# Init variables and assets
shop_id = 'jimmy_brings'
root_url = 'https://jimmybrings.com.au/'
requests_cache.install_cache(fpath_namer(shop_id, 'requests_cache'))
country = 'AUS'
searches, categories, products = {}, {}, {}
driver = CustomDriver(headless=True, download_images=False)
urls_ctgs_dict = {
    'champagne': 'https://jimmybrings.com.au/menu/',
    'sparkling': 'https://jimmybrings.com.au/menu/',
    'still_wines': 'https://jimmybrings.com.au/menu/',
    'whisky': 'https://jimmybrings.com.au/menu/',
    'cognac': 'https://jimmybrings.com.au/menu/',
    'vodka': 'https://jimmybrings.com.au/menu/',
}


def getprice(pricestr):
    if pricestr == '':
        return pricestr
    pricestr = pricestr.replace(',', '').strip()
    price = parse('${dol:d}.{pence:d}', pricestr)
    if price is None:
        price = parse('${dol:d}', pricestr)
        if price is not None:
            return price.named['dol'] * 100
        else:
            price = parse('{pence:d}p', pricestr)
            return price.named['pence']
    else:
        return price.named['dol'] * 100 + price.named['pence']


# Category Scraping - with requests - one page per category
for ctg, url in urls_ctgs_dict.items():
    categories[ctg] = []
    fpath = fpath_namer(shop_id, 'ctg', ctg, 0)
    if not op.exists(fpath):
        driver.get(url)
        sleep(2)
        driver.save_page(fpath, scroll_to_bottom=True)
    tree = etree.parse(open(fpath, 'rb'), parser=parser)
    for li in tree.xpath('//li[@class="menu-item"]'):
        produrl = ' '.join(''.join(li.xpath('.//h4//text()')).strip().split())
        products[produrl] = {
            'pdct_name_on_eretailer': ' '.join(''.join(li.xpath('.//h4//text()')).strip().split()),
            'raw_price': ''.join(w for t in li.xpath('.//div[@class="moduleResult"]/div[@class="mpricenew"]//text()') for w in t.split()).strip(),
            'pdct_img_main_url': clean_url(''.join(w for t in li.xpath('.//div[@class="menuimg"]/img/@src') for w in t.split()).strip(), root_url),
            'ctg_denom_txt': ctg,
            'volume': '750ml',
        }
        products[produrl]['price'] = getprice(products[produrl]['raw_price'])
        print(products[produrl])
        assert all(products[produrl][k] for k in products[produrl])

        categories[ctg].append(produrl)
    print(ctg, len(categories[ctg]))


# KW searches Scraping - with selenium - with search input - one page per search
for kw in keywords:
    try:
        searches[kw] = []
        number_of_pdcts_in_kw_search = 0
        search_input_box_xpath = u'//*[@id="src_inp"]'
        if not op.exists(fpath_namer(shop_id, 'search', kw, 0)):
            if not driver.check_exists_by_xpath(search_input_box_xpath):
                # Getting back to root if search input box is not found
                driver.get(root_url)
            driver.text_input(kw, search_input_box_xpath, enter=True)

        # Storing and extracting infos
        fpath = fpath_namer(shop_id, 'search', kw, 0)
        print(fpath)
        if not op.exists(fpath):
            sleep(2)
            driver.save_page(fpath, scroll_to_bottom=True)
        tree = etree.parse(open(fpath, 'rb'), parser=parser)
        for li in tree.xpath('//li[@class="menu-item" and not(@style="display: none;")]'):
            produrl = ' '.join(''.join(li.xpath('.//h4//text()')).strip().split())
            print(produrl)
            searches[kw].append(produrl)
        print(kw, 0, len(searches[kw]))
    except Exception:
        import traceback
        print("ERROR: ", kw)
        print(traceback.format_exc())


# Download images
brm = BrandMatcher()
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
