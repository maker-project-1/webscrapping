import os.path as op
from io import BytesIO
from time import sleep

from lxml import etree

parser = etree.HTMLParser()
from urllib.parse import urlsplit, parse_qs
import requests
import requests_cache, imghdr
from validators import validate_raw_files
from create_csvs import create_csvs
from custom_browser import CustomDriver

from ers import all_keywords_usa as keywords, mh_brands, clean_url, headers
from matcher import BrandMatcher
from ers import COLLECTION_DATE, file_hash, img_path_namer,fpath_namer
import shutil
driver = CustomDriver(headless=False, download_images=True)

# Init variables and assets
shop_id = 'tower'
root_url = 'http://buckhead.towerwinespirits.com'
session = requests_cache.core.CachedSession(
    fpath_namer(shop_id, 'requests_cache'), allowable_methods=('GET', 'POST'))
country = 'USA'
searches, categories, products = {}, {}, {}

from parse import parse


def getprice(pricestr):
    if not pricestr:
        return
    pricestr = pricestr.replace("Reg.", "").replace("\xa0", "")
    price = parse('${pound:d}.{pence:d}', pricestr)
    if not price:
        price = parse('${th:d},{pound:d}.{pence:d}', pricestr)
        return price.named['th'] * 100000 + price.named['pound'] * 100 + price.named['pence']
    return price.named['pound'] * 100 + price.named['pence']


urls_ctgs_dict = {
    'champagne': 'https://buckhead.towerwinespirits.com/main.asp?request=search&sel_variety=champagne%20blend',
    'sparkling': 'http://buckhead.towerwinespirits.com/main.asp?request=SEARCH&wine_type=sparkling',
    'whisky': 'http://buckhead.towerwinespirits.com/main.asp?request=TYPEPAGE&sel_category=1400,1200,1000&type=L',
    'cognac': 'http://buckhead.towerwinespirits.com/main.asp?request=TYPEPAGE&sel_category=1170&type=L',
    'vodka': 'http://buckhead.towerwinespirits.com/main.asp?request=TYPEPAGE&sel_category=1750&type=L',
    'red_wine': 'https://buckhead.towerwinespirits.com/main.asp?request=TYPEPAGE&selcolor=Red&type=W&',
    'white_wine': 'https://buckhead.towerwinespirits.com/main.asp?request=TYPEPAGE&selcolor=White&type=W&',
    'gin': 'https://buckhead.towerwinespirits.com/main.asp?request=TYPEPAGE&sel_category=1350&type=L',
    'rum': 'https://buckhead.towerwinespirits.com/main.asp?request=TYPEPAGE&sel_category=1550&type=L',
    'tequila': 'https://buckhead.towerwinespirits.com/main.asp?request=TYPEPAGE&sel_category=1700&type=L',
    'brandy': 'https://buckhead.towerwinespirits.com/main.asp?request=search&sel_category=1150&type=l',
    'liquor': 'https://buckhead.towerwinespirits.com/main.asp?request=search&sel_category=1300&type=l',
}

for ctg, url in urls_ctgs_dict.items():
    categories[ctg] = []
    number_of_pdcts_in_ctg = 0
    print("Scraping cat", ctg)
    for p in range(1, 1000):
        fpath = fpath_namer(shop_id, 'ctg', ctg, p)
        if not op.exists(fpath):
            driver.get(url)
            sleep(1)
            driver.save_page(fpath, scroll_to_bottom=True)
        # Parsing
        tree = etree.parse(BytesIO(open(fpath, 'rb').read()), parser=parser)

        for li in tree.xpath('//form[@name="frmsearch"]//td[@valign="top" and ./table]'):
            produrl = li.xpath('.//a[@class="Srch-producttitle"]/@href')[0]
            produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
            produrl = clean_url(produrl, root_url)
            products[produrl] = {
                'pdct_name_on_eretailer': ' '.join(''.join(li.xpath('.//a[@class="Srch-producttitle"]/text()')[:1]).split()),
                'volume': ' '.join(''.join(li.xpath('.//span[@class="Srch-bottlesize"]/text()')[:1]).split()),
                'raw_price': ' '.join(''.join(li.xpath('.//span[@class="RegularPrice"]/text()')).split()),
                'raw_promo_price': ' '.join(''.join(li.xpath('.//span[@class="cart-price-strike"]//text()')).split()),
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
            driver.waitclick('//b[contains(text(),">>")]')

# KW searches Scraping - with selenium - with nb page hard-coded in url - multiple page per search
search_url = "https://buckhead.towerwinespirits.com/main.asp?request=SEARCH&search={kw}"
for kw in keywords:
    searches[kw] = []
    number_of_pdcts_in_kw_search = 0

    # Storing and extracting infos
    urlp = search_url.format(kw=kw)

    fpath = fpath_namer(shop_id, 'search', kw, 0)
    if not op.exists(fpath):
        driver.get(urlp)
        sleep(1)
        driver.save_page(fpath, scroll_to_bottom=True)
    # Parsing
    tree = etree.parse(BytesIO(open(fpath, 'rb').read()), parser=parser)

    for li in tree.xpath('//form[@name="frmsearch"]//td[@valign="top" and ./table]'):
        produrl = li.xpath('.//a[@class="Srch-producttitle"]/@href')[0]
        produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
        produrl = clean_url(produrl, root_url)
        products[produrl] = {
            'pdct_name_on_eretailer': ' '.join(''.join(li.xpath('.//a[@class="Srch-producttitle"]/text()')[:1]).split()),
            'volume': ' '.join(''.join(li.xpath('.//span[@class="Srch-bottlesize"]/text()')[:1]).split()),
            'raw_price': ' '.join(''.join(li.xpath('.//span[@class="RegularPrice"]/text()')).split()),
            'raw_promo_price': ' '.join(''.join(li.xpath('.//span[@class="cart-price-strike"]//text()')).split()),
        }
        print(products[produrl], produrl)
        products[produrl]['price'] = getprice(products[produrl]['raw_price'])
        products[produrl]['promo_price'] = getprice(products[produrl]['raw_promo_price'])
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
        fname = fpath_namer(shop_id, 'pdct', d['pdct_name_on_eretailer'], 0)
        if not op.exists(fname):
            driver.get(url_mod)
            sleep(2)
            driver.save_page(fname, scroll_to_bottom=True)
        tree = etree.parse(open(fname), parser=parser)

        products[url].update({
            'pdct_img_main_url': clean_url(tree.xpath('//div[@id="loadarea"]/img/@src')[0], root_url),
            'ctg_denom_txt': tree.xpath('//div[@class="info_list"]//span[@class="iteminfo"]/a/text()')
        })
        print(products[url]['pdct_img_main_url'])

# Download images
for url, pdt in products.items():
     if 'pdct_img_main_url' in pdt and pdt['pdct_img_main_url']:
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
         else: 
             print('Warning :', tmp_file_path, imghdr.what(tmp_file_path))

create_csvs(products, categories, searches, shop_id, fpath_namer(shop_id, 'raw_csv'), COLLECTION_DATE)
validate_raw_files(fpath_namer(shop_id, 'raw_csv'))
driver.quit()
