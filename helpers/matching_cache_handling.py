import json
import os.path as op

import pandas as pd

from ers import BRAND_MATCHING_JSON
from ers import RAW_BRANDS_XLSX, RAW_KWS_XLSX, RAW_PDCTS_XLSX, RAW_CTGS_XLSX, RAW_PROMPTED_XLSX

# Clean cache
if False:
    if input('Clean cache BRAND_MATCHING_JSON ? y/n').lower() == 'y':
        with open(BRAND_MATCHING_JSON, 'w') as f:
            json.dump({}, f)
            raise Exception('Cache cleaned')

if True:
    # Brand matching cache storing
    if not op.exists(BRAND_MATCHING_JSON):
        with open(BRAND_MATCHING_JSON, 'w') as f:
            json.dump({}, f)
    else:
        with open(BRAND_MATCHING_JSON, 'r') as f:
            d = json.load(f)
            print('Existing cache has ', len(d.keys()), 'entries')
        if input('Do you want to clean BRAND_MATCHING_JSON cache ? y/n').lower() == 'y':
            d = {}
        else:
            print("Using existing cache")

    print('Reading csvs to upload to cache')
    df = pd.concat([
          pd.read_excel(RAW_KWS_XLSX, index_col=False)[['pdct_name_on_eretailer', 'brnd']],
          pd.read_excel(RAW_PDCTS_XLSX, index_col=False)[['pdct_name_on_eretailer', 'brnd']],
          pd.read_excel(RAW_CTGS_XLSX, index_col=False)[['pdct_name_on_eretailer', 'brnd']],
          pd.read_excel(RAW_BRANDS_XLSX, index_col=False)[['pdct_name_on_eretailer', 'brnd']],
          pd.read_excel(RAW_PROMPTED_XLSX, index_col=False)[['pdct_name_on_eretailer', 'brnd']]
    ])

    print(df.shape)
    df = pd.DataFrame(df[(df['pdct_name_on_eretailer'].notnull())])
    # df = pd.DataFrame(df[(df['brnd'].notnull()) & (df['pdct_name_on_eretailer'].notnull())])
    print(df.shape)
    df.drop_duplicates(keep='first', inplace=True)
    print(df.shape)

    #
    non_dups = df[~df.duplicated(['pdct_name_on_eretailer'], keep=False)]
    print('non_dups.shape', non_dups.shape)
    dups = df[df.duplicated(['pdct_name_on_eretailer'], keep=False)]
    dups = dups[dups['brnd'].notnull()]
    print('dups.shape', dups.shape)
    df = pd.DataFrame(pd.concat([dups, non_dups]))
    print(df.shape)
    df['ind'] = df.duplicated(['pdct_name_on_eretailer'], keep=False)
    df = df[~((df['ind']==True) & (df['brnd']=='Krug'))]
    df = df[~((df['ind']==True) & (df['brnd']=='Chandon'))]
    df[df.duplicated(['pdct_name_on_eretailer'], keep=False)].to_excel('/tmp/discording_brand_matches.xlsx') # For safe keeping
    assert df.duplicated(['pdct_name_on_eretailer']).sum() == 0
    for ix_, row in df.iterrows():
        d[row['pdct_name_on_eretailer']] = row['brnd']
    with open(BRAND_MATCHING_JSON, 'w') as f:
        json.dump(d, f)
    print('New cache has ', len(d.keys()), 'entries')


if False:
    # Product matching cache storing
    if not op.exists(PRODUCT_MATCHING_JSON):
        with open(PRODUCT_MATCHING_JSON, 'w') as f:
            json.dump({}, f)
    else:
        with open(PRODUCT_MATCHING_JSON, 'r') as f:
            d = json.load(f)
            print('Existing cache has ', len(d.keys()), 'entries')
        if not input('Do you want to override PRODUCT_MATCHING_JSON cache ? y/n').lower() == 'y':
            raise Exception

    df = pd.concat([
          pd.read_csv(RAW_PDCTS_XLSX, sep=';')[['pdct_name_on_eretailer', 'pdct_name']],
    ])

    print(df.shape)
    df = pd.DataFrame(df[(df['pdct_name_on_eretailer'].notnull())])
    print(df.shape)
    df.drop_duplicates(keep='first', inplace=True)
    print(df.shape)

    #
    non_dups = df[~df.duplicated(['pdct_name_on_eretailer'], keep=False)]
    print('non_dups.shape', non_dups.shape)
    dups = df[df.duplicated(['pdct_name_on_eretailer'], keep=False)]
    dups = dups[dups['pdct_name'].notnull()]
    print('pdct_name.shape', dups.shape)
    df = pd.DataFrame(pd.concat([dups, non_dups]))
    print(df.shape)
    df[df.duplicated(['pdct_name_on_eretailer'], keep=False)].to_excel('/tmp/discording_pdct_name_matches.xlsx') # For safe keeping
    assert df.duplicated(['pdct_name_on_eretailer']).sum() == 0
    d = {}
    for ix_, row in df.iterrows():
        d[row['pdct_name_on_eretailer']] = row['pdct_name']
    with open(PRODUCT_MATCHING_JSON, 'w') as f:
        json.dump(d, f)
    print('New cache PRODUCT_MATCHING_JSON has ', len(d.keys()), 'entries')


if False:
    # Brand matching cache storing
    if not op.exists(AMAZON_FR_BRAND_MATCHING_JSON):
        with open(AMAZON_FR_BRAND_MATCHING_JSON, 'w') as f:
            json.dump({}, f)
    else:
        with open(AMAZON_FR_BRAND_MATCHING_JSON, 'r') as f:
            d = json.load(f)
            print('Existing cache has ', len(d.keys()), 'entries')
        if not input('Do you want to override AMAZON_FR_BRAND_MATCHING_JSON cache ? y/n').lower() == 'y':
            raise Exception

    df = pd.concat([
        pd.read_csv(AMAZON_RAW_DATA_FR_CSV, sep=';')[['pdct_name_on_eretailer', 'brnd']],
    ])

    print(df.shape)
    df = pd.DataFrame(df[(df['pdct_name_on_eretailer'].notnull())])
    # df = pd.DataFrame(df[(df['brnd'].notnull()) & (df['pdct_name_on_eretailer'].notnull())])
    print(df.shape)
    df.drop_duplicates(keep='first', inplace=True)
    print(df.shape)

    #
    non_dups = df[~df.duplicated(['pdct_name_on_eretailer'], keep=False)]
    print('non_dups.shape', non_dups.shape)
    dups = df[df.duplicated(['pdct_name_on_eretailer'], keep=False)]
    dups = dups[dups['brnd'].notnull()]
    print('dups.shape', dups.shape)
    df = pd.DataFrame(pd.concat([dups, non_dups]))
    print(df.shape)
    df[df.duplicated(['pdct_name_on_eretailer'], keep=False)].to_excel(
        '/tmp/discording_brand_matches.xlsx')  # For safe keeping
    assert df.duplicated(['pdct_name_on_eretailer']).sum() == 0
    d = {}
    for ix_, row in df.iterrows():
        d[row['pdct_name_on_eretailer']] = row['brnd']
    with open(AMAZON_FR_BRAND_MATCHING_JSON, 'w') as f:
        json.dump(d, f)
    print('New cache has ', len(d.keys()), 'entries')

if False:
    # Brand matching cache storing
    if not op.exists(AMAZON_UK_BRAND_MATCHING_JSON):
        with open(AMAZON_UK_BRAND_MATCHING_JSON, 'w') as f:
            json.dump({}, f)
    else:
        with open(AMAZON_UK_BRAND_MATCHING_JSON, 'r') as f:
            d = json.load(f)
            print('Existing cache has ', len(d.keys()), 'entries')
        if not input('Do you want to override AMAZON_UK_BRAND_MATCHING_JSON cache ? y/n').lower() == 'y':
            raise Exception

    df = pd.concat([
        pd.read_csv(AMAZON_RAW_DATA_UK_CSV, sep=';')[['pdct_name_on_eretailer', 'brnd']],
    ])

    print(df.shape)
    df = pd.DataFrame(df[(df['pdct_name_on_eretailer'].notnull())])
    # df = pd.DataFrame(df[(df['brnd'].notnull()) & (df['pdct_name_on_eretailer'].notnull())])
    print(df.shape)
    df.drop_duplicates(keep='first', inplace=True)
    print(df.shape)

    #
    non_dups = df[~df.duplicated(['pdct_name_on_eretailer'], keep=False)]
    print('non_dups.shape', non_dups.shape)
    dups = df[df.duplicated(['pdct_name_on_eretailer'], keep=False)]
    dups = dups[dups['brnd'].notnull()]
    print('dups.shape', dups.shape)
    df = pd.DataFrame(pd.concat([dups, non_dups]))
    print(df.shape)
    df[df.duplicated(['pdct_name_on_eretailer'], keep=False)].to_excel(
        '/tmp/discording_brand_matches.xlsx')  # For safe keeping
    assert df.duplicated(['pdct_name_on_eretailer']).sum() == 0
    d = {}
    for ix_, row in df.iterrows():
        d[row['pdct_name_on_eretailer']] = row['brnd']
    with open(AMAZON_UK_BRAND_MATCHING_JSON, 'w') as f:
        json.dump(d, f)
    print('New cache has ', len(d.keys()), 'entries')

