import os.path as op

import pandas as pd

from ers import BASE_DIR
from ers import brands, pdcts
from matcher import BrandMatcher

# Copy paste the data from the Market Brief - Japan.xlsm to a single page with all the pdcts information
# Columns should be the ones that are the keys in the following rename_dict


# Import and clean the imported data
df = pd.read_excel(op.join(BASE_DIR, "ressources/mktbrief_data-jp.xlsx"))
rename_dict = {"Category": 'ctg',
        "Brand": 'brnd',
        "Family": 'pdct_family',
        "Product name FR": 'pdct_name',
        "Volume": 'volume_in_ml',
        "商品名 JP": 'pdct_query',
        "Priority": 'priority',
        "Vintage": 'vintage',
        "Flagship": 'flagship',
        "ACCESSIBLE stores": 'ACCESSIBLE',
        "SPECIAL stores": 'SPECIAL',
        "EXCLUSIVE stores": 'EXCLUSIVE',
        "Minimum Price": 'min_price',
        "Maximum Price": 'max_price',
        "Flagship product of brand": 'to_delete_flagship_pdct_of_brnd',
        "Competitor product name EN": 'competitor',
        "Competitor product name JP": 'competitor_query',
        "Insert the competitor's MinPrice": 'competitor_min_price',
        "Insert the competitor's MaxPrice": 'competitor_max_price',
}

df.rename(columns=rename_dict, inplace=True)
df = df[df.pdct_name != "delete"]


# Creating necessary values
df['country'] = 'JP'
df['continent'] = 'APAC'
df['source'] = 'APAC'
for c in ['program', 'pdct_names_equivalents', 'words_to_include', 'tolerance05', 'exclude_terms',
          'words_to_include_05', 'ref_pdct_key_viseo', 'brnd_order', 'abs_pdct_order', 'pdct_order',
          'pdct_quality_name']:
    df[c] = ''
df['competitor_volume_in_ml'] = 750  # WARNING : check if this is still good

# Correct product names
pdct_rename_dict = {
'Ardbeg 10 Years Old': 'Ardbeg Ten Years Old',
'Belvedere Pure Vodka': 'Belvedere Vodka',
'Dom Perignon Vintage 2009': 'Dom Pérignon Blanc Vintage 2009',
'Glenmorangie Original': 'Glenmorangie The Original',
'Hennessy VS Cognac': 'Hennessy V.S.',
'Hennessy VSOP Cognac': 'Hennessy V.S.O.P. Privilege',
'Hennessy XO Cognac ': 'Hennessy X.O.',
'Krug Grande Cuvée Champagne': 'Krug Grande Cuvée',
'Moët & Chandon Ice Impérial Rosé': 'Moët & Chandon Ice Rosé Impérial',
'Moët & Chandon Impérial Brut Magnum': 'Moët & Chandon Impérial Brut',
'Moët & Chandon Impérial Brut Half Bottle': 'Moët & Chandon Impérial Brut',
'Moët & Chandon Impérial Rosé': 'Moët & Chandon Impérial Rosé Champagne',
# 'Dom Ruinart Blanc de Blancs 2004': '',
# 'Dom Ruinart Blanc de Blancs 2006': '', #WARNING !
'Veuve Clicquot La Grande Dame Rosé 2006 ': 'Veuve Clicquot La Grande Dame Rosé 2006',
'Veuve Clicquot Vintage 2008': 'Veuve Clicquot Vintage Brut 2008',
'Veuve Clicquot Yellow Label Magnum': 'Veuve Clicquot Yellow Label Brut',
'Veuve Clicquot Yellow Label Half Bottle': 'Veuve Clicquot Yellow Label Brut',
'Veuve Clicquot Yellow Label': 'Veuve Clicquot Yellow Label Brut',
'Cloudy Bay Tekoko': 'Cloudy Bay Te Koko',
'Cloudy Bay Tewahi': 'Cloudy Bay Te Wahi',
# 'Newton Skyside Chardonnay': '',
# 'Newton Skyside Claret': '',
# 'Newton Unfiltered Cabernet Sauvigon': '',
# 'Newton Unfiltered Pinot Noir': '',
# 'Newton Puzzle': '',
'Dom Perignon P2 2000': 'Dom Pérignon P2 Vintage 2000',
'Moët & Chandon Impérial Rosé Half Bottle': 'Moët & Chandon Impérial Rosé Champagne',
}

df['pdct_name'].replace(pdct_rename_dict, inplace=True)


# Handle brands and brnd queries
df['brnd'].replace({'Cloudy bay': 'Cloudy Bay', "Chandon Australia": "Chandon"}, inplace=True)
df = pd.DataFrame(pd.merge(df, brands[['brnd', 'brnd_jp']], on=['brnd'], how='left', indicator=True))
assert df['_merge'].value_counts().iloc[0] == df.shape[0]
df.rename(columns={'brnd_jp': 'brnd_query'}, inplace=True)
df.drop(columns=['_merge'], inplace=True)
# add 'rose', 'box', 'pdct_img_ref_path' from pdcts
pdct_to_merge = pdcts[['pdct_name', 'rose', 'box', 'pdct_img_ref_path']]
pdct_to_merge.drop_duplicates(['pdct_name'], inplace=True)

df = pd.DataFrame(pd.merge(df, pdct_to_merge, on=['pdct_name'], how='left', indicator=True))
df['_merge'].value_counts()
df.drop(columns=['_merge'], inplace=True)


# Handling segments / must-haves
tdf = pd.DataFrame()
for segment in ['SPECIAL', "ACCESSIBLE", "EXCLUSIVE"]:
    tmp = pd.DataFrame(df.copy())
    tmp['segment'] = segment
    tmp['must_have'] = 1 * (tmp[segment] == 'Y')
    tdf = tdf.append(tmp)
tdf.drop(columns=['SPECIAL', "ACCESSIBLE", "EXCLUSIVE", '_merge', 'to_delete_flagship_pdct_of_brnd'],
         errors='ignore', inplace=True)

final_cols = ['continent', 'country', 'segment', 'ctg', 'brnd', 'brnd_query', 'pdct_name', 'pdct_quality_name',
              'pdct_query', 'pdct_family', 'pdct_order', 'brnd_order', 'abs_pdct_order', 'ref_pdct_key_viseo',
              'flagship', 'must_have', 'source', 'priority', 'min_price', 'max_price', 'competitor',
              'competitor_query', 'competitor_brnd', 'competitor_volume_in_ml', 'volume_in_ml',
              'box', 'rose', 'vintage', 'program', 'pdct_names_equivalents', 'words_to_include',
              'tolerance05', 'exclude_terms', 'words_to_include_05', 'pdct_img_ref_path',
              'competitor_min_price', 'competitor_max_price']

brm = BrandMatcher()
tdf['competitor_brnd'] = df['competitor'].apply(lambda x: brm.find_brand(x)['brand'] if x == x else '')
print("Differences in columns", set(final_cols) ^ set(tdf.columns))
tdf[final_cols].to_excel(op.join(BASE_DIR, "ressources/pdcts_jp.xlsx"), index=None)
print(f"soffice '{op.join(BASE_DIR, 'ressources/pdcts_jp.xlsx')}'")