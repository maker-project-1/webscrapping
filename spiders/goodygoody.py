import os.path as op
from io import BytesIO

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
shop_id = 'goodygoody'
root_url = 'https://www.goodygoody.com/'
requests_cache.install_cache(fpath_namer(shop_id, 'requests_cache'))
country = 'AUS'
searches, categories, products = {}, {}, {}
driver = CustomDriver(headless=True, download_images=True)

def getprice(pricestr):
    if pricestr == '':
        return pricestr
    pricestr = pricestr.replace(',', '').strip()
    price = parse('${dol:d}.{pence:d}', pricestr)
    if price is None:
        price = parse('{pence:d}p', pricestr)
        return price.named['pence']
    else:
        return price.named['dol'] * 100 + price.named['pence']


def init_goodygoody(driver):
    driver.get("https://www.goodygoody.com/Products/Products?searchTerm=champagne&category=&type=0&orderBy=name&minprice=&maxprice=")
    sleep(1)
    driver.waitclick('//*[@id="applyStoreButton"]')

goodygoody_was_initialised = False

urls_ctgs_dict = {
    'champagne': 'https://www.goodygoody.com/Products/Products?searchTerm=&category=4RDE&type=0&orderBy=name&minprice=&maxprice=',
    'sparkling': 'https://www.goodygoody.com/Products/Products?searchTerm=&category=4RDE&type=0&orderBy=name&minprice=&maxprice=',
    'still_wines': 'https://www.goodygoody.com/Products/Products?searchTerm=&category=4RAE&type=0&orderBy=name&minprice=&maxprice=',
    'whisky': 'https://www.goodygoody.com/Products/Products?searchTerm=&category=1ASC&type=0&orderBy=name&minprice=&maxprice=',
    'cognac': 'https://www.goodygoody.com/Products/Products?searchTerm=&category=1ACG&type=0&orderBy=name&minprice=&maxprice=',
    'vodka': 'https://www.goodygoody.com/Products/Products?searchTerm=&category=1AVK&type=0&orderBy=name&minprice=&maxprice=',
    'gin': 'https://www.goodygoody.com/Products/Products?searchTerm=&category=1AGN&type=0&orderBy=name&minprice=&maxprice=',
    'tequila': 'https://www.goodygoody.com/Products/Products?searchTerm=&category=1ATQ&type=0&orderBy=name&minprice=&maxprice=',
    'rum': 'https://www.goodygoody.com/Products/Products?searchTerm=&category=1ARM&type=0&orderBy=name&minprice=&maxprice=',
    'brandy': 'https://www.goodygoody.com/Products/Products?searchTerm=&category=1ABR&type=0&orderBy=name&minprice=&maxprice=',
    'bourbon': 'https://www.goodygoody.com/Products/Products?searchTerm=&category=1ABN&type=0&orderBy=name&minprice=&maxprice=',
}

# Categories scraping
for ctg, url in urls_ctgs_dict.items():
    categories[ctg] = []
    if not op.exists(fpath_namer(shop_id, 'ctg', ctg, 0)):
        driver.get(url)

    for p in range(100):
        # Scraping
        urlp = url.format(page=p+1)
        fpath = fpath_namer(shop_id, 'ctg', ctg, p)
        if not op.exists(fpath):
            if not goodygoody_was_initialised:
                init_goodygoody(driver)
                goodygoody_was_initialised = True
            sleep(2)
            driver.save_page(fpath)
        # Parsing
        tree = etree.parse(BytesIO(open(fpath, 'rb').read()), parser=parser)
        for li in tree.xpath('//div[@class="row productRow"]//div[@class="row"]'):
            pdct_name_on_eretailer = ' '.join(''.join(li.xpath('./div[2]/p[1]//text()')).split())
            products[pdct_name_on_eretailer] = {
                'pdct_name_on_eretailer': pdct_name_on_eretailer,
                'raw_price': ' '.join(''.join(li.xpath('./div[2]/br[1]/following-sibling::text()[1]')).split()),
                'volume': ' '.join(''.join(li.xpath('./div[2]/br[1]/preceding-sibling::text()[1]')).split()),
                'pdct_img_main_url': clean_url(' '.join(''.join(li.xpath('.//img[@class="img-thumbnail"]/@src')).split()), root_url),
                'ctg_denom_txt': pdct_name_on_eretailer,
            }
            print(products[pdct_name_on_eretailer], pdct_name_on_eretailer)
            products[pdct_name_on_eretailer]['price'] = getprice(products[pdct_name_on_eretailer]['raw_price'])
            # products[produrl]['promo_price'] = getprice(products[produrl]['raw_promo_price'])
            print(products[pdct_name_on_eretailer])
            categories[ctg].append(pdct_name_on_eretailer)

        # Going to next page if need be
        next_page_click = '//ul[@class="pager"]/li/a[@href="/roducts/next"]'
        if not op.exists(fpath_namer(shop_id, 'ctg', ctg, p+1)):
            if not driver.check_exists_by_xpath(next_page_click):
                break
            else:
                print('clicking next')
                driver.get("https://www.goodygoody.com/products/next")
print([(c, len(categories[c])) for c in categories])


# KW scraping
search_url = "https://www.goodygoody.com/Products/Products?searchTerm={kw}&category=&type=0&orderBy=name&minprice=&maxprice="
for kw in keywords:
    searches[kw] = []
    if not op.exists(fpath_namer(shop_id, 'search', kw, 0)):
        urlkw = search_url.format(kw=kw)
        driver.get(urlkw)

    for p in range(10):
        # Scraping
        fpath = fpath_namer(shop_id, 'search', kw, p)
        if not op.exists(fpath):
            if not goodygoody_was_initialised:
                init_goodygoody(driver)
                goodygoody_was_initialised = True
            sleep(2)
            driver.save_page(fpath)
        # Parsing
        tree = etree.parse(BytesIO(open(fpath, 'rb').read()), parser=parser)
        for li in tree.xpath('//div[@class="row productRow"]//div[@class="row"]'):
            pdct_name_on_eretailer = ' '.join(''.join(li.xpath('./div[2]/p[1]//text()')).split())
            products[pdct_name_on_eretailer] = {
                'pdct_name_on_eretailer': pdct_name_on_eretailer,
                'raw_price': ' '.join(''.join(li.xpath('./div[2]/br[1]/following-sibling::text()[1]')).split()),
                'volume': ' '.join(''.join(li.xpath('./div[2]/br[1]/preceding-sibling::text()[1]')).split()),
                'pdct_img_main_url': clean_url(' '.join(''.join(li.xpath('.//img[@class="img-thumbnail"]/@src')).split()), root_url),
                'ctg_denom_txt': pdct_name_on_eretailer,
            }
            products[pdct_name_on_eretailer]['price'] = getprice(products[pdct_name_on_eretailer]['raw_price'])
            print(products[pdct_name_on_eretailer])
            searches[kw].append(pdct_name_on_eretailer)

        # Going to next page if need be
        next_page_click = '//ul[@class="pager"]/li/a[@href="/products/next"]'
        if not op.exists(fpath_namer(shop_id, 'search', kw, p+1)):
            if not driver.check_exists_by_xpath(next_page_click):
                break
            else:
                print('clicking next')
                driver.get("https://www.goodygoody.com/products/next")



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
