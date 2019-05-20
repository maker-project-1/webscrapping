import os
# from ers import shops, COLLECTION_DATE, web_apis_traffic_sources_csv, web_apis_traffic_sources_aggregates_csv
import os.path as op

import numpy as np
import pandas as pd

BASE_DIR = "/code/mhers"
WAVE_NUMBER = 8

shops = pd.read_excel(op.join(BASE_DIR, "ressources/ERS-referential-shops.xlsx"), index_col=None)
COLLECTION_DATE = "2018-06-10"

web_apis_traffic_sources_csv = os.path.join(BASE_DIR,'data/w_{}/final_csvs'.format(WAVE_NUMBER), 'shopgrid_details - web_apis_traffic_sources_w{}.csv'.format(WAVE_NUMBER))
web_apis_traffic_sources_aggregates_csv = os.path.join(BASE_DIR,'data/w_{}/final_csvs'.format(WAVE_NUMBER), 'shopgrid_summary - web_apis_traffic_sources_w{}.csv'.format(WAVE_NUMBER))

# #####################################################################################################################
# web_apis_demographics_csv
# #####################################################################################################################

# This generates the dummy data and shouldn't be in production
mask = pd.DataFrame({'to_delete': [1]})
df = pd.DataFrame()
for c, row in shops.iterrows():
    tmp = pd.DataFrame(mask.copy())
    for k in ['shop_id', 'continent', 'country', 'region', 'segment']:
        tmp[k] = row[k]
    df = df.append(tmp)
df.drop(columns=['to_delete'], inplace=True)


# TODO  : delete the random data creation and fetch the data in the proper dataset
df['direct'] = np.random.random(size=(df.shape[0], 1)) * 0.3
df['email'] = np.random.random(size=(df.shape[0], 1)) * 0.2
df['referrals'] = np.random.random(size=(df.shape[0], 1)) * 0.2
df['social'] = np.random.random(size=(df.shape[0], 1)) * 0.1
df['paid_search'] = np.random.random(size=(df.shape[0], 1)) * 0.1
df['display_ads'] = np.random.random(size=(df.shape[0], 1)) * 0.1
df['organic_search'] = 1 - df['direct'] - df['email'] - df['referrals'] - df['social'] - df['paid_search'] - df['display_ads']

# Todo : Time Span is the time over which the aggregates are calculated
df['time_span'] = "Apr. 2016 - Aug. 2018"

# Collection date
print('WARNING : PLEASE ENSURE THE COLLECTION_DATE is accurate :', COLLECTION_DATE)
df['collection_date'] = COLLECTION_DATE

final_cols = ['collection_date', 'time_span', 'continent', 'country', 'region', 'segment', 'shop_id', 'direct', 'email',
              'referrals', 'social', 'paid_search', 'display_ads', 'organic_search']

df = df[final_cols]
df.to_csv(web_apis_traffic_sources_csv, sep=';', index=False, encoding='utf-8')
print("File web_apis_traffic_sources_csv stored at : ", web_apis_traffic_sources_csv)

# #####################################################################################################################
# web_apis_demographics_aggregates_csv
# #####################################################################################################################

df['region'].fillna("", inplace=True)

# Aggregating
res = []
agregation_levels_list = [

    ['continent', 'country', 'region', 'segment'],
    ['continent', 'country', 'segment'],
    ['continent', 'segment'],
    ['segment'],

    ['continent', 'country', 'region'],
    ['continent', 'country'],
    ['continent'],

    ['collection_date']
]

# All agregations
for agg_level in agregation_levels_list:
    dfG2 = df.groupby(agg_level, as_index=False)
    dfG2 = dfG2.agg({
        'direct': {'direct': 'mean'},
        'email': {'email': 'mean'},
        'referrals': {'referrals': 'mean'},
        'social': {'social': 'mean'},
        'paid_search': {'paid_search': 'mean'},
        'display_ads': {'display_ads': 'mean'},
        'organic_search': {'organic_search': 'mean'},

    }).reset_index()

    dfG2.columns = dfG2.columns.droplevel(1)
    dfG2 = pd.DataFrame(dfG2)
    print(agg_level, 'adding', dfG2.shape)
    res.append(dfG2)

# Aggregate on all-levels
all_dfs = pd.concat(res, axis=0, ignore_index=True)

# Collection date
print('WARNING : PLEASE ENSURE THE COLLECTION_DATE is accurate :', COLLECTION_DATE)
all_dfs['collection_date'] = COLLECTION_DATE

# Todo : Time Span is the time over which the aggregates are calculated
all_dfs['time_span'] = "Apr. 2016 - Aug. 2018"

final_cols = ['collection_date', 'time_span', 'continent', 'country', 'region', 'segment', 'direct', 'display_ads',
              'email', 'organic_search', 'paid_search', 'referrals', 'social']

all_dfs = all_dfs[final_cols]
all_dfs.to_csv(web_apis_traffic_sources_aggregates_csv, sep=';', index=None, encoding='utf-8')
print("File web_apis_traffic_sources_aggregates_csv stored at : ", web_apis_traffic_sources_aggregates_csv, " -")
