import re
from io import BytesIO

from lxml import etree

parser = etree.HTMLParser(encoding='utf-8')
from time import sleep
from urllib.parse import urlsplit, parse_qs
import requests
import requests_cache, imghdr
from ers import all_keywords_ch as keywords, fpath_namer, mh_brands, clean_url, headers

from matcher import BrandMatcher
from ers import COLLECTION_DATE, file_hash, img_path_namer
import shutil
from custom_browser import CustomDriver
from parse import parse
from validators import validate_raw_files
from create_csvs import create_csvs

# Init variables and assetssq
shop_id = "flaschenpost_ch"
root_url = "https://www.flaschenpost.ch"
requests_cache.install_cache(fpath_namer(shop_id, 'requests_cache'))
country = "CH"


searches, categories, products = {}, {}, {}
# If necessary
driver = CustomDriver(headless=False)



def getprice(pricestr):
    if pricestr == '':
        return pricestr
    pricestr = re.sub("[^0-9.chf]", "", pricestr.lower())
    price = parse('chf{pound:d}.{pence:d}', pricestr)
    if price is None:
        price = parse('{pence:d}p', pricestr)
        return price.named['pence']
    else:
        return price.named['pound'] * 100 + price.named['pence']



urls_ctgs_dict = {

    "champagne": "https://www.flaschenpost.ch/sortiment/gesamtsortiment.html?bx_products_sort=Champagner+und+Schaumwein&p={page}",
    "still_wines": "https://www.flaschenpost.ch/sortiment/gesamtsortiment.html?bx_di_grapes=Sauvignon+Blanc&p={page}",
    "red_wine": "https://www.flaschenpost.ch/sortiment/gesamtsortiment.html?sort=3685={page}",
    "white_wine": "https://www.flaschenpost.ch/sortiment/gesamtsortiment.html?sort=3688{page}",

}


# Category Scraping
for ctg, url in urls_ctgs_dict.items():
    categories[ctg] = []
    number_of_pdcts_in_ctg = 0
    for p in range(100):
        urlp = url.format(page=p+1)
        
        r = requests.get(urlp)
        with open('/tmp/' + shop_id + '_' + ctg + '.html', 'wb') as f:
            f.write(r.content)
        tree = etree.parse(BytesIO(r.content), parser=parser)
        
        for li in tree.xpath('//li[@itemtype="http://schema.org/Product"]'):
            produrl = li.xpath('.//a/@href')[0]
            produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
            produrl = clean_url(produrl, root_url)
            products[produrl] = {
                'pdct_name_on_eretailer': ' '.join(''.join(li.xpath('.//*[@itemprop="name"]//text()')).split()),
                'volume': ' '.join(''.join(li.xpath('.//span[@class="volume"]//text()')).split()).replace('(', '').replace(')', ''),
                'raw_price': ' '.join(''.join(li.xpath('.//span[contains(@class, "price") and contains(@id, "product-price")]//text()')).split()),
                'raw_promo_price': ' '.join(''.join(li.xpath('.//p[@class="old-price"]//text()')).split()),
                'ctg_denom_txt': ' '.join(''.join(li.xpath('.//*[@itemprop="name"]//text()')).split()),
                'pdct_img_main_url': li.xpath('.//a[@class="product-image"]/img[@class="lazy"]/@data-original')[:1],
            }
            if products[produrl]['pdct_img_main_url']:
                products[produrl]['pdct_img_main_url'] = products[produrl]['pdct_img_main_url'][0].replace(
                    "small_image/x300/17f82f742ffe127f42dca9de82fb58b1",
                    "image/9df78eab33525d08d6e5fb8d27136e95"
                )
            else:
                products[produrl]['pdct_img_main_url'] = ""
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
        if not r.from_cache:
            sleep(2)
print(categories)

# KW searches Scraping - with selenium - with nb page hard-coded in url - multiple page per search
search_url = "https://www.flaschenpost.ch/catalogsearch/result/index/?p={page}&q={kw}"
for kw in keywords:
    searches[kw] = []
    number_of_pdcts_in_kw_search = 0
    
    for p in range(10):
        # Storing and extracting infos
        urlp = search_url.format(kw=kw,page=p+1).replace(' ', '+')

        r = requests.get(urlp)
        with open('/tmp/' + shop_id + '_' + kw + '.html', 'wb') as f:
            f.write(r.content)
        tree = etree.parse(BytesIO(r.content), parser=parser)
        #
        # fpath = fpath_namer(shop_id, 'search', kw, p)
        # if not op.exists(fpath):
        #     driver.get(urlp)
        #     sleep(2)
        #     driver.save_page(fpath)
        # tree = etree.parse(BytesIO(open(fpath, 'rb').read()), parser=parser)

        for li in tree.xpath('//li[@itemtype="http://schema.org/Product"]'):
            produrl = li.xpath('.//a/@href')[0]
            produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
            produrl = clean_url(produrl, root_url)
            products[produrl] = {
                'pdct_name_on_eretailer': ' '.join(''.join(li.xpath('.//*[@itemprop="name"]//text()')).split()),
                'volume': ' '.join(''.join(li.xpath('.//span[@class="volume"]//text()')).split()).replace('(', '').replace(')', ''),
                'raw_price': ' '.join(''.join(li.xpath('.//span[contains(@class, "price") and contains(@id, "product-price")]//text()')).split()),
                'raw_promo_price': ' '.join(''.join(li.xpath('.//p[@class="old-price"]//text()')).split()),
                'ctg_denom_txt': ' '.join(''.join(li.xpath('.//*[@itemprop="name"]//text()')).split()),
                'pdct_img_main_url': li.xpath('.//a[@class="product-image"]/img[@class="lazy"]/@data-original')[:-1],
            }
            print(products[produrl], produrl)
            if products[produrl]['pdct_img_main_url']:
                products[produrl]['pdct_img_main_url'] = products[produrl]['pdct_img_main_url'][0].replace(
                    "small_image/x300/17f82f742ffe127f42dca9de82fb58b1",
                    "image/9df78eab33525d08d6e5fb8d27136e95"
                )
            else:
                products[produrl]['pdct_img_main_url'] = ""
            print(products[produrl], produrl)
            products[produrl]['price'] = getprice(products[produrl]['raw_price'])
            products[produrl]['promo_price'] = getprice(products[produrl]['raw_promo_price'])
            print(products[produrl])

            searches[kw].append(produrl)
        if len(set(searches[kw])) == number_of_pdcts_in_kw_search:
            break
        else:
            number_of_pdcts_in_kw_search = len(set(searches[kw]))
        if r.from_cache:
            sleep(2)
    print(kw, p, len(searches[kw]))


# Download images
brm = BrandMatcher()
l_products = []
for url, pdt in products.items():
    if pdt['pdct_name_on_eretailer'] in l_products:
        continue
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

        l_products.append(pdt['pdct_name_on_eretailer'])

create_csvs(products, categories, searches, shop_id, fpath_namer(shop_id, 'raw_csv'), COLLECTION_DATE)
validate_raw_files(fpath_namer(shop_id, 'raw_csv'))
driver.quit()


