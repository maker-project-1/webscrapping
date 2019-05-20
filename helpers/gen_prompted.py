import os.path as op
from glob import glob

incipit = """from time import sleep
import sys
try:
    reload(sys)
    sys.setdefaultencoding('utf-8')
except:
    pass
from lxml import etree
from io import BytesIO
import pandas as pd
import os.path as op
import pickle
parser = etree.HTMLParser(encoding='utf-8')
from custom_browser import CustomDriver


# Initing
driver = CustomDriver(headless=False)

"""

end = """
####
search_box_xpath = '//*'
items_xpath = '//*'
####

l = []
for kw in ['vodka', 'champagne', 'whisky', 'sparkling', 'cognac', 'still wine']:
    print(kw, shop_id)
    driver.get(root_url)
    driver.text_input(kw, search_box_xpath, timeout=5)
    try:driver.wait_for_xpath(items_xpath, timeout=5)
    except:
        print('No response for kw', kw)
        continue
    sleep(1.5)
    fpath = '/tmp/prompted ' + shop_id + ' ' + kw + '.html'
    driver.save_page(fpath, scroll_to_bottom=True)
    tree = etree.parse(BytesIO(open(fpath, 'rb').read()), parser=parser)
    for c, li in enumerate(tree.xpath(items_xpath)):
        txt = ' '.join(''.join(li.xpath('.//text()')).split())
        print(kw, shop_id, root_url, txt)
        tmp = {'shop_id': shop_id, 'kw': kw, 'num': c, 'product': txt}
        l.append(tmp)

from ers import BASE_DIR
pd.DataFrame(l).to_csv(op.join(BASE_DIR, "data", 'shop_id', shop_id + '_prompted.csv'), index=None, sep=";")
"""

for f in glob('../spiders/*.py'):
    if f == 'spiders/__init__.py':
        continue
    print(f)
    text = incipit

    for l in open(f):
        if l.startswith('shop_id'):
            exec(l)
            text += 'shop_id = "' + shop_id + '"\n'

        if l.startswith('root_url'):
            exec(l)
            text += 'root_url = "'  + root_url + '"\n'

    with open(op.join('../prompted', shop_id + '.py'), 'w') as f:
        f.write(text + end)

