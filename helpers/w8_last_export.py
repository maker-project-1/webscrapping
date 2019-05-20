import os.path as op
from glob import glob

import pandas as pd

orig_folder = "/code/mhers/data/w_8/final_csvs_20180821_orig"
dest_folder = "/code/mhers/data/w_8/final_csvs_20180821_wo_japan"

for c, p in enumerate(glob(op.join(orig_folder, '*.csv'))):
    df = pd.read_csv(p, sep=';', index_col=None)
    old_shape = df.shape
    if "country" in df.columns:
        df = df[df['country'] != 'JP']
    dest_p = op.join(dest_folder, op.basename(p))
    print(c, p, dest_p, old_shape, df.shape, '\n')
    df.to_csv(dest_p, sep=";", index=None)