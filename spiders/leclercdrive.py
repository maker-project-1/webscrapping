import os.path as op
from io import BytesIO

from lxml import etree

parser = etree.HTMLParser(encoding='utf-8')
from time import sleep
from ers import ctg_to_ctg_ind
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
from urllib.parse import urlsplit, parse_qs

# Init variables and assets
shop_id = 'leclercdrive'
root_url = 'https://fd9-courses.leclercdrive.fr'
requests_cache.install_cache(fpath_namer(shop_id, 'requests_cache'))
country = 'FR'
searches, categories, products = {}, {}, {}
driver = CustomDriver(headless=True, download_images=False)


urls_ctgs_dict = {
    'champagne': 'https://fd9-courses.leclercdrive.fr/magasin-056011-Senlis/rayon-284518-Champagnes-Mousseux-Cidres.aspx?Filtres=4-284542',
    'sparkling': 'https://fd9-courses.leclercdrive.fr/magasin-056011-Senlis/rayon-284518-Champagnes-Mousseux-Cidres.aspx?Filtres=4-284544',
    'vodka': 'https://fd9-courses.leclercdrive.fr/magasin-056011-Senlis/recherche.aspx?TexteRecherche=vodka',
    'cognac': 'https://fd9-courses.leclercdrive.fr/magasin-056011-Senlis/recherche.aspx?TexteRecherche=cognac',
    'whisky': 'https://fd9-courses.leclercdrive.fr/magasin-056011-Senlis/rayon-284519-Bieres-Alcools-et-Aperitifs.aspx?Filtres=4-284547',
    'still_wines': 'https://fd9-courses.leclercdrive.fr/magasin-056011-Senlis/rayon-289555-Vins.aspx',
    'liquor': 'https://fd9-courses.leclercdrive.fr/magasin-056011-Senlis/rayon-284519-Bieres-Alcools-et-Aperitifs.aspx?Filtres=4-286032',
    'rum': 'https://fd9-courses.leclercdrive.fr/magasin-056011-Senlis/rayon-284519-Bieres-Alcools-et-Aperitifs.aspx?Filtres=4-2845512',
    'red_wine': 'https://fd9-courses.leclercdrive.fr/magasin-056011-Senlis/rayon-289555-Vins.aspx?Filtres=4-289556',
    'white_wine': 'https://fd9-courses.leclercdrive.fr/magasin-056011-Senlis/rayon-289555-Vins.aspx?Filtres=4-289557',
}


def getprice(pricestr):
    pricestr = pricestr.replace(' ', '')
    if pricestr == '':
        return pricestr
    price = parse('{dol:d}.{pence:d}€', pricestr)
    if price is None:
        price = parse('{dol:d}€', pricestr)
        return price.named['dol'] * 100
    else:
        return price.named['dol'] * 100 + price.named['pence']


# Category Scraping - with selenium - one page per category
for ctg, url in urls_ctgs_dict.items():
    categories[ctg] = []
    fpath = fpath_namer(shop_id, 'ctg', ctg, 0)
    if not op.exists(fpath):
        driver.get(url)
        sleep(2)
        driver.save_page(fpath, scroll_to_bottom=True)
    tree = etree.parse(BytesIO(open(fpath, 'rb').read()), parser=parser)
    for li in tree.xpath('//ul[@id="ulListeProduits"]/li[not(contains(@class, "navailable"))]'):
        produrl = ' '.join(''.join(li.xpath('.//a[contains(@class, "_Product")]//text()')).split())
        products[produrl] = {
            'pdct_name_on_eretailer': produrl,
            'volume': produrl,
            'raw_price': ''.join(w for t in li.xpath('.//p[contains(@class, "_PrixUnitaire")]//text()')[:3] for w in t.split()).strip(),
            'raw_promo_price': ''.join(w for t in li.xpath('.//sdsf//text()')[:3] for w in t.split()).strip(),
            'pdct_img_main_url': clean_url(''.join(li.xpath('.//a[contains(@class, "_Product")]/img/@src')[0]), root_url),
            'ctg_denom_txt': " ".join(ctg_to_ctg_ind.keys()) ,
        }
        print(products[produrl], produrl)
        products[produrl]['price'] = getprice(products[produrl]['raw_price'])
        products[produrl]['promo_price'] = getprice(products[produrl]['raw_promo_price'])
        img_url = products[produrl]['pdct_img_main_url']
        query = urlsplit(img_url).query
        params = parse_qs(query)
        old_id = params['id'][0]
        new_id = str(int(old_id) - 1)
        products[produrl]['pdct_img_main_url'] = img_url.replace(old_id, new_id)
        print(products[produrl])
        categories[ctg].append(produrl)
print([(c, len(categories[c])) for c in categories])


# KW searches Scraping - with requests - one page per search
kw_search_url = "https://fd9-courses.leclercdrive.fr/magasin-056011-Senlis/recherche.aspx?TexteRecherche={kw}"
for kw in keywords:
    print('Requesting', kw)
    searches[kw] = []
    fpath = fpath_namer(shop_id, 'search', kw, 0)
    if not op.exists(fpath):
        driver.get(kw_search_url.format(kw=kw))
        sleep(2)
        driver.save_page(fpath, scroll_to_bottom=True)
    tree = etree.parse(BytesIO(open(fpath, 'rb').read()), parser=parser)
    for li in tree.xpath('//ul[@id="ulListeProduits"]/li[not(contains(@class, "navailable"))]'):
        produrl = ' '.join(''.join(li.xpath('.//a[contains(@class, "_Product")]//text()')).split())
        products[produrl] = {
            'pdct_name_on_eretailer': produrl,
            'volume': produrl,
            'raw_price': ''.join(w for t in li.xpath('.//p[contains(@class, "_PrixUnitaire")]//text()')[:3] for w in t.split()).strip(),
            'raw_promo_price': ''.join(w for t in li.xpath('.//sdsf//text()')[:3] for w in t.split()).strip(),
            'pdct_img_main_url': clean_url(''.join(li.xpath('.//a[contains(@class, "_Product")]/img/@src')[0]), root_url),
            'ctg_denom_txt': " ".join(ctg_to_ctg_ind.keys()) ,
        }
        print(products[produrl], produrl)
        products[produrl]['price'] = getprice(products[produrl]['raw_price'])
        products[produrl]['promo_price'] = getprice(products[produrl]['raw_promo_price'])
        img_url = products[produrl]['pdct_img_main_url']
        query = urlsplit(img_url).query
        params = parse_qs(query)
        old_id = params['id'][0]
        new_id = str(int(old_id) - 1)
        products[produrl]['pdct_img_main_url'] = img_url.replace(old_id, new_id)
        print(products[produrl])
        searches[kw].append(produrl)
    print(kw, len(searches[kw]))

# Download images
brm = BrandMatcher()
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
