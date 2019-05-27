
import os.path as op
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
from custom_browser import CustomDriver
from parse import parse
from validators import validate_raw_files
from create_csvs import create_csvs

# Init variables and assets
shop_id = "bodeboca"
root_url = "https://bodeboca.com"
requests_cache.install_cache(fpath_namer(shop_id, 'requests_cache'))
country = "ES"


searches, categories, products = {}, {}, {}
# If necessary
driver = CustomDriver(headless=False, download_images=True, firefox=True)


def getprice(pricestr):
    if pricestr == '':
        return pricestr
    pricestr = re.sub("[^0-9,€]", "", pricestr)
    pricestr = pricestr.split('€')[0] + '€'
    price = parse('{pound:d},{pence:d}€', pricestr)
    if price is None:
        price = parse('{pence:d}p', pricestr)
        return price.named['pence']
    else:
        return price.named['pound'] * 100 + price.named['pence']



urls_ctgs_dict = {
    "vodka": "https://www.bodeboca.com/destilados-licores?page={page}",
    "sparkling": 'https://www.bodeboca.com/vino/espumoso?page={page}',
    "cognac": "https://www.bodeboca.com/destilados-licores?page={page}",
    "champagne": 'https://www.bodeboca.com/vino/francia/champagne?page={page}',
    "still_wines": 'https://www.bodeboca.com/vino?page={page}',
    "whisky": 'https://www.bodeboca.com/destilados-licores?page={page}',
    "tequila": 'https://www.bodeboca.com/destilados-licores?page={page}',
    "rum": 'https://www.bodeboca.com/destilados-licores/ron?page={page}',
    "liquor": 'https://www.bodeboca.com/destilados-licores/licor?page={page}',
    "brandy": 'https://www.bodeboca.com/destilados-licores/brandy?page={page}',
    "red_wine": 'https://www.bodeboca.com/vino/tinto?page={page}',
    "white_wine": 'https://www.bodeboca.com/vino/blanco?page={page}',
}

# Category Scraping
for ctg, url in urls_ctgs_dict.items():
    categories[ctg] = []
    number_of_pdcts_in_ctg = 0
    for p in range(20):
        urlp = url.format(page=p+1)

        fpath = fpath_namer(shop_id, 'ctg', ctg, p)
        print(fpath, p, urlp)
        if not op.exists(fpath):
            driver.get(urlp)
            # driver.driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.7);")
            # print('sleeping')
            # sleep(10)
            # driver.waitclick('//*[contains(@class, "bb-modal-close-button")]', timeout=1, silent=False)
            driver.save_page(fpath, scroll_to_bottom=True)
        tree = etree.parse(BytesIO(open(fpath, 'rb').read()), parser=parser)

        for li in tree.xpath('//div[@id="venta-main"]/div'):
            produrl = li.xpath('.//a/@href')[0]
            produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
            produrl = clean_url(produrl, root_url)
            products[produrl] = {
                'pdct_name_on_eretailer': ' '.join(''.join(li.xpath('.//h2/a/text()')[:1]).split()),
                'raw_price': ' '.join(''.join(li.xpath('.//div[@class="wineblock-leftprice"]//*[@class="uc-price"]//text()')[:2]).split()),
                'raw_promo_price': ' '.join(''.join(li.xpath('.//div[@class="wineblock-price-rightcol"]//*[@class="uc-price"]//text()')[:2]).split()),
            }
            print(products[produrl], produrl)
            products[produrl]['price'] = getprice(products[produrl]['raw_price'])
            products[produrl]['promo_price'] = getprice(products[produrl]['raw_promo_price'])
            print(products[produrl])

            categories[ctg].append(produrl)
        if len(set(categories[ctg])) == number_of_pdcts_in_ctg:
            break
        else:
            number_of_pdcts_in_ctg = len(set(categories[ctg]))
print(categories)


# KW searches Scraping - with selenium - with nb page hard-coded in url - multiple page per search
search_url = "https://www.bodeboca.com/"
for kw in keywords:
    searches[kw] = []
    number_of_pdcts_in_kw_search = 0
    fpath = fpath_namer(shop_id, 'search', kw, 0)
    if not op.exists(fpath):
        driver.get(search_url)
        sleep(2)
        driver.text_input(kw, '//*[@id="bodeboca-search-box"]/input')
        sleep(2)
        driver.save_page(fpath, scroll_to_bottom=False)
    tree = etree.parse(BytesIO(open(fpath, 'rb').read()), parser=parser)

    for li in tree.xpath('//div[@id="search-results-main"]/div'):
        if not li.xpath('.//a/@href'):
            continue
        if not ' '.join(''.join(li.xpath('.//h2/a/text()')[:1]).split()):
            continue
        produrl = li.xpath('.//a/@href')[0]
        produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
        produrl = clean_url(produrl, root_url)
        products[produrl] = {
            'pdct_name_on_eretailer': ' '.join(''.join(li.xpath('.//h2/a/text()')[:1]).split()),
            'raw_price': ' '.join(
                ''.join(li.xpath('.//div[@class="wineblock-leftprice"]//*[@class="uc-price"]//text()')[:2]).split()),
            'raw_promo_price': ' '.join(''.join(
                li.xpath('.//div[@class="wineblock-price-rightcol"]//*[@class="uc-price"]//text()')[:2]).split()),
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

        r = requests.get(url_mod, headers)
        with open('/tmp/' + d['pdct_name_on_eretailer'].replace('/', "-") + '.html', 'wb') as f:
            f.write(r.content)
        tree = etree.parse(BytesIO(r.content), parser=parser)
        
        products[url].update({
            'volume': ' '.join(''.join(tree.xpath('//*[@id="main-section"]//*[@class="formato"]/text()')[:1]).split()),
            'pdct_img_main_url': clean_url(''.join(tree.xpath('//*[@id="main-section"]//img/@src')[:1       ]), root_url),
            'ctg_denom_txt': ' '.join(' '.join(tree.xpath('//div[@class="breadcrumb"]//text()')).split()),
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



