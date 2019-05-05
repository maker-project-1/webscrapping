import hashlib
import os
import os.path as op
import re

import pandas as pd
import regex
import unicodedata

BASE_DIR = op.dirname(__file__)

# Import brands
brands = pd.read_excel(op.join(BASE_DIR, "ressources/ERS-referential-brands.xlsx"), index_col=None)
# def clean_jp_str(jp_str):
#     return unicodedata.normalize('NFKC', jp_str.replace('・', '').replace(' ', ''))
# brands['brnd_jp_clean'] = brands['brnd_jp'].apply(lambda x: clean_jp_str(x) if x ==x else x )
# brands.to_excel('/tmp/brnd_jp_clean.xlsx')$

mod_brnds = brands[['brnd', 'ctg', 'is_mh', 'distributor']]
mod_brnds_undedup_shape = mod_brnds.shape[0]
mod_brnds = mod_brnds.drop_duplicates(['brnd'])
assert mod_brnds_undedup_shape == mod_brnds.shape[0]

pdcts = pd.read_excel(op.join(BASE_DIR, "ressources/ERS-referential-products.xlsx"), index_col=None)
other_pdcts = pd.read_excel(op.join(BASE_DIR, "ressources/ERS-referential-products-others.xlsx"), index_col=None)
pdcts['pdct_name'] = pdcts['pdct_name'].str.strip()
# pdcts.to_excel(op.join(BASE_DIR, "ressources/ERS-referential-products.xlsx"), index_col=None)
kws = pd.read_excel(op.join(BASE_DIR, "ressources/ERS-referential-keywords.xlsx"), index_col=None)
shops = pd.read_excel(op.join(BASE_DIR, "ressources/ERS-referential-shops.xlsx"), index_col=None)

shop_ctgs = pd.read_excel(op.join(BASE_DIR, "ressources/ERS-referential-shop_categories.xlsx"), index_col=None)
imgs_ref_orig = pd.read_excel(op.join(BASE_DIR, "ressources/imgs_referential_final.xlsx"), index_col=None)
imgs_ref = pd.read_excel(op.join(BASE_DIR, "ressources/ERS-referential-images.xlsx"), index_col=None)

# Currency
country_to_currency = {'UK': '£', 'FR': '€', 'USA': '$', 'AUS': '$', 'DE': '€', 'CH': 'CHF', 'ES': '€'}
# Brands and brand queries
mh_brands = list(brands.query('is_mh==True')['brnd'].dropna().unique())
all_brands = list(brands['brnd'].dropna().unique())
brnd_queries_to_brnd = pdcts[['brnd', 'brnd_query']].drop_duplicates().set_index('brnd_query').to_dict()['brnd']
brnd_to_ctgs = pdcts[['brnd', 'ctg']].drop_duplicates().dropna().set_index('brnd').to_dict()['ctg']


# Japanese specialties
ctg_to_japanese = dict(champagne='シャンパン', cognac='コニャック', vodka='ウォッカ',
                       sparkling='スパークリングワイン', whisky='ウィスキー', still_wine='まだワイン')

# Categories and ctg_ind
ctg_ind_to_ctg = dict(champagne='Champagne', sparkling='Sparkling', still_wines='Still Wine', whisky='Whisky',
                      cognac='Cognac', vodka='Vodka', gin='Gin', tequila='Tequila', red_wine='Red Wine',
                      white_wine='White Wine', rum='Rum', liquor='Liquor', brandy='Brandy', mezcal='Mezcal',
                      bourbon='Bourbon', schnapps='Schnapps', armagnac="Armagnac", scotch='Scotch')
ctg_to_ctg_ind = {v: k for k, v in ctg_ind_to_ctg.items()}
ctg_to_ctg_order = {'Champagne': 1, 'Cognac': 2, 'Whisky': 3, 'Vodka': 4, 'Sparkling': 5, 'Still Wine': 6}
mhers_ctgs = ctg_to_ctg_order.keys()

# Lists of Brands by country
categories_uk = list(pdcts.loc[pdcts['country'] == 'UK', 'ctg'].dropna().unique())
categories_fr = list(pdcts.loc[pdcts['country'] == 'FR', 'ctg'].dropna().unique())
categories_de = list(pdcts.loc[pdcts['country'] == 'DE', 'ctg'].dropna().unique())
categories_usa = list(pdcts.loc[pdcts['country'] == 'USA', 'ctg'].dropna().unique())
categories_aus = list(pdcts.loc[pdcts['country'] == 'AUS', 'ctg'].dropna().unique())
categories_ch = list(pdcts.loc[pdcts['country'] == 'CH', 'ctg'].dropna().unique())
categories_es = list(pdcts.loc[pdcts['country'] == 'ES', 'ctg'].dropna().unique())
categories_jp = list(pdcts.loc[pdcts['country'] == 'JP', 'ctg'].dropna().unique())


country_to_list_of_categories = {'UK': categories_uk, 'FR': categories_fr, 'USA': categories_usa,
                                 'AUS': categories_aus, 'DE': categories_de, 'CH': categories_ch,
                                 'ES': categories_es, 'JP': categories_jp}

# Lists of Brands by country
brands_queries_uk = list(pdcts.loc[pdcts['country'] == 'UK', 'brnd_query'].dropna().unique())
brands_queries_fr = list(pdcts.loc[pdcts['country'] == 'FR', 'brnd_query'].dropna().unique())
brands_queries_de = list(pdcts.loc[pdcts['country'] == 'DE', 'brnd_query'].dropna().unique())
brands_queries_usa = list(pdcts.loc[pdcts['country'] == 'USA', 'brnd_query'].dropna().unique())
brands_queries_aus = list(pdcts.loc[pdcts['country'] == 'AUS', 'brnd_query'].dropna().unique())
brands_queries_ch = list(pdcts.loc[pdcts['country'] == 'CH', 'brnd_query'].dropna().unique())
brands_queries_es = list(pdcts.loc[pdcts['country'] == 'ES', 'brnd_query'].dropna().unique())
brands_queries_jp = list(pdcts.loc[pdcts['country'] == 'JP', 'brnd_query'].dropna().unique())
country_to_list_of_brnd_query = {'UK': brands_queries_uk, 'FR': brands_queries_fr, 'USA': brands_queries_usa, 'AUS': brands_queries_aus,
                                 'DE': brands_queries_de, 'CH': brands_queries_ch, 'ES': brands_queries_es, 'JP': brands_queries_jp}

# Lists of Competitors by country
competitors_uk = list(pdcts.loc[pdcts['country'] == 'UK', 'competitor_query'].dropna().unique())
competitors_fr = list(pdcts.loc[pdcts['country'] == 'FR', 'competitor_query'].dropna().unique())
competitors_de = list(pdcts.loc[pdcts['country'] == 'DE', 'competitor_query'].dropna().unique())
competitors_usa = list(pdcts.loc[pdcts['country'] == 'USA', 'competitor_query'].dropna().unique())
competitors_aus = list(pdcts.loc[pdcts['country'] == 'AUS', 'competitor_query'].dropna().unique())
competitors_ch = list(pdcts.loc[pdcts['country'] == 'CH', 'competitor_query'].dropna().unique())
competitors_es = list(pdcts.loc[pdcts['country'] == 'ES', 'competitor_query'].dropna().unique())
competitors_jp = list(pdcts.loc[pdcts['country'] == 'JP', 'competitor_query'].dropna().unique())

competitors_to_competitors_queries = pdcts[['competitor', 'competitor_query']].drop_duplicates().set_index('competitor').to_dict()['competitor_query']
competitors_queries_to_competitors = {v: k for k, v in competitors_to_competitors_queries.items()}
country_to_list_of_competitor_queries = {'UK': competitors_uk, 'FR': competitors_fr, 'USA': competitors_usa,
                                         'AUS': competitors_aus, 'DE': competitors_de,
                                         'CH': competitors_ch, 'ES': competitors_es, 'JP': competitors_jp}

# List of keywords by country
keywords_uk = list(kws.loc[kws['country'] == 'UK', 'kw'].dropna().unique())
keywords_fr = list(kws.loc[kws['country'] == 'FR', 'kw'].dropna().unique())
keywords_de = list(kws.loc[kws['country'] == 'DE', 'kw'].dropna().unique())
keywords_usa = list(kws.loc[kws['country'] == 'USA', 'kw'].dropna().unique())
keywords_aus = list(kws.loc[kws['country'] == 'AUS', 'kw'].dropna().unique())
keywords_es = list(kws.loc[kws['country'] == 'ES', 'kw'].dropna().unique())
keywords_ch = list(kws.loc[kws['country'] == 'CH', 'kw'].dropna().unique())
keywords_jp = list(kws.loc[kws['country'] == 'JP', 'kw'].dropna().unique())
country_to_list_of_keywords = {'UK': keywords_uk, 'FR': keywords_fr, 'USA': keywords_usa,
                               'AUS': keywords_aus, 'DE': keywords_de,
                               'CH': keywords_ch, 'ES': keywords_es, 'JP': keywords_jp, }

# List of all keywords
all_keywords_uk = keywords_uk + brands_queries_uk + competitors_uk
all_keywords_fr = keywords_fr + brands_queries_fr + competitors_fr
all_keywords_de = keywords_de + brands_queries_de + competitors_de
all_keywords_usa = keywords_usa + brands_queries_usa + competitors_usa
all_keywords_aus = keywords_aus + brands_queries_aus + competitors_aus
all_keywords_ch = keywords_ch + brands_queries_ch + competitors_ch
all_keywords_es = keywords_es + brands_queries_es + competitors_es
all_keywords_jp = keywords_jp + brands_queries_jp + competitors_jp
kws_list = all_keywords_uk + all_keywords_fr + all_keywords_de + all_keywords_usa + all_keywords_aus + all_keywords_es + all_keywords_ch + all_keywords_jp


# Other Keywords
box_kws = [u" box", u"box ", u"wbox", u"gift ", u" gift", u"etui ", u" etui", u"étui ", u" étui", u'case', u'caisse', u'coffret']
rose_kws = [u'ros ', u' ros', 'ロゼ']


# List of shops
shop_id_to_country = shops[["shop_id", 'country']].set_index('shop_id').to_dict()['country']
shop_computer_id_to_country = shops[["shop_computer_id", 'country']].set_index('shop_computer_id').to_dict()['country']
shop_id_to_segment = shops[["shop_id", 'segment']].set_index('shop_id').to_dict()['segment']
shop_computer_id_to_shop_id = shops[['shop_computer_id', 'shop_id']].set_index('shop_computer_id').to_dict()['shop_id']
shop_id_to_shop_computer_id = shops[['shop_id', 'shop_computer_id']].set_index('shop_id').to_dict()['shop_computer_id']


# Important COLLECTION_DATE // WARNING, it should be a string
COLLECTION_DATE = "2018-09-15"
WAVE_NUMBER = 9


# RAW DATA FILES PATH
if not op.exists(op.join(BASE_DIR, "data", "w_{}".format(WAVE_NUMBER))):
    os.mkdir(op.join(BASE_DIR, "data", "w_{}".format(WAVE_NUMBER)))
RAW_BRANDS_XLSX = op.join(BASE_DIR, "data", "w_{}".format(WAVE_NUMBER), 'raw_brands_searches_extracts.xlsx')
RAW_COMPETITORS_XLSX = op.join(BASE_DIR, "data", "w_{}".format(WAVE_NUMBER), 'raw_competitors_searches_extracts.xlsx')
RAW_CTGS_XLSX = op.join(BASE_DIR, "data", "w_{}".format(WAVE_NUMBER), 'raw_ctg_page_extracts.xlsx')
RAW_KWS_XLSX = op.join(BASE_DIR, "data", "w_{}".format(WAVE_NUMBER), 'raw_kws_searches_extracts.xlsx')
RAW_PDCTS_XLSX = op.join(BASE_DIR, "data", "w_{}".format(WAVE_NUMBER), 'raw_products_pages_extracts.xlsx')
RAW_PROMPTED_XLSX = op.join(BASE_DIR, "data", "w_{}".format(WAVE_NUMBER), 'raw_prompted_extracts.xlsx')


# Matching and brand detection cache + translation cache
BRAND_MATCHING_JSON = op.join(BASE_DIR, "cache", "brand_matching.json")
PRODUCT_MATCHING_JSON = op.join(BASE_DIR, "cache", "product_matching.json")
AMAZON_FR_BRAND_MATCHING_JSON = op.join(BASE_DIR, "cache", "amazon_fr_brand_matching.json")
AMAZON_UK_BRAND_MATCHING_JSON = op.join(BASE_DIR, "cache", "amazon_uk_brand_matching.json")
JAPANESE_TRANSLATION_CACHE_JSON = op.join(BASE_DIR, "cache", "japanese_translation.json")

# Amazon Data
AMAZON_RAW_DATA_FR_CSV = op.join(BASE_DIR, "amazon/data", "amazon_fr_raw.csv")
AMAZON_RAW_DATA_FR_XLSX = op.join(BASE_DIR, "amazon/data", "amazon_fr_raw.xlsx")
PRIMENOW_RAW_DATA_FR_CSV = op.join(BASE_DIR, "amazon/data", "primenow_fr_raw.csv")
AMAZON_RAW_DATA_ONLY_MH_FR_XLSX = op.join(BASE_DIR, "amazon/data", "amazon_fr_raw_only_mh.xlsx")
AMAZON_RAW_SCORED_DATA_FR_CSV = op.join(BASE_DIR, "amazon/data", "amazon_fr_raw_score.csv")
AMAZON_KWS_SEARCHES_FR_CSV = op.join(BASE_DIR, "amazon/data", "amazon_fr_raw_kws_searches_extracts.csv")
AMAZON_CTG_PAGES_FR_CSV = op.join(BASE_DIR, "amazon/data", "amazon_fr_raw_ctg_pages_extracts.csv")
AMAZON_CTG_PAGES_FR_XLSX = op.join(BASE_DIR, "amazon/data", "amazon_fr_raw_ctg_pages_extracts.xlsx")
AMAZON_SHARE_OF_SHELF_FR_CSV = op.join(BASE_DIR, "amazon/data", "amazon_fr_share_of_shelf.csv")
AMAZON_SHARE_OF_SHELF_FR_XLSX = op.join(BASE_DIR, "amazon/data", "amazon_fr_share_of_shelf.xlsx")
AMAZON_CTG_SHARE_OF_SHELF_FR_CSV = op.join(BASE_DIR, "amazon/data", "amazon_fr_ctg_share_of_shelf.csv")
AMAZON_CTG_SHARE_OF_SHELF_FR_XLSX = op.join(BASE_DIR, "amazon/data", "amazon_fr_ctg_share_of_shelf.xlsx")


AMAZON_RAW_DATA_UK_CSV = op.join(BASE_DIR, "amazon/data", "amazon_uk_raw.csv")
AMAZON_RAW_DATA_UK_XLSX = op.join(BASE_DIR, "amazon/data", "amazon_uk_raw.xlsx")
PRIMENOW_RAW_DATA_UK_CSV = op.join(BASE_DIR, "amazon/data", "primenow_uk_raw.csv")
AMAZON_RAW_DATA_ONLY_MH_UK_XLSX = op.join(BASE_DIR, "amazon/data", "amazon_uk_raw_only_mh.xlsx")
AMAZON_RAW_SCORED_DATA_UK_CSV = op.join(BASE_DIR, "amazon/data", "amazon_uk_raw_score.csv")
AMAZON_KWS_SEARCHES_UK_CSV = "/data/eretail/amazon_uk/amazon_uk_raw_kws_searches_extracts.csv"
AMAZON_CTG_PAGES_UK_CSV = "/data/eretail/amazon_uk/amazon_uk_raw_ctg_pages_extracts.csv"
AMAZON_CTG_PAGES_UK_XLSX = "/data/eretail/amazon_uk/amazon_uk_raw_ctg_pages_extracts.xlsx"
AMAZON_SHARE_OF_SHELF_UK_CSV = "/data/eretail/amazon_uk/amazon_uk_share_of_shelf.csv"
AMAZON_SHARE_OF_SHELF_UK_XLSX = "/data/eretail/amazon_uk/amazon_uk_share_of_shelf.xlsx"
AMAZON_CTG_SHARE_OF_SHELF_UK_CSV = "/data/eretail/amazon_uk/amazon_uk_ctg_share_of_shelf.csv"
AMAZON_CTG_SHARE_OF_SHELF_UK_XLSX = "/data/eretail/amazon_uk/amazon_uk_ctg_share_of_shelf.xlsx"
AMAZON_AGG_SCORES_DATA_UK_XLSX = op.join(BASE_DIR, "amazon/data", "amazon_uk_agg_score.xlsx")
AMAZON_BEST_PRODUCTS_WHISKY_UK_XLSX = op.join(BASE_DIR, "amazon/data", "amazon_uk_whisky_best_products.xlsx")
AMAZON_BEST_PRODUCTS_CHAMPAGNE_UK_XLSX = op.join(BASE_DIR, "amazon/data", "amazon_uk_champagne_best_products.xlsx")


AMAZON_RAW_DATA_DE_CSV = op.join(BASE_DIR, "amazon/data", "amazon_de_raw.csv")
AMAZON_RAW_DATA_DE_XLSX = op.join(BASE_DIR, "amazon/data", "amazon_de_raw.xlsx")
PRIMENOW_RAW_DATA_DE_CSV = op.join(BASE_DIR, "amazon/data", "primenow_de_raw.csv")
AMAZON_RAW_DATA_ONLY_MH_DE_XLSX = op.join(BASE_DIR, "amazon/data", "amazon_de_raw_only_mh.xlsx")
AMAZON_RAW_SCORED_DATA_DE_CSV = op.join(BASE_DIR, "amazon/data", "amazon_de_raw_score.csv")
AMAZON_KWS_SEARCHES_DE_CSV = "/data/eretail/amazon_de/amazon_de_raw_kws_searches_extracts.csv"
AMAZON_CTG_PAGES_DE_CSV = "/data/eretail/amazon_de/amazon_de_raw_ctg_pages_extracts.csv"
AMAZON_CTG_PAGES_DE_XLSX = "/data/eretail/amazon_de/amazon_de_raw_ctg_pages_extracts.xlsx"
AMAZON_SHARE_OF_SHELF_DE_CSV = "/data/eretail/amazon_de/amazon_de_share_of_shelf.csv"
AMAZON_SHARE_OF_SHELF_DE_XLSX = "/data/eretail/amazon_de/amazon_de_share_of_shelf.xlsx"
AMAZON_CTG_SHARE_OF_SHELF_DE_CSV = "/data/eretail/amazon_de/amazon_de_ctg_share_of_shelf.csv"
AMAZON_CTG_SHARE_OF_SHELF_DE_XLSX = "/data/eretail/amazon_de/amazon_de_ctg_share_of_shelf.xlsx"
AMAZON_AGG_SCORES_DATA_DE_XLSX = op.join(BASE_DIR, "amazon/data", "amazon_de_agg_score.xlsx")
AMAZON_BEST_PRODUCTS_WHISKY_DE_XLSX = op.join(BASE_DIR, "amazon/data", "amazon_de_whisky_best_products.xlsx")
AMAZON_BEST_PRODUCTS_CHAMPAGNE_DE_XLSX = op.join(BASE_DIR, "amazon/data", "amazon_de_champagne_best_products.xlsx")


AMAZON_RAW_DATA_US_CSV = op.join(BASE_DIR, "amazon/data", "amazon_us_raw.csv")
AMAZON_RAW_DATA_US_XLSX = op.join(BASE_DIR, "amazon/data", "amazon_us_raw.xlsx")
PRIMENOW_RAW_DATA_US_CSV = op.join(BASE_DIR, "amazon/data", "primenow_us_raw.csv")
AMAZON_RAW_DATA_ONLY_MH_US_XLSX = op.join(BASE_DIR, "amazon/data", "amazon_us_raw_only_mh.xlsx")
AMAZON_RAW_SCORED_DATA_US_CSV = op.join(BASE_DIR, "amazon/data", "amazon_us_raw_score.csv")
AMAZON_KWS_SEARCHES_US_CSV = "/data/eretail/amazon_us/amazon_us_raw_kws_searches_extracts.csv"
AMAZON_CTG_PAGES_US_CSV = "/data/eretail/amazon_us/amazon_us_raw_ctg_pages_extracts.csv"
AMAZON_CTG_PAGES_US_XLSX = "/data/eretail/amazon_us/amazon_us_raw_ctg_pages_extracts.xlsx"
AMAZON_SHARE_OF_SHELF_US_CSV = "/data/eretail/amazon_us/amazon_us_share_of_shelf.csv"
AMAZON_SHARE_OF_SHELF_US_XLSX = "/data/eretail/amazon_us/amazon_us_share_of_shelf.xlsx"
AMAZON_CTG_SHARE_OF_SHELF_US_CSV = "/data/eretail/amazon_us/amazon_us_ctg_share_of_shelf.csv"
AMAZON_CTG_SHARE_OF_SHELF_US_XLSX = "/data/eretail/amazon_us/amazon_us_ctg_share_of_shelf.xlsx"
AMAZON_AGG_SCORES_DATA_US_XLSX = op.join(BASE_DIR, "amazon/data", "amazon_us_agg_score.xlsx")
AMAZON_BEST_PRODUCTS_WHISKY_US_XLSX = op.join(BASE_DIR, "amazon/data", "amazon_us_whisky_best_products.xlsx")
AMAZON_BEST_PRODUCTS_CHAMPAGNE_US_XLSX = op.join(BASE_DIR, "amazon/data", "amazon_us_champagne_best_products.xlsx")


AMAZON_RAW_DATA_JP_CSV = op.join(BASE_DIR, "amazon/data", "amazon_jp_raw.csv")
AMAZON_RAW_DATA_JP_XLSX = op.join(BASE_DIR, "amazon/data", "amazon_jp_raw.xlsx")
PRIMENOW_RAW_DATA_JP_CSV = op.join(BASE_DIR, "amazon/data", "primenow_jp_raw.csv")
AMAZON_RAW_DATA_ONLY_MH_JP_XLSX = op.join(BASE_DIR, "amazon/data", "amazon_jp_raw_only_mh.xlsx")
AMAZON_RAW_SCORED_DATA_JP_CSV = op.join(BASE_DIR, "amazon/data", "amazon_jp_raw_score.csv")
AMAZON_KWS_SEARCHES_JP_CSV = "/data/eretail/amazon_jp/amazon_jp_raw_kws_searches_extracts.csv"
AMAZON_CTG_PAGES_JP_CSV = "/data/eretail/amazon_jp/amazon_jp_raw_ctg_pages_extracts.csv"
AMAZON_CTG_PAGES_JP_XLSX = "/data/eretail/amazon_jp/amazon_jp_raw_ctg_pages_extracts.xlsx"
AMAZON_SHARE_OF_SHELF_JP_CSV = "/data/eretail/amazon_jp/amazon_jp_share_of_shelf.csv"
AMAZON_SHARE_OF_SHELF_JP_XLSX = "/data/eretail/amazon_jp/amazon_jp_share_of_shelf.xlsx"
AMAZON_CTG_SHARE_OF_SHELF_JP_CSV = "/data/eretail/amazon_jp/amazon_jp_ctg_share_of_shelf.csv"
AMAZON_CTG_SHARE_OF_SHELF_JP_XLSX = "/data/eretail/amazon_jp/amazon_jp_ctg_share_of_shelf.xlsx"
AMAZON_AGG_SCORES_DATA_JP_XLSX = op.join(BASE_DIR, "amazon/data", "amazon_jp_agg_score.xlsx")
AMAZON_BEST_PRODUCTS_WHISKY_JP_XLSX = op.join(BASE_DIR, "amazon/data", "amazon_jp_whisky_best_products.xlsx")
AMAZON_BEST_PRODUCTS_CHAMPAGNE_JP_XLSX = op.join(BASE_DIR, "amazon/data", "amazon_jp_champagne_best_products.xlsx")


# List of csv paths of resulting files
os.makedirs(os.path.join(BASE_DIR,'data/w_{}/final_csvs'.format(WAVE_NUMBER)), exist_ok=True)
referential_shops_csv = os.path.join(BASE_DIR,'data/w_{}/final_csvs'.format(WAVE_NUMBER), 'referential_shops_w{}.csv'.format(WAVE_NUMBER))
shop_x_ctg_indicators_csv = os.path.join(BASE_DIR,'data/w_{}/final_csvs'.format(WAVE_NUMBER), 'shopgrid_details - shop_x_ctg_indicators_w{}.csv'.format(WAVE_NUMBER))
shop_inventory_csv = os.path.join(BASE_DIR,'data/w_{}/final_csvs'.format(WAVE_NUMBER), 'shopgrid_details - shop_inventory_w{}.csv'.format(WAVE_NUMBER))
first10pdcts_csv = os.path.join(BASE_DIR,'data/w_{}/final_csvs'.format(WAVE_NUMBER), 'shopgrid_details - first_10_pdcts_on_kw_w{}.csv'.format(WAVE_NUMBER))
kw_on_search_bar_csv = os.path.join(BASE_DIR,'data/w_{}/final_csvs'.format(WAVE_NUMBER), 'shopgrid_details - kw_on_search_bar_w{}.csv'.format(WAVE_NUMBER))
share_of_shelves_by_eretailer_with_competitors_csv = os.path.join(BASE_DIR,'data/w_{}/final_csvs'.format(WAVE_NUMBER), 'shopgrid_details - share_of_shelves_by_eretailer_with_competitors_w{}.csv'.format(WAVE_NUMBER))
ctg_x_brnd_indicators_csv = os.path.join(BASE_DIR,'data/w_{}/final_csvs'.format(WAVE_NUMBER), 'shopgrid_details - ctg_x_brnd_indicators_w{}.csv'.format(WAVE_NUMBER))
brnd_search_consistency_csv = os.path.join(BASE_DIR,'data/w_{}/final_csvs'.format(WAVE_NUMBER), 'shopgrid_details - brnd_search_consistency_w{}.csv'.format(WAVE_NUMBER))
avg_kpis_per_brnd_csv = os.path.join(BASE_DIR,'data/w_{}/final_csvs'.format(WAVE_NUMBER), 'shopgrid_summary - avg_kpis_per_brnd_w{}.csv'.format(WAVE_NUMBER))
avg_kpis_per_ctg_csv = os.path.join(BASE_DIR,'data/w_{}/final_csvs'.format(WAVE_NUMBER), 'shopgrid_summary - avg_kpis_per_ctg_w{}.csv'.format(WAVE_NUMBER))
step_2_kpis_agregation_csv = os.path.join(BASE_DIR,'data/w_{}/final_csvs'.format(WAVE_NUMBER), 'shopgrid_summary - step_2_kpis_agregation_w{}.csv'.format(WAVE_NUMBER))
tmp_shop_inventory_csv = os.path.join(BASE_DIR,'data/w_{}/final_csvs'.format(WAVE_NUMBER), 'shopgrid_details - shop_inventory_w{}.csv'.format(WAVE_NUMBER))
shop_indexes_csv = os.path.join(BASE_DIR,'data/w_{}/final_csvs'.format(WAVE_NUMBER), 'clevel - shop_indexes_w{}.csv'.format(WAVE_NUMBER))
international_agregates_csv = os.path.join(BASE_DIR,'data/w_{}/final_csvs'.format(WAVE_NUMBER), 'clevel - international_agregates_w{}.csv'.format(WAVE_NUMBER))
actions_plans_csv = os.path.join(BASE_DIR,'data/w_{}/final_csvs'.format(WAVE_NUMBER), 'shopgrid_details - actions_plans_w{}.csv'.format(WAVE_NUMBER))
action_plans_aggregates_csv = os.path.join(BASE_DIR,'data/w_{}/final_csvs'.format(WAVE_NUMBER), 'shopgrid_summary - action_plans_aggregates_w{}.csv'.format(WAVE_NUMBER))
detailed_plan_achievement_csv = os.path.join(BASE_DIR,'data/w_{}/final_csvs'.format(WAVE_NUMBER), 'shopgrid_details - detailed_plan_achievement_w{}.csv'.format(WAVE_NUMBER))
competitors_prices_csv = os.path.join(BASE_DIR,'data/w_{}/final_csvs'.format(WAVE_NUMBER), 'shopgrid_details - competitors_prices_w{}.csv'.format(WAVE_NUMBER))
brand_rank_category_keyword_prompted_csv = os.path.join(BASE_DIR,'data/w_{}/final_csvs'.format(WAVE_NUMBER), 'shopgrid_details - brand_rank_category_keyword_prompted_w{}.csv'.format(WAVE_NUMBER))
competitors_on_prompted_csv = os.path.join(BASE_DIR,'data/w_{}/final_csvs'.format(WAVE_NUMBER), 'shopgrid_details - competitors_on_prompted_w{}.csv'.format(WAVE_NUMBER))


ctg_share_of_shelf_csv = os.path.join(BASE_DIR,'data/w_{}/final_csvs'.format(WAVE_NUMBER), 'shopgrid_details - ctg_share_of_shelf_w{}.csv'.format(WAVE_NUMBER))
ctg_share_of_shelf_aggregates_csv = os.path.join(BASE_DIR,'data/w_{}/final_csvs'.format(WAVE_NUMBER), 'shopgrid_summary - ctg_share_of_shelf_aggregates_w{}.csv'.format(WAVE_NUMBER))
eretail_kit_detection_csv = os.path.join(BASE_DIR,'data/w_{}/final_csvs'.format(WAVE_NUMBER), 'shopgrid_details - eretail_kit_detection_w{}.csv'.format(WAVE_NUMBER))
eretail_kit_detection_aggregates_csv = os.path.join(BASE_DIR,'data/w_{}/final_csvs'.format(WAVE_NUMBER), 'shopgrid_summary - eretail_kit_detection_aggregates_w{}.csv'.format(WAVE_NUMBER))

# Automated checking
shop_inventory_lw_csv = op.join(BASE_DIR, 'data/w_{}/final_csvs'.format(WAVE_NUMBER - 1), 'shopgrid_details - shop_inventory_w8.csv')

# Objective Grids
OBJECTIVE_GRIDS_REWORKED_XLSX = op.join(BASE_DIR, 'data', 'w_{w}'.format(w=WAVE_NUMBER), 'objective_grid_reworked_w_{w}.xlsx'.format(w=WAVE_NUMBER))


# Similar Web API - paths
SIMILARWEB_YEAR_MONTH = "2018-09" # TODO : check if needs to be updated
assert re.compile('^20\d{2}-\d{2}$').match(SIMILARWEB_YEAR_MONTH)
SIMILARWEB_DATA_ROOT_FOLDER = op.join(BASE_DIR, "data/similarweb")
SIMILARWEB_DATA_YEAR_MONTH_FOLDER = op.join(BASE_DIR, "data/similarweb", SIMILARWEB_YEAR_MONTH)
SIMILARWEB_DATA_YEAR_MONTH_RAW_DATA_FOLDER = op.join(BASE_DIR, "data/similarweb", SIMILARWEB_YEAR_MONTH, "raw")
SIMILARWEB_DATA_YEAR_MONTH_CLEAN_CSVS_FOLDER = op.join(BASE_DIR, "data/similarweb", SIMILARWEB_YEAR_MONTH, "clean_csvs")
SIMILARWEB_DATA_YEAR_MONTH_FORMATTED_DATA_FOLDER = op.join(BASE_DIR, "data/similarweb", SIMILARWEB_YEAR_MONTH, "formatted_data")
for folder in [SIMILARWEB_DATA_YEAR_MONTH_CLEAN_CSVS_FOLDER, SIMILARWEB_DATA_YEAR_MONTH_RAW_DATA_FOLDER,
               SIMILARWEB_DATA_YEAR_MONTH_FORMATTED_DATA_FOLDER]:
    os.makedirs(folder, exist_ok=True)

# web_apis_traffic_aggregates_csv = os.path.join(BASE_DIR,'data/w_{}/final_csvs'.format(WAVE_NUMBER), 'shopgrid_summary - web_apis_traffic_w{}.csv'.format(WAVE_NUMBER))

similar_web_aggregates_csv = op.join(SIMILARWEB_DATA_YEAR_MONTH_FORMATTED_DATA_FOLDER, f'similar_web_aggregates_{SIMILARWEB_YEAR_MONTH}.csv')
similar_web_monthly_visits_csv = op.join(SIMILARWEB_DATA_YEAR_MONTH_FORMATTED_DATA_FOLDER, f'similar_web_monthly_visits_{SIMILARWEB_YEAR_MONTH}.csv')


# web_apis_traffic_csv = os.path.join(BASE_DIR,'data/w_{}/final_csvs'.format(WAVE_NUMBER), 'shopgrid_details - web_apis_traffic_w{}.csv'.format(WAVE_NUMBER))
# web_apis_traffic_aggregates_csv = os.path.join(BASE_DIR,'data/w_{}/final_csvs'.format(WAVE_NUMBER), 'shopgrid_summary - web_apis_traffic_w{}.csv'.format(WAVE_NUMBER))
#
# web_apis_demographics_csv = os.path.join(BASE_DIR,'data/w_{}/final_csvs'.format(WAVE_NUMBER), 'shopgrid_details - web_apis_demographics_w{}.csv'.format(WAVE_NUMBER))
# web_apis_demographics_aggregates_csv = os.path.join(BASE_DIR,'data/w_{}/final_csvs'.format(WAVE_NUMBER), 'shopgrid_summary - web_apis_demographics_w{}.csv'.format(WAVE_NUMBER))
#
# web_apis_traffic_sources_csv = os.path.join(BASE_DIR,'data/w_{}/final_csvs'.format(WAVE_NUMBER), 'shopgrid_details - web_apis_traffic_sources_w{}.csv'.format(WAVE_NUMBER))
# web_apis_traffic_sources_aggregates_csv = os.path.join(BASE_DIR,'data/w_{}/final_csvs'.format(WAVE_NUMBER), 'shopgrid_summary - web_apis_traffic_sources_w{}.csv'.format(WAVE_NUMBER))


# Testings
TEST_PAGES_FOLDER_PATH = op.join(BASE_DIR, "data/eretail/test_pages")


def fpath_namer(shop_id, type_storage, identifier=None, page=1):
    assert type_storage in ['ctg', 'search', 'pdct', 'other', 'raw_csv', 'requests_cache', "prompted"]
    folder = BASE_DIR

    # Generate the folders if they don't exist
    for k in ["cache", "w_" + str(WAVE_NUMBER),  shop_id, type_storage]:
        folder = op.join(folder, k)
        if not os.path.exists(folder):
            os.mkdir(folder)

    if type_storage == 'raw_csv':
        return op.join(BASE_DIR, "cache", "w_" + str(WAVE_NUMBER), shop_id, type_storage)
    if type_storage == 'prompted':
        return op.join(BASE_DIR, "cache", "w_" + str(WAVE_NUMBER), shop_id, "prompted.xlsx")
    elif type_storage == 'requests_cache':
        return op.join(BASE_DIR, "cache", "w_" + str(WAVE_NUMBER), shop_id, shop_id)
    else:
        filename = identifier.replace('/', '-') + '-page' + str(page) + ".html"
        return op.join(BASE_DIR, "cache", "w_" + str(WAVE_NUMBER), shop_id, type_storage, filename)


pattern_japanese_chinese_caracters = regex.compile(r'([\p{IsHan}\p{IsBopo}\p{IsHira}\p{IsKatakana}]+)', re.UNICODE)


def img_path_namer(shop_id,  identifier):
    nb_car_fname = 75 if bool(pattern_japanese_chinese_caracters.search(identifier)) else 250
    clean_identifier = " ".join(identifier.replace('/', '-').split())[:nb_car_fname]

    # Generate the folders if they don't exist
    folder = BASE_DIR
    for k in ["data", "w_" + str(WAVE_NUMBER), 'images', shop_id, 'images']:
        folder = op.join(folder, k)
        if not os.path.exists(folder):
            os.mkdir(folder)
    return op.join(BASE_DIR, "data", "w_" + str(WAVE_NUMBER), 'images', shop_id, 'images', clean_identifier)


def clean_url(href, root_url):
    res = href
    if href.startswith('//'):
        assert root_url.split(':')[0].lower() in ('http', 'https')
        res = root_url.split(':')[0] + ':' + href
    elif href.startswith('/'):
        res = os.path.join(root_url, href[1:])
    elif href.startswith('./'):
        res = os.path.join(root_url, href[2:])
    if not res.startswith('http'):
        res = os.path.join(root_url, href)
    return res


headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:50.0) Gecko/20100101 Firefox/50.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}


def file_hash(filename):
    h = hashlib.sha256()
    with open(filename, 'rb', buffering=0) as f:
        for b in iter(lambda: f.read(128 * 1024), b''):
            h.update(b)
    return h.hexdigest()

# print(file_hash('/code/mhers/data/millesima/images/Moët & Chandon : Grand Vintage 2008.png'))


def clean_xpathd_text(str_or_list, unicodedata_normalize=False):
    if type(str_or_list) != list:
        str_or_list = [str_or_list]
    tmp = ' '.join(w for t in str_or_list for w in t.split()).strip()
    if unicodedata_normalize:
        tmp = unicodedata.normalize('NFKC', tmp)
    return tmp

# foo = u'１２３４５６７８９０'
# foo2 = "〈福光屋〉加賀鳶 純米大吟醸 極上原酒 １８００ｍｌ"
#
# clean_xpathd_text(foo, unicodedata_normalize=True)
# clean_xpathd_text(foo2, unicodedata_normalize=True)


import requests
import shutil
import imghdr
import gzip
import magic


def download_img(img_url, orig_img_path, shop_id="test", decode_content=False, gzipped=False, debug=False):
    response = requests.get(img_url, stream=True, verify=False, headers=headers)
    response.raw.decode_content = decode_content

    tmp_file_path = '/tmp/' + shop_id + 'mhers_tmp_{}.imgtype'.format(abs(hash(img_url)))
    with open(tmp_file_path, 'wb') as out_file:
        shutil.copyfileobj(response.raw, out_file)

    if gzipped:
        f = gzip.open(tmp_file_path, 'rb')
        file_content = f.read()
        with open(tmp_file_path, 'wb') as out_file:
            out_file.write(file_content)
        f.close()

    if imghdr.what(tmp_file_path) is not None:
        img_path = orig_img_path.split('.')[0] + '.' + imghdr.what(tmp_file_path)
        shutil.copyfile(tmp_file_path, img_path)
        if not debug and op.exists(tmp_file_path):
            os.remove(tmp_file_path)
        return img_path
    elif "image" in magic.from_file(tmp_file_path, mime=True):
        img_path = orig_img_path.split('.')[0] + '.' + magic.from_file(tmp_file_path, mime=True).split('/')[-1]
        shutil.copyfile(tmp_file_path, img_path)
        if not debug and op.exists(tmp_file_path):
            os.remove(tmp_file_path)
        return img_path
    else:
        print("WARNING Img not downloaded: ", tmp_file_path, img_url, imghdr.what(tmp_file_path))


if __name__ == '__main__':
    hard_img_url1 = "http://www2.takashimaya.co.jp/sto/image/product/product_image_main/0576/0000880576-001a.jpg"
    orig_img_path = '/tmp/test_img.png'
    print(download_img(hard_img_url1, orig_img_path, shop_id="test", decode_content=False, gzipped=True, debug=False))