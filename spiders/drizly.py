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

from ers import all_keywords_usa as keywords, fpath_namer, mh_brands, clean_url, headers
from matcher import BrandMatcher
from ers import COLLECTION_DATE, file_hash, img_path_namer, clean_xpathd_text
import shutil
from parse import parse
import re
from custom_browser import CustomDriver


# Init variables and assets
shop_id = 'drizly'
root_url = 'https://www.drizly.com'
requests_cache.install_cache(fpath_namer(shop_id, 'requests_cache'))
country = 'USA'
searches, categories, products = {}, {}, {}
driver = CustomDriver(headless=True, download_images=True)


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
    'champagne': 'https://drizly.com/champagne/c196479/page{page}',
    'sparkling': 'https://drizly.com/wine/c3-c196553/page{page}',
    'still_wines': 'https://drizly.com/white-wine/c8/page{page}',
    'white_wine': 'https://drizly.com/white-wine/c8/page{page}',
    'red_wine': 'https://drizly.com/white-wine/c7/page{page}',
    'whisky': 'https://drizly.com/scotch/c196927/page{page}',
    'cognac': 'https://drizly.com/liquor/c4-c83/page{page}',
    'vodka': 'https://drizly.com/vodka/c89/page{page}',
    'gin': 'https://drizly.com/gin/c84/page{page}',
    'tequila': 'https://drizly.com/tequila/c88/page{page}',
    'rum': 'https://drizly.com/rum/c87/page{page}',
}


def init_drizly(driver):
    driver.get("https://drizly.com/beer/c2")
    sleep(2)
    driver.waitclick('//*[@class="AddressSelect"]')
    driver.text_input('1557 5th Avenue, New York, NY, United States', '//*[@id="address_field"]')
    sleep(1)
    driver.text_input('', '//*[@id="address_field"]', enter=True)
    sleep(3)
drizly_was_initialised = False


# Categories scraping
for ctg, url in urls_ctgs_dict.items():
    categories[ctg] = []
    number_of_pdcts_in_ctg = 0
    for p in range(100):
        # Scraping
        urlp = url.format(page=p+1)
        fpath = fpath_namer(shop_id, 'ctg', ctg, p)
        if not op.exists(fpath):
            if not drizly_was_initialised:
                init_drizly(driver)
                drizly_was_initialised = True
            driver.get(urlp)
            sleep(2)
            driver.save_page(fpath)
        # Parsing
        tree = etree.parse(BytesIO(open(fpath, 'rb').read()), parser=parser)
        for li in tree.xpath('//ul//li[contains(@class, "CatalogResults__CatalogListItem")]'):
            produrl = li.xpath('.//a/@href')[0]
            produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
            produrl = clean_url(produrl, root_url)
            products[produrl] = {
                'pdct_name_on_eretailer': ' '.join(''.join(li.xpath('.//h3//text()')).split()),
                'raw_price': ' '.join(''.join(li.xpath('.//*[contains(@class, "CatalogItem__CatalogItemDetails__Price")]//text()')).split()),
                'volume': ' '.join(''.join(li.xpath('.//*[contains(@class, "CatalogItem__CatalogItemDetails__Variation")]//text()')).split()).replace('.0ml', 'ml'),
                'raw_promo_price': "",
                'pdct_img_main_url': clean_xpathd_text(li.xpath('.//div[contains(@class, "CatalogItemImage")]/@style')),
                'ctg_denom_txt': ctg,
            }
            print(products[produrl], produrl)
            products[produrl]['price'] = getprice(products[produrl]['raw_price'])
            products[produrl]['promo_price'] = getprice(products[produrl]['raw_promo_price'])
            img_url = products[produrl]['pdct_img_main_url']
            products[produrl]['pdct_img_main_url'] = \
            re.search('(?<=url\().+?(?=\))', img_url).group().replace('"', '').split('.gif')[
                0] + '.gif'
            print(products[produrl])

            categories[ctg].append(produrl)

        # Checking if it was the last page
        if len(set(categories[ctg])) == number_of_pdcts_in_ctg:
            break
        else:
            number_of_pdcts_in_ctg = len(set(categories[ctg]))
print([(c, len(categories[c])) for c in categories])


# KW searches Scraping - with selenium - one page per search
search_url = "https://drizly.com/search?utf8=%E2%9C%93&q={kw}"
for kw in keywords:
    searches[kw] = []
    # Storing and extracting infos
    fpath = fpath_namer(shop_id, 'search', kw, 0)
    url = search_url.format(kw=kw, page=0)
    if not op.exists(fpath):
        if not drizly_was_initialised:
            init_drizly(driver)
            drizly_was_initialised = True
        driver.get(url)
        sleep(2)
        driver.save_page(fpath, scroll_to_bottom=True)
    tree = etree.parse(BytesIO(open(fpath, 'rb').read()), parser=parser)
    produrl = li.xpath('.//a/@href')[0]
    produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
    produrl = clean_url(produrl, root_url)
    products[produrl] = {
        'pdct_name_on_eretailer': ' '.join(''.join(li.xpath('.//h3//text()')).split()),
        'raw_price': ' '.join(
            ''.join(li.xpath('.//*[contains(@class, "CatalogItem__CatalogItemDetails__Price")]//text()')).split()),
        'volume': ' '.join(
            ''.join(li.xpath('.//*[contains(@class, "CatalogItem__CatalogItemDetails__Variation")]//text()')).split()).replace('.0ml', 'ml'),
        'raw_promo_price': "",
        'pdct_img_main_url': clean_xpathd_text(li.xpath('.//div[contains(@class, "CatalogItemImage")]/@style')),
        'ctg_denom_txt': ctg,
    }
    print(products[produrl], produrl)
    products[produrl]['price'] = getprice(products[produrl]['raw_price'])
    products[produrl]['promo_price'] = getprice(products[produrl]['raw_promo_price'])
    img_url = products[produrl]['pdct_img_main_url']
    products[produrl]['pdct_img_main_url'] = re.search('(?<=url\().+?(?=\))', img_url).group().replace('"', '').split('.gif')[0] + '.gif'
    print(products[produrl])

    searches[kw].append(produrl)
    print(kw, len(searches[kw]))

print(list(set(products)))


brm = BrandMatcher()
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
