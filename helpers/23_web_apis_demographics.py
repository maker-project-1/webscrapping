import os
# from ers import shops, COLLECTION_DATE, web_apis_demographics_csv, web_apis_demographics_aggregates_csv
import os.path as op

import numpy as np
import pandas as pd

BASE_DIR = "/code/mhers"
WAVE_NUMBER = 8

shops = pd.read_excel(op.join(BASE_DIR, "ressources/ERS-referential-shops.xlsx"), index_col=None)
COLLECTION_DATE = "2018-06-10"

web_apis_demographics_csv = os.path.join(BASE_DIR,'data/w_{}/final_csvs'.format(WAVE_NUMBER), 'shopgrid_details - web_apis_demographics_w{}.csv'.format(WAVE_NUMBER))
web_apis_demographics_aggregates_csv = os.path.join(BASE_DIR,'data/w_{}/final_csvs'.format(WAVE_NUMBER), 'shopgrid_summary - web_apis_demographics_w{}.csv'.format(WAVE_NUMBER))


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

df['female_pct'] = np.random.random(size=(df.shape[0], 1))
df['male_pct'] = 1 - df['female_pct']
df['age25_34'] = np.random.random(size=(df.shape[0], 1)) * 0.4
df['age35_44'] = np.random.random(size=(df.shape[0], 1)) * 0.3
df['age45_54'] = np.random.random(size=(df.shape[0], 1)) * 0.1
df['age55_64'] = np.random.random(size=(df.shape[0], 1)) * 0.1
df['age65+'] = np.random.random(size=(df.shape[0], 1)) * 0.1
df['age18_24'] = 1 - df['age65+'] - df['age25_34'] - df['age35_44'] - df['age45_54'] - df['age55_64']

# Collection date
print('WARNING : PLEASE ENSURE THE COLLECTION_DATE is accurate :', COLLECTION_DATE)
df['collection_date'] = COLLECTION_DATE


# Todo : Time Span is the time over which the aggregates are calculated
df['time_span'] = "Apr. 2016 - Aug. 2018"


final_cols = ['collection_date', 'time_span', 'continent', 'country', 'region', 'segment', 'shop_id',
              'female_pct', 'male_pct', 'age18_24', 'age25_34', 'age35_44', 'age45_54', 'age55_64', 'age65+']

df = df[final_cols]
df.to_csv(web_apis_demographics_csv, sep=';', index=False, encoding='utf-8')
print("File web_apis_demographics_csv stored at : ", web_apis_demographics_csv)

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

]

# All agregations
for agg_level in agregation_levels_list:
    dfG2 = df.groupby(agg_level, as_index=False)
    dfG2 = dfG2.agg({
        'female_pct': {'female_pct': 'mean'},
        'male_pct': {'male_pct': 'mean'},
        'age18_24': {'age18_24': 'mean'},
        'age25_34': {'age25_34': 'mean'},
        'age35_44': {'age35_44': 'mean'},
        'age45_54': {'age45_54': 'mean'},
        'age55_64': {'age55_64': 'mean'},
        'age65+': {'age65+': 'mean'},
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

final_cols = ['collection_date', 'time_span', 'continent', 'country', 'region', 'segment', 'time_span',
              'female_pct', 'male_pct', 'age18_24', 'age25_34', 'age35_44', 'age45_54', 'age55_64', 'age65+']

all_dfs = all_dfs[final_cols]
all_dfs.to_csv(web_apis_demographics_aggregates_csv, sep=';', index=False, encoding='utf-8')
print("File web_apis_demographics_aggregates_csv stored at : ", web_apis_demographics_aggregates_csv, " -")
