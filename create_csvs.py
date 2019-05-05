import os.path as op
import os.path as op
from copy import deepcopy

import pandas as pd

from ers import brnd_queries_to_brnd, competitors_queries_to_competitors, ctg_ind_to_ctg, kws_list
from extractors import calc_volume_in_ml


def create_csvs(products, categories, searches, shop_id, dest_folder, collection_date, special_country=None):

    if special_country == 'JP':
        pass
        # TODO

    ##################################################################
    # def gen_raw_brands_searches_extracts_csv(pkl_path, dest_folder):

    # Generating df
    l = []
    for k in searches.keys():
        if k not in brnd_queries_to_brnd.keys():
            continue
        for c, url in enumerate(searches[k]):
            tmp = deepcopy(products[url])
            tmp.update({'brnd': brnd_queries_to_brnd[k], 'brnd_query': k, "page": 1, 'num': c+1})
            l.append(tmp)
    df = pd.DataFrame(l)

    # # Cleaning text variables
    for c in ["pdct_name_on_eretailer", "raw_price", "raw_promo_price"]:
        if c in df.columns:
            df[c] = df[c].apply(lambda x: " ".join(str(x).split()) if ' ' in str(x) else x)

    # Adding other variables
    df['shop_id'] = shop_id
    df['collection_date'] = collection_date

    brands_list_of_cols = ["shop_id", "shop_url", "collection_date", "brnd", "brnd_query", "page", "num",
                           "pdct_name_on_eretailer", "raw_price", 'price', "raw_promo_price", 'promo_price']
    df = df[[c for c in brands_list_of_cols if c in df.columns]]

    # Storing final file
    fpath = op.join(dest_folder, "raw_brands_searches_extracts.xlsx")
    df.to_excel(fpath, index=None)
    print(fpath)

    ##################################################################
    # def gen_raw_competitors_searches_extracts_csv(pkl_path, dest_folder):

    # Generating df
    l = []
    for k in searches.keys():
        if k not in competitors_queries_to_competitors.keys():
            continue
        for c, url in enumerate(searches[k]):
            # print(c, products[url])
            tmp = deepcopy(products[url])
            tmp.update({'competitor': competitors_queries_to_competitors[k], 'competitor_query': k, "page": 1, 'num': c + 1})
            l.append(tmp)
    df = pd.DataFrame(l)

    # Cleaning text variables
    for c in ["pdct_name_on_eretailer", "raw_price", "raw_promo_price"]:
        if c in df.columns:
            df[c] = df[c].apply(lambda x: " ".join(str(x).split()) if ' ' in str(x) else x)

    # Adding other variables
    df['shop_id'] = shop_id
    df['collection_date'] = collection_date
    competitors_list_of_cols = ["shop_id", "shop_url", "collection_date", "page", "num", "competitor", 'competitor_query',
                                "pdct_name_on_eretailer", "raw_price", 'price', "raw_promo_price", 'promo_price']
    df = df[[c for c in competitors_list_of_cols if c in df.columns]]

    # Storing final file
    fpath = op.join(dest_folder, "raw_competitors_searches_extracts.xlsx")
    df.to_excel(fpath, index=None)
    print(fpath)

    ##################################################################
    # def gen_raw_ctg_page_extracts_csv(pkl_path, dest_folder):

    # Generating df
    l = []
    for k in categories.keys():
        for c, url in enumerate(categories[k]):
            # print(c, products[url])
            tmp = deepcopy(products[url])
            tmp.update({"ctg_ind": k, "ctg": ctg_ind_to_ctg[k], "page": 1, 'num': c + 1})
            l.append(tmp)
    df = pd.DataFrame(l)

    # Cleaning text variables
    for c in ["pdct_name_on_eretailer", "raw_price", "raw_promo_price"]:
        if c in df.columns:
            df[c] = df[c].apply(lambda x: " ".join(str(x).split()) if ' ' in str(x) else x)

    # Adding other variables
    df['shop_id'] = shop_id
    df['collection_date'] = collection_date
    ctg_list_of_cols = ["shop_id", "shop_url", "collection_date", "page", "num", "ctg", "pdct_name_on_eretailer", "raw_price", 'price', "raw_promo_price", 'promo_price']
    df = df[[c for c in ctg_list_of_cols if c in df.columns]]

    # Storing final file
    fpath = op.join(dest_folder, "raw_ctg_page_extracts.xlsx")
    df.to_excel(fpath, index=None)
    print(fpath)

    ##################################################################
    # def gen_raw_kws_searches_extracts_csv(pkl_path, dest_folder):

    # Generating df
    l = []
    for kw in searches.keys():
        # print(kws_list)
        # print(kw, kw not in kws_list)
        if kw not in kws_list:
            continue
        for c, url in enumerate(searches[kw]):
            # print(c, products[url])
            tmp = deepcopy(products[url])
            tmp.update({'kw': kw, "page": 1, 'num': c + 1})
            l.append(tmp)
    df = pd.DataFrame(l)

    # Cleaning text variables
    for c in ["pdct_name_on_eretailer", "raw_price", "raw_promo_price"]:
        if c in df.columns:
            df[c] = df[c].apply(lambda x: " ".join(str(x).split()) if ' ' in str(x) else x)

    # Adding other variables
    df['shop_id'] = shop_id
    df['collection_date'] = collection_date
    kws_list_of_cols = ["shop_id", "shop_url", "collection_date", "page", "num", "kw",
                        "pdct_name_on_eretailer", "raw_price", 'price', "raw_promo_price", 'promo_price']
    df = df[[c for c in kws_list_of_cols if c in df.columns]]

    # Storing final file
    fpath = op.join(dest_folder, "raw_kws_searches_extracts.xlsx")
    df.to_excel(fpath, index=None)
    print(fpath)

    ##################################################################
    # def gen_raw_products_pages_extracts_csv(pkl_path, dest_folder):

    # Generating df
    l = []
    for idprod, product in products.items():
        tmp = deepcopy(product)
        l.append(tmp)
    df = pd.DataFrame(l)

    # Cleaning text variables
    for c in ["pdct_name_on_eretailer", "raw_price", "raw_promo_price", 'ctg_denom_txt', 'volume']:
        if c in df.columns:
            df[c] = df[c].apply(lambda x: " ".join(str(x).split()) if ' ' in str(x) else x)

    # Adding other variables
    df['shop_id'] = shop_id
    df['collection_date'] = collection_date
    if "volume" in df.columns:
        df['volume_in_ml'] = df.apply(lambda row: calc_volume_in_ml(row['volume']) if row['volume'] == row['volume'] and type(row['volume']) in [str] else 0, axis=1)
    else:
        df['volume_in_ml'] = 750
    products_list_of_cols = ["shop_id", "shop_url", "collection_date", "pdct_name_on_eretailer", "brnd",
                           "raw_price", 'price', "raw_promo_price", 'promo_price',
                           "volume", 'volume_in_ml', "pdct_img_main_url", "ctg_denom_txt", 'img_path', 'img_hash']
    df = df[[c for c in products_list_of_cols if c in df.columns]]

    # Storing final file
    fpath = op.join(dest_folder, "raw_products_pages_extracts.xlsx")
    df.to_excel(fpath, index=None)
    print(fpath)
