import os.path as op
import sys
from io import BytesIO

from lxml import etree

parser = etree.HTMLParser(encoding='utf-8')
from time import sleep
from urllib.parse import urlsplit, parse_qs
import requests
import requests_cache, imghdr

from validators import validate_raw_files
from create_csvs import create_csvs
sys.path.append(op.abspath(__file__ + "/../../"))

from ers import all_keywords_fr as keywords, fpath_namer, mh_brands, clean_url, headers
from matcher import BrandMatcher
from ers import COLLECTION_DATE, file_hash, img_path_namer
import shutil
from custom_browser import CustomDriver
from parse import parse


# Init variables and assets
shop_id = 'vinatis'
root_url = 'https://www.vinatis.com'
requests_cache.install_cache(fpath_namer(shop_id, 'requests_cache'))
country = 'FR'
searches, categories, products = {}, {}, {}
driver = CustomDriver(headless=True, download_images=False)


def getprice(pricestr):
    pricestr = pricestr.replace(' ', '')
    if pricestr == '':
        return pricestr
    price = parse('{dol:d},{pence:d}€', pricestr)
    if price is None:
        price = parse('{pence:d}p', pricestr)
        return price.named['pence']
    else:
        return price.named['dol'] * 100 + price.named['pence']


urls_ctgs_dict = {
    'champagne': 'https://www.vinatis.com/champagne-cuvees-mythiques#p1&n15&t7&f[]7[]43:f[]27[]11426[]s',
    'whisky': 'https://www.vinatis.com/achat-spiritueux-scotch-whisky-ecossais',
    'cognac': 'https://www.vinatis.com/achat-spiritueux-cognac-armagnac#p1&n15&t7&f[]73[]190570:f[]73[]190644:f[]27[]11427[]s',
    'vodka': 'https://www.vinatis.com/achat-spiritueux-vodka#p1&n15&t7&f[]73[]190577:f[]27[]11427[]s',
    'red_wine': 'https://www.vinatis.com/achat-vin-rouge#p1&n15&t7&f[]3[]33:f[]27[]11425:f[]27[]26006[]s',
    'white_wine': 'https://www.vinatis.com/achat-vin-blanc#p1&n15&t7&f[]3[]30:f[]27[]11425:f[]27[]12582:f[]27[]26006[]s',
    'tequila': 'https://www.vinatis.com/tequila#p1&n15&t7&f[]73[]190571:f[]27[]11427[]s',
    'gin': 'https://www.vinatis.com/tequila#p1&n15&t7&f[]27[]11427:f[]73[]190578',
    'rum': 'https://www.vinatis.com/achat-spiritueux#p1&n15&t7&f[]27[]11427:f[]73[]190572',
    'liquor': 'https://www.vinatis.com/achat-spiritueux#p1&n15&t7&f[]27[]11427:f[]73[]190645',
}


# Category Scraping - with selenium - multiple pages per category (click on next page)
for ctg, url in urls_ctgs_dict.items():
    categories[ctg] = []
    number_of_pdcts_in_ctg = 0
    if not op.exists(fpath_namer(shop_id, 'ctg', ctg, 0)):
        # Getting to ctg url
        driver.get(url)
    for p in range(10):
        fpath = fpath_namer(shop_id, 'ctg', ctg, p)
        if not op.exists(fpath):
            driver.save_page(fpath)
            sleep(2)
        tree = etree.parse(open(fpath, 'rb'), parser=parser)
        for li in tree.xpath('//div[@class="row no-margin full-height padding-5"]'):
            produrl = li.xpath('.//h2/span/a/@href')[0]
            produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
            products[produrl] = {
                'pdct_name_on_eretailer': " ".join("".join(li.xpath('.//h2//text()')).split()),
                'raw_price': ''.join(w for t in li.xpath('.//span[@id="our_price_display"]/span[1]/span[contains(@class, "text-bold taille-")]/text()') for w in t.split()).strip(),
                'raw_promo_price': ''.join(w for t in li.xpath('.//span[@id="old_price_display"]//text()') for w in t.split()).strip(),
            }
            print(products[produrl], produrl)
            products[produrl]['price'] = getprice(products[produrl]['raw_price'])
            products[produrl]['promo_price'] = getprice(products[produrl]['raw_promo_price'])
            print(products[produrl])
            categories[ctg].append(produrl)
        # Going to next page if need be
        next_page_click = '//div[@class="pagination_ajax"]//span[contains(@class, "pagination_right")]'
        if not op.exists(fpath_namer(shop_id, 'ctg', ctg, p+1)):
            if not driver.check_exists_by_xpath(next_page_click):
                break
            else:
                driver.waitclick(next_page_click)
    print(ctg, url, p, len(categories[ctg]))


# KW searches Scraping - with selenium - with search string - multiple page per search
search_url = "https://www.vinatis.com/recherche?search_query={kw}"
for kw in keywords:
    searches[kw] = []
    if not op.exists(fpath_namer(shop_id, 'search', kw, 0)):
        driver.get(search_url.format(kw=kw))
    for p in range(10):
        # Storing and extracting infos
        fpath = fpath_namer(shop_id, 'search', kw, p)
        if not op.exists(fpath):
            driver.save_page(fpath)
            sleep(2)
        tree = etree.parse(open(fpath, 'rb'), parser=parser)
        for li in tree.xpath('//div[@class="row no-margin full-height padding-5"]'):
            produrl = li.xpath('.//h2/span/a/@href')[0]
            produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
            products[produrl] = {
                'pdct_name_on_eretailer': " ".join("".join(li.xpath('.//h2//text()')).split()),
                'raw_price': ''.join(w for t in li.xpath('.//span[@id="our_price_display"]/span[1]/span[contains(@class, "text-bold taille-")]/text()') for w in t.split()).strip(),
                'raw_promo_price': ''.join(w for t in li.xpath('.//span[@id="old_price_display"]//text()') for w in t.split()).strip(),
            }
            print(products[produrl], produrl)
            products[produrl]['price'] = getprice(products[produrl]['raw_price'])
            products[produrl]['promo_price'] = getprice(products[produrl]['raw_promo_price'])
            print(products[produrl])
            searches[kw].append(produrl)

        # Going to next page if need be
        next_page_click = '//div[@class="pagination_ajax"]//span[contains(@class, "pagination_right")]'
        if not op.exists(fpath_namer(shop_id, 'ctg', ctg, p+1)):
            if not driver.check_exists_by_xpath(next_page_click):
                break
            else:
                driver.waitclick(next_page_click)
    print(kw, p, len(searches[kw]))


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
            'pdct_img_main_url': clean_url(''.join(tree.xpath('//*[@id="view_full_size"]/img/@src')), root_url),
            'ctg_denom_txt': ' '.join(' '.join(tree.xpath('//div[@class="title "]//h2/span[2]//text()')).split()),
            'volume': ' '.join(' '.join(tree.xpath('//div[@class="title "]//h2/span[1]/span//text()')).split()),
        })
        print(products[url])
        if not r.from_cache:
            sleep(3)


# Download images
for url, pdt in products.items():
     if 'pdct_img_main_url' in pdt and pdt['pdct_img_main_url']:
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
