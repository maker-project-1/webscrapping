from lxml import etree
from io import BytesIO
from io import BytesIO

from lxml import etree

parser = etree.HTMLParser(encoding='utf-8')
from time import sleep
from urllib.parse import urlsplit, parse_qs
import requests
import requests_cache, imghdr
from parse import parse
from validators import validate_raw_files
from create_csvs import create_csvs


from ers import all_keywords_uk as keywords
from ers import fpath_namer, mh_brands, clean_url
from matcher import BrandMatcher
from ers import COLLECTION_DATE, file_hash, img_path_namer
import shutil


# Init variables and assets
shop_id = 'the_whisky_exchange'
root_url = 'https://www.thewhiskyexchange.com'
requests_cache.install_cache(fpath_namer(shop_id, 'requests_cache'))
country = 'UK'
searches, categories, products = {}, {}, {}

urls_ctgs_dict = {
    'champagne': 'https://www.thewhiskyexchange.com/c/330/champagne?pg={page}#productlist-filter',
    'sparkling': 'https://www.thewhiskyexchange.com/c/581/sparkling-wine?pg={page}#productlist-filter',
    'still_wines': 'https://www.thewhiskyexchange.com/c/644/wine?filter=true&rfdata=~type.White&pg={page}#productlist-filter',
    'whisky': 'https://www.thewhiskyexchange.com/c/304/blended-scotch-whisky?pg={page}#productlist-filter',
    'cognac':'https://www.thewhiskyexchange.com/c/351/cognac?pg={page}#productlist-filter',
    'vodka': 'https://www.thewhiskyexchange.com/c/335/vodka?pg={page}#productlist-filter',
    'red_wine': 'https://www.thewhiskyexchange.com/c/644/wine?pg={page}&filter=true&rfdata=~type.Red#productlist-filter',
    'white_wine': 'https://www.thewhiskyexchange.com/c/644/wine?pg={page}&filter=true&rfdata=~type.White#productlist-filter',
    'gin': 'https://www.thewhiskyexchange.com/c/338/gin?pg={page}&filter=true#productlist-filter',
    'tequila': 'https://www.thewhiskyexchange.com/c/359/tequila?pg={page}&filter=true#productlist-filter',
    'rum': 'https://www.thewhiskyexchange.com/c/339/rum?pg={page}&filter=true#productlist-filter',
    'brandy': 'https://www.thewhiskyexchange.com/c/367/brandy-and-marc?pg={page}&filter=true#productlist-filter',
}


headers = {
    'cookie': 'twe-site-ccsettings=countrycode=gb&currencycode=gbp&vatprice=true; rtwe_sorting=expr=pasc; rtwe_viewmode=mode=grid; rtwe_paging=pagesize=200; __utma=233136347.943212255.1512512485.1512512485.1512512485.1; __utmb=233136347.4.10.1512512485; __utmc=233136347; __utmz=233136347.1512512485.1.1.utmcsr=google|utmccn=(organic)|utmcmd=organic|utmctr=(not%20provided); _uetsid=_uet3cd097fd',
    'dnt': '1',
    'accept-encoding': 'gzip, deflate, br',
    'accept-language': 'en-US,en;q=0.9',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/62.0.3202.94 Chrome/62.0.3202.94 Safari/537.36',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'cache-control': 'max-age=0',
    'authority': 'www.thewhiskyexchange.com',
    'referer': 'https://www.thewhiskyexchange.com/c/518/golden-rum',
}

def getprice(pricestr):
    if pricestr == '':
        return pricestr
    pricestr = pricestr.replace(',', '').strip()
    price = parse('£{pound:d}.{pence:d}', pricestr)
    if price is None:
        price = parse('£{pound:d}', pricestr)
        if price is None:
            price = parse('{pence:d}p', pricestr)
            return price.named['pence']
        else:
            return price.named['pound'] * 100
    else:
        return price.named['pound'] * 100 + price.named['pence']


# Category Scraping
for ctg, url in urls_ctgs_dict.items():
    categories[ctg] = []
    number_of_pdcts_in_ctg = 0
    for p in range(100):
        urlp = url.format(page=p+1)
        r = requests.get(urlp, headers=headers)
        tree = etree.parse(BytesIO(r.content), parser=parser)
        for li in tree.xpath('//div[@class="products-wrapper"]//div[@class="item"]'):
            produrl = li.xpath('./a/@href')[0]
            produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
            categories[ctg].append(produrl)
            products[produrl] = {
                'pdct_name_on_eretailer': li.xpath('.//div[@class="name"]//text()')[0],
                'raw_price': ''.join(w for t in li.xpath('.//span[@class="price"]//text()') for w in t.split()).strip(),
            }
            # print(ctg, p, products[produrl])
            products[produrl]['price'] = getprice(products[produrl]['raw_price'])
            assert all(products[produrl][k] for k in products[produrl])
        if len(set(categories[ctg])) == number_of_pdcts_in_ctg:
            break
        else:
            number_of_pdcts_in_ctg = len(set(categories[ctg]))
        if not r.from_cache:
            sleep(3)
    print(ctg, len(categories[ctg]))

assert len(products) > 100

#  Search scraping
for kw in keywords:
    searches[kw] = []
    kw_search_url = "https://www.thewhiskyexchange.com/search?q={kw}"
    r = requests.get(kw_search_url.format(kw=kw))
    tree = etree.parse(BytesIO(r.content), parser=parser)
    for li in tree.xpath('//div[@class="products-wrapper"]//div[@class="item"]'):
        produrl = li.xpath('./a/@href')[0]
        produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
        searches[kw].append(produrl)
        products[produrl] = {
            'pdct_name_on_eretailer': li.xpath('.//div[@class="name"]//text()')[0],
            'raw_price': ''.join(w for t in li.xpath('.//span[@class="price"]//text()') for w in t.split()).strip(),
        }
        # print(kw, products[produrl])
        products[produrl]['price'] = getprice(products[produrl]['raw_price'])
    if not r.from_cache:
        sleep(3)
assert sum(len(searches[kw]) for kw in searches) > 100


# Download the pages
brm = BrandMatcher()
for url in sorted(products):
    d = products[url]
    if brm.find_brand(d['pdct_name_on_eretailer'])['brand'] in mh_brands:
        url_mod = clean_url(url, root_url=root_url)
        r = requests.get(url_mod, headers)
        with open('/tmp/' + shop_id + ' ' + d['pdct_name_on_eretailer'].replace('/', "-") + '.html', 'wb') as f:
            f.write(r.content)
        tree = etree.parse(BytesIO(r.content), parser=parser)
        products[url] = {
            'pdct_name_on_eretailer': ''.join(tree.xpath('//h1[@itemprop="name"]//text()')),
            'volume': ''.join(''.join(tree.xpath('//span[@class="strength"]//text()')).split('/')[:1]),
            'raw_price': ''.join(tree.xpath('//div[@class="price-content"]/span[@class="price"]//text()')),
            'raw_promo_price': ''.join(tree.xpath('//span[@class="was"]//text()')).replace("(Was ", "").replace(')', ''),
            'pdct_img_main_url': ''.join(tree.xpath('//*[@id="productDefaultImage"]/img/@data-original')),
            # 'pdct_img_main_url': clean_url(''.join(tree.xpath('//*[@id="productDefaultImage"]/img/@src')), root_url),
            'ctg_denom_txt': ''.join(tree.xpath('//ul[@class="breadcrumb__list"]//text()')),
        }
        print(d['pdct_name_on_eretailer'], products[url])
        products[url]['price'] = getprice(products[url]['raw_price'])
        products[url]['promo_price'] = getprice(products[url]['raw_promo_price'])
        print(d['pdct_name_on_eretailer'], products[url])


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