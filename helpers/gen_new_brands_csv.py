from collections import Counter

import pandas as pd

from ers import brands

"""
WARNING!   USE /code/mhers/ressources/ERS-referential-brands-old2018030509.csv as starting point for brands
"""

# Importing Data from MH
df = pd.read_excel('/code/mhers/ressources/Key Premium Brands of Top Suppliers.xlsx', index_col=None)
df.rename(columns={'Owner': 'distributor', 'Brand': 'brnd'}, inplace=True)

data = Counter(" ".join(df['brnd'].unique()).split(" ")).most_common(20) # Use the names of brands to determine ctg

d_common_words = {'Scotch': 'Whisky',
    'Malt': 'Whisky',
    'Vodka': 'Vodka',
    'Champagne': 'Champagne',
    'Liqueur': 'Other',
    'Tequila': 'Tequila',
    'Sparkling': 'Sparkling',
    'Wine': 'Still Wine',
    'Whisky': 'Whisky',
    'Bourbon': 'Other',
    'Whiskey': 'Whisky',
    'Brandy': 'Cognac',
    'Rum': 'Rum',
    'Gin': 'Gin',
    'Cognac': 'Cognac',
}


def detect_ctg(s):
    for k in d_common_words:
        if k in s:
            return d_common_words[k]
    return None


df['ctg'] = df['brnd'].apply(lambda x: detect_ctg(x))


# Clean the names of brands and remove duplicates
def clean_brnd_names(s):
    l = s.split()
    for k in d_common_words.keys():
        if k in l:
            l.remove(k)
    return " ".join(l)

# Hand Cleaning
df['new_brnd_name'] = df['brnd'].apply(lambda x: clean_brnd_names(x))
df['new_brnd_name'] = df['new_brnd_name'].replace('Moet et Chandon', 'Moët & Chandon')
df['new_brnd_name'] = df['new_brnd_name'].replace("Dewar's", "Dewar")
df['new_brnd_name'] = df['new_brnd_name'].replace("Stranahan's", "Stranahan")
df = df[df.new_brnd_name != 'Moet et Chandon Marc']
df = df[df.brnd != 'Glenfiddich Liqueur']
df = df[df.brnd != 'Courvoisier Liqueurs']
df = df[df.brnd != 'Royal Salute by Chivas Scotch']
df = df[df.brnd != 'Absolut Tune Liqueur']
df = df[df.brnd != 'Suntory Hibiki Whisky']
df = df[df.brnd != 'Suntory Single Malts Whisky']
df = df[df.brnd != 'Suntory Whisky']
df = df[df.brnd != 'Mumm Napa Sparkling Wine']
df = df[df.brnd != 'Mumm Sparkling Wine']
df = df[df.brnd != 'Deutz Sparkling Wine']

list_of_brands = list(brands['brnd'].dropna().unique())
df['detected_brnd'] = df['new_brnd_name'].apply(lambda x: find_brand(x, list_of_brands)['brand'] if type(x) == str else None)
df['score'] = df['new_brnd_name'].apply(lambda x: find_brand(x, list_of_brands)['score'] if type(x) == str else None)

df.loc[df['new_brnd_name'] =='Menger Krug', 'detected_brnd'] = 'Menger Krug'
df.loc[df['new_brnd_name'] =='Glen Grant', 'detected_brnd'] = 'Glen Grant'
df.loc[df['new_brnd_name'] =='Dufftown Glenlivet', 'detected_brnd'] = 'Dufftown Glenlivet'
df.loc[df['new_brnd_name'] =='Four Bells', 'detected_brnd'] = 'Four Bells'
df.loc[df['new_brnd_name'] =='Green Point', 'detected_brnd'] = 'Green Point'
df[df.duplicated(['detected_brnd'], keep=False)].to_excel('/tmp/dup_brands.xlsx')
df.to_excel('/tmp/match_brands.xlsx')
df.drop(columns=['brnd'], inplace=True)
df.rename(columns={'new_brnd_name': 'brnd'}, inplace=True)

# Generating new brands file
final_brands_expected_nb = df[df['score'] == 0].shape[0] + brands.shape[0]
print('brandsshape', brands.shape)
br = pd.merge(brands, df[['brnd', 'distributor']], on='brnd', how='left')
print('brandsshape', br.shape)
### Creating values for the new file
tmp = df[df['score'] == 0][['brnd', 'ctg', 'distributor']]
tmp['is_mh'] = False
tmp['brnd_order'] = None
tmp['large_selection'] = True
tmp['close_selection'] = False
tmp['is_competitor'] = False
br = br.append(tmp)
assert br.shape[0] == final_brands_expected_nb
cols = ['distributor'] + list(brands.columns)
br.loc[br['is_mh'] == True, 'distributor'] = 'Moët Hennessy'
br.loc[br['ctg'].isnull(), 'ctg'] = 'Other'
br.drop_duplicates(inplace=True)
br = br[br.brnd != 'Mumm Sparkling Wine']
br = br[~((br.brnd == 'Grants') & (br.ctg == 'Sparkling'))]
br = br[~((br.brnd == 'Crown Royal') & (br.ctg == 'Other'))]
br = br[~((br.brnd == 'Godiva') & (br.ctg == 'Other'))]
br = br[~((br.brnd == 'Smooth Ambler') & (br.ctg == 'Other'))]
br = br[~((br.brnd == 'X-Rated') & (br.ctg == 'Other'))]
br = br[~((br.brnd == 'Sipsmith') & (br.ctg == 'Gin'))]
br = br[~((br.brnd == 'Chambord') & (br.ctg == 'Other'))]
br = br[~((br.brnd == 'Larios') & (br.distributor == 'Beam Suntory'))]
br = br[~((br.brnd == 'Dunhill') & (br.distributor == 'Edrington'))]
br[br.duplicated('brnd', keep=False)].to_excel('/tmp/test.xlsx')
assert br[br.duplicated('brnd', keep=False)].shape[0] == 0
br[cols].to_csv('/code/mhers/ressources/ERS-referential-brands-algo.csv', sep=';', index=None)
