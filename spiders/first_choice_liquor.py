from lxml import etree
from io import BytesIO
from io import BytesIO

from lxml import etree

parser = etree.HTMLParser(encoding='utf-8')
from time import sleep
from urllib.parse import urlsplit, parse_qs
import requests
import requests_cache, imghdr

from validators import validate_raw_files
from create_csvs import create_csvs

from ers import all_keywords_aus as keywords, fpath_namer, mh_brands, clean_url, headers
from matcher import BrandMatcher
from ers import COLLECTION_DATE, file_hash, img_path_namer
import shutil
from parse import parse


# Init variables and assets
shop_id = 'first_choice_liquor'
root_url = 'https://www.firstchoiceliquor.com.au'
requests_cache.install_cache(fpath_namer(shop_id, 'requests_cache'))
country = 'AUS'
searches, categories, products = {}, {}, {}

def getprice(pricestr):
    if pricestr == '':
        return pricestr
    pricestr = pricestr.replace(',', '').strip()
    price = parse('${dol:d}.{pence:d}', pricestr)
    if price is None:
        price = parse('{pence:d}p', pricestr)
        return price.named['pence']
    else:
        return price.named['dol'] * 100 + price.named['pence']


urls_ctgs_dict = {
            'champagne': 'https://www.firstchoiceliquor.com.au/Sparkling?facets=region%3dChampagne&show=500',
            'sparkling': 'https://www.firstchoiceliquor.com.au/Sparkling?show=500',
            'still_wines': 'https://www.firstchoiceliquor.com.au/White%20Wine?show=500',
            'whisky': 'https://www.firstchoiceliquor.com.au/Spirits?facets=spiritproducttype%3dMalt+Scotch+Whisky&show=500',
            'cognac':'https://www.firstchoiceliquor.com.au/Spirits?facets=spiritproducttype%3dMalt+Scotch+Whisky&show=500',
            'vodka': 'https://www.firstchoiceliquor.com.au/Spirits?facets=spiritproducttype%3dVodka&show=500',
            'rum': 'https://www.firstchoiceliquor.com.au/Spirits?facets=spiritproducttype%3dRum+-+Dark&show=500',
            'liquor': 'https://www.firstchoiceliquor.com.au/Spirits?facets=spiritproducttype%3dImported+Liqueurs&show=500',
}

# Category Scraping - with requests - one page per category
for ctg, url in urls_ctgs_dict.items():
    categories[ctg] = []
    r = requests.get(url)
    tree = etree.parse(BytesIO(r.content), parser=parser)
    for li in tree.xpath('//ul[@class="productList"]/li'):
        produrl = li.xpath('.//a/@href')[0]
        produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
        produrl = clean_url(produrl, root_url)
        products[produrl] = {
            'pdct_name_on_eretailer': ''.join(li.xpath('.//h2//text()')).strip(),
            'raw_price': ''.join(w for t in li.xpath('(.//span[contains(@class, "price ")])[last()]//text()') for w in t.split()).strip(),
        }
        # print(products[produrl], produrl)
        products[produrl]['price'] = getprice(products[produrl]['raw_price'])
        # print(products[produrl])
        assert all(products[produrl][k] for k in products[produrl])

        categories[ctg].append(produrl)
    if not r.from_cache:
        sleep(3)
    print(ctg, len(categories[ctg]))



# KW searches Scraping - with requests - one page per search
kw_search_url = "https://www.firstchoiceliquor.com.au/Search?q={kw}&show=500"
for kw in keywords:
    searches[kw] = []
    url = kw_search_url.format(kw=kw)
    r = requests.get(url)
    tree = etree.parse(BytesIO(r.content), parser=parser)
    for li in tree.xpath('//ul[@class="productList"]/li'):
        produrl = li.xpath('.//a/@href')[0]
        produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
        produrl = clean_url(produrl, root_url)
        products[produrl] = {
            'pdct_name_on_eretailer': ''.join(li.xpath('.//h2//text()')).strip(),
            'raw_price': ''.join(w for t in li.xpath('(.//span[contains(@class, "price ")])[last()]//text()') for w in t.split()).strip(),
        }
        # print(products[produrl], produrl)
        products[produrl]['price'] = getprice(products[produrl]['raw_price'])
        # print(products[produrl])
        assert all(products[produrl][k] for k in products[produrl])
        searches[kw].append(produrl)
    assert all(products[produrl][k] for k in products[produrl])
    if not r.from_cache:
        sleep(3)
    print(kw, len(searches[kw]))


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
            'volume': d['pdct_name_on_eretailer'],
            'pdct_img_main_url': clean_url(''.join(tree.xpath('//div[@class="fullImg"]/img/@src')), root_url),
            'ctg_denom_txt': ' '.join(' '.join(tree.xpath('//ul[@class="breadcrumbs"]//text()')).split()),
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
