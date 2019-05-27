import os.path as op
from io import BytesIO
from time import sleep

from lxml import etree

parser = etree.HTMLParser()
import requests_cache, imghdr, requests
from validators import validate_raw_files
from create_csvs import create_csvs
from custom_browser import CustomDriver
from urllib.parse import quote_plus
from urllib.parse import urlsplit, parse_qs

from ers import all_keywords_de as keywords, mh_brands
from matcher import BrandMatcher
from ers import COLLECTION_DATE, file_hash, img_path_namer, fpath_namer, clean_url
import shutil
from helpers.random_user_agent import randomua
driver = CustomDriver(headless=True)
from parse import parse

# Init variables and assets
shop_id = 'spirituosen_superbillig'
root_url = 'https://www.spirituosen-superbillig.com/'
session = requests_cache.CachedSession(fpath_namer(shop_id, 'requests_cache'))
session.headers = {'User-Agent': randomua()}
country = 'DE'
searches, categories, products = {}, {}, {}


def getprice(pricestr):
    if not pricestr:
        return
    price = parse('{pound:d} €', pricestr)
    if price:
        return price.named['pound'] * 100
    price = parse('{pound:d},{pence:d} €', pricestr)
    if price:
        return price.named['pound'] * 100 + price.named['pence']
    price = parse('{th:d},{pound:d} €', pricestr)
    if price:
        return price.named['th'] * 100000 + price.named['pound'] * 100
    price = parse('{th:d}.{pound:d},{pence:d} €', pricestr)
    if price:
        return price.named['th'] * 100000 + price.named['pound'] * 100 + price.named['pence']
    print('pb price', pricestr)
    raise Exception


categories_urls = {
    'champagne': 'https://www.spirituosen-superbillig.com/Champagner.html',
    'cognac': 'https://www.spirituosen-superbillig.com/Cognac.html',
    'sparkling': 'https://www.spirituosen-superbillig.com/Prosecco.html',
    'vodka': 'https://www.spirituosen-superbillig.com/Vodka-Wodka.html',
    'whisky': 'https://www.spirituosen-superbillig.com/Whisky-Whiskey.html',
    'gin': 'https://www.spirituosen-superbillig.com/Gin.html',
    'rum': 'https://www.spirituosen-superbillig.com/Rum.html',
    'liquor': 'https://www.spirituosen-superbillig.com/Likoer.html',
    'tequila': 'https://www.spirituosen-superbillig.com/Tequila-Mezcal.html',
    'brandy': 'https://www.spirituosen-superbillig.com/Brandy.html',
}

for ctg, url in categories_urls.items():
    print('Scraping ctg :', ctg)
    categories[ctg] = []
    fpath = fpath_namer(shop_id, 'ctg', ctg, 0)
    if not op.exists(fpath):
        driver.get(url)
        sleep(2)
        print('Scrolling to bottom')
        driver.smooth_scroll()
        # print('Clicking to bottom')
        # driver.click_to_bottom('//*[@id="pacerGoOnButton"]/button')
        driver.save_page(fpath)
        print(fpath)
    tree = etree.parse(BytesIO(open(fpath, 'rb').read()), parser=parser)

    for li in tree.xpath('//li[@class="art_box"]'):
        produrl = li.xpath('.//a/@href')[0]
        produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
        produrl = clean_url(produrl, root_url)
        products[produrl] = {
            'pdct_name_on_eretailer': ' '.join(''.join(li.xpath('.//*[@class="se_name"]//text()')[0]).split()),
            'volume': ' '.join(''.join(li.xpath('.//*[@class="se_name"]//text()')[0]).split()),
            'raw_price': "".join(li.xpath('.//span[@class="se_vk"]//text()')[:1]).replace('â‚¬*', '€').replace('â¬*', '€'),
        }
        print(products[produrl], produrl)
        products[produrl]['price'] = getprice(products[produrl]['raw_price'])
        print(products[produrl])

        categories[ctg].append(produrl)

print([(c, len(categories[c])) for c in categories])


for kw in keywords:
    searches[kw] = []
    url = 'https://www.spirituosen-superbillig.com/s01.php?shopid=s01&ag=1&cur=eur&sp=de&pp=suche&suchstr={kw}'.format(kw=quote_plus(kw))
    fpath = fpath_namer(shop_id, 'search', kw, 0)
    if not op.exists(fpath):
        driver.get(url)
        driver.save_page(fpath, scroll_to_bottom=True)
    tree = etree.parse(BytesIO(open(fpath, 'rb').read()), parser=parser)
    # Parsing

    for li in tree.xpath('//li[@class="art_box"]'):
        produrl = li.xpath('.//a/@href')[0]
        produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
        produrl = clean_url(produrl, root_url)
        products[produrl] = {
            'pdct_name_on_eretailer': ' '.join(''.join(li.xpath('.//*[@class="se_name"]//text()')[0]).split()),
            'volume': ' '.join(''.join(li.xpath('.//*[@class="se_name"]//text()')[0]).split()),
            'raw_price': "".join(li.xpath('.//span[@class="se_vk"]//text()')[:1]).replace('â‚¬*', '€').replace('â¬*',
                                                                                                               '€'),
        }
        print(products[produrl], produrl)
        products[produrl]['price'] = getprice(products[produrl]['raw_price'])
        print(products[produrl])

        searches[kw].append(produrl)
    print(kw, 0, len(searches))


brm = BrandMatcher()

for url, product in products.items():
    if brm.find_brand(product['pdct_name_on_eretailer'])['brand'] in mh_brands:
        print(url)
        fname = fpath_namer(shop_id, 'pdct', product['pdct_name_on_eretailer'], 0)
        if not op.exists(fname):
            driver.get(url)
            sleep(2)
            driver.save_page(fname)
        tree = etree.parse(open(fname), parser=parser)

        data = {
            'pdct_img_main_url': clean_url("".join(tree.xpath('//img[@class="langesBild"]/@src')[:1]), root_url),
            'ctg_denom_txt': ' '.join(tree.xpath('//*[@typeof="v:Breadcrumb"]/text()')),
        }
        product.update(data)
        print(product)


# Download images
for url, pdt in products.items():
     if 'pdct_img_main_url' in pdt and pdt['pdct_img_main_url']:
         print(pdt['pdct_name_on_eretailer'] + "." + pdt['pdct_img_main_url'].split('.')[-1])
         response = requests.get(pdt['pdct_img_main_url'], stream=True, verify=False)
         # response.raw.decode_content = True
         tmp_file_path = '/tmp/mhers_tmp_{}.img'.format(abs(hash(pdt['pdct_img_main_url'])))
         img_path = img_path_namer(shop_id, pdt['pdct_name_on_eretailer'])
         with open(tmp_file_path, 'wb') as out_file:
             shutil.copyfileobj(response.raw, out_file)
         if imghdr.what(tmp_file_path) is not None:
             img_path = img_path.split('.')[0] + '.' + imghdr.what('/tmp/mhers_tmp_{}.img'.format(abs(hash(pdt['pdct_img_main_url']))))
             shutil.copyfile('/tmp/mhers_tmp_{}.img'.format(abs(hash(pdt['pdct_img_main_url']))), img_path)
             products[url].update({'img_path': img_path, 'img_hash': file_hash(img_path)})

create_csvs(products, categories, searches, shop_id, fpath_namer(shop_id, 'raw_csv'), COLLECTION_DATE)
validate_raw_files(fpath_namer(shop_id, 'raw_csv'))
