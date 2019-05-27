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
shop_id = 'wine_anthology'
root_url = 'https://www.wineanthology.com'
requests_cache.install_cache(fpath_namer(shop_id, 'requests_cache'))
country = 'USA'
searches, categories, products = {}, {}, {}
driver = CustomDriver(headless=True, download_images=False)

driver.get(root_url)


def getprice(pricestr):
    if not pricestr:
        return None
    print('pricestr', pricestr)
    price = parse('${pound:d}.{pence:d}', pricestr)
    if not price:
        price = parse('${th:d},{pound:d}.{pence:d}', pricestr)
        if not price:
            price = parse('${pound:d}', pricestr)
            return price.named['pound'] * 100
        return price.named['th'] * 100000 + price.named['pound'] * 100 + price.named['pence']
    return price.named['pound'] * 100 + price.named['pence']


urls_ctgs_dict = {
    'champagne': 'https://www.wineanthology.com/c-4-france.aspx?pagenum={page}&search=&min=&max=&priceidx=&vintage=&grape=&region=&type=Champagne&sort=0',
    'sparkling': 'https://www.wineanthology.com/c-185-varietal.aspx?pagenum={page}&search=&min=&max=&priceidx=&vintage=&grape=&region=&type=Sparkling%20Wine&sort=0',
    'still_wines': 'https://www.wineanthology.com/c-2-wine.aspx?pagenum={page}&search=&min=&max=&priceidx=&vintage=&grape=Sauvignon%20Blanc&region=&type=&sort=0',
    'whisky': 'https://www.wineanthology.com/c-550-whiskey.aspx?pagenum={page}&sort=0',
    'cognac': 'https://www.wineanthology.com/c-528-cognac.aspx?pagenum={page}&sort=0',
    'vodka': 'https://www.wineanthology.com/c-540-vodka.aspx?pagenum={page}&sort=0',
    'red_wine': 'https://www.wineanthology.com/c-2-wine.aspx?term=red%20wine&pagenum={page}&sort=0',
    'white_wine': 'https://www.wineanthology.com/c-2-wine.aspx?term=white%20wine&pagenum={page}&sort=0',
    'gin': 'https://www.wineanthology.com/c-2-wine.aspx?term=gin&pagenum={page}&sort=0',
    'rum': 'https://www.wineanthology.com/c-2-wine.aspx?term=rum&pagenum={page}&sort=0',
    'tequila': 'https://www.wineanthology.com/c-2-wine.aspx?term=tequila&pagenum={page}&sort=0',
    'brandy': 'https://www.wineanthology.com/c-2-wine.aspx?term=brandy&pagenum={page}&sort=0',
    'liquor': 'https://www.wineanthology.com/c-2-wine.aspx?term=liquor&pagenum={page}&sort=0',
}


# Category Scraping - with requests - multiple pages per category
for ctg, url in urls_ctgs_dict.items():
    categories[ctg] = []
    number_of_pdcts_in_ctg = 0
    for p in range(100):
        urlp = url.format(page=p+1)
        fpath = fpath_namer(shop_id, 'ctg', ctg, p)
        if not op.exists(fpath):
            driver.get(urlp)
            driver.wait_for_xpath('//div[@id="productResults"]//div[contains(@class, "product-list-item")]//div[contains(@class, "product-hover")]', timeout=5)
            driver.save_page(fpath, scroll_to_bottom=True)
        tree = etree.parse(BytesIO(open(fpath, 'rb').read()), parser=parser)
        for li in tree.xpath('//div[@id="productResults"]//div[contains(@class, "product-list-item")]//div[contains(@class, "product-hover")]'):
            produrl = li.xpath('.//a/@href')[0]
            produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(
                urlsplit(produrl).query) else produrl
            produrl = clean_url(produrl, root_url)
            products[produrl] = {
                'pdct_name_on_eretailer': ''.join(li.xpath('.//a[@class="list-item-name-link product-list-item-name-link"]//text()')).strip(),
                'raw_promo_price': ''.join(w for t in li.xpath('.//li[contains(@class, "wa_regular_price")]//text()') for w in t.split()).strip(),
                'raw_price': ''.join(w for t in li.xpath('.//li[contains(@class, "wa_sale_price")]//text()') for w in t.split()).strip(),

            }
            # print(products[produrl], produrl)
            products[produrl]['price'] = getprice(products[produrl]['raw_price'].replace('SoldOut', ''))
            products[produrl]['promo_price'] = getprice(products[produrl]['raw_promo_price'])
            print(products[produrl])
            categories[ctg].append(produrl)

        # Checking if it was the last page
        if len(set(categories[ctg])) == number_of_pdcts_in_ctg:
            break
        else:
            number_of_pdcts_in_ctg = len(set(categories[ctg]))

    print(ctg, len(categories[ctg]))


# KW searches Scraping - with selenium - with nb page hard-coded in url - multiple page per search
search_url = "https://www.wineanthology.com/search.aspx?searchterm={kw}&pagenum={page}"
for kw in keywords:
    searches[kw] = []
    number_of_pdcts_in_kw_search = 0
    for p in range(10):
        urlp = search_url.format(kw=kw, page=p+1)
        fpath = fpath_namer(shop_id, 'search', kw)
        if not op.exists(fpath):
            driver.get(urlp)
            driver.wait_for_xpath('//div[@id="productResults"]//div[contains(@class, "product-list-item")]//div[contains(@class, "product-hover")]', timeout=10)
            driver.save_page(fpath, scroll_to_bottom=True)
        tree = etree.parse(BytesIO(open(fpath, 'rb').read()), parser=parser)
        for li in tree.xpath('//div[contains(@class, "search-page-products")]//div[contains(@class, "product-list-item")]//div[contains(@class, "product-hover")]'):
            produrl = li.xpath('.//a/@href')[0]
            produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(
                urlsplit(produrl).query) else produrl
            produrl = clean_url(produrl, root_url)
            products[produrl] = {
                'pdct_name_on_eretailer': ''.join(li.xpath('.//a[@class="list-item-name-link product-list-item-name-link"]//text()')).strip(),
                'raw_promo_price': ''.join(w for t in li.xpath('.//li[contains(@class, "wa_regular_price")]//text()') for w in t.split()).strip(),
                'raw_price': ''.join(w for t in li.xpath('.//li[contains(@class, "wa_sale_price")]//text()') for w in t.split()).strip(),
            }
            # print(products[produrl], produrl)
            products[produrl]['price'] = getprice(products[produrl]['raw_price'].replace('SoldOut', ''))
            products[produrl]['promo_price'] = getprice(products[produrl]['raw_promo_price'])
            print(products[produrl])
            searches[kw].append(produrl)
        if len(set(searches[kw])) == number_of_pdcts_in_kw_search:
            break
        else:
            number_of_pdcts_in_kw_search = len(set(searches[kw]))
    print(kw, p, len(searches[kw]))


# Download the pages - with requests
brm = BrandMatcher()
for url in sorted(list(set(products))):
    d = products[url]
    if brm.find_brand(d['pdct_name_on_eretailer'])['brand'] in mh_brands:
        print(d['pdct_name_on_eretailer'])
        url_mod = clean_url(url, root_url=root_url)
        r = requests.get(url_mod, headers)
        with open('/tmp/' + shop_id + ' ' + d['pdct_name_on_eretailer'].replace('/', "-") + '.html', 'wb') as f:
            f.write(r.content)
        tree = etree.parse(BytesIO(r.content), parser=parser)
        products[url].update({
            'volume': ' '.join(' '.join(tree.xpath('//tr[./th="Size:"]/td/text()')[:1]).split()),
            'pdct_img_main_url': clean_url(''.join(tree.xpath('//div[@class="medium-image-wrap"]/img/@src')), root_url).replace('medium', 'large'),
            'ctg_denom_txt': ' '.join(' '.join(tree.xpath('//div[@class="breadcrumb"]//text()')).split()),
        })
        print(products[url])
        if not r.from_cache:
            sleep(3)

# Download images
for url, pdt in products.items():
     if 'pdct_img_main_url' in pdt and pdt['pdct_img_main_url'] and brm.find_brand(pdt['pdct_name_on_eretailer'])['brand'] in mh_brands:
         print(pdt['pdct_name_on_eretailer'] + "." + pdt['pdct_img_main_url'].split('.')[-1])
         print(pdt['pdct_img_main_url'])
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
