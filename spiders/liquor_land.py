import os.path as op
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
from custom_browser import CustomDriver


# Init variables and assets
shop_id = 'liquor_land'
root_url = 'https://www.liquorland.com.au'
requests_cache.install_cache(fpath_namer(shop_id, 'requests_cache'))
country = 'AUS'
searches, categories, products = {}, {}, {}
driver = CustomDriver(headless=True, download_images=False)


def getprice(pricestr):
    if not pricestr:
        return
    pricestr = pricestr.replace('$', '')
    price = parse('{pound:d}', pricestr)
    if price:
        return price.named['pound'] * 100
    price = parse('{pound:d}.{pence:d}', pricestr)
    if price:
        return price.named['pound'] * 100 + price.named['pence']
    price = parse('{th:d},{pound:d}', pricestr)
    if price:
        return price.named['th'] * 100000 + price.named['pound'] * 100
    price = parse('{th:d},{pound:d}.{pence:d}', pricestr)
    if price:
        return price.named['th'] * 100000 + price.named['pound'] * 100 + price.named['pence']
    raise Exception


urls_ctgs_dict = {
    'champagne': 'https://www.liquorland.com.au/Sparkling?facets=region%3dChampagne&show=200&page={page}',
    'sparkling': 'https://www.liquorland.com.au/Sparkling?show=200&page={page}',
    'still_wines': 'https://www.liquorland.com.au/White%20Wine?show=200&page={page}',
    'whisky': 'https://www.liquorland.com.au/Spirits?show=200&facets=spiritproducttype%3dBlended+Scotch+Whisky&page={page}',
    'cognac': 'https://www.liquorland.com.au/Spirits?show=200&facets=spiritproducttype%3dBrandy&page={page}',
    'vodka': 'https://www.liquorland.com.au/Spirits?show=200&facets=spiritproducttype%3dVodka&page={page}',
    'red_wine': 'https://www.liquorland.com.au/Red%20Wine?show=200&page={page}',
    'white_wine': 'https://www.liquorland.com.au/White%20Wine?show=200&page={page}',
    'gin': 'https://www.liquorland.com.au/Spirits?facets=spiritproducttype%3dGin?show=200&page={page}',
    'rum': 'https://www.liquorland.com.au/Spirits?facets=spiritproducttype%3dRum+-+Dark?show=200&page={page}',
    'bourbon': 'https://www.liquorland.com.au/Spirits?facets=spiritproducttype%3dBourbon?show=200&page={page}',
    'liquor': 'https://www.liquorland.com.au/Spirits?facets=spiritproducttype%3dImported+Liqueurs?show=200&page={page}',
    'tequila': 'https://www.liquorland.com.au/Spirits?facets=spiritproducttype%3dTequila?show=200&page={page}',
}

# Category Scraping - with selenium - one page per category
for ctg, url in urls_ctgs_dict.items():
    categories[ctg] = []
    number_of_pdcts_in_ctg = 0
    for p in range(20):
        fpath = fpath_namer(shop_id, 'ctg', ctg, p)
        if not op.exists(fpath):
            driver.get(url.format(page=p))
            sleep(2)
            driver.save_page(fpath, scroll_to_bottom=True)
        tree = etree.parse(BytesIO(open(fpath, 'rb').read()), parser=parser)
        for li in tree.xpath('//ul[@class="productList"]/li'):
            produrl = li.xpath('.//div/h2/a/@href')[0]
            produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
            produrl = clean_url(produrl, root_url)
            products[produrl] = {
                'pdct_name_on_eretailer': "".join(li.xpath('.//div/h2//text()')).strip(),
                'raw_price': ''.join(w for t in li.xpath('.//div[@class="valueLarge"]//text()') for w in t.split()).strip().replace('ea', ''),
                'raw_promo_price': ''.join(w for t in li.xpath('.//p[@class="specials"]//text()') for w in t.split()).strip().lower(),
            }
            print(products[produrl], produrl)
            products[produrl]['price'] = getprice(products[produrl]['raw_price'])
            if products[produrl]['raw_promo_price'] and 'save' in products[produrl]['raw_promo_price'].lower():
                products[produrl]['raw_promo_price'] = products[produrl]['raw_promo_price'].lower().replace('save', '')
                products[produrl]['promo_price'] = getprice(products[produrl]['raw_promo_price']) + products[produrl]['price'] if getprice(products[produrl]['raw_promo_price']) and products[produrl]['price'] else ''
            else:
                products[produrl]['raw_promo_price'] = ""
            print(products[produrl])
            categories[ctg].append(produrl)

        # Checking if it was the last page
        if len(set(categories[ctg])) == number_of_pdcts_in_ctg:
            break
        else:
            number_of_pdcts_in_ctg = len(set(categories[ctg]))

print([(c, len(categories[c])) for c in categories])


# KW searches Scraping - with selenium - one page per search
search_url = "https://www.liquorland.com.au/Search?q={kw}&show=200"
for kw in keywords:
    searches[kw] = []
    # Storing and extracting infos
    fpath = fpath_namer(shop_id, 'search', kw, 0)
    url = search_url.format(kw=kw, page=0)
    if not op.exists(fpath):
        driver.get(url)
        sleep(2)
        driver.save_page(fpath, scroll_to_bottom=True)
    tree = etree.parse(BytesIO(open(fpath, 'rb').read()), parser=parser)
    for li in tree.xpath('//ul[@class="productList"]/li'):
        produrl = li.xpath('.//div/h2/a/@href')[0]
        produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
        produrl = clean_url(produrl, root_url)
        products[produrl] = {
            'pdct_name_on_eretailer': "".join(li.xpath('.//div/h2//text()')).strip(),
            'raw_price': ''.join(
                w for t in li.xpath('.//div[@class="valueLarge"]//text()') for w in t.split()).strip().replace('ea',
                                                                                                               ''),
            'raw_promo_price': ''.join(
                w for t in li.xpath('.//p[@class="specials"]//text()') for w in t.split()).strip().lower(),
        }
        print(products[produrl], produrl)
        products[produrl]['price'] = getprice(products[produrl]['raw_price'])
        if products[produrl]['raw_promo_price'] and 'save' in products[produrl]['raw_promo_price'].lower():
            products[produrl]['raw_promo_price'] = products[produrl]['raw_promo_price'].lower().replace('save', '')
            products[produrl]['promo_price'] = getprice(products[produrl]['raw_promo_price']) + products[produrl][
                'price'] if getprice(products[produrl]['raw_promo_price']) and products[produrl]['price'] else ''
        else:
            products[produrl]['raw_promo_price'] = ""
        print(products[produrl])
        searches[kw].append(produrl)
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
import magic
for url, pdt in products.items():
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
         elif any(x in magic.from_file(tmp_file_path, mime=True).lower() for x in ['jpeg', 'jpg', 'png']):
             magic_extension = magic.from_file(tmp_file_path, mime=True).lower()
             if 'jpeg' in magic_extension:
                extension = 'jpeg'
             elif 'jpg' in magic_extension:
                 extension = 'jpg'
             else:
                 extension = 'png'
             img_path = img_path.split('.')[0] + '.' + extension
             shutil.copyfile('/tmp/' + shop_id + 'mhers_tmp_{}.imgtype'.format(abs(hash(pdt['pdct_img_main_url']))), img_path)
             products[url].update({'img_path': img_path, 'img_hash': file_hash(img_path)})
         else:
             print('Warning :', tmp_file_path, imghdr.what(tmp_file_path))

create_csvs(products, categories, searches, shop_id, fpath_namer(shop_id, 'raw_csv'), COLLECTION_DATE)
validate_raw_files(fpath_namer(shop_id, 'raw_csv'))
driver.quit()
