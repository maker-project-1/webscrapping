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
shop_id = 'twin_liquors'
root_url = 'http://www.twinliquors.com'
requests_cache.install_cache(fpath_namer(shop_id, 'requests_cache'))
country = 'USA'
searches, categories, products = {}, {}, {}
driver = CustomDriver(headless=True, download_images=False)

urls_ctgs_dict = {
    'champagne': 'http://twinliquors.com/shop/catalogsearch/result/?q=champagne',
    'sparkling': 'http://twinliquors.com/shop/catalogsearch/result/?q=Sparkling+wine',
    'still_wines': 'http://twinliquors.com/shop/wine.html',
    'whisky': 'http://twinliquors.com/shop/catalogsearch/result/?q=whisky',
    'cognac': 'http://twinliquors.com/shop/catalogsearch/result/?q=cognac',
    'vodka': 'http://twinliquors.com/shop/catalogsearch/result/?q=vodka',
    'red_wine': 'http://twinliquors.com/shop/catalogsearch/result/?q=red+wine',
    'white_wine': 'http://twinliquors.com/shop/catalogsearch/result/?q=red+wine',
    'tequila': 'http://twinliquors.com/shop/catalogsearch/result/?q=tequila',
    'gin': 'http://twinliquors.com/shop/catalogsearch/result/?q=gin',
    'rum': 'http://twinliquors.com/shop/catalogsearch/result/?q=rum',
    'liquor': 'http://twinliquors.com/shop/catalogsearch/result/?q=liquor',
}


def getprice(pricestr):
    if not pricestr:
        return ''
    price = parse('${pound:d}.{pence:d}', pricestr)
    if not price:
        price = parse('${th:d},{pound:d}.{pence:d}', pricestr)
        return price.named['th'] * 100000 + price.named['pound'] * 100 + price.named['pence']
    return price.named['pound'] * 100 + price.named['pence']


# Category Scraping - with selenium - multiple pages per category (click on next page)
for ctg, url in urls_ctgs_dict.items():
    categories[ctg] = []
    number_of_pdcts_in_ctg = 0
    if not op.exists(fpath_namer(shop_id, 'ctg', ctg, 0)):
        # Getting to ctg url
        driver.get(url)
    for p in range(100):
        fpath = fpath_namer(shop_id, 'ctg', ctg, p)
        if not op.exists(fpath):
            driver.save_page(fpath)
            sleep(2)
        tree = etree.parse(open(fpath, 'rb'), parser=parser)
        for li in tree.xpath('//div[@class="col-main-content"]//ul/li'):
            produrl = li.xpath('.//h2[@class="product-name"]/a/@href')[0]
            produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
            products[produrl] = {
                'pdct_name_on_eretailer': "".join(li.xpath('.//h2[@class="product-name"]//text()')),
                'raw_price': ''.join(w for t in li.xpath('.//span[@class="price"]/text()') for w in t.split()).strip(),
            }
            print(products[produrl], produrl)
            products[produrl]['price'] = getprice(products[produrl]['raw_price'])
            print(products[produrl])
            categories[ctg].append(produrl)
        # Going to next page if need be
        next_page_click = '//a[@class="next i-next"]'
        if not op.exists(fpath_namer(shop_id, 'ctg', ctg, p+1)):
            if not driver.check_exists_by_xpath(next_page_click):
                break
            else:
                driver.waitclick(next_page_click)
    print(ctg, url, p, len(categories[ctg]))


# KW searches Scraping - with selenium - one page per search
search_url = "http://twinliquors.com/shop/catalogsearch/result/?q={kw}"
for kw in keywords:
    searches[kw] = []
    # Storing and extracting infos
    fpath = fpath_namer(shop_id, 'search', kw, 0)
    url = search_url.format(kw=kw, page=0)
    if not op.exists(fpath):
        driver.get(url)
        sleep(2)
        driver.save_page(fpath, scroll_to_bottom=True)
    tree = etree.parse(BytesIO(open(fpath, 'rb').read()), parser=parser)
    for li in tree.xpath('//div[@class="col-main-content"]//ul/li'):
        produrl = li.xpath('.//h2[@class="product-name"]/a/@href')[0]
        produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
        products[produrl] = {
            'pdct_name_on_eretailer': "".join(li.xpath('.//h2[@class="product-name"]//text()')),
            'raw_price': ''.join(w for t in li.xpath('.//span[@class="price"]/text()') for w in t.split()).strip(),
        }
        print(products[produrl], produrl)
        products[produrl]['price'] = getprice(products[produrl]['raw_price'])
        print(products[produrl])
        searches[kw].append(produrl)
    print(kw, len(searches[kw]))

# Download the pages - with requests
brm = BrandMatcher()
for url in sorted(list(set(products))):
    d = products[url]
    if brm.find_brand(d['pdct_name_on_eretailer'])['brand'] in mh_brands:
        url_mod = clean_url(url, root_url=root_url)
        print(d['pdct_name_on_eretailer'], url_mod, url)
        r = requests.get(url_mod, headers, verify=False)
        with open('/tmp/' + shop_id + ' ' + d['pdct_name_on_eretailer'].replace('/', "-") + '.html', 'wb') as f:
            f.write(r.content)
        tree = etree.parse(BytesIO(r.content), parser=parser)
        products[url].update({
            'volume': ' '.join(' '.join(tree.xpath('//div[@class="short-description"]//text()')[:1]).split()),
            'pdct_img_main_url': clean_url(''.join(tree.xpath('//a[@id="zoom1"]/@href')), root_url),
            'ctg_denom_txt': ' '.join(' '.join(tree.xpath('//div[@class="short-description"]//text()')).split()),
        })
        print(products[url])
        if not r.from_cache:
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
