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

from ers import all_keywords_uk as keywords, fpath_namer, mh_brands, clean_url, headers
from matcher import BrandMatcher
from ers import COLLECTION_DATE, file_hash, img_path_namer
import shutil
from parse import parse

# Init variables and assets
shop_id = 'harrods'
root_url = 'https://www.harrods.com/'
requests_cache.install_cache(fpath_namer(shop_id, 'requests_cache'))
country = 'UK'
searches, categories, products = {}, {}, {}

urls_ctgs_dict = {
    'champagne': 'https://www.harrods.com/en-gb/food-and-wine/wine-and-spirits/champagne-and-sparkling?view=Product&list=List&viewAll=True',
    'sparkling': 'https://www.harrods.com/en-gb/food-and-wine/wine-and-spirits/champagne-and-sparkling?view=Product&list=List&viewAll=True',
    'still_wines': 'https://www.harrods.com/en-gb/food-and-wine/wine-and-spirits/white-wine?view=Product&list=List&viewAll=True',
    'whisky': 'https://www.harrods.com/en-gb/food-and-wine/wine-and-spirits/spirits?view=Product&list=List&viewAll=True&categoryFilterIds=34605',
    'cognac':'https://www.harrods.com/en-gb/food-and-wine/wine-and-spirits/spirits?view=Product&list=List&viewAll=True&categoryFilterIds=23692',
    'vodka': 'https://www.harrods.com/en-gb/food-and-wine/wine-and-spirits/spirits?view=Product&list=List&viewAll=True&categoryFilterIds=23688',
}

cookies = {'ctry': 'UK', 'curr': 'GBP'}


def getprice(pricestr):
    if pricestr == '' or pricestr == '£':
        return ''
    pricestr = pricestr.replace(',', '').strip()
    price = parse('£{pound:d}.{pence:d}', pricestr)
    if price is None:
        price = parse('{pence:d}p', pricestr)
        return price.named['pence']
    else:
        return price.named['pound'] * 100 + price.named['pence']


# Change the Currency
session = requests.session()
session.get(urls_ctgs_dict['champagne'], cookies=cookies)
data = [
  ('CountryCode', 'GB'),
  ('ddlItemCheckboxddl5aok', '64'),
  ('ddlItemCheckboxddl0nmb', '19'),
  ]
session.post('https://www.harrods.com/en-gb/countrycurrencyselector', headers=headers, cookies=cookies, data=data)
cookies = session.cookies.get_dict()
print(cookies)
# cookies.update({'ctry': 'UK', 'curr': 'GBP'})


# Category Scraping
for ctg, url in urls_ctgs_dict.items():
    categories[ctg] = []
    number_of_pdcts_in_ctg = 0
    r = session.get(url, cookies=cookies, headers=headers)
    with open('/tmp/' + shop_id + '_' + ctg + '.html', 'wb') as f:
        f.write(r.content)
    tree = etree.parse(BytesIO(r.content), parser=parser)
    for li in tree.xpath('//li[@class="product-grid_item"]'):
        produrl = li.xpath('.//a[contains(@class, "product-card_link")]/@href')[0]
        produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
        produrl = clean_url(produrl, root_url)
        categories[ctg].append(produrl)
        products[produrl] = {
            'pdct_name_on_eretailer': ' '.join([li.xpath('.//span[@class="product-card_brand"]//text()')[0],
                                       li.xpath('.//span[@class="product-card_name"]//text()')[0]]),
            'raw_price': '£' + ''.join(w for t in li.xpath('.//span[@class="price_amount"]/@content') for w in t.split()).strip(),
        }
        print(products[produrl], produrl)
        products[produrl]['price'] = getprice(products[produrl]['raw_price'])
        assert all(products[produrl][k] for k in products[produrl])
    if not r.from_cache:
        sleep(3)
    print(ctg, len(categories[ctg]))


# Keywords scraping
for kw in keywords:
    searches[kw] = []
    kw_search_url = "https://www.harrods.com/en-gb/search?searchTerm={kw}"
    print(kw, kw_search_url.format(kw=kw))
    r = session.get(kw_search_url.format(kw=kw), cookies=cookies)
    tree = etree.parse(BytesIO(r.content), parser=parser)
    for li in tree.xpath('//li[@class="product-grid_item"]'):
        produrl = li.xpath('.//a[contains(@class, "product-card_link")]/@href')[0]
        produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
        produrl = clean_url(produrl, root_url)
        searches[kw].append(produrl)
        products[produrl] = {
            'pdct_name_on_eretailer': ' '.join([li.xpath('.//span[@class="product-card_brand"]//text()')[0],
                                       li.xpath('.//span[@class="product-card_name"]//text()')[0]]),
            'raw_price': '£' + ''.join(w for t in li.xpath('.//span[@class="price_amount"]/@content') for w in t.split()).strip(),
        }
        print(kw, products[produrl])
        products[produrl]['price'] = getprice(products[produrl]['raw_price'])
        print(kw, products[produrl])
    assert all(products[produrl][k] for k in products[produrl])
    if not r.from_cache:
        sleep(3)
    print(kw, len(searches[kw]))

# Download the pages
brm = BrandMatcher()
for url in sorted(products):
    d = products[url]
    if brm.find_brand(d['pdct_name_on_eretailer'])['brand'] in mh_brands:
        print(d['pdct_name_on_eretailer'])
        url_mod = clean_url(url, root_url=root_url)
        r = session.get(url_mod, cookies=cookies)
        with open('/tmp/' + shop_id + ' ' + d['pdct_name_on_eretailer'].replace('/', "-") + '.html', 'wb') as f:
            f.write(r.content)
        tree = etree.parse(BytesIO(r.content), parser=parser)
        products[url] = {
            'pdct_name_on_eretailer': ' '.join(w for t in tree.xpath('//h1[@class="buying-controls_title"]//text()') for w in t.split()).strip(),
            'volume': ''.join(tree.xpath('//span[contains(@id, "productSize")]//text()')).strip(),
            'raw_price': ' '.join(w for t in tree.xpath('//section[@class="pdp_buying-controls"]//div[@class="price"]//text()') for w in t.split()).strip(),
            # 'raw_promo_price': ''.join(tree.xpath('//span[@class="product-action__price-text"]//fdsfdsf//text()')), # No because mix 6
            'pdct_img_main_url': clean_url(''.join(tree.xpath('//section[@class="pdp_images"]//img/@src')), root_url),
            'ctg_denom_txt': ' '.join(' '.join(tree.xpath('//section[@class="breadcrumb"]//text()')).split()),
        }
        products[url]['price'] = getprice(products[url]['raw_price'])
        print(products[url])

        if not r.from_cache:
            sleep(3)



# Download images
for url, pdt in products.items():
     if 'pdct_img_main_url' in pdt and pdt['pdct_img_main_url']:
         print(pdt['pdct_name_on_eretailer'] + "." + pdt['pdct_img_main_url'].split('.')[-1])
         response = requests.get(pdt['pdct_img_main_url'], stream=True, verify=False)
         # response.raw.decode_content = True
         tmp_file_path = '/tmp/mhers_tmp_{}.img'.format(abs(hash(pdt['pdct_img_main_url'])))
         img_path = img_path_namer(shop_id, pdt['pdct_name_on_eretailer'])
         with open(tmp_file_path, 'wb') as out_file:
             shutil.copyfileobj(response.raw, out_file)
         if imghdr.what(tmp_file_path) is not None:
             img_path = img_path.split('.')[0] + '.' + imghdr.what('/tmp/mhers_tmp_{}.img'.format(abs(hash(pdt['pdct_img_main_url']))))
             shutil.copyfile('/tmp/mhers_tmp_{}.img'.format(abs(hash(pdt['pdct_img_main_url']))), img_path)
             products[url].update({'img_path': img_path, 'img_hash': file_hash(img_path)})

create_csvs(products, categories, searches, shop_id, fpath_namer(shop_id, 'raw_csv'), COLLECTION_DATE)
validate_raw_files(fpath_namer(shop_id, 'raw_csv'))