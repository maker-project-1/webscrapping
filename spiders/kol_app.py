from lxml import etree
from io import BytesIO
from io import BytesIO

from lxml import etree

parser = etree.HTMLParser(encoding='utf-8')
import requests
import requests_cache, imghdr

from validators import validate_raw_files
from create_csvs import create_csvs

from ers import fpath_namer, mh_brands, headers
from matcher import BrandMatcher
from ers import COLLECTION_DATE, file_hash, img_path_namer
import shutil

# Init variables and assets
shop_id = 'kol_app'
root_url = 'https://kol-app.com'
requests_cache.install_cache(fpath_namer(shop_id, 'requests_cache'))
country = 'UK'
searches, categories, products = {}, {}, {}

categories_urls = {
    'champagne': 'https://kol-app.com/fr/categorie/bulles/champagnes',
    'sparkling': 'https://kol-app.com/fr/categorie/bulles/les-effervescents',
    'still_wines': 'https://kol-app.com/fr/categorie/vins',
    'whisky': 'https://kol-app.com/fr/categorie/spiritueux/whisky',
    'cognac': 'https://kol-app.com/fr/categorie/spiritueux/cognac',
    'vodka': 'https://kol-app.com/fr/categorie/spiritueux/vodka',
    'red_wine': 'https://kol-app.com/fr/categorie/vins/rouge',
    'white_wine': 'https://kol-app.com/fr/categorie/vins/blanc',
    'rum': 'https://kol-app.com/fr/categorie/spiritueux/rhum',
    'tequila': 'https://kol-app.com/fr/categorie/spiritueux/tequila',
    'gin': 'https://kol-app.com/fr/categorie/spiritueux/gin',
}

tmp_categories = {}
# Category Scraping
for ctg, url in categories_urls.items():
    spliturl = url.split('/')
    breadcrum = spliturl[spliturl.index('categorie') + 1:]
    r = requests.get(url)
    tree = etree.parse(BytesIO(r.content), parser=parser)
    volumes = {}
    for a in tree.xpath(
            '//article[@class="c-product-detail o-catalog__item__detail js-catalog-detail"]'):
        name = a.xpath('.//h3[@class="c-product-detail__title"]//text()')[0]
        infos = a.xpath('.//span[@class="c-product-detail__ref"]//text()')[0].strip().split('-')
        volume = infos[0]
        volumes[name] = volume

    articles = [a for a in tree.xpath(
        '//article[@class="c-product-item o-catalog__item__preview js-catalog-preview"]')]
    tmp_categories[ctg] = [a.attrib['id'] for a in articles]
    categories[ctg] = []
    for a in articles:
        if a.attrib['data-product-name'] in volumes:
            spliturl = url.split('/')
            categories[ctg].append(a.attrib['id'])
            products[a.attrib['id']] = {
                'pdct_name_on_eretailer': a.attrib['data-product-name'],
                'volume': volumes[a.attrib['data-product-name']],
                'price':  float(a.attrib['data-price']),
                'pdct_img_main_url': a.xpath('.//img/@src')[0],
                'ctg_denom_txt': breadcrum
            }



# WARNING pas de recherche : match la catégorie et ajoute une ancre sur le produit trouvé

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
