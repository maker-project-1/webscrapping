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
from parse import parse


# Init variables and assets
shop_id = "mel_rose"
root_url = "http://www.melandrose.com/" 
requests_cache.install_cache(fpath_namer(shop_id, 'requests_cache'))
country = "USA"
searches, categories, products = {}, {}, {}
# If necessary


def getprice(pricestr):
    if pricestr == '':
        return pricestr
    pricestr = re.sub("[^0-9.$]", "", pricestr)
    price = parse('${pound:d}.{pence:d}', pricestr)
    if price is None:
        price = parse('{pence:d}p', pricestr)
        return price.named['pence']
    else:
        return price.named['pound'] * 100 + price.named['pence']


urls_ctgs_dict = {'vodka': 'http://www.melandrose.com/istar.asp?a=3&dept=10&class=25&sortby=&numperpage=100&pos={page}',
                  'sparkling': 'http://www.melandrose.com/istar.asp?a=3&dept=3&class=3&sortby=&numperpage=100&pos={page}',
                  'cognac': 'http://www.melandrose.com/istar.asp?a=3&dept=10&class=6&sortby=&numperpage=100&pos={page}',
                  'champagne': 'http://www.melandrose.com/istar.asp?a=3&dept=3&class=1&sortby=&numperpage=100&pos={page}',
                  'still_wines': 'http://www.melandrose.com/istar.asp?a=3&dept=14&sortby=&numperpage=100&pos={page}',
                  'whisky': 'http://www.melandrose.com/istar.asp?a=3&dept=10&class=26&sortby=&numperpage=100&pos={page}',
                  'red_wine': 'http://www.melandrose.com/istar.asp?a=29&search=red+wine&sortby=&numperpage=100&pos={page}',
                  'white_wine': 'http://www.melandrose.com/istar.asp?a=29&search=white+wine&sortby=&numperpage=100&pos={page}',
                  'gin': 'http://www.melandrose.com/istar.asp?a=3&dept=10&class=7&sortby=&numperpage=100&pos={page}',
                  'tequila': 'http://www.melandrose.com/istar.asp?a=3&dept=10&class=23&sortby=&numperpage=100&pos={page}',
                  'rum': 'http://www.melandrose.com/istar.asp?a=3&dept=10&class=17&sortby=&numperpage=100&pos={page}',
                  'brandy': 'http://www.melandrose.com/istar.asp?a=3&dept=10&class=4&sortby=&numperpage=100&pos={page}',
                  }


# Category Scraping
for ctg, url in urls_ctgs_dict.items():
    categories[ctg] = []
    number_of_pdcts_in_ctg = 0
    for p in range(20):
        urlp = url.format(page=p*100)
        r = requests.get(urlp)
        with open('/tmp/' + shop_id + '_' + ctg + '.html', 'wb') as f:
            f.write(r.content)
        tree = etree.parse(BytesIO(r.content), parser=parser)
        
        for li in tree.xpath('//table[@class="istar browse-iconic"]//td[contains(@class, "tablerow1 content") and div]'):
            produrl = li.xpath('.//div[contains(@class, "shortdescription")]/a/@href')[0]
            produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
            produrl = clean_url(produrl, root_url)
            products[produrl] = {
                'pdct_name_on_eretailer': ' '.join(''.join(li.xpath('.//div[contains(@class, "shortdescription")]/a//text()')).split()).strip(),
                'raw_price': ' '.join(''.join(li.xpath('.//div[contains(@class, "regularprice")]/span//text()')).split()).strip(),
                'raw_promo_price': ' '.join(''.join(li.xpath('.//div[contains(@class, "regularprice")]/sqd//text()')).split()).strip(),
            }
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
print([(c, len(categories[c])) for c in categories])

# KW searches Scraping - with selenium - with nb page hard-coded in url - multiple page per search
search_url = "http://www.melandrose.com/istar.asp?a=29&search={kw}&sortby=&numperpage=100&pos={page}"
for kw in keywords:
    searches[kw] = []
    number_of_pdcts_in_kw_search = 0
    
    for p in range(10):
        # Storing and extracting infos
        urlp = search_url.format(kw=kw, page=p*100)

        r = requests.get(urlp)
        with open('/tmp/' + shop_id + " " + kw + '.html', 'wb') as f:
            f.write(r.content)
        tree = etree.parse(BytesIO(r.content), parser=parser)
        
        for li in tree.xpath('//table[@class="istar browse-iconic"]//td[contains(@class, "tablerow1 content") and div]'):
            produrl = li.xpath('.//div[contains(@class, "shortdescription")]/a/@href')[0]
            produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
            produrl = clean_url(produrl, root_url)
            products[produrl] = {
                'pdct_name_on_eretailer': ' '.join(''.join(li.xpath('.//div[contains(@class, "shortdescription")]/a//text()')).split()).strip(),
                'raw_price': ' '.join(''.join(li.xpath('.//div[contains(@class, "regularprice")]/span//text()')).split()).strip(),
                'raw_promo_price': ' '.join(''.join(li.xpath('.//div[contains(@class, "regularprice")]/sqd//text()')).split()).strip(),
            }
            print(products[produrl], produrl)
            products[produrl]['price'] = getprice(products[produrl]['raw_price'])
            products[produrl]['promo_price'] = getprice(products[produrl]['raw_promo_price'])
            print(products[produrl])
            
            searches[kw].append(produrl)
        if len(set(searches[kw])) == number_of_pdcts_in_kw_search:
            break
        else:
            number_of_pdcts_in_kw_search = len(set(searches[kw]))
        if not r.from_cache:
            sleep(2)
    print(kw, p, len(searches[kw]))


# Download the pages - with selenium
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
            'volume': ''.join(tree.xpath('//div[contains(@class, "departmenttext productHeader")]/span//text()')).strip(),
            'pdct_img_main_url': clean_url(''.join(tree.xpath('//input[@name="productPicture"]/@value')), root_url),
            'ctg_denom_txt': d['pdct_name_on_eretailer'],
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
