from lxml import etree
import os.path as op
from io import BytesIO

import pandas as pd
from lxml import etree

parser = etree.HTMLParser(encoding='utf-8')
from custom_browser import CustomDriver

# Initing
driver = CustomDriver(headless=False)

shop_id = "leshop"
root_url = "https://www.leshop.ch/"

####
search_box_xpath = '//*[@id="autocompleteSearchInput"]'
items_xpath = '//*[@data-ng-controller="AutocompleteSearchCtrl as controller"]//div[@class="item"]'
####

l = []
for kw in ['vodka', 'champagne', 'whisky', 'sparkling', 'cognac', 'still wine']:
    driver.get(root_url)
    driver.text_input(kw, search_box_xpath, timeout=5)
    try:driver.wait_for_xpath(items_xpath, timeout=5)
    except:
        continue
    fpath = '/tmp/prompted ' + shop_id + ' ' + kw + '.html'
    driver.save_page(fpath, scroll_to_bottom=True)
    tree = etree.parse(BytesIO(open(fpath, 'rb').read()), parser=parser)
    for c, li in enumerate(tree.xpath(items_xpath)):
        txt = ' '.join(''.join(li.xpath('.//text()')).split())
        print(kw, shop_id)
        tmp = {'shop_id': shop_id, 'kw': kw, 'num': c, 'product': txt}
        l.append(tmp)

df = pd.DataFrame(l).to_csv(op.join("../data_prompted", shop_id + '.csv'), index=None, sep=";")
