import os.path as op
from io import BytesIO

from lxml import etree

parser = etree.HTMLParser()
from time import sleep
import requests
import requests_cache, imghdr

from validators import validate_raw_files
from create_csvs import create_csvs
from ers import all_keywords_de as keywords, fpath_namer, mh_brands, headers
from matcher import BrandMatcher
from ers import COLLECTION_DATE, file_hash, img_path_namer
import shutil
from custom_browser import CustomDriver

# Init variables and assets
shop_id = 'wine_in_black'
root_url = 'https://www.wine-in-black.de/'
requests_cache.install_cache(fpath_namer(shop_id, 'requests_cache'))
country = 'DE'
searches, categories, products = {}, {}, {}
driver = CustomDriver(headless=True, download_images=True)


from parse import parse


def zero_or_more_string(text):
    return text


zero_or_more_string.pattern = r".*"


def getprice(pricestr):
    if not pricestr:
        return None
    price = parse('{int:d},{dec:d} €{star:z}', pricestr, {"z": zero_or_more_string})
    return price.named['int'] * 100 + price.named['dec']




url = 'https://www.wine-in-black.de/champagne'
ctg = 'champagne'
fpath = fpath_namer(shop_id, 'ctg', ctg)
if not op.exists(fpath):
    driver.get(url)
    sleep(2)
    driver.save_page(fpath)
tree = etree.parse(BytesIO(open(fpath, 'rb').read()), parser=parser)

categories['champagne'] = []
for a in tree.xpath('.//div[@class="productTiles"]/div'):
    data = {
        'url': a.xpath('.//a/@href')[0],
        'pdct_name_on_eretailer': (
            ''.join(t.strip() for t in a.xpath(
                './/div[contains(@class, "product-tile__producer")]//text()') if t.strip()) + ' '
            ''.join(t.strip() for t in a.xpath('.//div[contains(@class, "product-tile__name")]//text()') if t.strip())),
        'price': getprice(''.join(t.strip() for t in a.xpath('.//div[contains(@class, "prices__original")]/span[1]//text()'))),
        'promo_price': getprice(''.join(t.strip() for t in a.xpath('.//div[contains(@class, "prices__value")]/span[1]//text()'))),
        # 'img': a.xpath('.//img/@src')[0]
    }
    assert data['price'] or data['promo_price']
    categories['champagne'].append(data['url'])
    products[data['url']] = data

search_url = "https://www.wine-in-black.de/search?q={kw}"
for kw in keywords:
    print(kw)
    searches[kw] = []
    fpath = fpath_namer(shop_id, 'search', kw)
    if not op.exists(fpath):
        driver.get(search_url.format(kw=kw))
        sleep(2)
        driver.save_page(fpath)
    tree = etree.parse(BytesIO(open(fpath, 'rb').read()), parser=parser)
    for a in tree.xpath('.//div[@class="productTiles"]/div'):
        data = {
            'url': a.xpath('.//a/@href')[0],
            'pdct_name_on_eretailer': (
                ''.join(t.strip() for t in a.xpath(
                    './/div[contains(@class, "product-tile__producer")]//text()') if t.strip()) + ' ' +
                                                                                                  ''.join(
                    t.strip() for t in a.xpath('.//div[contains(@class, "product-tile__name")]//text()') if t.strip())),
            'price': getprice(
                ''.join(t.strip() for t in a.xpath('.//div[contains(@class, "prices__original")]/span[1]//text()'))),
            'promo_price': getprice(
                ''.join(t.strip() for t in a.xpath('.//div[contains(@class, "prices__value")]/span[1]//text()'))),
            # 'img': a.xpath('.//img/@src')[0]
        }
        print(data)
        assert data['price'] or data['promo_price']
        searches[kw].append(data['url'])
        products[data['url']] = data


for url in products:
    r = requests.get('https://www.wine-in-black.de' + url)
    products[url].update({
        'ctg_denom_txt': ' '.join(' '.join(tree.xpath('//div[@class="productIcons__itemText"]//text()')).split()),
        'pdct_img_main_url': tree.xpath('//picture/source/@srcset')[0].split()[:1][0],
    })
    print(products[url])
    tree = etree.parse(BytesIO(r.content), parser=parser)
    for li in tree.xpath('//li[@class="productAttributes__item"]'):
        label = li.xpath('.//div[@class="productAttributes__itemLabel"]//text()')[0].strip()
        value = li.xpath('.//div[@class="productAttributes__itemValue"]//text()')[0].strip()
        if 'Volume' in label:
            products[url]['volume'] = value
    if not r.from_cache:
        sleep(2)


print([(c, len(categories[c])) for c in categories])
print([(c, len(searches[c])) for c in searches])

# Download images
brm = BrandMatcher()
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
