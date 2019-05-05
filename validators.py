import os.path as op
import re
from glob import glob

import numpy as np
import pandas as pd
from PIL import Image

from ers import country_to_list_of_brnd_query, country_to_list_of_competitor_queries, country_to_list_of_keywords
from ers import country_to_list_of_categories, shop_computer_id_to_country, mh_brands, shop_ctgs, \
    shop_computer_id_to_shop_id
from ers import shops

reurl = re.compile(
    r'^https?://'  # http:// or https://
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
    r'localhost|'  # localhost...
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
    r'(?::\d+)?'  # optional port
    r'(?:/?|[/?]\S+)$', re.IGNORECASE)


def is_valid_url(url):
    # print(type(url is not None and reurl.search(url)), url is not None and reurl.search(url) is not None)
    return url is not None and reurl.search(url) is not None


def spiders_supervision(spiders_folder='/code/mhers/spiders'):
    """This script is intended to provide a quick supervision of all the spiders files"""

    ## Checking that every shop has a spider

    all_shops = set(shops['shop_computer_id'].unique())
    all_spiders = set([x.split('/')[-1].split('.')[0] for x in glob(op.join(spiders_folder, '*.py')) if '__' not in x])
    print('Spiders number : ', len(all_spiders))
    print('Shops number : ', len(all_shops))
    print("Missing spiders :", sorted(list(all_shops - all_spiders)))
    print("Spiders not present in shops referential:", sorted([x for x in list(all_spiders - all_shops)]))

    ## Checking that every spiders has the right shop_id
    count = 0
    for p in [p for p in glob(op.join(spiders_folder, '*')) if '__' not in p]:
        with open(p, 'r') as f:
            for c, l in enumerate(f.readlines()):
                if l.startswith('shop_id ='):
                    shop_computer_id_dtctd = l.replace('shop_id', '').replace(' ', '').replace('=', '').replace(
                        "'", '').replace('"', '').replace('\n', '')
                    if shop_computer_id_dtctd != p.split('/')[-1].split('.')[0]:
                        print(p, 'has a wrong "shop_id = ..." at line', c + 1)
                        print('-----', shop_computer_id_dtctd, p.split('/')[-1].split('.')[0])
                        count += 1
    print("Total of ", count, "problems with shop_ids")

    # Checking that every scraper has data retrieved
    scraped_data_existing_shop_ids = set()
    missing_files = []
    file_names = ["raw_ctg_page_extracts.xlsx", "raw_competitors_searches_extracts.xlsx",
                  "raw_brands_searches_extracts.xlsx", "raw_kws_searches_extracts.xlsx",
                  "raw_products_pages_extracts.xlsx"]
    for folder in glob("/code/mhers/cache/w_8/*/raw_csv"):
        shop_id = folder.split('/')[-2]
        for fname in file_names:
            if not op.exists(op.join(folder, fname)):
                print(fname)
                missing_files.append(fname)
                break
        else:
            scraped_data_existing_shop_ids.add(shop_id)
    print("Missing files for shop_ids : ", sorted(list(all_shops - scraped_data_existing_shop_ids)))
    print("Missing files : ", missing_files)


def validate_raw_files(folder, special_country=None):
    """
    Validates raw informations from extracted CSVs :
    """
    if special_country=='JP':
        pass
        # TODO

    # Getting important features
    result = {}
    fpath = op.join(folder, "raw_ctg_page_extracts.xlsx")
    fpath_ind = "raw_ctg_page_extracts.xlsx"
    print('Testing', folder)
    df = pd.read_excel(fpath, index_col=None)
    shop_id = list(df["shop_id"].unique())[0]
    result = []
    country = shop_computer_id_to_country[shop_id]
    brnd_queries = country_to_list_of_brnd_query[country]
    keywords = country_to_list_of_keywords[country]
    competitor_queries = country_to_list_of_competitor_queries[country]
    categories = country_to_list_of_categories[country]
    shop_categories = shop_ctgs.loc[(shop_ctgs.shop_id == shop_id) & (shop_ctgs.ctg_is_listed == 1), "ctg"].tolist()

    # ## Testing raw_brands_searches_extracts_csv
    fpath = op.join(folder, "raw_brands_searches_extracts.xlsx")
    tmp_result = {'shop_id': shop_id, 'fpath_ind': "raw_brands_searches_extracts.xlsx"}
    print('Testing', fpath)
    assert op.exists(fpath)

    df = pd.read_excel(fpath, index_col=None)
    tmp_result['nb_lines'] = df.shape[0]
    # print('Working on', fpath, 'shape and cols', df.shape, df.columns)
    if df.shape[0] < 5:
        print(fpath, 'strangely small number of lines : ', df.shape[0])

    if df.shape[0] == 0:
        print(fpath, 'has no lines')
    else:
        required_columns = ['price', 'pdct_name_on_eretailer']
        missing_columns = list(set(required_columns) - set(df.columns))
        tmp_result['missing_columns'] = missing_columns
        if missing_columns:
            print("With ", fpath, 'missing columns : ', missing_columns)

        cols_that_shouldnt_be_empty = ["shop_id", "collection_date", "page", "num", "brnd", "brnd_query"]
        tmp = [c for c in cols_that_shouldnt_be_empty if len(df) - df[c].count() > 0]
        if tmp:
            print("With ", fpath, 'empty values in columns : ', tmp)

        missing_brands = list(set(brnd_queries) - set(df['brnd_query'].unique()))
        tmp_result['missing_brands'] = missing_brands
        if missing_brands:
            print('With ', fpath, 'missing brand', missing_brands)

        if 'price' in df.columns:
            if 'promo_price' in df.columns:
                pct_price_available = df[(df['price'] > 0) | (df['promo_price'] > 0) ].shape[0] / df.shape[0]
            else:
                pct_price_available = df[(df['price'] > 0)].shape[0] / df.shape[0]
            if pct_price_available < 0.9:
                print('With ', fpath, ' pct of price available =', pct_price_available)

        cols_to_check = ["shop_id", "collection_date", "page", "num", "brnd", "brnd_query", 'price', 'promo_price']
        for c in (c for c in cols_to_check if c in df.columns):
            tmp_result['pct_notnull_' + c ] = df[c].notnull().mean()
    result.append(tmp_result)

    # ## Testing raw_competitors_searches_extracts_csv
    fpath = op.join(folder, "raw_competitors_searches_extracts.xlsx")
    tmp_result = {'shop_id': shop_id, 'fpath_ind': "raw_competitors_searches_extracts.xlsx"}
    print('Testing', fpath)
    assert op.exists(fpath)

    df = pd.read_excel(fpath, index_col=None)
    tmp_result['nb_lines'] = df.shape[0]
    # print('Working on', fpath, 'shape and cols', df.shape, df.columns)
    if df.shape[0] < 5:
        print(fpath, 'strangely small number of lines : ', df.shape[0])

    if df.shape[0] == 0:
        print(fpath, 'has no lines')
    else:
        required_columns = ['price', 'pdct_name_on_eretailer']
        missing_columns = list(set(required_columns) - set(df.columns))
        tmp_result['missing_columns'] = missing_columns
        if missing_columns:
            print("With ", fpath, 'missing columns : ', missing_columns)

        cols_that_shouldnt_be_empty = ["shop_id", "collection_date", "page", "num", "competitor_query", "competitor"]
        tmp = [c for c in cols_that_shouldnt_be_empty if len(df) - df[c].count() > 0]
        if tmp:
            print("With ", fpath, 'empty values in columns : ', tmp)

        missing_competitors = list(set(competitor_queries) - set(df['competitor_query'].unique()))
        tmp_result["missing_competitors"] = missing_competitors
        if missing_competitors:
            print('With ', fpath, 'missing competitors', missing_competitors)

        if 'price' in df.columns:
            if 'promo_price' in df.columns :
                pct_price_available = df[(df['price'] > 0) | (df['promo_price'] > 0) ].shape[0] / df.shape[0]
            else:
                pct_price_available = df[(df['price'] > 0)].shape[0] / df.shape[0]
            if pct_price_available < 0.9:
                print('With ', fpath, ' pct of price available =', pct_price_available)

        cols_to_check = ["shop_id", "collection_date", "page", "num", "competitor_query", "competitor", 'price', 'promo_price']
        for c in (c for c in cols_to_check if c in df.columns):
            tmp_result['pct_notnull_' + c ] = df[c].notnull().mean()
    result.append(tmp_result)


    ### Testing raw_ctg_page_extracts_csv
    fpath = op.join(folder, "raw_ctg_page_extracts.xlsx")
    tmp_result = {'shop_id': shop_id, 'fpath_ind': "raw_ctg_page_extracts.xlsx"}
    print('Testing', fpath)
    assert op.exists(fpath)

    df = pd.read_excel(fpath, index_col=None)
    tmp_result['nb_lines'] = df.shape[0]
    # print('Working on', fpath, 'shape and cols', df.shape, df.columns)
    if df.shape[0] < 5:
        print(fpath, 'strangely small number of lines : ', df.shape[0])

    required_columns = ['price', 'pdct_name_on_eretailer']
    missing_columns = list(set(required_columns) - set(df.columns))
    tmp_result['missing_columns'] = missing_columns
    if missing_columns:
        print("With ", fpath, 'missing columns : ', missing_columns)

    cols_that_shouldnt_be_empty = ["shop_id", "collection_date", "page", "num", "ctg"]
    tmp = [c for c in cols_that_shouldnt_be_empty if len(df) - df[c].count() > 0]
    if tmp:
        print("With ", fpath, 'empty values in columns : ', tmp)

    missing_categories = list(set(shop_categories) - set(df['ctg'].unique()))
    tmp_result["missing_categories"] = missing_categories
    if missing_categories:
        print('With ', fpath, 'missing categories', missing_categories)

    if 'price' in df.columns:
        if 'promo_price' in df.columns:
            pct_price_available = df[(df['price'] > 0) | (df['promo_price'] > 0)].shape[0] / df.shape[0]
        else:
            pct_price_available = df[(df['price'] > 0)].shape[0] / df.shape[0]
        if pct_price_available < 0.9:
            print('With ', fpath, ' pct of price available =', pct_price_available)

    cols_to_check = ["shop_id", "collection_date", "page", "num", 'ctg', 'price', 'promo_price']
    for c in (c for c in cols_to_check if c in df.columns):
        tmp_result['pct_notnull_' + c] = df[c].notnull().mean()
    result.append(tmp_result)


    ### Testing raw_kws_searches_extracts_csv
    fpath = op.join(folder, "raw_kws_searches_extracts.xlsx")
    tmp_result = {'shop_id': shop_id, 'fpath_ind': "raw_kws_searches_extracts.xlsx"}
    print('Testing', fpath)
    assert op.exists(fpath)

    df = pd.read_excel(fpath, index_col=None)
    tmp_result['nb_lines'] = df.shape[0]
    # print('Working on', fpath, 'shape and cols', df.shape, df.columns)
    if df.shape[0] < 5:
        print(fpath, 'strangely small number of lines : ', df.shape[0])

    if df.shape[0] == 0:
        print(fpath, 'has no lines')
    else:
        required_columns = ['price', 'pdct_name_on_eretailer', "price", "promo_price"]
        missing_columns = list(set(required_columns) - set(df.columns))
        tmp_result['missing_columns'] = missing_columns
        if missing_columns:
            print("With ", fpath, 'missing columns : ', missing_columns)

        cols_that_shouldnt_be_empty = ["shop_id", "collection_date", "page", "num", "kw"]
        tmp = [c for c in cols_that_shouldnt_be_empty if len(df) - df[c].count() > 0]
        if tmp:
            print("With ", fpath, 'empty values in columns : ', tmp)

        missing_keywords = list(set(keywords) - set(df['kw'].unique()))
        tmp_result["missing_keywords"] = missing_keywords
        if missing_keywords:
            print('With ', fpath, 'missing kws', missing_keywords)

        if 'price' in df.columns:
            if 'promo_price' in df.columns :
                pct_price_available = df[(df['price'] > 0) | (df['promo_price'] > 0) ].shape[0] / df.shape[0]
            else:
                pct_price_available = df[(df['price'] > 0)].shape[0] / df.shape[0]
            if pct_price_available < 0.9:
                print('With ', fpath, ' pct of price available =', pct_price_available)

        cols_to_check = ["shop_id", "collection_date", "page", "num", 'kw', 'price', 'promo_price']
        for c in (c for c in cols_to_check if c in df.columns):
            tmp_result['pct_notnull_' + c] = df[c].notnull().mean()
    result.append(tmp_result)


    ### Testing raw_products_pages_extracts_csv
    fpath = op.join(folder, "raw_products_pages_extracts.xlsx")
    tmp_result = {'shop_id': shop_id, 'fpath_ind': "raw_products_pages_extracts.xlsx"}
    print('Testing', fpath)
    assert op.exists(fpath)

    df = pd.read_excel(fpath, index_col=None)
    tmp_result['nb_lines'] = df.shape[0]
    # print('Working on', fpath, 'shape and cols', df.shape, df.columns)
    if df.shape[0] < 5:
        print(fpath, 'strangely small number of lines : ', df.shape[0])

    required_columns = ['price', 'pdct_name_on_eretailer']
    missing_columns = list(set(required_columns) - set(df.columns))
    tmp_result['missing_columns'] = missing_columns
    if missing_columns:
        print("With ", fpath, 'missing columns : ', missing_columns)

    cols_that_shouldnt_be_empty = ["shop_id", "collection_date"]
    tmp = [c for c in cols_that_shouldnt_be_empty if len(df) - df[c].count() > 0]
    if tmp:
        print("With ", fpath, 'empty values in columns : ', tmp)

    cols_to_check = ["shop_id", "collection_date", "page", 'price', "pdct_img_main_url", 'promo_price']
    for c in (c for c in cols_to_check if c in df.columns):
        tmp_result['pct_notnull_' + c] = df[c].notnull().mean()

    # Testing volume
    tmp = df[df.brnd.isin(mh_brands)]
    tmp1 = tmp.drop_duplicates(['pdct_name_on_eretailer', 'price'])
    tmp2 = tmp.drop_duplicates(['pdct_name_on_eretailer', 'price', 'volume_in_ml'])
    if tmp1.shape[0] != tmp2.shape[0]:
        print('WARNING !!! volume_in_ml seems erroneous !!!!!!!!!!!!!!!!!')

    if 'price' in df.columns:
        if 'promo_price' in df.columns:
            pct_price_available = df[(df['price'] > 0) | (df['promo_price'] > 0)].shape[0] / df.shape[0]
        else:
            pct_price_available = df[(df['price'] > 0)].shape[0] / df.shape[0]
        if pct_price_available < 0.9:
            print('With ', fpath, ' pct of price available =', pct_price_available)

    df['tmp_url_valid'] = df['pdct_img_main_url'].apply(lambda x: is_valid_url(x) if type(x) == str else np.NaN)
    if df['tmp_url_valid'].mean() < 0.85:
        print('With ', fpath, ' pct url_valid is low : ', df['tmp_url_valid'].mean())
    tmp_result["pct_img_url_valid"] = df['tmp_url_valid'].mean()
    assert df.loc[df['volume_in_ml'] > 0].shape[0] >= 1

    df['img_size'] = df['img_path'].apply(lambda x: op.getsize(x) if x==x else None)
    df['img_length'] = df['img_path'].apply(lambda x: Image.open(x).size[0] if x==x else None)
    df['img_height'] = df['img_path'].apply(lambda x: Image.open(x).size[1] if x==x else None)
    print('\n\nImages tests --------------')
    # from matcher import BrandMatcher
    # brm = BrandMatcher()
    # df['brnd'] = df['pdct_name_on_eretailer'].apply(lambda x: brm.find_brand(x)['brand'] if type(x) == str else None)
    df.to_excel('/tmp/' + shop_id + 'test_products.xlsx')
    print('Stored testing file at : ', '/tmp/' + shop_id + 'test_products.xlsx')
    print("Number of products with image : ", df['pdct_img_main_url'].count())
    print('Number of images downloaded', df[df.img_path.notnull()].shape[0])
    # print("Percentage of images downloaded : ", df.loc[df.brnd.isin(mh_brands), 'img_path'].count() / df.loc[df.brnd.isin(mh_brands), 'pdct_img_main_url'].count())
    print("Size of Images (in ko)", df['img_size'].mean())
    print("Length of Images (in px)", df['img_length'].mean())
    print("Height of Images (in px)", df['img_height'].mean())
    tmp_result["pct_img_downloaded"] =  df['img_path'].count() / df['pdct_img_main_url'].count()
    tmp_result["img_height_mean"] =  df['img_height'].mean()
    tmp_result["img_length_mean"] =  df['img_length'].mean()
    tmp_result["img_size_mean"] =  df['img_size'].mean()
    if df['img_height'].mean() < 100 or df['img_length'].mean() < 100:
        print(" ========================> WARNING : small lgnth or width of the images. Mean height (in px):", df['img_height'].mean())
    if df['img_size'].mean() < 100:
        print(" ========================> WARNING : small size of the images. Mean :", df['img_size'].mean()/1000, "ko")
    print('All tests passed for data in folder ', folder)
    result.append(tmp_result)

    return result


def check_products_detection(shop_computer_id, dest_folder, shop_inventory_csv_lw):
    """
    Checks the number of products detected against last wave
    :param shop_id:
    :return:
    """
    shop_id = shop_computer_id_to_shop_id[shop_computer_id]
    shop_inv = pd.read_csv(shop_inventory_csv_lw, index_col=None, sep=';')
    df = pd.read_excel(op.join(dest_folder, "raw_products_pages_extracts.xlsx"), index_col=False)
    lw_df = shop_inv[(shop_inv.shop_id == shop_id) & shop_inv.pdct_name_on_eretailer.notnull()]

    if lw_df.shape[0] == 0:
        print("LAST WAVE SHOP INVENTORY has no products for : ", shop_id)
        return None

    print("====================\nNumber of products per brand")
    for ix, mh_brand in enumerate(mh_brands):
        print(mh_brand, "nb pdcts in last wave: ", lw_df[lw_df.brnd == mh_brand].shape[0],
              ' - in this wave', df[df.brnd == mh_brand].shape[0])
        if lw_df[lw_df.brnd == mh_brand].shape[0] - df[df.brnd == mh_brand].shape[0] > 2:
            print("WARNING possible missing products in ", mh_brand, '!!!!!!!!!!!!!!!!!!!!!!!!!')


if __name__ == '__main__':
    if True:
        spiders_supervision()


