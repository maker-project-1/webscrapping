from io import BytesIO

from lxml import etree

parser = etree.HTMLParser()
from time import sleep
import requests_cache, imghdr

from validators import validate_raw_files
from create_csvs import create_csvs
from ers import all_keywords_de as keywords, mh_brands
from matcher import BrandMatcher
from ers import COLLECTION_DATE, file_hash, fpath_namer, img_path_namer
from helpers.random_user_agent import randomua
import shutil
import requests


# Init variables and assets
shop_id = 'bottleworld'
root_url = 'https://www.bottleworld.de'
session = requests_cache.CachedSession(fpath_namer(shop_id, 'requests_cache'))
session.headers = {'User-Agent': randomua()}
country = 'DE'
searches, categories, products = {}, {}, {}


from parse import parse


def getprice(pricestr):
    if not pricestr:
        return
    if pricestr.endswith('€'):
        pricestr = pricestr[:-1].strip()
    price = parse('{pound:d}', pricestr)
    if price:
        return price.named['pound'] * 100
    price = parse('{pound:d},{pence:d}', pricestr)
    if price:
        return price.named['pound'] * 100 + price.named['pence']
    price = parse('{th:d}.{pound:d}', pricestr)
    if price:
        return price.named['th'] * 100000 + price.named['pound'] * 100
    price = parse('{th:d}.{pound:d},{pence:d}', pricestr)
    if price:
        return price.named['th'] * 100000 + price.named['pound'] * 100 + price.named['pence']
    print('pb price', pricestr, '"')
    raise Exception


categories_urls = {
    'champagne': 'https://www.bottleworld.de/champagner-und-co/show/all',
    'cognac': "https://www.bottleworld.de/weitere/cognac-und-co/show/all",
    'sparkling': "https://www.bottleworld.de/sparkling-wine/show/all",
    'vodka': "https://www.bottleworld.de/wodka/show/all",
    'whisky': "https://www.bottleworld.de/whiskey/show/all",
    'still_wines': "https://www.bottleworld.de/wein/show/all",
    'gin': 'https://www.bottleworld.de/gin/show/all',
    'tequila': 'https://www.bottleworld.de/tequilla/show/all',
    'red_wine': 'https://www.bottleworld.de/wein/wein-sorten/rotwein/show/all',
    'white_wine': 'https://www.bottleworld.de/wein/wein-sorten/weisswein/show/all',
    'rum': 'https://www.bottleworld.de/rum/show/all',
    'liquor': 'https://www.bottleworld.de/likoer/show/all',
}


def getproduct(a):
    data = {
        'url': a.xpath('.//h2/a/@href')[0],
        'pdct_name_on_eretailer': a.xpath('.//h2/a/text()')[0],
        'price': getprice(a.xpath('.//span[@class="price"]/text()')[0].strip()),
        'img': a.xpath('.//a[@class="product-image"]/img/@src')[0]
    }
    # pprint(data)
    assert data['price']
    products[data['url']] = data


for cat, url in categories_urls.items():
    categories[cat] = []
    r = session.get(url)
    with open('/tmp/bottle.html', 'wb') as fd:
        fd.write(r.content)
    tree = etree.parse(BytesIO(r.content), parser=parser)
    articles = tree.xpath('//li[@class="item"]')
    aurls = [a.xpath('.//h2/a/@href')[0] for a in articles]
    categories[cat] = aurls
    [getproduct(a) for a in articles]
    print(cat, len(aurls))

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-extensions")
chrome_options.add_experimental_option(
    "prefs",  {"profile.managed_default_content_settings.images": 2})
driver = webdriver.Chrome(chrome_options=chrome_options)


def getproduct(a):
    data = {
        'url': 'https://www.bottleworld.de' + a.xpath('.//a[@class="exo-prod-url"]/@href')[0],
        'pdct_name_on_eretailer': a.xpath('.//a[@class="exo-prod-url"]/text()')[0],
        'price': getprice(a.xpath('.//div[@class="exo-prodPrice"]/span/text()')[0].strip()),
        'img': a.xpath('.//div[@class="exo-img"]//img/@src')[0]
    }
    assert data['price']
    products[data['url']] = data


driver.get('https://www.bottleworld.de/')
sleep(1)

for kw in keywords:
    searches[kw] = []
    for page in range(1, 5):
        driver.execute_script("window.location.hash='#q%3D{kw}%26t%3Dno%26npp%3D64%26p%3D{page}'".format(
            page=page, kw='%2520'.join(kw.split())))
        sleep(1)
        tree = etree.parse(BytesIO(driver.page_source.encode()), parser=parser)
        articles = tree.xpath('//div[@class="exo-result"]')
        aurls = ['https://www.bottleworld.de' +
                 a.xpath('.//a[@class="exo-prod-url"]/@href')[0] for a in articles]
        if not articles or all(a in searches[kw] for a in aurls):
            break
        searches[kw] += aurls
        [getproduct(a) for a in articles]
        print(kw,  len(articles), len(searches[kw]))

brm = BrandMatcher()
for url, product in products.items():
    if brm.find_brand(product['pdct_name_on_eretailer'])['brand'] in mh_brands:
        r = session.get(url)
        tree = etree.parse(BytesIO(r.content), parser=parser)
        with open('/tmp/' + shop_id + ' ' + product['pdct_name_on_eretailer'].replace('/', "-") + '.html', 'wb') as f:
            f.write(r.content)
        if tree.xpath('//meta[@property="og:image"]/@content'):
            product['pdct_img_main_url'] = tree.xpath('//meta[@property="og:image"]/@content')[0]


# Download images
for url, pdt in products.items():
     if 'pdct_img_main_url' in pdt and pdt['pdct_img_main_url'] and brm.find_brand(pdt['pdct_name_on_eretailer'])['brand'] in mh_brands:
         print(pdt['pdct_name_on_eretailer'] + "." + pdt['pdct_img_main_url'].split('.')[-1])
         print(pdt['pdct_img_main_url'])
         # url_img = pdt['pdct_img_main_url']
         tmp_file_path = '/tmp/' + shop_id + 'mhers_tmp_{}.imgtype'.format(abs(hash(pdt['pdct_img_main_url'])))
         img_path = img_path_namer(shop_id, pdt['pdct_name_on_eretailer'])
         # driver.get(pdt['pdct_img_main_url'])
         # file_ = open(tmp_file_path, 'w')
         # file_.write(driver.page_source)
         # file_.close()
         # response = requests.get(pdt['pdct_img_main_url'], stream=True, verify=False, headers=headers)
         # with open(tmp_file_path, 'wb') as out_file:
         #     response.raw.decode_content = True
         #     shutil.copyfileobj(response.raw, out_file)
         # response = requests.get(pdt['pdct_img_main_url'], stream=True, verify=False, headers=headers)
         response = requests.get(pdt['pdct_img_main_url'])
         with open(tmp_file_path, 'wb') as f:
             f.write(response.content)
         if imghdr.what(tmp_file_path) is not None:
             img_path = img_path.split('.')[0] + '.' + imghdr.what('/tmp/' + shop_id + 'mhers_tmp_{}.imgtype'.format(abs(hash(pdt['pdct_img_main_url']))))
             shutil.copyfile('/tmp/' + shop_id + 'mhers_tmp_{}.imgtype'.format(abs(hash(pdt['pdct_img_main_url']))), img_path)
             products[url].update({'img_path': img_path, 'img_hash': file_hash(img_path)})
         else:
             print("WARNING : ", tmp_file_path, pdt['pdct_img_main_url'], imghdr.what(tmp_file_path))

create_csvs(products, categories, searches, shop_id, fpath_namer(shop_id, 'raw_csv'), COLLECTION_DATE)
validate_raw_files(fpath_namer(shop_id, 'raw_csv'))
driver.quit()

# Img download problem

# url_img = "https://www.bottleworld.de/media/catalog/product/cache/1/image/9df78eab33525d08d6e5fb8d27136e95/1/2/1232_veuve_clicquot_champagner_la_grande_dame_rose_0_75l.jpeg"
#
# import requests
# with open('/home/renaud/FB_IMG_1490534565948.jpg', 'wb') as f:
#     f.write(requests.get(url_img).content)