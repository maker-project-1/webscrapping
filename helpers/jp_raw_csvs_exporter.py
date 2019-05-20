import os
import os.path as op
from distutils.dir_util import copy_tree

from ers import shops, BASE_DIR, WAVE_NUMBER

# copy_tree("/a/b/c", "/x/y/z")

shops_jp = list(shops.loc[shops.country == 'JP', 'shop_computer_id'].unique())
shops_jp.remove('seiyu')
shops_jp.remove('bic_camera')

for shop_jp in shops_jp:
    print(shop_jp)
    orig_folder = op.join(BASE_DIR, "cache", "w_" + str(WAVE_NUMBER), shop_jp, 'raw_csv')
    assert op.isdir(orig_folder)
    dest_folder= op.join('/home/renaud/Desktop/mh_export_jp', shop_jp)
    os.makedirs(dest_folder, exist_ok=True)
    copy_tree(orig_folder, dest_folder)
