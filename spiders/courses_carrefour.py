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

from ers import all_keywords_fr as keywords, fpath_namer, mh_brands, clean_url, headers
from matcher import BrandMatcher
from ers import COLLECTION_DATE, file_hash, img_path_namer
import shutil
from custom_browser import CustomDriver
from parse import parse


# Init variables and assets
shop_id = 'courses_carrefour'
root_url = 'https://courses-en-ligne.carrefour.fr'
requests_cache.install_cache(fpath_namer(shop_id, 'requests_cache'))
country = 'FR'
searches, categories, products = {}, {}, {}
# If necessary
driver = CustomDriver(headless=False, download_images=False)


def getprice(pricestr):
    if pricestr == '':
        return pricestr
    price = parse('{dol:d},{pence:d}€', pricestr)
    if price is None:
        price = parse('{pence:d}', pricestr)
        return price.named['pence']
    else:
        return price.named['dol'] * 100 + price.named['pence']


urls_ctgs_dict = {
            'champagne': 'https://courses-en-ligne.carrefour.fr/tous-les-rayons/boissons-et-cave-a-vins/champagnes-et-vins-petillants?page={page}',
            # 'sparkling': 'https://courses-en-ligne.carrefour.fr/tous-les-rayons/boissons-et-cave-a-vins/champagnes-et-vins-petillants/vins-petillants-et-mousseux?page={page}',
            # 'still_wines': 'https://courses-en-ligne.carrefour.fr/tous-les-rayons/boissons-et-cave-a-vins/aperitifs-et-alcools/whisky/whiskies-de-degustation?page={page}',
            'whisky': 'https://courses-en-ligne.carrefour.fr/tous-les-rayons/boissons-et-cave-a-vins/aperitifs-et-alcools/whisky?page={page}/',
            'cognac': "https://courses-en-ligne.carrefour.fr/tous-les-rayons/boissons-et-cave-a-vins/aperitifs-et-alcools/liqueurs-et-digestifs",
            'vodka': 'https://courses-en-ligne.carrefour.fr/tous-les-rayons/boissons-et-cave-a-vins/aperitifs-et-alcools/vodkas-gins-et-tequila',
        }

def init_carrefour(driver):
    driver.get("https://courses-en-ligne.carrefour.fr/prehome")
    driver.text_input('port de bouc', '//*[@class="cd-AutocompleteContainer"]//input', enter=False)
    driver.waitclick('//*[@class="r-ResetList cd-SearchList"]/li[1]')
    sleep(5)

carrefour_was_initialised = False

# Categories scraping
for ctg, url in urls_ctgs_dict.items():
    categories[ctg] = []
    number_of_pdcts_in_ctg = 0
    for p in range(100):
        # Scraping
        urlp = url.format(page=p+1)
        fpath = fpath_namer(shop_id, 'ctg', ctg, p)
        if not op.exists(fpath):
            if not carrefour_was_initialised:
                init_carrefour(driver)
                carrefour_was_initialised = True
            driver.get(urlp)
            sleep(2)
            driver.save_page(fpath, scroll_to_bottom=True)
        # Parsing
        tree = etree.parse(BytesIO(open(fpath, 'rb').read()), parser=parser)
        for li in tree.xpath('//div[@class="cd-Product js-crossBlock "]'):
            produrl = li.xpath('.//h4/a/@href')[0]
            produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(
                urlsplit(produrl).query) else produrl
            produrl = clean_url(produrl, root_url)
            raw_price = ''.join(w for t in li.xpath('.//div[contains(@class, "cd-ProductPriceUnit")]//text()') for w in t.split()).strip()
            raw_promo_price = ''.join(w for t in li.xpath('.//span[@class="cd-ProductPricePreDiscount"]//text()') for w in t.split()).strip()
            raw_price = raw_price.replace(raw_promo_price, '')
            products[produrl] = {
                'pdct_name_on_eretailer': ' '.join(''.join(li.xpath('.//h4//text()')).split()),
                'raw_price': raw_price,
                'raw_promo_price': raw_promo_price,
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
print([(c, len(categories[c])) for c in categories])


# KW searches Scraping - with selenium - one page per search
search_url = "https://courses-en-ligne.carrefour.fr/search?q={kw}"
for kw in keywords:
    searches[kw] = []
    # Storing and extracting infos
    fpath = fpath_namer(shop_id, 'search', kw, 0)
    url = search_url.format(kw=kw, page=0)
    if not op.exists(fpath):
        if not carrefour_was_initialised:
            init_carrefour(driver)
            carrefour_was_initialised = True
        driver.get(url)
        sleep(2)
        driver.save_page(fpath, scroll_to_bottom=True)
    tree = etree.parse(BytesIO(open(fpath, 'rb').read()), parser=parser)
    for li in tree.xpath('//div[@class="cd-Product js-crossBlock "]'):
        produrl = li.xpath('.//h4/a/@href')[0]
        produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
        produrl = clean_url(produrl, root_url)
        raw_price = ''.join(w for t in li.xpath('.//div[contains(@class, "cd-ProductPriceUnit")]//text()') for w in t.split()).strip()
        raw_promo_price = ''.join(w for t in li.xpath('.//span[@class="cd-ProductPricePreDiscount"]//text()') for w in t.split()).strip()
        raw_price = raw_price.replace(raw_promo_price, '')
        products[produrl] = {
            'pdct_name_on_eretailer': ' '.join(''.join(li.xpath('.//h4//text()')).split()),
            'raw_price': raw_price,
            'raw_promo_price': raw_promo_price,
        }
        print(products[produrl], produrl)
        products[produrl]['price'] = getprice(products[produrl]['raw_price'])
        products[produrl]['promo_price'] = getprice(products[produrl]['raw_promo_price'])
        print(products[produrl])
        searches[kw].append(produrl)
    print(kw, len(searches[kw]))

print(list(set(products)))

# Download the pages - with selenium
brm = BrandMatcher()
l_products = []
for url in sorted(list(set(products))):
    d = products[url]
    if d['pdct_name_on_eretailer'] in l_products:
        continue
    if brm.find_brand(d['pdct_name_on_eretailer'])['brand'] in mh_brands:
        print(d['pdct_name_on_eretailer'])
        url_mod = clean_url(url, root_url=root_url)
        fname = fpath_namer(shop_id, 'pdct', d['pdct_name_on_eretailer'], 0)
        if not op.exists(fname):
            if not carrefour_was_initialised:
                init_carrefour(driver)
                carrefour_was_initialised = True
            driver.get(url_mod)
            sleep(2)
            driver.save_page(fname, scroll_to_bottom=True)
        tree = etree.parse(open(fname), parser=parser)
        products[url].update({
            'volume' : ''.join(tree.xpath('//div[@class="cd-ProductDescription"]//text()')[0]).strip(),
            'pdct_img_main_url': ''.join(tree.xpath('//*[@id="productSlider"]/li[@data-itemnb="0"]/@data-imgname')[0]),
            'ctg_denom_txt': ' '.join(tree.xpath('//div[@class="cd-NavSubMenu"]//text()')),
        })
        print(products[url])
        l_products.append(d['pdct_name_on_eretailer'])

# Download images

cookies_ = driver.get(root_url).driver.get_cookies()[0]
cookies_ = {'value': cookies_['value']}

for url, pdt in products.items():
     if 'pdct_img_main_url' in pdt and pdt['pdct_img_main_url'] and brm.find_brand(pdt['pdct_name_on_eretailer'])['brand'] in mh_brands:
         print(pdt['pdct_name_on_eretailer'] + "." + pdt['pdct_img_main_url'].split('.')[-1])
         print(pdt['pdct_img_main_url'])
         response = requests.get(pdt['pdct_img_main_url'], stream=False, verify=False, headers=headers, cookies=cookies_)
         # response.raw.decode_content = True
         tmp_file_path = '/tmp/' + shop_id + 'mhers_tmp_{}.imgtype'.format(abs(hash(pdt['pdct_img_main_url'])))
         img_path = img_path_namer(shop_id, pdt['pdct_name_on_eretailer'])
         with open(tmp_file_path, 'wb') as out_file:
             out_file.write(response.content)
         driver.get(pdt['pdct_img_main_url'])
         driver.driver.save_screenshot(tmp_file_path)
         if imghdr.what(tmp_file_path) is not None:
             img_path = img_path.split('.')[0] + '.' + imghdr.what('/tmp/' + shop_id + 'mhers_tmp_{}.imgtype'.format(abs(hash(pdt['pdct_img_main_url']))))
             shutil.copyfile('/tmp/' + shop_id + 'mhers_tmp_{}.imgtype'.format(abs(hash(pdt['pdct_img_main_url']))), img_path)
             products[url].update({'img_path': img_path, 'img_hash': file_hash(img_path)})
             print("Updated img info in", products[url])
         else:
             print("WARNING", tmp_file_path, 'has img type', imghdr.what(tmp_file_path))

create_csvs(products, categories, searches, shop_id, fpath_namer(shop_id, 'raw_csv'), COLLECTION_DATE)
validate_raw_files(fpath_namer(shop_id, 'raw_csv'))
driver.quit()
