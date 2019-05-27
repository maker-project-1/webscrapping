from lxml import etree
from io import BytesIO
from io import BytesIO

from lxml import etree

parser = etree.HTMLParser()
from urllib.parse import quote_plus
import requests
import requests_cache, imghdr

from validators import validate_raw_files
from create_csvs import create_csvs
from ers import all_keywords_usa as keywords, fpath_namer, mh_brands, clean_url, headers
from matcher import BrandMatcher
from ers import COLLECTION_DATE, file_hash, img_path_namer
import shutil
import re
# Init variables and assets
shop_id = 'astor_wines'
root_url = 'http://www.astorwines.com'
requests_cache.install_cache(fpath_namer(shop_id, 'requests_cache'))
country = 'USA'
searches, categories, products = {}, {}, {}


from parse import parse


def getprice(pricestr):
    if not pricestr:
        return
    pricestr = re.sub("[^0-9.$]", "", pricestr)
    price = parse('${pound:d}.{pence:d}', pricestr)
    if not price:
        price = parse('${th:d},{pound:d}.{pence:d}', pricestr)
        return price.named['th'] * 100000 + price.named['pound'] * 100 + price.named['pence']
    return price.named['pound'] * 100 + price.named['pence']


categories_urls = {
    'champagne': 'http://www.astorwines.com/WineSearchResult.aspx?search=Advanced&term=&cat=1&region=champagne&Page={page}',
    'cognac': "http://www.astorwines.com/SpiritsSearchResult.aspx?p=2&search=Advanced&searchtype=Contains&term=&cat=2&style=2_27&Page={page}",
    'sparkling': "http://www.astorwines.com/WineSearchResult.aspx?p=1&search=Advanced&searchtype=Contains&term=&cat=1&style=2&sparkling=True&Page={page}",
    'vodka': "http://www.astorwines.com/SpiritsSearchResult.aspx?p=2&search=Advanced&searchtype=Contains&term=&cat=2&style=1_20&Page={page}",
    'whisky': "http://www.astorwines.com/SpiritsSearchResult.aspx?p=2&search=Advanced&searchtype=Contains&term=&cat=2&style=2_33&Page={page}",
    'still_wines': "http://www.astorwines.com/WineSearchResult.aspx?p=1&search=Advanced&searchtype=Contains&term=&cat=1&color=White&Page={page}",
    'gin': 'http://www.astorwines.com/SpiritsSearchResult.aspx?p=2&search=Advanced&searchtype=Contains&term=&cat=2&style=1_19&Page={page}',
    'tequila': 'http://www.astorwines.com/SpiritsSearchResult.aspx?p=2&search=Advanced&searchtype=Contains&term=&cat=2&style=1_21&Page={page}',
    'red_wine': 'http://www.astorwines.com/WineSearchResult.aspx?p=1&search=Advanced&searchtype=Contains&term=&cat=1&color=Red&Page={page}',
    'white_wine': 'http://www.astorwines.com/WineSearchResult.aspx?p=1&search=Advanced&searchtype=Contains&term=&cat=1&color=White&Page={page}',
    'rum': 'http://www.astorwines.com/SpiritsSearchResult.aspx?p=2&search=Advanced&searchtype=Contains&term=&cat=2&style=1_22&Page={page}',
    'armagnac': "http://www.astorwines.com/SpiritsSearchResult.aspx?p=2&search=Advanced&searchtype=Contains&term=&cat=2&style=2_25&Page={page}",
    'bourbon': 'http://www.astorwines.com/SpiritsSearchResult.aspx?p=2&search=Advanced&searchtype=Contains&term=&cat=2&style=2_32&Page={page}',
}

tmp_categories = {}
for cat, url in categories_urls.items():
    categories[cat] = []
    tmp_categories[cat] = []
    for page in range(1, 100):
        print(page, url.format(page=page))
        r = requests.get(url.format(page=page))
        tree = etree.parse(BytesIO(r.content), parser=parser)
        articles = tree.xpath('//*[@id="search-results"]//div[@class="item-teaser"]')
        aurls = [a.xpath('.//h2[contains(@class, "item-name")]/a/@href')[0] for a in articles]
        if not articles or all(a in tmp_categories[cat] for a in aurls):
            break
        tmp_categories[cat] += aurls
        for a in articles:
            aurl = a.xpath('.//h2[contains(@class, "item-name")]/a/@href')[0]
            data = {
                'url': a.xpath('.//h2[contains(@class, "item-name")]/a/@href')[0],
                'pdct_name_on_eretailer': a.xpath('.//h2[contains(@class, "item-name")]/a/text()')[0],
                'volume': a.xpath('.//span[@class="small"]//text()')[0].split('|')[-1].strip(),
                'promo_price': getprice(''.join(a.xpath('.//div[contains(@class, "bottle-price-container")]//span[@class="price-sale"]/text()'))),
                'price': getprice(''.join(a.xpath('.//div[contains(@class, "bottle-price-container")]/span[last()-1]/text()|.//span[@class="price-value price-old price-bottle"]//text()'))),
                'img': a.xpath('.//img[contains(@id, "imgItem")]/@src')[0]
            }
            if not data['price'] and not data['promo_price']:
                assert b'This item is currently out of stock' in etree.tostring(a)
            categories[cat].append(aurl)
            products[aurl] = data
        print(cat,  len(articles), len(categories[cat]))


tmp_searches = {}
for kw in keywords:
    searches[kw] = []
    tmp_searches[kw] = []
    for page in range(1, 1000):
        url = 'http://www.astorwines.com/WineSearchResult.aspx?p=1&search=Advanced&searchtype=Contains&tm={kw}&Page={page}'.format(
            page=page, kw=quote_plus(kw))
        print("Requeting", url)
        r = requests.get(url)
        print("Finished")
        with open('/tmp/astor.html', 'wb') as f:
            f.write(r.content)
        tree = etree.parse(BytesIO(r.content), parser=parser)
        articles = tree.xpath('//*[@id="search-results"]//div[@class="item-teaser"]')
        aurls = [a.xpath('.//h2[contains(@class, "item-name")]/a/@href')[0] for a in articles]
        if not articles or all(a in tmp_searches[kw] for a in aurls):
            break
        tmp_searches[kw] += aurls
        for a in articles:
            if not a.xpath('.//span[@class="small"]//text()'):
                print('NOT A BOTTLE', a.xpath('.//h2[contains(@class, "item-name")]/a/text()')[0])
                continue  # its a book !
            aurl = a.xpath('.//h2[contains(@class, "item-name")]/a/@href')[0]
            data = {
                'url': a.xpath('.//h2[contains(@class, "item-name")]/a/@href')[0],
                'pdct_name_on_eretailer': a.xpath('.//h2[contains(@class, "item-name")]/a/text()')[0],
                'volume': a.xpath('.//span[@class="small"]//text()')[0].split('|')[-1].strip(),
                'promo_price': getprice(''.join(a.xpath('.//div[contains(@class, "bottle-price-container")]//span[@class="price-sale"]/text()'))),
                'price': getprice(''.join(a.xpath('.//div[contains(@class, "bottle-price-container")]/span[last()-1]/text()|.//span[@class="price-value price-old price-bottle"]//text()'))),
                'pdct_img_main_url': clean_url(a.xpath('.//img[contains(@id, "imgItem")]/@src')[0], root_url)
            }
            print(data['pdct_img_main_url'])
            if not data['price'] and not data['promo_price']:
                assert b'This item is currently out of stock' in etree.tostring(a)
            searches[kw].append(aurl)
            products[aurl] = data
        print(kw, page,  len(articles), len(searches[kw]))


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