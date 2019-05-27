import re
from io import BytesIO

from lxml import etree

parser = etree.HTMLParser(encoding='utf-8')
from time import sleep
from urllib.parse import urlsplit, parse_qs
import requests
import requests_cache, imghdr
from ers import all_keywords_es as keywords, fpath_namer, mh_brands, clean_url, headers

from matcher import BrandMatcher
from ers import COLLECTION_DATE, file_hash, img_path_namer
import shutil
from parse import parse
from validators import validate_raw_files
from create_csvs import create_csvs

# Init variables and assets
shop_id = "vinissimus"
root_url = "https://www.vinissimus.com/es/"
requests_cache.install_cache(fpath_namer(shop_id, 'requests_cache'))
country = "ES"


searches, categories, products = {}, {}, {}
# If necessary
# driver = CustomDriver(headless=False)



def getprice(pricestr):
    if pricestr == '':
        return pricestr
    pricestr = re.sub("[^0-9,€]", "", pricestr)
    price = parse('{pound:d},{pence:d}€', pricestr)
    if price is None:
        price = parse('{pence:d}p', pricestr)
        return price.named['pence']
    else:
        return price.named['pound'] * 100 + price.named['pence']


urls_ctgs_dict = {
    "vodka": "https://www.vinissimus.com/es/destilados/?id_tipo_destilado=vo&start={page}",
    "sparkling": "https://www.vinissimus.com/es/vinos/espumoso/index.html?start={page}",
    "cognac": "https://www.vinissimus.com/es/destilados/?id_tipo_destilado=co&start={page}",
    "champagne": "https://www.vinissimus.com/es/vinos/espumoso/index.html?id_region=cha&start={page}",
    "still_wines": "https://www.vinissimus.com/es/vinos/blanco/index.html?start={page}",
    "whisky": "https://www.vinissimus.com/es/destilados/index.html?id_tipo_destilado=ws&start={page}",
    "red_wine": "https://www.vinissimus.com/es/vinos/tinto/index.html?id_tipo_destilado=ws&start={page}",
    "white_wine": "https://www.vinissimus.com/es/vinos/blanco/index.html?id_tipo_destilado=ws&start={page}",
    "gin": "https://www.vinissimus.com/es/destilados/?id_tipo_destilado=gi&start={page}",
    "tequila": "https://www.vinissimus.com/es/destilados/?id_tipo_destilado=te&start={page}",
    "rum": "https://www.vinissimus.com/es/destilados/?id_tipo_destilado=ro&start={page}",
    "brandy": "https://www.vinissimus.com/es/destilados/?id_tipo_destilado=br&start={page}",
    "bourbon": "https://www.vinissimus.com/es/destilados/?id_tipo_destilado=bo&start={page}",
    "liquor": "https://www.vinissimus.com/es/destilados/?id_tipo_destilado=ot&start={page}",
}


# Category Scraping
for ctg, url in urls_ctgs_dict.items():
    categories[ctg] = []
    number_of_pdcts_in_ctg = 0
    for p in range(100):
        urlp = url.format(page=p*50)

        r = requests.get(urlp)
        with open('/tmp/' + shop_id + '_' + ctg + '.html', 'wb') as f:
            f.write(r.content)
        tree = etree.parse(BytesIO(r.content), parser=parser)
        
        for li in tree.xpath('.//table[@class="table product product-view-2"]/tr'):
            produrl = li.xpath('.//a/@href')[0]
            produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
            produrl = clean_url(produrl, root_url)
            products[produrl] = {
                'pdct_name_on_eretailer': ' '.join(''.join(li.xpath('.//h3//text()')).split()),
                'ctg_denom_txt': ' '.join(''.join(li.xpath('.//h3//text()')).split()),
                'volume': ' '.join(''.join(li.xpath('.//h3//text()')).split()),
                'raw_price': ' '.join(''.join(li.xpath('.//span[@class="price"]//text()')).split()),
                'pdct_img_main_url': clean_url(''.join(li.xpath('.//*[@class="image"]//img/@src')), root_url),
                'raw_promo_price' : '',
            }
            if not products[produrl]['raw_price']:
                products[produrl]['raw_price'] = ' '.join(''.join(li.xpath('.//span[@class="price clearfix"]/text()')).split())
                products[produrl]['raw_promo_price'] = ' '.join(''.join(li.xpath('.//span[@class="price clearfix"]//*[@class="dto"]//text()')).split())

            print(products[produrl], produrl)
            products[produrl]['pdct_img_main_url'] = products[produrl]['pdct_img_main_url'].replace("80x80", '174x241')
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
            sleep(1)
print(categories)

# KW searches Scraping - with selenium - with nb page hard-coded in url - multiple page per search
search_url = "https://www.vinissimus.com/es/resultados_buscador.html?start={page}&query={kw}"
for kw in keywords:
    searches[kw] = []
    number_of_pdcts_in_kw_search = 0
    
    for p in range(10):
        # Storing and extracting infos
        urlp = search_url.format(kw=kw, page=p*50)

        r = requests.get(urlp)
        with open('/tmp/' + shop_id + '_' + kw + '.html', 'wb') as f:
            f.write(r.content)
        tree = etree.parse(BytesIO(r.content), parser=parser)

        for li in tree.xpath('.//table[@class="table product product-view-2"]/tr'):
            produrl = li.xpath('.//a/@href')[0]
            produrl = parse_qs(urlsplit(produrl).query)['url'][0] if 'url' in parse_qs(urlsplit(produrl).query) else produrl
            produrl = clean_url(produrl, root_url)
            products[produrl] = {
                'pdct_name_on_eretailer': ' '.join(''.join(li.xpath('.//h3//text()')).split()),
                'ctg_denom_txt': ' '.join(''.join(li.xpath('.//h3//text()')).split()),
                'volume': ' '.join(''.join(li.xpath('.//h3//text()')).split()),
                'raw_price': ' '.join(''.join(li.xpath('.//span[@class="price"]//text()')).split()),
                'pdct_img_main_url': clean_url(''.join(li.xpath('.//*[@class="image"]//img/@src')), root_url),
                'raw_promo_price' : '',
            }
            if not products[produrl]['raw_price']:
                products[produrl]['raw_price'] = ' '.join(''.join(li.xpath('.//span[@class="price clearfix"]/text()')).split())
                products[produrl]['raw_promo_price'] = ' '.join(''.join(li.xpath('.//span[@class="price clearfix"]//*[@class="dto"]//text()')).split())

            print(products[produrl], produrl)
            products[produrl]['pdct_img_main_url'] = products[produrl]['pdct_img_main_url'].replace("80x80", '174x241')
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


