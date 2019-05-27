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

from ers import all_keywords_fr as keywords, fpath_namer, mh_brands, clean_url, headers
from matcher import BrandMatcher
from ers import COLLECTION_DATE, file_hash, img_path_namer
import shutil
from parse import parse

# Init variables and assets
shop_id = 'nicolas'
root_url = 'http://www.nicolas.com'
requests_cache.install_cache(fpath_namer(shop_id, 'requests_cache'))
country = 'FR'
searches, categories, products = {}, {}, {}


def getprice(pricestr):
    pricestr = pricestr.replace(' ', '')
    if pricestr == '':
        return pricestr
    price = parse('{dol:d},{pence:d}€', pricestr)
    if price is None:
        price = parse('{dol:d},€{pence:d}', pricestr)
        if price is None:
            price = parse('{dol:d}€', pricestr)
            return price.named['dol'] * 100
        return price.named['dol'] * 100 + price.named['pence']
    else:
        return price.named['dol'] * 100 + price.named['pence']



# CTG scrapping
urls_ctgs_dict = {
    'champagne': 'http://www.nicolas.com/fr/Champagne/c/02/?q=%3Arelevance&page={page}&show=All',
    'sparkling': 'http://www.nicolas.com/fr/Mousseux-and-Cremants/c/0202/?q=%3Arelevance&page={page}&show=All',
    'still_wines': 'http://www.nicolas.com/fr/Wines/c/01/?q=%3Arelevance&page={page}&show=All',
    'whisky': 'http://www.nicolas.com/fr/Liquors/Whisky/c/0312/?q=%3Arelevance&page={page}&show=All',
    'cognac': 'http://www.nicolas.com/fr/Liquors/c/03/?q=%3Arelevance%3AregionCode%3ACOGNAC&page={page}&show=All',
    'vodka': 'http://www.nicolas.com/fr/Spiritueux/Vodka/c/0308/?q=%3Arelevance&page={page}&show=All',
    'red_wine': 'https://www.nicolas.com/fr/Vins/Vin-Rouge/c/0111/?q=%3Arelevance&page={page}&show=All',
    'white_wine': 'https://www.nicolas.com/fr/Vins/Vin-Blanc/c/0106/?q=%3Arelevance&page={page}&show=All',
    'gin': 'https://www.nicolas.com/fr/Spiritueux/Gin/c/0307/?q=%3Arelevance&page={page}&show=All',
    'rum': 'https://www.nicolas.com/fr/Spiritueux/Rhum/c/0311/?q=%3Arelevance&page={page}&show=All',
    'liquor': 'https://www.nicolas.com/fr/Spiritueux/Liqueur/c/0306/?q=%3Arelevance&page={page}&show=All',
}



# Category Scraping
for ctg, url in urls_ctgs_dict.items():
    categories[ctg] = []
    number_of_pdcts_in_ctg = 0
    for p in range(100):
        urlp = url.format(page=p)
        r = requests.get(urlp)
        print(p, ctg)
        with open('/tmp/' + shop_id + '_' + ctg + '.html', 'wb') as f:
            print('/tmp/' + ctg + '.html')
            f.write(r.content)
        tree = etree.parse(BytesIO(r.content), parser=parser)
        for li in tree.xpath('//div[@class="ns-ListingProduct-item " and not(div[contains(@class, "--catalog")])]'):
            produrl = li.xpath('.//div[@class="ns-Product "]/a/@href')[0]
            produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(
                urlsplit(produrl).query) else produrl
            categories[ctg].append(produrl)
            products[produrl] = {
                'pdct_name_on_eretailer': li.xpath('.//figcaption[@class="ns-Product-title"]//text()')[0],
                'raw_price': ''.join(w for t in li.xpath('.//*[@class="ns-Product-priceContainer"]/span[contains(@class, "ns-Product-price") and not(contains(@class, "loyalityPrice"))]//text()') for w in t.split()).strip(),
                'raw_promo_price': ''.join(w for t in li.xpath('.//div[contains(@class, "strikePrice") and not(contains(@class, "loyalityPrice"))]//text()') for w in t.split()).strip(),
            }
            products[produrl]['raw_price'] = products[produrl]['raw_price'].replace(products[produrl]['raw_promo_price'], '')
            # products[produrl]['raw_price'] =
            # assert all(products[produrl][k] for k in products[produrl])
            print(products[produrl], produrl)
            products[produrl]['price'] = getprice(products[produrl]['raw_price'])
            products[produrl]['promo_price'] = getprice(products[produrl]['raw_promo_price'])
            print(products[produrl])

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
    kw_search_url = "http://www.nicolas.com/fr/search/?sort=relevance&q={kw}%3Arelevance&show=All#"
    r = requests.get(kw_search_url.format(kw=kw))
    tree = etree.parse(BytesIO(r.content), parser=parser)
    for li in tree.xpath('//div[@class="ns-ListingProduct-item " and not(div[contains(@class, "--catalog")])]'):
        produrl = li.xpath('.//div[@class="ns-Product "]/a/@href')[0]
        produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(
            urlsplit(produrl).query) else produrl
        searches[kw].append(produrl)
        products[produrl] = {
            'pdct_name_on_eretailer': li.xpath('.//figcaption[@class="ns-Product-title"]//text()')[0],
            'raw_price': ''.join(w for t in li.xpath(
                './/*[@class="ns-Product-priceContainer"]/span[contains(@class, "ns-Product-price") and not(contains(@class, "loyalityPrice"))]//text()')
                                 for w in t.split()).strip(),
            'raw_promo_price': ''.join(w for t in li.xpath(
                './/div[contains(@class, "strikePrice") and not(contains(@class, "loyalityPrice"))]//text()') for w in
                                       t.split()).strip(),
        }
        print(products[produrl], produrl)
        products[produrl]['price'] = getprice(products[produrl]['raw_price'])
        products[produrl]['promo_price'] = getprice(products[produrl]['raw_promo_price'])
        print(products[produrl])
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
            # 'pdct_name_on_eretailer': ' '.join(w for t in tree.xpath('//h1[@class="ns-Product-title"]//text()') for w in t.split()).strip(),
            'volume': ''.join(tree.xpath('//p[@class="ns-Product-bottle"]//text()')),
            # 'raw_price': ''.join(w for t in tree.xpath('//div[@class="ns-ProductDetails-infosRight"]//span[@class="ns-Price ns-Product-price "]//text()') for w in t.split()).strip(),
            # 'raw_promo_price': ''.join(tree.xpath('//span[@content="ns-Price ns-Product-price "]/csqcsqc//text()')),
            'pdct_img_main_url': ''.join(tree.xpath('//div/figure/img/@src')),
            'ctg_denom_txt': ' '.join(tree.xpath('//ol[@class="ns-Breadcrumb "]//text()')),
        })
        if not r.from_cache:
            sleep(3)
        print(products[url]['pdct_name_on_eretailer'], products[url]['volume'],
              products[url]['raw_price'], products[url]['pdct_img_main_url'])

from pprint import pprint
pprint(products)

# df = pd.DataFrame.from_dict(products, "index")
# df['url'] = df.index
# df.reset_index(level=0, inplace=True)
# test_products_df(df, country, strict=True)


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
