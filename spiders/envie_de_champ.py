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

from ers import fpath_namer, mh_brands, clean_url, headers
from matcher import BrandMatcher
from ers import COLLECTION_DATE, file_hash, img_path_namer
import shutil
from parse import parse


# Init variables and assets
shop_id = 'envie_de_champ'
root_url = 'https://www.enviedechamp.com'
requests_cache.install_cache(fpath_namer(shop_id, 'requests_cache'))
country = 'FR'
searches, categories, products = {}, {}, {}


def getprice(pricestr):
    pricestr = pricestr.replace(' ', '')
    if pricestr == '':
        return pricestr
    price = parse('{dol:d},{pence:d}€', pricestr)
    if price is None:
        price = parse('{dol:d}€', pricestr)
        return price.named['dol'] * 100
    else:
        return price.named['dol'] * 100 + price.named['pence']


urls_ctgs_dict = {
            'champagne': 'https://www.enviedechamp.com/fr/champagnes-prix-31-50',
        }

# Category Scraping - with requests - one page per category
for ctg, url in urls_ctgs_dict.items():
    categories[ctg] = []
    r = requests.get(url)
    tree = etree.parse(BytesIO(r.content), parser=parser)
    with open('/tmp/test.html', 'wb') as f:
        f.write(r.content)
    for li in tree.xpath('//li/div[@class="block"]'):
        produrl = li.xpath('.//div[@class="protext"]/h2/a/@href')[0]
        produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
        produrl = clean_url(produrl, root_url)
        products[produrl] = {
            'pdct_name_on_eretailer': " ".join(li.xpath('.//div[@class="protext"]/h2/a//text()')),
            'raw_promo_price': ''.join(w for t in li.xpath('.//span/span[@class="reduction_with_tax"]//text()') for w in t.split()).strip().replace('/btl', ''),
            'raw_price':
                ' '.join(w for t in li.xpath('.//strong/span[@class="withtax_price"]//text()') for w in t.split()).strip()
                    .replace('Au lieu de ', '').replace('/btl', ''),
        }
        print(products[produrl], produrl)
        products[produrl]['price'] = getprice(products[produrl]['raw_price'])
        products[produrl]['promo_price'] = getprice(products[produrl]['raw_promo_price'])
        print(products[produrl])

        categories[ctg].append(produrl)
    if not r.from_cache:
        sleep(3)
    print(ctg, len(categories[ctg]))


# Category Scraping -
ctg = 'champagne'
other_champagne_ctg_url = ['https://www.enviedechamp.com/fr/champagnes-prix-21-30',
                           'https://www.enviedechamp.com/fr/champagnes-prix-51-75',
                           'https://www.enviedechamp.com/fr/champagnes-prix-76-150',
                           'https://www.enviedechamp.com/fr/champagnes-prix-151-999999999']
for url in other_champagne_ctg_url:
    r = requests.get(url)
    tree = etree.parse(BytesIO(r.content), parser=parser)
    with open('/tmp/' + shop_id + '_champagne' + url.split('/')[-1] + '.html', 'wb') as f:
        f.write(r.content)
    for li in tree.xpath('//li/div[@class="block"]'):
        produrl = li.xpath('.//div[@class="protext"]/h2/a/@href')[0]
        produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
        produrl = clean_url(produrl, root_url)
        products[produrl] = {
            'pdct_name_on_eretailer': " ".join(li.xpath('.//div[@class="protext"]/h2/a//text()')),
            'raw_promo_price': ''.join(w for t in li.xpath('.//span/span[@class="reduction_with_tax"]//text()') for w in t.split()).strip().replace('/btl', ''),
            'raw_price':
                ' '.join(w for t in li.xpath('.//strong/span[@class="withtax_price"]//text()') for w in t.split()).strip()
                    .replace('Au lieu de ', '').replace('/btl', ''),
        }
        print(products[produrl], produrl)
        products[produrl]['price'] = getprice(products[produrl]['raw_price'])
        products[produrl]['promo_price'] = getprice(products[produrl]['raw_promo_price'])
        print(products[produrl])

        categories[ctg].append(produrl)
    if not r.from_cache:
        sleep(3)
    print(ctg, len(categories[ctg]))


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
            'volume': " ".join(' '.join(tree.xpath('//div[@class="block1"]//li/text()')).split()),
            'pdct_img_main_url': ''.join(tree.xpath('//div[@id="image-block"]//img/@data-zoom-image')),
            'ctg_denom_txt': ' '.join(' '.join(tree.xpath('//*[@class="breadcrumb clearfix"]//text()')).split()),
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
