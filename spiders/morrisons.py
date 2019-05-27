import os.path as op
from io import BytesIO

from lxml import etree

parser = etree.HTMLParser()
from time import sleep
import requests_cache, imghdr
from validators import validate_raw_files
from create_csvs import create_csvs
from urllib.parse import urlsplit, parse_qs

from ers import all_keywords_uk as keywords, mh_brands, clean_url
from matcher import BrandMatcher
from ers import COLLECTION_DATE, file_hash, img_path_namer, fpath_namer
import shutil
from custom_browser import CustomDriver
import requests

# Init variables and assets
shop_id = 'morrisons'
root_url = 'https://groceries.morrisons.com'
session = requests_cache.CachedSession(fpath_namer(shop_id, 'requests_cache'))
country = 'UK'
searches, categories, products = {}, {}, {}
driver = CustomDriver(headless=True)

from parse import parse


def getprice(pricestr):
    if not pricestr:
        return
    price = parse('£{pound:d}', pricestr)
    if price:
        return price.named['pound'] * 100
    price = parse('£{pound:d}.{pence:d}', pricestr)
    if price:
        return price.named['pound'] * 100 + price.named['pence']
    price = parse('£{th:d},{pound:d}.{pence:d}', pricestr)
    if price:
        return price.named['th'] * 100000 + price.named['pound'] * 100 + price.named['pence']


urls_ctgs_dict = {
    'champagne': 'https://groceries.morrisons.com/webshop/getCategories.do?tags=%7C105651%7C103120%7C152226%7C154006%7C159995&Asidebar=1',
    'sparkling': 'https://groceries.morrisons.com/webshop/getCategories.do?tags=%7C105651%7C103120%7C152226%7C154006%7C159998&Asidebar=1',
    'still_wines': 'https://groceries.morrisons.com/webshop/getCategories.do?tags=%7C105651%7C103120%7C152391%7C160120&Asidebar=3',
    'whisky': 'https://groceries.morrisons.com/webshop/getCategories.do?tags=%7C105651%7C103120%7C105916%7C151509&Asidebar=3',
    'cognac': 'https://groceries.morrisons.com/webshop/getCategories.do?tags=%7C105651%7C103120%7C105916%7C151517&Asidebar=3',
    'vodka': 'https://groceries.morrisons.com/webshop/getCategories.do?tags=%7C105651%7C103120%7C105916%7C151525&Asidebar=3',
    'red_wine': 'https://groceries.morrisons.com/webshop/getCategories.do?tags=%7C105651%7C103120%7C152226%7C160014&Asidebar=1',
    'white_wine': 'https://groceries.morrisons.com/webshop/getCategories.do?tags=%7C105651%7C103120%7C152226%7C160038&Asidebar=1',
    'gin': 'https://groceries.morrisons.com/webshop/getCategories.do?tags=%7C105651%7C103120%7C105916%7C151526&Asidebar=1',
    'brandy': 'https://groceries.morrisons.com/webshop/getCategories.do?tags=%7C105651%7C103120%7C105916%7C151517&Asidebar=1',
    'rum': 'https://groceries.morrisons.com/webshop/getCategories.do?tags=%7C105651%7C103120%7C105916%7C151520&Asidebar=1',
    'liquor': 'https://groceries.morrisons.com/webshop/getCategories.do?tags=%7C105651%7C103120%7C105916%7C151516&Asidebar=1',
}

for ctg, url in urls_ctgs_dict.items():
    categories[ctg] = []
    number_of_pdcts_in_ctg = 0

    for p in range(1):
        fpath = fpath_namer(shop_id, 'ctg', ctg, p)
        if not op.exists(fpath):
            driver.get(url)
            sleep(2)
            driver.smooth_scroll(10)
            driver.save_page(fpath, scroll_to_bottom=True)
        tree = etree.parse(BytesIO(open(fpath, 'rb').read()), parser=parser)

        for li in tree.xpath('//ul[contains(@class, "fops-shelf")]/li[@class="fops-item"]'):
            if not li.xpath('.//a/@href') or not li.xpath('.//h4//text()'):
                continue
            produrl = li.xpath('.//a/@href')[0]
            produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(
                urlsplit(produrl).query) else produrl
            produrl = clean_url(produrl, root_url)
            products[produrl] = {
                'pdct_name_on_eretailer': li.xpath('.//h4//text()')[0].strip(),
                'raw_price': li.xpath('.//*[contains(@class, "fop-price")]//text()')[0].strip(),
                'raw_promo_price': "".join(li.xpath('.//span[contains(@class, "fop-old-price")]//text()')[:1]).strip(),
                'volume': ''.join(li.xpath('.//span[@class="fop-catch-weight"]/text()'))
            }
            print(products[produrl], produrl)
            products[produrl]['price'] = getprice(products[produrl]['raw_price'])
            products[produrl]['promo_price'] = getprice(products[produrl]['raw_promo_price'])
            print(products[produrl])

            categories[ctg].append(produrl)

        # # Checking if it was the last page
        # if len(set(categories[ctg])) == number_of_pdcts_in_ctg:
        #     break
        # else:
        #     number_of_pdcts_in_ctg = len(set(categories[ctg]))
print([(c, len(categories[c])) for c in categories])

# KW searches Scraping - with selenium - with nb page hard-coded in url - multiple page per search
search_url = "https://groceries.morrisons.com/webshop/getSearchProducts.do?clearTabs=yes&isFreshSearch=true&chosenSuggestionPosition=&entry={kw}"
for kw in keywords:
    print("KW = ", kw)
    searches[kw] = []
    number_of_pdcts_in_kw_search = 0

    # Storing and extracting infos
    urlp = search_url.format(kw=kw)

    fpath = fpath_namer(shop_id, 'search', kw, 0)
    if not op.exists(fpath):
        driver.get(urlp)
        sleep(2)
        driver.save_page(fpath, scroll_to_bottom=True)
    tree = etree.parse(BytesIO(open(fpath, 'rb').read()), parser=parser)

    for li in tree.xpath('//ul[contains(@class, "fops-shelf")]/li[@class="fops-item"]'):
        if not li.xpath('.//a/@href') or not li.xpath('.//h4//text()'):
            continue
        produrl = li.xpath('.//a/@href')[0]
        produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(
            urlsplit(produrl).query) else produrl
        produrl = clean_url(produrl, root_url)
        products[produrl] = {
            'pdct_name_on_eretailer': "".join(li.xpath('.//h4//text()')[:1]).strip(),
            'raw_price': " ".join(li.xpath('.//*[contains(@class, "fop-price")]//text()')[:1]).strip(),
            'raw_promo_price': "".join(li.xpath('.//span[contains(@class, "fop-old-price")]//text()')[:1]).strip(),
            'volume': ''.join(li.xpath('.//span[@class="fop-catch-weight"]/text()'))
        }
        print(products[produrl], produrl)
        products[produrl]['price'] = getprice(products[produrl]['raw_price'])
        products[produrl]['promo_price'] = getprice(products[produrl]['raw_promo_price'])
        print(products[produrl])
        searches[kw].append(produrl)

    print(kw, len(searches[kw]))

brm = BrandMatcher()
for url, product in products.items():
    if brm.find_brand(product['pdct_name_on_eretailer'])['brand'] in mh_brands:
        r = session.get(url)
        print('/tmp/' + shop_id + ' ' + product['pdct_name_on_eretailer'].replace('/', "-") + '.html')
        with open('/tmp/' + shop_id + ' ' + product['pdct_name_on_eretailer'].replace('/', "-") + '.html', 'wb') as f:
            f.write(r.content)
        tree = etree.parse(BytesIO(r.content), parser=parser)
        data = {
            'pdct_img_main_url': clean_url("".join(tree.xpath('//div[@class="zoomInner"]/img/@src')[:1]), root_url),
            'ctg_denom_txt': ''.join(tree.xpath('//ul[@class="categories"]//h4/a/text()')),
        }
        product.update(data)

# print("warning : no pagination, limit to 50, np for champagne, cognac, etc")
# print(products)

# Download images
for url, pdt in products.items():
     if 'pdct_img_main_url' in pdt and pdt['pdct_img_main_url'] and brm.find_brand(pdt['pdct_name_on_eretailer'])['brand'] in mh_brands:
         print(pdt['pdct_name_on_eretailer'] + "." + pdt['pdct_img_main_url'].split('.')[-1])
         response = requests.get(pdt['pdct_img_main_url'], stream=True, verify=False)
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
