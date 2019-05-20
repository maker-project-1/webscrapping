import os
# from ers import shops, COLLECTION_DATE, web_apis_traffic_csv, web_apis_traffic_aggregates_csv
import os.path as op

import numpy as np
import pandas as pd

BASE_DIR = "/code/mhers"
WAVE_NUMBER = 8

shops = pd.read_excel(op.join(BASE_DIR, "ressources/ERS-referential-shops.xlsx"), index_col=None)
COLLECTION_DATE = "2018-06-10"

web_apis_traffic_csv = os.path.join(BASE_DIR,'data/w_{}/final_csvs'.format(WAVE_NUMBER), 'shopgrid_details - web_apis_traffic_w{}.csv'.format(WAVE_NUMBER))
web_apis_traffic_aggregates_csv = os.path.join(BASE_DIR,'data/w_{}/final_csvs'.format(WAVE_NUMBER), 'shopgrid_summary - web_apis_traffic_w{}.csv'.format(WAVE_NUMBER))


# #####################################################################################################################
# web_apis_traffic_csv
# #####################################################################################################################

# This generates the dummy data and shouldn't be in production
pd.to_datetime('2017-04-01')
mask = pd.DataFrame({'year_month': [pd.to_datetime(x) for x in ['2018/07', '2018/06', '2018/05', '2018/04', '2018/03',
                                                              '2018/02', '2018/01', '2017/12', '2017/11', '2017/10',
                                                              '2017/9', '2017/8', '2017/7', '2017/6', '2017/5',
                                                              '2017/4', '2017/3', '2017/2', '2017/1', ]]})
df = pd.DataFrame()
for c, row in shops.iterrows():
    tmp = pd.DataFrame(mask.copy())
    for k in ['shop_id', 'continent', 'country', 'region', 'segment']:
        tmp[k] = row[k]
    df = df.append(tmp)

# TODO  : delete the random data creation and fetch the data in the proper dataset
df['desktop_nb_visits'] = np.random.randint(0, 1000, size=(df.shape[0], 1))
df['mobile_nb_visits'] = np.random.randint(0, 1000, size=(df.shape[0], 1))
df['total_nb_visits'] = df['mobile_nb_visits'] + df['desktop_nb_visits']
df['visit_duration_in_seconds'] = np.random.randint(0, 350, size=(df.shape[0], 1))
df['nb_page_view_per_visit'] = np.random.randint(0, 10, size=(df.shape[0], 1))
df['bounce_rate'] = np.random.random(size=(df.shape[0], 1))


# TODO : Compute real growth rates
df['desktop_nb_visits_vs_lm'] = pd.DataFrame(np.random.random(size=(df.shape[0], 1))*2 - 1)
df['mobile_nb_visits_vs_lm'] = pd.DataFrame(np.random.random(size=(df.shape[0], 1))*2 - 1)
df['total_nb_visits_vs_lm'] = pd.DataFrame(np.random.random(size=(df.shape[0], 1))*2 - 1)
df['visit_duration_in_seconds_vs_lm'] = pd.DataFrame(np.random.random(size=(df.shape[0], 1))*2 - 1)
df['nb_page_view_per_visit_vs_lm'] = pd.DataFrame(np.random.random(size=(df.shape[0], 1))*2 - 1)
df['bounce_rate_vs_lm'] = pd.DataFrame(np.random.random(size=(df.shape[0], 1))*2 - 1)


# Collection date
print('WARNING : PLEASE ENSURE THE COLLECTION_DATE is accurate :', COLLECTION_DATE)
df['collection_date'] = COLLECTION_DATE

final_cols = ['collection_date', 'year_month', 'continent', 'country', 'region', 'segment', 'shop_id',
       'desktop_nb_visits', 'mobile_nb_visits', 'total_nb_visits', 'visit_duration_in_seconds', 'nb_page_view_per_visit', 'bounce_rate',
       'desktop_nb_visits_vs_lm', 'mobile_nb_visits_vs_lm', 'total_nb_visits_vs_lm', 'visit_duration_in_seconds_vs_lm',
       'nb_page_view_per_visit_vs_lm', 'bounce_rate_vs_lm']

df = df[final_cols]
df.to_csv(web_apis_traffic_csv, sep=';', index=False, encoding='utf-8')
print("File web_apis_traffic_csv stored at : ", web_apis_traffic_csv)

# #####################################################################################################################
# web_apis_traffic_aggregates_csv
# #####################################################################################################################

# Preparing for aggregation
df.drop(columns=['collection_date', 'desktop_nb_visits_vs_lm', 'mobile_nb_visits_vs_lm', 'total_nb_visits_vs_lm',
                 'visit_duration_in_seconds_vs_lm','nb_page_view_per_visit_vs_lm', 'bounce_rate_vs_lm'], inplace=True)

df['region'].fillna("", inplace=True)

# Aggregating
res = []
agregation_levels_list = [
    ['continent', 'country', 'region', 'segment', 'shop_id'],

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
                     'desktop_nb_visits': {'desktop_nb_visits': 'mean'},
                     'mobile_nb_visits': {'mobile_nb_visits': 'mean'},
                     'total_nb_visits': {'total_nb_visits': 'mean'},
                     'visit_duration_in_seconds': {'visit_duration_in_seconds': 'mean'},
                     'nb_page_view_per_visit': {'nb_page_view_per_visit': 'mean'},
                     'bounce_rate': {'bounce_rate': 'mean'},
                     }).reset_index()

    dfG2.columns = dfG2.columns.droplevel(1)
    dfG2 = pd.DataFrame(dfG2)
    res.append(dfG2)


# Aggregate on all-levels
all_dfs = pd.concat(res, axis=0, ignore_index=True)

# Todo : Time Span is the time over which the aggregates are calculated
all_dfs['time_span'] = "Apr. 2016 - Aug. 2018"

# Collection date
print('WARNING : PLEASE ENSURE THE COLLECTION_DATE is accurate :', COLLECTION_DATE)
all_dfs['collection_date'] = COLLECTION_DATE

final_cols = ['collection_date', 'time_span', 'continent', 'country', 'region', 'segment', 'shop_id',
       'desktop_nb_visits', 'mobile_nb_visits', 'total_nb_visits', 'visit_duration_in_seconds',
       'nb_page_view_per_visit', 'bounce_rate',]

all_dfs = all_dfs[final_cols]
all_dfs.to_csv(web_apis_traffic_aggregates_csv, sep=';', index=False, encoding='utf-8')
print("File web_apis_traffic_aggregates_csv stored at : ", web_apis_traffic_aggregates_csv, " -")
