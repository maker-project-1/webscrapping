import os.path as op

from lxml import etree

parser = etree.HTMLParser()
from time import sleep
import requests
import imghdr


from validators import validate_raw_files
from create_csvs import create_csvs
from ers import all_keywords_usa as keywords, fpath_namer, mh_brands, headers
from matcher import BrandMatcher
from ers import COLLECTION_DATE, file_hash, img_path_namer
import shutil
from custom_browser import CustomDriver
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Init variables and assets
shop_id = 'abcfws'
root_url = 'http://www.abcfws.com/'
# requests_cache.install_cache(fpath_namer(shop_id, 'requests_cache'))
country = 'USA'
searches, categories, products = {}, {}, {}
driver = CustomDriver(headless=True, download_images=True)


from parse import parse


def getprice(pricestr):
    if not pricestr:
        return
    price = parse('${pound:d}.{pence:d}', pricestr)
    if not price:
        price = parse('${th:d},{pound:d}.{pence:d}', pricestr)
        return price.named['th'] * 100000 + price.named['pound'] * 100 + price.named['pence']
    return price.named['pound'] * 100 + price.named['pence']


categories_urls = {
    'champagne': 'https://www.abcfws.com/thumbnail/WINE/SPARKLING-WINE/CHAMPAGNE/pc/2/c/28/30.uts?currentIndex={start}&pageSize=48',
    'cognac': 'https://www.abcfws.com/category/SPIRITS/BRANDY-COGNAC/pc/46/84.uts?currentIndex={start}&pageSize=48',
    'sparkling': 'http://www.abcfws.com/category/WINE/SPARKLING-WINE/pc/2/68.uts?currentIndex={start}&pageSize=48',
    'vodka': 'https://www.abcfws.com/category/SPIRITS/VODKA/pc/46/47.uts?pageSize=48&currentIndex={start}',
    'whisky': 'https://www.abcfws.com/thumbnail/SPIRITS/WHISKEY/IRISH-WHISKEY/pc/46/c/67/71.uts?currentIndex={start}&pageSize=48',
    'still_wines': 'https://www.abcfws.com/category/WINE/WHITE/pc/2/31.uts?currentIndex={start}&pageSize=48',
    'white_wine':'https://www.abcfws.com/category/WINE/WHITE/pc/2/16.uts?currentIndex={start}&pageSize=48',
    'red_wine':'https://www.abcfws.com/category/WINE/RED/pc/2/3.uts?currentIndex={start}&pageSize=48',
    'gin':'https://www.abcfws.com/category/SPIRITS/GIN/pc/46/50.uts?currentIndex={start}&pageSize=48',
    'tequila':'https://www.abcfws.com/category/SPIRITS/TEQUILA/pc/46/59.uts?currentIndex={start}&pageSize=48',
    'rum':'https://www.abcfws.com/category/SPIRITS/RUM/pc/46/51.uts?currentIndex={start}&pageSize=48',
    'scotch':'https://www.abcfws.com/thumbnail/SPIRITS/WHISKEY/SCOTCH/pc/46/c/67/74.uts?currentIndex={start}&pageSize=48',
    'bourbon':'https://www.abcfws.com/thumbnail/SPIRITS/WHISKEY/BOURBON/pc/46/c/67/69.uts?currentIndex={start}&pageSize=48',
}

for ctg, url in categories_urls.items():
    categories[ctg] = []
    for p, start in enumerate(range(0, 1000, 48)):
        # r = requests.get(url.format(start=start))
        fpath = fpath_namer(shop_id, 'ctg', ctg, p)
        if not op.exists(fpath):
            driver.get(url.format(start = start))
            sleep(2)
            driver.save_page(fpath, scroll_to_bottom=True)
        # tree = etree.parse(BytesIO(r.content), parser=parser)
        tree = etree.parse(open(fpath, 'rb'), parser=parser)
        articles = tree.xpath('//section[contains(@class, "productsList")]/div[@class="product"]')
        aurls = [a.xpath('.//div[@class="name"]/a/@href')[0] for a in articles]
        if not articles:
            break
        categories[ctg] += aurls
        for a in articles:
            data = {
                'url': a.xpath('.//div[@class="name"]/a/@href')[0],
                'pdct_name_on_eretailer': a.xpath('.//div[@class="name"]/a/text()')[0].strip(),
                'volume': a.xpath('.//div[@class="volume"]//text()')[0].strip(),
                'price': getprice(''.join(a.xpath('.//div[@class="price pl0"]/span/text()')).strip()),
                'raw_promo_price': getprice(''.join(a.xpath('.//div[@class="price pl0"]/strike/text()'))),
                # 'img': a.xpath('.//img[@title]/@src')[0],
            }
            if not data['price']:
                assert (a.xpath('.//a[@href="/BourbonLottery"]')
                        or a.xpath('.//a[@class="js-storeAvailabilitySelector"]//text()'))

            products[data['url']] = data
        print(ctg, start, len(articles), len(categories[ctg]))

for kw in keywords:
    searches[kw] = []
    for start in range(0, 1000, 48):
        url = 'http://www.abcfws.com/catalog/search.cmd?form_state=searchForm2&keyword={kw}&currentIndex={start}&pageSize=48'.format(
            kw=kw, start=start)
        # r = requests.get(url)
        # tree = etree.parse(BytesIO(r.content), parser=parser)
        fpath = '/tmp/' + kw.replace(' ', "-") + '.html'
        if not op.exists(fpath):
            driver.get(url)
            sleep(2)
            driver.save_page(fpath, scroll_to_bottom=True)
        tree = etree.parse(open(fpath, 'rb'), parser=parser)
        articles = tree.xpath('//section[contains(@class, "productsList")]/div[@class="product"]')
        aurls = [a.xpath('.//div[@class="name"]/a/@href')[0] for a in articles]
        if not articles:
            break
        searches[kw] += aurls
        for a in articles:
            data = {
                'url': a.xpath('.//div[@class="name"]/a/@href')[0],
                'pdct_name_on_eretailer': a.xpath('.//div[@class="name"]/a/text()')[0].strip(),
                'volume': a.xpath('.//div[@class="volume"]//text()')[0].strip(),
                'price': getprice(''.join(a.xpath('.//div[@class="price pl0"]/span/text()')).strip()),
                'raw_promo_price': getprice(''.join(a.xpath('.//div[@class="price pl0"]/strike/text()'))),
                # 'img': a.xpath('.//img[@title]/@src')[0],
            }
            if not data['price']:
                if not (a.xpath('.//a[@href="/BourbonLottery"]')
                        or a.xpath('.//a[@class="js-storeAvailabilitySelector"]//text()')):
                    print('NOPRICE', data['pdct_name_on_eretailer'])

            products[data['url']] = data
            products[data['url']]['pdct_name_on_eretailer'] = products[data['url']]['pdct_name_on_eretailer'][:-1]
        print(kw, start, len(articles), len(searches[kw]))

brm = BrandMatcher()
for url in sorted(set([tmp for tmp, v in products.items()])):
    d = products[url]
    if brm.find_brand(d['pdct_name_on_eretailer'])['brand'] in mh_brands:
        print(d['pdct_name_on_eretailer'])
        fpath = '/tmp/' + url.replace('/', "-") + '.html'
        if not op.exists(fpath):
            driver.driver.switch_to.window(driver.driver.window_handles[-1])
            driver.get(url)
            sleep(2)
            driver.save_page(fpath, scroll_to_bottom=True)
        tree = etree.parse(open(fpath, 'rb'), parser=parser)
        # r = requests.get(url)
        # tree = etree.parse(BytesIO(r.content), parser=parser)
        data = {
            'pdct_img_main_url': ''.join(tree.xpath('//img[@class="js_mainImage"]/@src')),
            'ctg_denom_txt': ''.join([t.text for li in tree.xpath('//div[@class="breadcrumb-container"]/ul/li') for t in li]),
        }
        products[url].update(data)
        print(products[url])
        # if not r.from_cache:
        #     sleep(2)


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
