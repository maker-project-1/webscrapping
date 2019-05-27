import os.path as op
from io import BytesIO

from lxml import etree

parser = etree.HTMLParser()
from time import sleep
from urllib.parse import urlsplit, parse_qs
import requests
import requests_cache, imghdr
from validators import validate_raw_files
from create_csvs import create_csvs

for p in range(100):from ers import all_keywords_usa as keywords, fpath_namer, mh_brands, clean_url, headers
from matcher import BrandMatcher
from ers import COLLECTION_DATE, file_hash, img_path_namer
import shutil
from custom_browser import CustomDriver
from parse import parse


# Init variables and assets
shop_id = 'stew_leonards'
root_url = 'https://danbury.stewswines.com/'
requests_cache.install_cache(fpath_namer(shop_id, 'requests_cache'))
country = 'USA'
searches, categories, products = {}, {}, {}
driver = CustomDriver(headless=False)


def getprice(pricestr):
    if not pricestr:
        return ""
    price = parse('${pound:d}.{pence:d}', pricestr)
    if not price:
        price = parse('${th:d},{pound:d}.{pence:d}', pricestr)
        return price.named['th'] * 100000 + price.named['pound'] * 100 + price.named['pence']
    return price.named['pound'] * 100 + price.named['pence']


urls_ctgs_dict = {
    'champagne': 'https://danbury.stewswines.com/wines/Champagne',
    'sparkling': 'https://danbury.stewswines.com/wines/Sparkling',
    'still_wines': 'https://danbury.stewswines.com/wines/?page={page}&sortby=sort_item_order&l=100&item_type=wine',
    'whisky': 'https://danbury.stewswines.com/spirits/Single-Malt-Scotch-Whisky',
    'cognac': 'https://danbury.stewswines.com/spirits/?varietal=Cognac&sortby=sort_item_order&item_type=spirits',
    'vodka': 'https://danbury.stewswines.com/spirits/Vodka?page={page}&varietal=Vodka&sortby=sort_item_order&item_type=spirits',
}


def init_site(driver):
    driver.get("https://danbury.stewswines.com/search/categories/Sparkling%20Wine/page/1")
    sleep(1)
    driver.waitclick('//button[@id="age-verified"]')
    sleep(1)

site_was_initialised = False


# Categories scraping
for ctg, url in urls_ctgs_dict.items():
    categories[ctg] = []
    number_of_pdcts_in_ctg = 0
    for p in range(100):
        print(ctg, p)
        fpath = fpath_namer(shop_id, 'ctg', ctg, p)
        print(fpath)
        if not op.exists(fpath):
            # if not site_was_initialised:
            #     init_site(driver)
            #     site_was_initialised = True
            driver.get(url.format(page=p+1))
            driver.save_page(fpath, scroll_to_bottom=True)

        # Parsing
        tree = etree.parse(open(fpath, 'rb'), parser=parser)
        for li in tree.xpath('//*[@class="product-list"]/div'):
            produrl = "".join(li.xpath('.//a[@class="rebl15"]/@href'))
            produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(
                urlsplit(produrl).query) else produrl

            produrl = clean_url(produrl, root_url)
            products[produrl] = {
                'pdct_name_on_eretailer': li.xpath('.//a[@class="rebl15"]/text()')[0].strip(),
                'volume': li.xpath('.//a[@class="rebl15"]/text()')[0].strip(),
                'price': getprice(''.join(li.xpath('.//span[@class="rd14"]//text()')).strip()),
                # 'promo_price': getprice(''.join(li.xpath('.//s[@class="regular-price"]//text()')).strip()),
            }
            # if not products[produrl]['price']:
            # products[produrl]['price'] = getprice(''.join(li.xpath('.//span[@class="price"]//text()')).strip())
            print(products[produrl], produrl)
            categories[ctg].append(produrl)

        if len(set(categories[ctg])) == number_of_pdcts_in_ctg:
            break
        else:
            number_of_pdcts_in_ctg = len(set(categories[ctg]))
print([(ctg, len(val)) for ctg, val in categories.items()])

# KW searches Scraping - with selenium - with nb page hard-coded in url - multiple page per search
search_url = "https://danbury.stewswines.com/websearch_results.html?page={page}&sortby=sort_item_order&l=100"
for kw in keywords:
    searches[kw] = []
    number_of_pdcts_in_kw_search = 0

    for p in range(10):
        # Storing and extracting infos
        fpath = fpath_namer(shop_id, 'search', kw, p)
        if not op.exists(fpath):
            # if not site_was_initialised:
            #     init_site(driver)
            #     site_was_initialised = True
            driver.get(search_url.format(kw=kw, page=p + 1))
            driver.save_page(fpath, scroll_to_bottom=True)

        # Parsing
        tree = etree.parse(open(fpath, 'rb'), parser=parser)
        for li in tree.xpath('//*[@class="product-list"]/div'):
            produrl = "".join(li.xpath('.//a[@class="rebl15"]/@href'))
            produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(
                urlsplit(produrl).query) else produrl

            produrl = clean_url(produrl, root_url)
            products[produrl] = {
                'pdct_name_on_eretailer': li.xpath('.//a[@class="rebl15"]/text()')[0].strip(),
                'volume': li.xpath('.//a[@class="rebl15"]/text()')[0].strip(),
                'price': getprice(''.join(li.xpath('.//span[@class="rd14"]//text()')).strip()),
                # 'promo_price': getprice(''.join(li.xpath('.//s[@class="regular-price"]//text()')).strip()),
            }
            # if not products[produrl]['price']:
            # products[produrl]['price'] = getprice(''.join(li.xpath('.//span[@class="price"]//text()')).strip())
            print(products[produrl], produrl)

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
            'ctg_denom_txt': products[url]['pdct_name_on_eretailer'],
            'pdct_img_main_url' : clean_url("".join(tree.xpath('//img[@itemprop="image"]/@src')[:1]), root_url),
        })
        if tree.xpath('//div[@class="product-image"]//img/@data-src'):
            products[url]['pdct_img_main_url'] = clean_url(tree.xpath('//div[@class="product-image"]//img/@data-src')[0], root_url)
        if tree.xpath('//div[@class="product-image"]//img/@src'):
            products[url]['pdct_img_main_url'] = clean_url(tree.xpath('//div[@class="product-image"]//img/@src')[0], root_url)

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
