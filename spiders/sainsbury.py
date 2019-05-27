import os.path as op
from io import BytesIO

from lxml import etree

parser = etree.HTMLParser(encoding='utf-8')
from time import sleep
from urllib.parse import urlsplit, parse_qs
import requests
import requests_cache, imghdr
from parse import parse
from validators import validate_raw_files
from create_csvs import create_csvs


from ers import all_keywords_uk as keywords
from ers import fpath_namer, mh_brands, clean_url, headers
from matcher import BrandMatcher
from ers import COLLECTION_DATE, file_hash, img_path_namer
import shutil
from custom_browser import CustomDriver


# Init variables and assets
shop_id = 'sainsbury'
root_url = 'https://www.sainsburys.co.uk'
requests_cache.install_cache(fpath_namer(shop_id, 'requests_cache'))
country = 'UK'
searches, categories, products = {}, {}, {}
driver = CustomDriver(headless=True, download_images=False)


def getprice(pricestr):
    if pricestr == '':
        return pricestr
    pricestr = pricestr.replace(',', '').strip()
    price = parse('£{pound:d}.{pence:d}', pricestr)
    if price is None:
        price = parse('{pence:d}p', pricestr)
        return price.named['pence']
    else:
        return price.named['pound'] * 100 + price.named['pence']


urls_ctgs_dict = {
            'champagne'   : 'https://www.sainsburys.co.uk/shop/CategoryDisplay?langId=44&storeId=10151&catalogId=10123&categoryId=340867&orderBy=FAVOURITES_ONLY%7CSEQUENCING%7CTOP_SELLERS&beginIndex=0&promotionId=&listId=&searchTerm=&hasPreviousOrder=&previousOrderId=&categoryFacetId1=&categoryFacetId2=&ImportedProductsCount=&ImportedStoreName=&ImportedSupermarket=&bundleId=&parent_category_rn=340854&top_category=340854&pageSize=108#langId=44&storeId=10151&catalogId=10123&categoryId=340867&parent_category_rn=340854&top_category=340854&pageSize=108&orderBy=FAVOURITES_ONLY%7CSEQUENCING%7CTOP_SELLERS&searchTerm=&beginIndex=0',
            'sparkling'   : 'https://www.sainsburys.co.uk/shop/gb/groceries/beer-wine-and-spirits-/CategoryDisplay?langId=44&storeId=10151&catalogId=10123&categoryId=340869&orderBy=FAVOURITES_ONLY%7CSEQUENCING%7CTOP_SELLERS&beginIndex=0&promotionId=&listId=&searchTerm=&hasPreviousOrder=&previousOrderId=&categoryFacetId1=&categoryFacetId2=&ImportedProductsCount=&ImportedStoreName=&ImportedSupermarket=&bundleId=&parent_category_rn=340854&top_category=340854&pageSize=108',
            'still_wines' : 'https://www.sainsburys.co.uk/shop/gb/groceries/beer-wine-and-spirits-/CategoryDisplay?langId=44&storeId=10151&catalogId=10123&categoryId=340914&orderBy=FAVOURITES_FIRST&beginIndex=0&promotionId=&listId=&searchTerm=&hasPreviousOrder=&previousOrderId=&categoryFacetId1=&categoryFacetId2=&ImportedProductsCount=&ImportedStoreName=&ImportedSupermarket=&bundleId=&parent_category_rn=340854&top_category=340854&pageSize=108#langId=44&storeId=10151&catalogId=10123&categoryId=340914&parent_category_rn=340854&top_category=340854&pageSize=108&orderBy=FAVOURITES_FIRST&searchTerm=&beginIndex=0',
            'whisky'      : 'https://www.sainsburys.co.uk/shop/CategoryDisplay?pageSize=108&searchTerm=&catalogId=10123&orderBy=FAVOURITES_FIRST&top_category=340854&parent_category_rn=340854&listId=&categoryId=340926&langId=44&beginIndex=36&storeId=10151&promotionId=',
            'cognac'      : 'https://www.sainsburys.co.uk/shop/gb/groceries/beer-wine-and-spirits-/brandy---cognac-44#langId=44&storeId=10151&catalogId=10123&categoryId=340891&parent_category_rn=340854&top_category=340854&pageSize=108&orderBy=FAVOURITES_ONLY%7CSEQUENCING%7CTOP_SELLERS&searchTerm=&beginIndex=0',
            'vodka'       : 'https://www.sainsburys.co.uk/shop/gb/groceries/beer-wine-and-spirits-/vodka-340889-44#langId=44&storeId=10151&catalogId=10123&categoryId=340889&parent_category_rn=340854&top_category=340854&pageSize=108&orderBy=FAVOURITES_ONLY%7CSEQUENCING%7CTOP_SELLERS&searchTerm=&beginIndex=0',
            'red_wine'    : 'https://www.sainsburys.co.uk/shop/gb/groceries/beer-wine-and-spirits-/vodka-340889-44#langId=44&storeId=10151&catalogId=10123&categoryId=340889&parent_category_rn=340854&top_category=340854&pageSize=108&orderBy=FAVOURITES_ONLY%7CSEQUENCING%7CTOP_SELLERS&searchTerm=&beginIndex=0',
            'white_wine'  : 'https://www.sainsburys.co.uk/shop/gb/groceries/beer-wine-and-spirits-/white-wine-44#langId=44&storeId=10151&catalogId=10123&categoryId=340889&parent_category_rn=340854&top_category=340854&pageSize=108&orderBy=FAVOURITES_ONLY%7CSEQUENCING%7CTOP_SELLERS&searchTerm=&beginIndex=0',
            'gin'         : 'https://www.sainsburys.co.uk/shop/gb/groceries/beer-wine-and-spirits-/gin-340887-44#langId=44&storeId=10151&catalogId=10123&categoryId=340889&parent_category_rn=340854&top_category=340854&pageSize=108&orderBy=FAVOURITES_ONLY%7CSEQUENCING%7CTOP_SELLERS&searchTerm=&beginIndex=0',
            'rum'         : 'https://www.sainsburys.co.uk/shop/gb/groceries/beer-wine-and-spirits-/rum-44#langId=44&storeId=10151&catalogId=10123&categoryId=340889&parent_category_rn=340854&top_category=340854&pageSize=108&orderBy=FAVOURITES_ONLY%7CSEQUENCING%7CTOP_SELLERS&searchTerm=&beginIndex=0',
            'tequila'     : 'https://www.sainsburys.co.uk/shop/gb/groceries/beer-wine-and-spirits-/tequila-44#langId=44&storeId=10151&catalogId=10123&categoryId=340889&parent_category_rn=340854&top_category=340854&pageSize=108&orderBy=FAVOURITES_ONLY%7CSEQUENCING%7CTOP_SELLERS&searchTerm=&beginIndex=0',
            'liquor'      : 'https://www.sainsburys.co.uk/shop/gb/groceries/beer-wine-and-spirits-/liqueurs---speciality-spirits#langId=44&storeId=10151&catalogId=10123&categoryId=340889&parent_category_rn=340854&top_category=340854&pageSize=108&orderBy=FAVOURITES_ONLY%7CSEQUENCING%7CTOP_SELLERS&searchTerm=&beginIndex=0',

}


# Categories scraping
for ctg, url in urls_ctgs_dict.items():
    print(ctg, url)
    categories[ctg] = []
    fpath = fpath_namer(shop_id, 'ctg', ctg, 0)
    if not op.exists(fpath):
        driver.get(url)
        sleep(1)
        driver.save_page(fpath, scroll_to_bottom=True)
    tree = etree.parse(BytesIO(open(fpath, 'rb').read()), parser=parser)
    for li in tree.xpath('//ul[@class="productLister gridView"]/li'):
        produrl = li.xpath('.//h3/a/@href')[0]
        produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
        categories[ctg].append(produrl)
        products[produrl] = {
            'pdct_name_on_eretailer': " ".join("".join(li.xpath('.//div[@class="productNameAndPromotions"]//h3//text()')).split()),
            'raw_price': " ".join("".join(li.xpath('.//p[@class="pricePerUnit"]/text()')[0]).split()),
        }
        print(products[produrl])
        products[produrl]['price'] = getprice(products[produrl]['raw_price'])
        print(products[produrl])
print([(c, len(categories[c])) for c in categories])


for kw in keywords:
    searches[kw] = []
    number_of_pdcts_in_kw_search = 0
    search_input_box_xpath = u'//*[@id="search"]'
    fpath = fpath_namer(shop_id, 'search', kw, 0)

    if not op.exists(fpath_namer(shop_id, 'search', kw, 0)):
        if not driver.check_exists_by_xpath(search_input_box_xpath):
            # Getting back to root if search input box is not found
            driver.get('https://www.sainsburys.co.uk/shop/gb/groceries/beer-wine-and-spirits-/')
        driver.text_input(kw, search_input_box_xpath, enter=True)
        sleep(2)
        driver.save_page(fpath, scroll_to_bottom=True)

    # Storing and extracting infos
    tree = etree.parse(open(fpath, 'rb'), parser=parser)
    for li in tree.xpath('//ul[@class="productLister gridView"]/li'):
        produrl = li.xpath('.//h3/a/@href')[0]
        produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
        searches[kw].append(produrl)
        products[produrl] = {
            'pdct_name_on_eretailer': " ".join("".join(li.xpath('.//div[@class="productNameAndPromotions"]//h3//text()')).split()),
            'raw_price': " ".join("".join(li.xpath('.//p[@class="pricePerUnit"]/text()')[0]).split()),
        }
        print(products[produrl])
        products[produrl]['price'] = getprice(products[produrl]['raw_price'])
        print(products[produrl])
    print(searches)


# Download the pages
brm = BrandMatcher()
for url in sorted(products):
    d = products[url]
    if brm.find_brand(d['pdct_name_on_eretailer'])['brand'] in mh_brands:
        url_mod = clean_url(url, root_url=root_url)
        fname = fpath_namer(shop_id, 'pdct', d['pdct_name_on_eretailer'], 0)
        if not op.exists(fname):
            print(url_mod)
            driver.get(url_mod)
            sleep(2)
            driver.save_page(fname, scroll_to_bottom=True)
        tree = etree.parse(open(fname), parser=parser)
        products[url] = {
            'pdct_name_on_eretailer': ''.join(tree.xpath('//div[@class="productTitleDescriptionContainer"]/h1/text()')),
            'volume': ''.join(tree.xpath('//div[@class="productTitleDescriptionContainer"]/h1//text()')),
            'raw_price': ''.join(tree.xpath('//div[@class="priceTab activeContainer priceTabContainer"]/div/p[1]/text()')),
            'raw_promo_price': ''.join(tree.xpath('//ghjklm')),
            'pdct_img_main_url': clean_url(''.join(tree.xpath('//*[@id="productImageHolder"]//img/@src')), root_url),
            'ctg_denom_txt': ' '.join(''.join(tree.xpath('//ul[@id="breadcrumbNavList"]//text()')).split()),
        }
        products[url]['price'] = getprice(products[url]['raw_price'])
        print(d['pdct_name_on_eretailer'], products[url])



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
