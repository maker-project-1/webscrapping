from lxml import etree
from io import BytesIO
from io import BytesIO

from lxml import etree

parser = etree.HTMLParser(encoding='utf-8')
from time import sleep
from urllib.parse import urlsplit, parse_qs
import requests
import requests_cache
from validators import validate_raw_files
from create_csvs import create_csvs
from ers import all_keywords_uk as keywords, fpath_namer, mh_brands, clean_url, headers
from matcher import BrandMatcher
from ers import COLLECTION_DATE, file_hash
from parse import parse
from ers import img_path_namer
from ers import clean_xpathd_text

# Init variables and assets
shop_id = '31dover'
root_url = 'https://www.31dover.com/'
requests_cache.install_cache(fpath_namer(shop_id, 'requests_cache'))

country = 'UK'
searches, categories, products = {}, {}, {}


def getprice(pricestr):
    if not pricestr:
        return None
    pricestr = pricestr.replace(',', '')
    price = parse('£{pound:d}.{pence:d}', pricestr)
    if price is None:
        price = parse('{pence:d}p', pricestr)
        return price.named['pence']
    else:
        return price.named['pound'] * 100 + price.named['pence']


# Ctg scrapping
urls_ctgs_dict = {
    'champagne': 'http://www.31dover.com/champagne/filter/page/1/show/all.html',
    'cognac': 'http://www.31dover.com/spirits/cognac-brandy/filter/page/1/show/all.html',
    'whisky': 'http://www.31dover.com/spirits/whisky/filter/page/1/show/all.html',
    'still_wines': 'http://www.31dover.com/wines/filter/page/1/show/all.html',
    'sparkling': 'http://www.31dover.com/champagne/sparkling/filter/page/1/show/all.html',
    'vodka': 'http://www.31dover.com/spirits/vodka/filter/page/1/show/all.html',
    'gin': 'https://www.31dover.com/spirits/gin/filter/show/all.html',
    'tequila': 'https://www.31dover.com/spirits/tequila/filter/show/all.html',
    'red_wine': 'https://www.31dover.com/wines/red-wine/filter/show/all.html',
    'white_wine': 'https://www.31dover.com/wines/white-wine/filter/show/all.html',
    'rum': 'https://www.31dover.com/spirits/rum/filter/show/all.html',
}


# Category Scraping
for ctg, url in urls_ctgs_dict.items():
    categories[ctg] = []
    number_of_pdcts_in_ctg = 0
    for p in range(200):
        urlp = url.format(page=p)
        r = requests.get(urlp)
        tree = etree.parse(BytesIO(r.content), parser=parser)
        with open('/tmp/' + ctg.replace('/', "-") + '.html', 'wb') as f:
            print('/tmp/' + ctg.replace('/', "-") + '.html')
            f.write(r.content)
        for li in tree.xpath('//ul[contains(@class, "product")]/li[contains(@class, "item")]'):
            if not li.xpath('.//div/h2/a/@href'):
                continue
            produrl = li.xpath('.//div/h2/a/@href')[0]
            produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
            categories[ctg].append(produrl)
            products[produrl] = {
                'pdct_name_on_eretailer': li.xpath('.//div/h2/a/text()')[0],
                'raw_price': ''.join(w for t in li.xpath('.//div[@class="price-box"]//span[@class="price"]/text()')[0] for w in t.split()).strip(),
                'raw_promo_price': clean_xpathd_text(li.xpath('.//p[@class="special-price"]//text()')[:1]),
                'currency': '£',
            }
            products[produrl]['price'] = getprice(products[produrl]['raw_price'])
            products[produrl]['promo_price'] = getprice(products[produrl]['raw_promo_price'])
        if len(set(categories[ctg])) == number_of_pdcts_in_ctg:
            break
        else:
            number_of_pdcts_in_ctg = len(set(categories[ctg]))
        if not r.from_cache:
            sleep(3)
    print(ctg, len(categories[ctg]))

assert len(products) > 100


#  Search scraping
kw_search_url = "https://shop.31dover.com/search?p=Q&lbc=31dover&uid=318224614&w={kw}&af=&isort=score&method=and&view=grid&af=&ts=infinitescroll"
for kw in keywords:
    searches[kw] = []
    for p in range(10):
        print(kw, p)
        nbdone = len(products)
        url = kw_search_url.format(kw=kw)
        urlp = url + ('&srt=' + str(p * 32) if p else '')
        r = requests.get(urlp)
        with open('/tmp/' + shop_id + ' ' + kw + '.html', 'wb') as f:
            f.write(r.content)
        tree = etree.parse(BytesIO(r.content), parser=parser)
        for li in tree.xpath('//ul[contains(@class, "product")]//li[@class="item"]'):
            produrl = li.xpath('.//h2/a/@href')[0]
            produrl = parse_qs(urlsplit(produrl).query)['url'][0]
            searches[kw].append(produrl)
            products[produrl] = {
                'pdct_name_on_eretailer': li.xpath('.//div/h2/a/text()')[0],
                'raw_price': ''.join(w for t in li.xpath('.//div[@class="price-box"]//span[@class="price"]/text()')[0] for w in t.split()).strip(),
                'raw_promo_price': clean_xpathd_text(li.xpath('.//p[@class="special-price"]//text()')[:1]),
                'currency': '£',
            }
            products[produrl]['raw_price'] = ''.join(
                w for t in li.xpath('.//div[@class="price-box"]//span[@class="price"]/text()')[:1] for w in
                t.split()).strip()
            products[produrl]['price'] = getprice(products[produrl]['raw_price'])
            products[produrl]['promo_price'] = getprice(products[produrl]['raw_promo_price'])

        if nbdone == len(products):
            break
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

        products[url].update({
            'pdct_name_on_eretailer': ' '.join(w for t in tree.xpath('//div[contains(@class,"product-name")]/h1//text()') for w in t.split()).strip(),
            'volume': ' '.join(tree.xpath('//ul[@class="ingredients"]//text()')),
            # 'raw_price': ''.join(w for t in tree.xpath('//*[contains(@id, "product-price-")]//text()') for w in t.split()).strip(),
            'raw_promo_price': ''.join(tree.xpath('//*[contains(@id, "old-price-")]//text()')),
            'pdct_img_main_url': ''.join(tree.xpath('//*[@class="product-img-box"]//a[@id="zoom1"]/@href')),
            'ctg_denom_txt': ' '.join(tree.xpath('//div[@class="grid-full breadcrumbs"]//text()')),
        })

        if not r.from_cache:
            sleep(3)
        # print(products[url]['pdct_name_on_eretailer'], products[url]['raw_price'], products[url]['pdct_img_main_url'])
        print(products[url]['pdct_img_main_url'])


# Download images
from ers import download_img

for url, pdt in products.items():
    if 'pdct_img_main_url' in pdt and pdt['pdct_img_main_url'] and brm.find_brand(pdt['pdct_name_on_eretailer'])['brand'] in mh_brands:
        print(pdt['pdct_name_on_eretailer'] + "." + pdt['pdct_img_main_url'].split('.')[-1])
        orig_img_path = img_path_namer(shop_id, pdt['pdct_name_on_eretailer'])
        img_path = download_img(pdt['pdct_img_main_url'], orig_img_path, shop_id=shop_id, decode_content=False, gzipped=False, debug=False)
        if img_path:
            products[url].update({'img_path': img_path, 'img_hash': file_hash(img_path)})


create_csvs(products, categories, searches, shop_id, fpath_namer(shop_id, 'raw_csv'), COLLECTION_DATE)
validate_raw_files(fpath_namer(shop_id, 'raw_csv'))

