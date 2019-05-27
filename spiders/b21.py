
import os.path as op
from io import BytesIO

from lxml import etree

parser = etree.HTMLParser()
from urllib.parse import urlsplit, parse_qs
import requests
import requests_cache, imghdr


from validators import validate_raw_files
from create_csvs import create_csvs
from ers import all_keywords_usa as keywords, fpath_namer, mh_brands, clean_url, headers
from matcher import BrandMatcher
from ers import COLLECTION_DATE, file_hash, img_path_namer
import shutil
import re
from custom_browser import CustomDriver

# Init variables and assets
shop_id = 'b21'
root_url = 'https://www.b-21.com/'
requests_cache.install_cache(fpath_namer(shop_id, 'requests_cache'))
country = 'USA'
searches, categories, products = {}, {}, {}
tmp_searches, tmp_categories = {}, {}
driver = CustomDriver(headless=False) # WARNING !! PLEASE use Chrome for this one


from parse import parse

def getprice(pricestr):
    if not pricestr:
        return
    pricestr = re.sub("[^0-9.$]", "", pricestr)
    price = parse('${pound:d}.{pence:d}', pricestr)
    if not price:
        price = parse('${th:d},{pound:d}.{pence:d}', pricestr)
        return price.named['th'] * 100000 + price.named['pound'] * 100 + price.named['pence']
    return price.named['pound'] * 100 + price.named['pence']


urls_ctgs_dict = {
    'sparkling': 'https://www.b-21.com/searchprods.asp?searchstring=sparkling&pagenumber={page}&val=0',
    'cognac': 'https://www.b-21.com/searchprods.asp?searchstring=cognac&pagenumber={page}&val=0',
    'champagne': 'https://www.b-21.com/searchprods.asp?searchstring=champagne&pagenumber={page}&val=0',
    'vodka': 'https://www.b-21.com/searchprods.asp?searchstring=vodka&pagenumber={page}&val=0',
    'whisky': 'https://www.b-21.com/searchprods.asp?searchstring=whisky&pagenumber={page}&val=0',
    'still_wines': 'https://www.b-21.com/searchprods.asp?searchstring=wine&pagenumber={page}&val=0',
    'red_wine': 'https://www.b-21.com/searchprods.asp?searchstring=red+wine&pagenumber={page}&val=0',
    'white_wine': 'https://www.b-21.com/searchprods.asp?searchstring=white+wine&pagenumber={page}&val=0',
    'tequila': 'https://www.b-21.com/searchprods.asp?searchstring=tequila&pagenumber={page}&val=0',
    'gin': 'https://www.b-21.com/searchprods.asp?searchstring=gin&pagenumber={page}&val=0',
    'rum': 'https://www.b-21.com/searchprods.asp?searchstring=rum&pagenumber={page}&val=0',
    'brandy': 'https://www.b-21.com/searchprods.asp?searchstring=brandy&pagenumber={page}&val=0',
}

for ctg, caturl in urls_ctgs_dict.items():
    categories[ctg] = []
    number_of_pdcts_in_ctg = 0
    req_sent = False
    if not op.exists(fpath_namer(shop_id, 'ctg', ctg, 1)):
        req_sent = True
        driver.get('https://www.b-21.com/')
        driver.text_input(ctg, '//input[@id="code"]', enter=True)
    for page in range(1, 100):
        url = caturl.format(page=page)
        fpath = fpath_namer(shop_id, 'ctg', ctg, page)
        if not op.exists(fpath) and req_sent:
            driver.smooth_scroll()
            driver.save_page(fpath, scroll_to_bottom=True)
        elif not op.exists(fpath) and not req_sent:
            break
        tree = etree.parse(open(fpath, 'rb'), parser=parser)
        for tr in tree.xpath('//div[contains(@class, "c data2")]/table[3]/tbody/tr'):
            if not tr.xpath('.//*[contains(@class, "prodstitle")]/@href'):
                continue
            produrl = tr.xpath('.//*[contains(@class, "prodstitle")]/@href')[0]
            produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
            produrl = clean_url(produrl, root_url)
            products[produrl] = {
                'volume': tr.xpath('.//*[contains(@class, "prodstitle")]/@title')[0],
                'pdct_name_on_eretailer': tr.xpath('.//*[contains(@class, "prodstitle")]/@title')[0],
                'raw_price': ''.join(tr.xpath('.//span[contains(@class, "prodsprice")]/text()')).strip(),
                'raw_promo_price': ''.join(tr.xpath('.//span[contains(@class, "prodsprice")]/s/text()')).strip(),
            }
            print(products[produrl], produrl)
            products[produrl]['price'] = getprice(products[produrl]['raw_price'])
            products[produrl]['promo_price'] = getprice(products[produrl]['raw_promo_price'])
            print(products[produrl])

            categories[ctg].append(produrl)
        if req_sent and not driver.waitclick('//div[contains(@class, "c data2")]/table[last()]//a[contains(text(),"{page}")]'.format(page=page+1)):
            break
    print(ctg, len(categories[ctg]))


######################################
# # KW searches scrapping ############
######################################

# KW searches Scraping - with requests - one page per search
kw_search_url = 'https://www.b-21.com/searchprods.asp?searchstring={kw}&pagenumber={page}&val=0'
for kw in keywords:
    searches[kw] = []
    number_of_pdcts_in_kw_search = 0
    req_sent = False

    if not op.exists(fpath_namer(shop_id, 'search', kw, 0)):
        req_sent = True
        driver.get('https://www.b-21.com/')
        driver.text_input(kw, '//input[@id="code"]', enter=True)

    for p in range(2):
        fpath = fpath_namer(shop_id, 'search', kw, 0)
        if not op.exists(fpath) and req_sent:
            driver.smooth_scroll()
            driver.save_page(fpath, scroll_to_bottom=True)
        elif not op.exists(fpath) and not req_sent:
            break
        tree = etree.parse(open(fpath, 'rb'), parser=parser)
        for tr in tree.xpath('//div[contains(@class, "c data2")]/table[3]/tbody/tr'):
            if not tr.xpath('.//*[contains(@class, "prodstitle")]/@href'):
                continue
            produrl = tr.xpath('.//*[contains(@class, "prodstitle")]/@href')[0]
            produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
            produrl = clean_url(produrl, root_url)
            products[produrl] = {
                'volume': tr.xpath('.//*[contains(@class, "prodstitle")]/@title')[0],
                'pdct_name_on_eretailer': tr.xpath('.//*[contains(@class, "prodstitle")]/@title')[0],
                'raw_price': ''.join(tr.xpath('.//span[contains(@class, "prodsprice")]/text()')).strip(),
                'raw_promo_price': ''.join(tr.xpath('.//span[contains(@class, "prodsprice")]/s/text()')).strip(),
            }
            print(products[produrl], produrl)
            products[produrl]['price'] = getprice(products[produrl]['raw_price'])
            products[produrl]['promo_price'] = getprice(products[produrl]['raw_promo_price'])
            print(products[produrl])

            searches[kw].append(produrl)
        if req_sent and not driver.waitclick('//div[contains(@class, "c data2")]/table[last()]//a[contains(text(),"{page}")]'.format(page=p+1)):
            break

    print(kw, len(searches[kw]))

# Download the pages - with selenium
brm = BrandMatcher()
for url in sorted(list(set(products))):
    d = products[url]
    if brm.find_brand(d['pdct_name_on_eretailer'])['brand'] in mh_brands:
        print(d['pdct_name_on_eretailer'], url)

        r = requests.get(url, headers)
        with open('/tmp/' + shop_id + ' ' + d['pdct_name_on_eretailer'].replace('/', "-") + '.html', 'wb') as f:
            f.write(r.content)
        tree = etree.parse(BytesIO(r.content), parser=parser)

        products[url].update({
            'pdct_img_main_url': clean_url(''.join(tree.xpath('//div[@class="thumb-image"]/img/@src')), root_url),
            'ctg_denom_txt': d['pdct_name_on_eretailer'],
            'volume': d['pdct_name_on_eretailer'],
        })
        print(products[url])


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
         else:
             print("Warning", img_path, pdt['pdct_img_main_url'])

create_csvs(products, categories, searches, shop_id, fpath_namer(shop_id, 'raw_csv'), COLLECTION_DATE)
validate_raw_files(fpath_namer(shop_id, 'raw_csv'))
