
import os.path as op
import re
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
shop_id = "wine_com"
root_url = "http://www.wine.com/" 
requests_cache.install_cache(fpath_namer(shop_id, 'requests_cache'))
country = "USA"


searches, categories, products = {}, {}, {}
# If necessary
driver = CustomDriver(headless=True)



def getprice(pricestr):
    print(pricestr)
    if pricestr == '':
        return pricestr
    pricestr = re.sub("[^0-9.$]", "", pricestr)
    price = parse('${pound:d}.{pence:d}', pricestr)
    if price is None:
        price = parse('{pence:d}p', pricestr)
        if price is None:
            price = parse('${dol:d}', pricestr)
            return price.named['dol'] * 100
        else:
            return price.named['pence']
    else:
        return price.named['pound'] * 100 + price.named['pence']




urls_ctgs_dict = {
    "champagne": "http://www.wine.com/v6/wineshop/list.aspx?N=7155+123+102+2331&state=CA&pagelength=100", 
    "still_wines": "https://www.wine.com/list/wine/white-wine/7155-125?pagelength=100", 
    "sparkling": "http://www.wine.com/v6/Champagne-and-Sparkling/wine/list.aspx?N=7155+123&pagelength=100",
    "red_wine": "https://www.wine.com/list/wine/red-wine/7155-124?showOutOfStock=false&pagelength=100",
    "white_wine": "https://www.wine.com/list/wine/white-wine/7155-125?showOutOfStock=false&pagelength=100",
}


# Category Scraping
for ctg, url in urls_ctgs_dict.items():
    categories[ctg] = []

    fpath = fpath_namer(shop_id, 'ctg', ctg, 0)
    if not op.exists(fpath):
        driver.get(url)
        sleep(1)
        driver.save_page(fpath, scroll_to_bottom=True)
    tree = etree.parse(BytesIO(open(fpath, 'rb').read()), parser=parser)
        
    # r = requests.get(urlp)
    # with open('/tmp/' + shop_id + '_' + ctg + '.html', 'wb') as f:
    #     f.write(r.content)
    # tree = etree.parse(BytesIO(r.content), parser=parser)
        
    for li in tree.xpath('//div[@class="prodItemInfo"]'):
        produrl = li.xpath('.//a[contains(@class, "prodItemInfo_link")]/@href')[0]
        produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
        produrl = clean_url(produrl, root_url)
        products[produrl] = {
            'pdct_name_on_eretailer': ' '.join(''.join(li.xpath('.//span[@class="prodItemInfo_name"]//text()')).split()),
            'raw_price': ' '.join(''.join(li.xpath('.//div[@class="productPrice_price-sale"]//text()')).split()),
            'raw_promo_price': ' '.join(''.join(li.xpath('.//div[@class="productPrice_price-reg has-strike"]//text()')).split()),
        }
        print(products[produrl], produrl)
        if not products[produrl]['raw_price']:
            products[produrl]['raw_price'] = ' '.join(''.join(li.xpath('.//div[@class="productPrice_price-reg"]//text()')).split())
        # print("resr", products[produrl]['raw_price'].strip())
        products[produrl]['price'] = getprice('$' + products[produrl]['raw_price'].replace(' ', '.')) if products[produrl]['raw_price'].strip() else ''
        if products[produrl]['raw_promo_price']:
            products[produrl]['promo_price'] = getprice('$' + products[produrl]['raw_promo_price'].replace(' ', '.'))
        else:
            products[produrl]['promo_price'] = ''
        print(products[produrl])

        categories[ctg].append(produrl)

        # if not r.from_cache:
        #     sleep(2)
print([(c, len(categories[c])) for c in categories])


# KW searches Scraping - with selenium - with nb page hard-coded in url - multiple page per search
search_url = "https://www.wine.com/search/{kw}"
for kw in keywords:
    searches[kw] = []

    r = requests.get(search_url.format(kw=kw))
    with open('/tmp/' + shop_id + '_' + kw + '.html', 'wb') as f:
        f.write(r.content)
    tree = etree.parse(BytesIO(r.content), parser=parser)

    for li in tree.xpath('//div[@class="prodItemInfo"]'):
        produrl = li.xpath('.//a[contains(@class, "prodItemInfo_link")]/@href')[0]
        produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(
            urlsplit(produrl).query) else produrl
        produrl = clean_url(produrl, root_url)
        products[produrl] = {
            'pdct_name_on_eretailer': ' '.join(
                ''.join(li.xpath('.//span[@class="prodItemInfo_name"]//text()')).split()),
            'raw_price': ' '.join(''.join(li.xpath('.//div[@class="productPrice_price-sale"]//text()')).split()),
            'raw_promo_price': ' '.join(
                ''.join(li.xpath('.//div[@class="productPrice_price-reg has-strike"]//text()')).split()),
        }
        print(products[produrl], produrl)
        if not products[produrl]['raw_price']:
            products[produrl]['raw_price'] = ' '.join(
                ''.join(li.xpath('.//div[@class="productPrice_price-reg"]//text()')).split())
        products[produrl]['price'] = getprice('$' + products[produrl]['raw_price'].replace(' ', '.'))  if products[produrl]['raw_price'].strip() else ''
        if products[produrl]['raw_promo_price']:
            products[produrl]['promo_price'] = getprice(
                '$' + products[produrl]['raw_promo_price'].replace(' ', '.'))
        else:
            products[produrl]['promo_price'] = ''
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
        
        # fname = fpath_namer(shop_id, 'pdct', d['pdct_name_on_eretailer'], 0)
        # if not op.exists(fname):
        #     driver.get(url_mod)
        #     sleep(2)
        #     driver.save_page(fname, scroll_to_bottom=True)
        # tree = etree.parse(open(fname), parser=parser)
        
        r = requests.get(url_mod, headers)
        with open('/tmp/' + shop_id + '_' + d['pdct_name_on_eretailer'].replace('/', "-") + '.html', 'wb') as f:
            f.write(r.content)
        tree = etree.parse(BytesIO(r.content), parser=parser)
        
        products[url].update({
            'volume': ' '.join(''.join(tree.xpath('//section/div/div/h1//text()')).split()),
            'pdct_img_main_url': clean_url(''.join(tree.xpath('//div/picture//img/@src')[:1]), root_url),
            'ctg_denom_txt': ' '.join(' '.join(tree.xpath('//div[@class="viewMoreModule_text"]//text()')).split()),
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
