import os.path as op
import re
from io import BytesIO

from lxml import etree
from parse import parse

parser = etree.HTMLParser()
from time import sleep
from urllib.parse import urlsplit, parse_qs
import requests
import requests_cache, imghdr

from validators import validate_raw_files
from create_csvs import create_csvs
from ers import all_keywords_usa as keywords, fpath_namer, mh_brands, clean_url, headers
from custom_browser import CustomDriver
from matcher import BrandMatcher
from ers import COLLECTION_DATE, file_hash, img_path_namer
import shutil


# Init variables and assets
shop_id = 'applejack_wines_spirits'
root_url = 'https://applejack.com'
requests_cache.install_cache(fpath_namer(shop_id, 'requests_cache'))
country = 'USA'
searches, categories, products = {}, {}, {}
driver = CustomDriver(headless=True)


# Download categories
urls_ctgs_dict = {
            'champagne': 'http://applejack.com/Wine/custitem_cseg_aws_country/France/custitem_cseg_aws_region/Champagne?show=50&display=list',
            'cognac': 'http://applejack.com/Spirits/custitem_aws_product_type/Cognac?show=50&display=list',
            'vodka': 'http://applejack.com/Spirits/custitem_aws_product_type/Vodka?show=50&display=list',
            'whisky': 'http://applejack.com/Spirits/custitem_aws_product_type/Scotch?show=50&display=list',
            'sparkling': 'http://applejack.com/custitem_aws_varietal/Sparkling-Wine?show=50&display=list',
            'still_wines': 'http://applejack.com/Wine?show=50&display=list',
            'tequila': 'https://applejack.com/Spirits/custitem_aws_product_type/Tequila?show=50&display=list',
            'red_wine': 'https://applejack.com/Wine/custitem_aws_product_type/Red-Wine?show=50&display=list',
            'white_wine': 'https://applejack.com/Wine/custitem_aws_product_type/White-Wine?show=50&display=list',
            'rum': 'https://applejack.com/Spirits/custitem_aws_product_type/Rum?show=50&display=list',
            'bourbon': 'https://applejack.com/Spirits/custitem_aws_product_type/Bourbon?show=50&display=list',
            'brandy': 'https://applejack.com/Spirits/custitem_aws_product_type/Brandy?show=50&display=list',
            'schnapps': 'https://applejack.com/Spirits/custitem_aws_product_type/Schnapps?show=50&display=list',
            'liquor': 'https://applejack.com/Spirits/custitem_aws_product_type/Liqueur?show=50&display=list',
        }


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


# Simple case, where the page is hard-coded in the url
for ctg, url in urls_ctgs_dict.items():
    categories[ctg] = []
    number_of_pdcts_in_ctg = 0
    for p in range(100):
        urlp = url + "&page=" + str(p)
        fpath = fpath_namer(shop_id, 'ctg', ctg, p)
        if not op.exists(fpath):
            driver.get(urlp)
            sleep(2)
            driver.save_page(fpath)
        tree = etree.parse(open(fpath, 'rb'), parser=parser)
        for li in tree.xpath('//div[@itemprop="itemListElement"]'):
            produrl = li.xpath('.//a/@href')[0]
            produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
            categories[ctg].append(produrl)
            products[produrl] = {
                'pdct_name_on_eretailer': li.xpath('.//span[@itemprop="name"]//text()')[0],
                'raw_price': li.xpath('.//span[contains(@class, "price-lead")]//text()')[0].split('to ')[-1],
            }
            print(products[produrl], produrl)
            products[produrl]['price'] = getprice(products[produrl]['raw_price'])
            print(products[produrl], produrl)

        if len(set(categories[ctg])) == number_of_pdcts_in_ctg:
            break
        else:
            number_of_pdcts_in_ctg = len(set(categories[ctg]))

# Difficult case, where you should click a button to get on next page and send the request via the search bar
search_url = 'https://applejack.com/custitem_item_type/Item?keywords={kw}'
for kw in keywords:
    print('\n\n', kw)
    searches[kw] = []
    number_of_pdcts_in_kw_search = 0
    search_input_box_xpath = u'//div[@data-view="ItemsSeacher"]/span/input[2]'
    if not op.exists(fpath_namer(shop_id, 'search', kw, 0)):
        # if not driver.check_exists_by_xpath(search_input_box_xpath):
        #     # Getting back to root if search input box is not found
        #     driver.get('https://applejack.com')
        # driver.text_input(kw, search_input_box_xpath, enter=True)
        driver.get(search_url.format(kw=kw))
        sleep(4)
    for p in range(10):
        # Storing and extracting infos
        fpath = fpath_namer(shop_id, 'search', kw, p)
        if not op.exists(fpath):
            sleep(2)
            driver.save_page(fpath)
        tree = etree.parse(open(fpath, 'rb'), parser=parser)
        for li in tree.xpath('//div[@itemprop="itemListElement"]'):
            produrl = li.xpath('.//a/@href')[0]
            produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
            searches[kw].append(produrl)
            products[produrl] = {
                'pdct_name_on_eretailer': li.xpath('.//span[@itemprop="name"]//text()')[0],
                'raw_price': li.xpath('//span[contains(@class, "item-views-price-lead")]//text()')[0].split('to ')[-1],
            }
            print(products
                  [produrl], produrl)
            products[produrl]['price'] = getprice(products[produrl]['raw_price'])
            print(products[produrl], produrl)

        # Going to next page if need be
        next_page_click = '//ul[@class="global-views-pagination-links "]/li/a/i[contains(@class, "next")]'
        if not driver.check_exists_by_xpath(next_page_click):
            break
        else:
            driver.waitclick(next_page_click)

# Download the pages
brm = BrandMatcher()
to_remove_products = []
for url in sorted(products):
    d = products[url]
    if brm.find_brand(d['pdct_name_on_eretailer'])['brand'] in mh_brands:
        url_mod = clean_url(url, root_url=root_url)
        r = requests.get(url_mod, headers)
        with open('/tmp/' + shop_id + '--' + d['pdct_name_on_eretailer'] + '.html', 'wb') as f:
            f.write(r.content)
        tree = etree.parse(BytesIO(r.content), parser=parser)
        products[url].update({
            # 'pdct_name_on_eretailer': ''.join(tree.xpath('//h4[@class="item-details-content-header-title"]//text()')),
            'volume': ''.join(tree.xpath('//div[@class="item-description"]//text()')),
            'raw_promo_price': ''.join(tree.xpath('.//small[contains(@class, "item-views-price-old")]//text()')),
            'raw_price': ''.join(tree.xpath('.//*[contains(@class, "item-views-price-lead")]//text()')),
            'pdct_img_main_url': ''.join(tree.xpath('//div[@class="item-details-image-gallery"]//img/@src')),
            'ctg_denom_txt': ''.join(tree.xpath('//section[@class="item-details-main-content"]//text()')),
        })
        print("products[url]['raw_price']", products[url]['raw_price'])
        if not "to" in products[url]['raw_price'].lower():
            print(products[url], url)
            products[url]['promo_price'] = getprice(products[url]['raw_promo_price'])
            print(products[url], url)
            if not r.from_cache:
                sleep(3)
        else:
            to_remove_products += [url]
            for i in range(1, 7):
                url_vol = url_mod + '?size=' + str(i)
                print("Requesting :", url_vol)
                fpath = fpath_namer(shop_id, 'pdct', d['pdct_name_on_eretailer'] + '?size=' + str(i))
                if not op.exists(fpath):
                    driver.get(url_vol)
                    sleep(2)
                    driver.save_page(fpath)
                tree = etree.parse(open(fpath, 'rb'), parser=parser)
                products[url + '?size=' + str(i)] = {
                    'pdct_name_on_eretailer': ''.join(tree.xpath('//h4[@class="item-details-content-header-title"]//text()')),
                    'volume': ''.join(tree.xpath('//p[@class="item-views-option-tile-title"]//text()')),
                    'raw_promo_price': ''.join(tree.xpath('.//*[contains(@class, "item-views-price-old")]//text()')),
                    'raw_price': ''.join(tree.xpath('.//*[contains(@class, "item-views-price-lead")]//text()')),
                    'pdct_img_main_url': ''.join(tree.xpath('//div[@class="item-details-image-gallery"]//img/@src')),
                    'ctg_denom_txt': ''.join(tree.xpath('//section[@class="item-details-main-content"]//text()')),
                }
                print(products[url + '?size=' + str(i)]['raw_price'].lower())
                if "to" not in products[url + '?size=' + str(i)]['raw_price'].lower():
                    print(products[url + '?size=' + str(i)], url + '?size=' + str(i))
                    products[url + '?size=' + str(i)]['promo_price'] = getprice(products[url + '?size=' + str(i)]['raw_promo_price'])
                    products[url + '?size=' + str(i)]['price'] = getprice(products[url + '?size=' + str(i)]['raw_price'])
                    print(products[url + '?size=' + str(i)], url + '?size=' + str(i))
                else:
                    del products[url + '?size=' + str(i)]
                if not r.from_cache:
                    sleep(3)


products['/Belvedere-Vodka'] = products['/Belvedere-Vodka?size=' + str(3)]
del products['/Belvedere-Vodka?size=' + str(3)]

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