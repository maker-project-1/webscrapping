import re
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
from ers import COLLECTION_DATE, file_hash, img_path_namer
import shutil
from parse import parse


# Init variables and assets
shop_id = "total_wine"
root_url = "http://www.totalwine.com/" 
requests_cache.install_cache(fpath_namer(shop_id, 'requests_cache'))
country = "USA"


searches, categories, products = {}, {}, {}
# If necessary
# driver = CustomDriver(headless=True)



def getprice(pricestr):
    if pricestr == '' or pricestr == '$':
        return None
    pricestr = re.sub("[^0-9.$]", "", pricestr)
    price = parse('${pound:d}.{pence:d}', pricestr)
    if price is None:
        price = parse('{pence:d}p', pricestr)
        return price.named['pence']
    else:
        return price.named['pound'] * 100 + price.named['pence']




urls_ctgs_dict = {
    "vodka": "http://www.totalwine.com/spirits/c/c0030?text=&spiritsvarietaltype=vodka&viewall=true&tab=fullcatalog&pagesize=100&page={page}",
    "cognac": "http://www.totalwine.com/spirits/brandy-cognac/c/000770?tab=fullcatalog&text=&pagesize=100&page={page}",
    "champagne": "http://www.totalwine.com/wine/champagne-sparkling-wine/sparkling-wine/c/000044?pagesize=100&page={page}",
    "sparkling": "http://www.totalwine.com/wine/champagne-sparkling-wine/sparkling-wine/c/000044?pagesize=100&page={page}",
    "still_wines": "http://www.totalwine.com/wine/c/c0020?viewall=true&pagesize=100&page={page}",
    "whisky": "http://www.totalwine.com/spirits/c/c0030?spiritsproducttype=scotch&text=&viewall=true&tab=fullcatalog&pagesize=100&page={page}",
    'red_wine':'http://www.totalwine.com/wine/red-wine/c/000009?viewall=true&pagesize=100&page={page}',
    'white_wine':'http://www.totalwine.com/wine/white-wine/c/000002?viewall=true&pagesize=100&page={page}',
    'gin':'http://www.totalwine.com/spirits/gin/c/000870?viewall=true&pagesize=100&page={page}',
    'tequila':'http://www.totalwine.com/spirits/tequila/c/000824?viewall=true&pagesize=100&page={page}',
    'rum':'http://www.totalwine.com/spirits/rum/c/000871?viewall=true&pagesize=100&page={page}',
    'liquor':'http://www.totalwine.com/spirits/liqueurs-cordials-schnapps/c/000778?viewall=true&pagesize=100&page={page}',
    'brandy':'http://www.totalwine.com/spirits/brandy-cognac/c/000770?viewall=true&pagesize=100&page={page}',
    'bourbon':'http://www.totalwine.com/spirits/bourbon/c/000773?viewall=true&pagesize=100&page={page}',
}

# Category Scraping
for ctg, url in urls_ctgs_dict.items():
    categories[ctg] = []
    number_of_pdcts_in_ctg = 0
    for p in range(100):
        urlp = url.format(page=p+1)
        
        # fpath = fpath_namer(shop_id, 'ctg', ctg, p)
        # if not op.exists(fpath):
        #     driver.get(urlp)
        #     sleep(2)
        #     driver.save_page(fpath)
        # tree = etree.parse(BytesIO(open(fpath, 'rb').read()), parser=parser)
        
        r = requests.get(urlp)
        with open('/tmp/' + shop_id + '_' + ctg + '.html', 'wb') as f:
            f.write(r.content)
        tree = etree.parse(BytesIO(r.content), parser=parser)
        
        for li in tree.xpath('//ul[contains(@class, "plp-list")]/li'):
            produrl = li.xpath('.//h2[contains(@class, "plp-product-title")]/a/@href')[0]
            produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
            produrl = clean_url(produrl, root_url)
            products[produrl] = {
                'pdct_name_on_eretailer': ' '.join(''.join(li.xpath('.//h2[contains(@class, "plp-product-title")]/a//text()')).split()),
                'raw_price': ' '.join(''.join(li.xpath('.//span[@class="price"]//text()')).split()),
                'raw_promo_price': ' '.join(''.join(li.xpath('.//span[@class="cart-price-strike"]//text()')).split()),
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
        if not r.from_cache:
            sleep(2)
print([(c, len(categories[c])) for c in categories])

# KW searches Scraping - with selenium - with nb page hard-coded in url - multiple page per search
search_url = "http://www.totalwine.com/search/all?text={kw}&tab=fullcatalog&page={page}&pagesize=100"
for kw in keywords:
    searches[kw] = []
    number_of_pdcts_in_kw_search = 0
    
    for p in range(10):
        # Storing and extracting infos
        urlp = search_url.format(kw=kw,page=p)
        
        # fpath = fpath_namer(shop_id, 'search', kw, p)
        # if not op.exists(fpath):
        #     driver.get(urlp)
        #     sleep(2)
        #     driver.save_page(fpath)
        # tree = etree.parse(BytesIO(open(fpath, 'rb').read()), parser=parser)
        
        r = requests.get(urlp)
        with open('/tmp/' + shop_id + '_' + kw + '.html', 'wb') as f:
            f.write(r.content)
        tree = etree.parse(BytesIO(r.content), parser=parser)
        
        for li in tree.xpath('//ul[contains(@class, "plp-list")]/li'):
            produrl = li.xpath('.//h2[contains(@class, "plp-product-title")]/a/@href')[0]
            produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
            produrl = clean_url(produrl, root_url)
            products[produrl] = {
                'pdct_name_on_eretailer': ' '.join(''.join(li.xpath('.//h2[contains(@class, "plp-product-title")]/a//text()')).split()),
                'raw_price': ' '.join(''.join(li.xpath('.//span[@class="price"]//text()')).split()),
                'raw_promo_price': ' '.join(''.join(li.xpath('.//span[@class="cart-price-strike"]//text()')).split()),
            }
            print(products[produrl], produrl)
            products[produrl]['price'] = getprice(products[produrl]['raw_price'])
            products[produrl]['promo_price'] = getprice(products[produrl]['raw_promo_price'])
            print(products[produrl])
            
            searches[kw].append(produrl)
        if len(set(searches[kw])) == number_of_pdcts_in_kw_search:
            break
        else:
            number_of_pdcts_in_kw_search = len(set(searches[kw]))
        if not r.from_cache:
            sleep(2)
    print(kw, p, len(searches[kw]))


# Download the pages - with selenium
brm = BrandMatcher()
for url in sorted(list(set(products))):
    d = products[url]
    if brm.find_brand(d['pdct_name_on_eretailer'])['brand'] in mh_brands:
        print(d['pdct_name_on_eretailer'], url)
        url_mod = clean_url(url, root_url=root_url)
        
        # fname = fpath_namer(shop_id, 'pdct', d['pdct_name_on_eretailer'], 0)
        # if not op.exists(fname):
        #     driver.get(url_mod)
        #     sleep(2)
        #     driver.save_page(fname, scroll_to_bottom=True)
        # tree = etree.parse(open(fname), parser=parser)
        
        r = requests.get(url_mod, headers)
        with open('/tmp/' + shop_id + " --" + d['pdct_name_on_eretailer'].replace('/', "-") + '.html', 'wb') as f:
            f.write(r.content)
        print('/tmp/' + shop_id + " --" + d['pdct_name_on_eretailer'].replace('/', "-") + '.html')
        tree = etree.parse(BytesIO(r.content), parser=parser)
        
        products[url].update({
            'volume': ' '.join(''.join(tree.xpath('//section[@class="pdp-tab-overview-type"]//text()')).split()),
            'pdct_img_main_url': tree.xpath('//img[contains(@class, "anPDPImage")]/@src'),
            'ctg_denom_txt': ' '.join(' '.join(tree.xpath('//*[@class="pdp-wrapper"]//text()')).split()),
        })
        if type(products[url]['pdct_img_main_url']) == list and len(products[url]['pdct_img_main_url']) >= 2:
            products[url]['pdct_img_main_url'] = clean_url(''.join(products[url]['pdct_img_main_url'][0]), root_url)
        print(products[url]['pdct_img_main_url'])
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
