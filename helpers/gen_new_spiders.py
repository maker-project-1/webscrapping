import os
import os.path as op

import pandas as pd

from ers import TEST_PAGES_FOLDER_PATH

df = pd.read_excel('/code/mhers/ressources/ERS-referential-shops-japan.xlsx', index_col=None)

for c, row in df.iterrows():
    SHOP_ID = row['shop_computer_id']
    SHOP_URL = row['shop_url']
    COUNTRY = row['country']
    COUNTRY_LOWER = COUNTRY.lower()

    #  Create the folders :
    shop_testpages_folder = op.join(TEST_PAGES_FOLDER_PATH, SHOP_ID)
    if not op.exists(shop_testpages_folder):
        os.mkdir(shop_testpages_folder)
        for name in ['ctg_page_test.html', 'kw_page_test.html', 'pdct_page_test.html']:
            with open(op.join(shop_testpages_folder, name), 'w') as f:
                f.write(' ')

    t = open('/code/mhers/helpers/exple_spider.py', 'r').read()
    t = t.replace('COUNTRYLOWER', '"' + COUNTRY_LOWER + '"')
    t = t.replace('COUNTRY', '"' + COUNTRY + '"')
    t = t.replace('SHOP_URL', '"' + SHOP_URL + '"')
    t = t.replace('SHOP_ID', '"' + SHOP_ID + '"')

    with open(op.join('/data/eretail/japanese_stores/spiders', SHOP_ID + '.py'), 'w') as f:
        f.write(t)
