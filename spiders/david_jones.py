
import os.path as op
import re

from lxml import etree

parser = etree.HTMLParser(encoding='utf-8')
from time import sleep
from urllib.parse import urlsplit, parse_qs
import requests
import requests_cache
from validators import validate_raw_files
from create_csvs import create_csvs
from ers import all_keywords_aus as keywords, fpath_namer, mh_brands, clean_url

from matcher import BrandMatcher
from ers import COLLECTION_DATE, file_hash, img_path_namer
from custom_browser import CustomDriver
from parse import parse


# Init variables and assets
shop_id = "david_jones"
root_url = "http://www.davidjones.com"
requests_cache.install_cache(fpath_namer(shop_id, 'requests_cache'))
country = "AUS"


searches, categories, products = {}, {}, {}
# If necessary
driver = CustomDriver(headless=True)


def getprice(pricestr):
    if pricestr == '':
        return pricestr
    pricestr = re.sub("[^0-9.$]", "", pricestr)
    price = parse('${pound:d}.{pence:d}', pricestr)
    if price is None:
        price = parse('{pence:d}p', pricestr)
        return price.named['pence']
    else:
        return price.named['pound'] * 100 + price.named['pence']


urls_ctgs_dict = {
    'champagne': 'https://www.davidjones.com/home-and-food/food-and-wine/wine-champagne-and-spirits/champagne-and-sparkling-wines',
    'sparkling': 'https://www.davidjones.com/home-and-food/food-and-wine/wine-champagne-and-spirits/champagne-and-sparkling-wines',
    'liquor': 'https://www.davidjones.com/home-and-food/food-and-wine/wine-champagne-and-spirits/liquor-and-spirits',
    'vodka': 'https://www.davidjones.com/home-and-food/food-and-wine/wine-champagne-and-spirits/liquor-and-spirits',
    'whisky': 'https://www.davidjones.com/home-and-food/food-and-wine/wine-champagne-and-spirits/liquor-and-spirits',
    'cognac': 'https://www.davidjones.com/home-and-food/food-and-wine/wine-champagne-and-spirits/liquor-and-spirits',
    'red_wine': 'https://www.davidjones.com/home-and-food/food-and-wine/wine-champagne-and-spirits/red-wine',
    'white_wine': 'https://www.davidjones.com/home-and-food/food-and-wine/wine-champagne-and-spirits/white-wine',
    'still_wines': 'https://www.davidjones.com/home-and-food/food-and-wine/wine-champagne-and-spirits/white-wine',
}


# Category Scraping - with selenium - multiple pages per category (click on next page)
for ctg, url in urls_ctgs_dict.items():
    categories[ctg] = []
    number_of_pdcts_in_ctg = 0
    fpath = fpath_namer(shop_id, 'ctg', ctg, 0)
    if not op.exists(fpath):
        driver.get(url)
        click_trials = 0
        while True:
            driver.scroll_to_bottom()
            sleep(2)
            if driver.wait_for_xpath('//a[@class="btn load-products loading-button externalLink"]'):
                driver.waitclick('//a[@class="btn load-products loading-button externalLink"]')
                click_trials += 1
                if click_trials > 1:
                    break
            else:
                break
        driver.save_page(fpath)

    tree = etree.parse(open(fpath, 'rb'), parser=parser)
    # for li in tree.xpath('//li[contains(@id,"WC_CatalogSearchResultDisplay")]'):
    for li in tree.xpath('//div[@class="item isUpdated"]'):
        if not li.xpath('.//figure/a/@href'):
            continue
        # produrl = li.xpath('./a/@href')[0]
        produrl = li.xpath('.//figure/a/@href')[0]
        produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
        products[produrl] = {
            'pdct_name_on_eretailer': ' '.join(t.strip() for t in li.xpath('.//h4//text()')),
            'raw_price': ' '.join(t.strip() for t in li.xpath('.//*[@class="price was"]//text()')),
            'raw_promo_price': ' '.join(t.strip() for t in li.xpath('.//*[@itemprop="price"]//text()')),
            'pdct_img_main_url': clean_url(li.xpath('.//figure/a/img/@src')[0], root_url)

        }
        print(products[produrl], produrl)
        products[produrl]['price'] = getprice(products[produrl]['raw_price'])
        products[produrl]['promo_price'] = getprice(products[produrl]['raw_promo_price'])
        print(products[produrl])

        categories[ctg].append(produrl)
    print(ctg, url, 0, len(categories[ctg]))

print([(c, len(categories[c])) for c in categories])


# KW searches Scraping - with selenium - with nb page hard-coded in url - multiple page per search
search_url = "https://search.www.davidjones.com/search?w={kw}"
for kw in keywords:
    searches[kw] = []
    number_of_pdcts_in_kw_search = 0

    # Storing and extracting infos
    urlp = search_url.format(kw=kw)
    fpath = fpath_namer(shop_id, 'search', kw, 0)

    if not op.exists(fpath):
        driver.get(urlp)
        click_trials = 0
        while True:
            driver.scroll_to_bottom()
            sleep(2)
            if driver.wait_for_xpath('//a[@class="btn load-products loading-button externalLink"]'):
                driver.waitclick('//a[@class="btn load-products loading-button externalLink"]')
                click_trials += 1
                if click_trials > 1:
                    break
            else:
                break
        driver.save_page(fpath)

    tree = etree.parse(open(fpath, 'rb'), parser=parser)
    # for li in tree.xpath('//li[contains(@id,"WC_CatalogSearchResultDisplay")]'):
    for li in tree.xpath('//div[contains(@class,"item") and contains(@class, "isUpdated")]'):
        if not li.xpath('.//figure/a/@href'):
            continue
        # produrl = li.xpath('./a/@href')[0]
        produrl = li.xpath('.//figure/a/@href')[0]
        produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
        products[produrl] = {
            'pdct_name_on_eretailer': ' '.join(t.strip() for t in li.xpath('.//h4//text()')),
            'raw_price': ' '.join(t.strip() for t in li.xpath('.//*[@class="price was"]//text()')),
            'raw_promo_price': ' '.join(t.strip() for t in li.xpath('.//*[@itemprop="price"]//text()')),
            'pdct_img_main_url': clean_url(li.xpath('.//figure/a/img/@src')[0], root_url)

        }
        print(products[produrl], produrl)
        products[produrl]['price'] = getprice(products[produrl]['raw_price'])
        products[produrl]['promo_price'] = getprice(products[produrl]['raw_promo_price'])
        print(products[produrl])
        searches[kw].append(produrl)
    print(kw, len(searches[kw]))


# Download the pages - with selenium
brm = BrandMatcher()
for url in sorted(list(set(products))):
    d = products[url]
    if brm.find_brand(d['pdct_name_on_eretailer'])['brand'] in mh_brands:
        print(d['pdct_name_on_eretailer'])
        url_mod = clean_url(url, root_url=root_url)
        
        fname = fpath_namer(shop_id, 'pdct', d['pdct_name_on_eretailer'], 0)
        if not op.exists(fname):
            driver.get(url_mod)
            sleep(2)
            driver.save_page(fname, scroll_to_bottom=True)
        tree = etree.parse(open(fname), parser=parser)

        products[url].update({
            'volume': ' '.join(''.join(tree.xpath('//span[@class="one-item selected"]//text()')).split()),
            'pdct_img_main_url': clean_url(''.join(tree.xpath('//section[@class="product-detail"]//img[@itemprop="image"]/@src')), root_url),
            'ctg_denom_txt': ' '.join(' '.join(tree.xpath('//ul[@id="breadcrumb"]//text()')).split()),
        })
        print(products[url])

# Download images
for url, pdt in products.items():
     if 'pdct_img_main_url' in pdt and pdt['pdct_img_main_url'] and brm.find_brand(pdt['pdct_name_on_eretailer'])['brand'] in mh_brands:
         print(pdt['pdct_name_on_eretailer'] + "." + pdt['pdct_img_main_url'].split('.')[-1])
         print(pdt['pdct_img_main_url'])
         img_path = img_path_namer(shop_id, pdt['pdct_name_on_eretailer'] + "." + pdt['pdct_img_main_url'].split('.')[-1])
         r = requests.get(pdt['pdct_img_main_url'])
         with open(img_path, 'wb') as out_file:
             out_file.write(r.content)
         products[url].update({'img_path': img_path, 'img_hash': file_hash(img_path)})

create_csvs(products, categories, searches, shop_id, fpath_namer(shop_id, 'raw_csv'), COLLECTION_DATE)
validate_raw_files(fpath_namer(shop_id, 'raw_csv'))
driver.quit()
