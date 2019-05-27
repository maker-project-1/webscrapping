from lxml import etree
from io import BytesIO
from io import BytesIO

from lxml import etree

parser = etree.HTMLParser(encoding='iso-8859-1')
from time import sleep
from urllib.parse import urlsplit, parse_qs
import requests
import requests_cache, imghdr
from validators import validate_raw_files
from create_csvs import create_csvs
from ers import all_keywords_usa as keywords, fpath_namer, mh_brands, clean_url, headers

from matcher import BrandMatcher
from ers import COLLECTION_DATE, file_hash, img_path_namer
import shutil
from custom_browser import CustomDriver
from parse import parse
import re


# Init variables and assets
shop_id = "pogos_wine_spirits"
root_url = "https://www.pogoswine.com/" 
requests_cache.install_cache(fpath_namer(shop_id, 'requests_cache'))
country = "USA"


searches, categories, products = {}, {}, {}
# If necessary
driver = CustomDriver(headless=True)


def getprice(pricestr):
    if pricestr == '':
        return pricestr
    if pricestr.count('$') >= 2:
        pricestr = "$" + pricestr.split('$')[1]
    pricestr = re.sub("[^0-9.$]", "", pricestr)
    price = parse('${pound:d}.{pence:d}', pricestr)
    if price is None:
        price = parse('{pence:d}p', pricestr)
        return price.named['pence']
    else:
        return price.named['pound'] * 100 + price.named['pence']


urls_ctgs_dict = {
    "vodka": "https://www.pogoswine.com/spirits/Vodka/?sortby=sort_item_order&l=100", 
    "sparkling": "https://www.pogoswine.com/wines/?item_type=sparkling&sortby=sort_item_order&l=100", 
    "cognac": "https://www.pogoswine.com/spirits/?varietal=Cognac&country=France&sortby=sort_item_order&l=100", 
    "champagne": "https://www.pogoswine.com/wines/All/All/All/Champagne?page=1&sortby=sort_item_order&region=Champagne&l=100&item_type=wine", 
    "still_wines": "https://www.pogoswine.com/wines/?page={page}&sortby=sort_item_order&l=100&item_type=wine", 
    "whisky": "https://www.pogoswine.com/spirits/Whiskey/?sortby=sort_item_order&l=100",
    "red_wine": "https://www.pogoswine.com/wines/?item_type=red&sortby=sort_item_order&l=10",
    "white_wine": "https://www.pogoswine.com/wines/?item_type=white&sortby=sort_item_order&l=10",
    "gin": "https://www.pogoswine.com/spirits/Gin/?sortby=sort_item_order&l=100",
    "rum": "https://www.pogoswine.com/spirits/Rum/?sortby=sort_item_order&l=100",
    "tequila": "https://www.pogoswine.com/spirits/Tequila/?sortby=sort_item_order&l=100",
    "brandy": "https://www.pogoswine.com/spirits/Brandy/?sortby=sort_item_order&l=100",
}


# Category Scraping
for ctg, url in urls_ctgs_dict.items():
    categories[ctg] = []
    number_of_pdcts_in_ctg = 0
    for p in range(100):
        urlp = url.format(page=p+1)
        
        r = requests.get(urlp)
        with open('/tmp/' + shop_id + ctg + '.html', 'wb') as f:
            f.write(r.content)
        tree = etree.parse(BytesIO(r.content), parser=parser)
        
        for li in tree.xpath('//div[contains(@class, "product-list")]/div/table'):
            produrl = li.xpath('.//a[contains(@class, "rebl15")]/@href')[0]
            produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
            produrl = clean_url(produrl, root_url)
            products[produrl] = {
                'pdct_name_on_eretailer': ' '.join(''.join(li.xpath('.//a[contains(@class, "rebl15")]//text()')).split()).strip(),
                'raw_price': ' '.join(''.join(li.xpath('.//span[@class="rd14"]//text()')).split()).strip(),
                'raw_promo_price': ' '.join(''.join(li.xpath('.//td[contains(@class, "orig14")]//text()')[:1]).split()).strip(),
            }
            print(ctg, p, products[produrl], produrl)
            products[produrl]['raw_price'] = re.sub('Case Price \(\d+\)', "", products[produrl]['raw_price'])
            products[produrl]['raw_promo_price'] = re.sub('Case Price \(\d+\)', "", products[produrl]['raw_promo_price'])
            products[produrl]['price'] = getprice(products[produrl]['raw_price'])
            products[produrl]['promo_price'] = getprice(products[produrl]['raw_promo_price'])
            print(products[produrl])
            
            categories[ctg].append(produrl)

        # Checking if it was the last page
        if len(set(categories[ctg])) == number_of_pdcts_in_ctg:
            break
        else:
            number_of_pdcts_in_ctg = len(set(categories[ctg]))
        # if not r.from_cache:
        #     sleep(2)
print([(c, len(categories[c])) for c in categories])




# KW searches Scraping - with selenium - with nb page hard-coded in url - multiple page per search
search_url = "https://www.pogoswine.com/websearch_results.html?page={page}&kw={kw}&sortby=sort_item_order&l=100"
for kw in keywords:
    searches[kw] = []
    number_of_pdcts_in_kw_search = 0
    
    for p in range(10):
        # Storing and extracting infos
        urlp = search_url.format(kw=kw,page=p)

        r = requests.get(urlp)
        with open('/tmp/' + shop_id + " " + kw + '.html', 'wb') as f:
            f.write(r.content)
        tree = etree.parse(BytesIO(r.content), parser=parser)
        
        for li in tree.xpath('//div[contains(@class, "product-list")]/div/table'):
            produrl = li.xpath('.//a[contains(@class, "rebl15")]/@href')[0]
            produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
            produrl = clean_url(produrl, root_url)
            products[produrl] = {
                'pdct_name_on_eretailer': ' '.join(''.join(li.xpath('.//a[contains(@class, "rebl15")]//text()')).split()).strip(),
                'raw_price': ' '.join(''.join(li.xpath('.//span[@class="rd14"]//text()')).split()).strip(),
                'raw_promo_price': ' '.join(''.join(li.xpath('.//td[contains(@class, "orig14")]//text()')[:1]).split()).strip(),
            }
            print(products[produrl], produrl)
            products[produrl]['raw_price'] = re.sub('Case Price \(\d+\)', "", products[produrl]['raw_price'])
            products[produrl]['raw_promo_price'] = re.sub('Case Price \(\d+\)', "", products[produrl]['raw_promo_price'])
            products[produrl]['price'] = getprice(products[produrl]['raw_price'])
            products[produrl]['promo_price'] = getprice(products[produrl]['raw_promo_price'])
            print(products[produrl])
            
            searches[kw].append(produrl)
        if len(set(searches[kw])) == number_of_pdcts_in_kw_search:
            break
        else:
            number_of_pdcts_in_kw_search = len(set(searches[kw]))
        # if not r.from_cache:
        #     sleep(2)
    print(kw, p, len(searches[kw]))

# Download the pages
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
            'volume': ''.join(tree.xpath('//*[@id="content"]//h1//text()')).strip(),
            'pdct_img_main_url': clean_url(''.join(tree.xpath('//div[@id="galsec"]//img[@itemprop="image"]/@src')), root_url),
            'ctg_denom_txt': ' '.join(' '.join(tree.xpath('//*[@id="prodata"]//text()')).split()),
        })
        print(products[url])
        if not r.from_cache:
            sleep(2)

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
