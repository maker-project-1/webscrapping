
import os.path as op
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
from custom_browser import CustomDriver
from parse import parse


# Init variables and assets
shop_id = "freshdirect"
root_url = "http://www.freshdirect.com" 
requests_cache.install_cache(fpath_namer(shop_id, 'requests_cache'))
country = "USA"


searches, categories, products = {}, {}, {}
# If necessary
driver = CustomDriver(headless=False)


def getprice(pricestr):
    if pricestr == '':
        return pricestr
    if "/ea" in pricestr:
        pricestr = pricestr.split('/ea')[0]
    print(pricestr.count('$'), pricestr)
    if pricestr.count('$') == 2:
        pricestr = pricestr.split(' ')[0]
    print(pricestr)
    pricestr = re.sub("[^0-9.$]", "", pricestr)
    price = parse('${pound:d}.{pence:d}', pricestr)
    if price is None:
        price = parse('${pound:d}', pricestr)
        return price.named['pound'] * 100
    else:
        return price.named['pound'] * 100 + price.named['pence']

pricestr = '$39.99/ea $27.99/ea'
getprice(pricestr)
pricestr = '$49.99 $34.99'
getprice(pricestr)


def init_freshdirect(driver):
    driver.get('https://www.freshdirect.com/health_warning.jsp?successPage=/pdp.jsp%3FproductId%3Dwin_pid_5002555%26catId%3Dvin_spirits_vodka_vodka')
    driver.waitclick('//*[@name="see_beer_button"]')
    sleep(2)


freshdirect_was_initialised = False


urls_ctgs_dict = {
    "vodka": "https://www.freshdirect.com/browse.jsp?pageType=browse&id=vin_spirits_vodka&pageSize=100&all=false&activePage={page}&sortBy=Sort_PopularityUp&orderAsc=true&activeTab=product",
    "sparkling": "https://www.freshdirect.com/browse.jsp?pageType=browse&id=vin_type_sparkling&pageSize=100&all=true&activePage={page}&sortBy=Sort_PopularityUp&orderAsc=false&activeTab=product&FG_win_CountryRegion_l1=clearall&FG_win_varietal=clearall&FG_wine_price=clearall",
    "cognac": "https://www.freshdirect.com/browse.jsp?pageType=browse&id=vin_spirits_brandy&pageSize=100&all=false&activePage={page}&sortBy=Sort_PopularityUp&orderAsc=true&activeTab=product",
    "champagne": "https://www.freshdirect.com/srch.jsp?pageType=search&searchParams=champagne&pageSize=100&all=false&activePage={page}&sortBy=Sort_Relevancy&orderAsc=true&activeTab=product",
    "still_wines": "https://www.freshdirect.com/browse.jsp?pageType=browse&id=vin_type_whites&pageSize=100&all=true&activePage={page}&sortBy=Sort_PopularityUp&orderAsc=true&activeTab=product&FG_win_CountryRegion_l1=clearall&FG_wine_price=clearall",
    "whisky": "https://www.freshdirect.com/browse.jsp?pageType=browse&id=vin_spirits_whiskey&pageSize=100&all=true&activePage={page}&sortBy=Sort_PopularityUp&orderAsc=true&activeTab=product",
    "red_wine": "https://www.freshdirect.com/browse.jsp?pageType=browse&id=vin_type_reds&pageSize=100&all=true&activePage=1&sortBy=Sort_PopularityUp&orderAsc=true&activeTab=product",
    "white_wine": "https://www.freshdirect.com/browse.jsp?pageType=browse&id=vin_type_whites&pageSize=100&all=true&activePage=1&sortBy=Sort_PopularityUp&orderAsc=true&activeTab=product",
    "gin": "https://www.freshdirect.com/browse.jsp?pageType=browse&id=vin_spirits_gin&pageSize=100&all=false&activePage=1&sortBy=Sort_PopularityUp&orderAsc=true&activeTab=product",
    "liquor": "https://www.freshdirect.com/browse.jsp?pageType=browse&id=vin_spirits_liqueurs&pageSize=100&all=true&activePage=1&sortBy=Sort_PopularityUp&orderAsc=true&activeTab=product",

}

# Categories scraping
for ctg, url in urls_ctgs_dict.items():

    categories[ctg] = []
    number_of_pdcts_in_ctg = 0
    for p in range(100):
        print(ctg, p)
        fpath = fpath_namer(shop_id, 'ctg', ctg, p)
        if not op.exists(fpath):
            # if not freshdirect_was_initialised:
            #     init_freshdirect(driver)
            #     freshdirect_was_initialised = True
            driver.get(url.format(page=p+1))
            sleep(1)
            driver.save_page(fpath, scroll_to_bottom=True)

        # Parsing
        tree = etree.parse(BytesIO(open(fpath, 'rb').read()), parser=parser)
        for li in tree.xpath('//ul[contains(@class, "products transactional")]/li'):
            produrl = li.xpath('.//a[@class="portrait-item-image-link"]/@href')[0]
            produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(
                urlsplit(produrl).query) else produrl
            produrl = clean_url(produrl, root_url)
            products[produrl] = {
                'pdct_name_on_eretailer': ' '.join(
                    ''.join(li.xpath('.//div[@class="portrait-item-header"]//text()')).split()),
                'raw_price': ' '.join(
                    ''.join(li.xpath('.//div[@class="portrait-item-price"]/text()')[:1]).split()),
                'raw_promo_price': ' '.join(''.join(li.xpath(
                    './/div[contains(@class, "portrait-item-price")]/s/text()')).split()),
            }
            if not products[produrl]['raw_price']:
                products[produrl]['raw_price'] = ' '.join(''.join(li.xpath('.//span[@class="save-price"]/text()')).split())
            print(products[produrl], produrl)
            products[produrl]['price'] = getprice(products[produrl]['raw_price'])
            products[produrl]['promo_price'] = getprice(products[produrl]['raw_promo_price'])
            print(products[produrl])
            categories[ctg].append(produrl)

        if len(set(categories[ctg])) == number_of_pdcts_in_ctg:
            break
        else:
            number_of_pdcts_in_ctg = len(set(categories[ctg]))

print([(ctg, len(val)) for ctg, val in categories.items()])


# KW searches Scraping - with selenium - with nb page hard-coded in url - multiple page per search
search_url = "https://www.freshdirect.com/srch.jsp?pageType=search&searchParams={kw}&pageSize=100&all=false&activePage={page}&sortBy=Sort_Relevancy&orderAsc=true&activeTab=product"
for kw in keywords:
    searches[kw] = []
    number_of_pdcts_in_kw_search = 0
    
    for p in range(3):
        # Storing and extracting infos
        urlp = search_url.format(kw=kw, page=p)
        
        fpath = fpath_namer(shop_id, 'search', kw, p)
        if not op.exists(fpath):
            # if not freshdirect_was_initialised:
            #     init_freshdirect(driver)
            #     freshdirect_was_initialised = True
            driver.get(urlp)
            sleep(3)
            driver.save_page(fpath, scroll_to_bottom=True)
        tree = etree.parse(BytesIO(open(fpath, 'rb').read()), parser=parser)

        # Parsing
        for li in tree.xpath('//ul[contains(@class, "products transactional")]/li'):
            produrl = li.xpath('.//a[@class="portrait-item-image-link"]/@href')[0]
            produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(
                urlsplit(produrl).query) else produrl
            produrl = clean_url(produrl, root_url)
            products[produrl] = {
                'pdct_name_on_eretailer': ' '.join(
                    ''.join(li.xpath('.//div[@class="portrait-item-header"]//text()')).split()),
                'raw_price': ' '.join(
                    ''.join(li.xpath('.//div[@class="portrait-item-price"]/text()')[:1]).split()),
                'raw_promo_price': ' '.join(''.join(li.xpath(
                    './/div[contains(@class, "portrait-item-price")]/s/text()')).split()),
            }
            if not products[produrl]['raw_price']:
                products[produrl]['raw_price'] = ' '.join(''.join(li.xpath('.//span[@class="save-price"]/text()')).split())
            print(products[produrl], produrl)
            products[produrl]['price'] = getprice(products[produrl]['raw_price'])
            products[produrl]['promo_price'] = getprice(products[produrl]['raw_promo_price'])
            print(products[produrl])


            searches[kw].append(produrl)
        if len(set(searches[kw])) == number_of_pdcts_in_kw_search:
            break
        else:
            number_of_pdcts_in_kw_search = len(set(searches[kw]))

    print(kw, p, len(searches[kw]))




# Download the pages - with selenium
brm = BrandMatcher()
for url in sorted(list(set(products))):
    d = products[url]
    if brm.find_brand(d['pdct_name_on_eretailer'])['brand'] in mh_brands:
        print(d['pdct_name_on_eretailer'])
        url_mod = clean_url(url, root_url=root_url)
        
        fname = fpath_namer(shop_id, 'pdct', d['pdct_name_on_eretailer'], 0)
        if not op.exists(fname):
            if not freshdirect_was_initialised:
                init_freshdirect(driver)
                freshdirect_was_initialised = True
            driver.get(url_mod)
            sleep(2)
            driver.save_page(fname, scroll_to_bottom=True)
        tree = etree.parse(open(fname), parser=parser)

        products[url].update({
            'pdct_name_on_eretailer': ' '.join(''.join(tree.xpath('//h1[@class="pdpTitle"]//span[1]//text()')).split()),
            'volume': ' '.join(''.join(tree.xpath('//div[contains(@class, "pdp-info")]//text()')).split()),
            'pdct_img_main_url': clean_url(''.join(tree.xpath('//div[@class="main-image"]/img/@src')), root_url),
            'ctg_denom_txt': ' '.join(' '.join(tree.xpath('//ul[@class="breadcrumbs"]//text()')).split()),
        })
        print(products[url])




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
