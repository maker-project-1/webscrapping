import os.path as op

import pandas as pd

old_obj_grids_folder = "/data/eretail/objective_grids/objective_grids_from_markets"
new_obj_grids_folder = "/home/renaud/Dropbox/Etaonis/Google Drive/Missions/MH/Scraping/Objectives Grids 2018"
old_to_new_obj_grids_d = {
    op.join(old_obj_grids_folder, "MHUK_ERS_Objectives grid.xlsx"): op.join(new_obj_grids_folder, "Objective Grid - UK - .xlsx"),
    op.join(old_obj_grids_folder, "Objective Grid - DE -  2018.xlsx"): op.join(new_obj_grids_folder, "Objective Grid - DE - .xlsx"),
    op.join(old_obj_grids_folder, "Objective Grid - FR 2018.xlsx"): op.join(new_obj_grids_folder, "Objective Grid - FR - .xlsx"),
    op.join(old_obj_grids_folder, "Objective Grid - USA - Central.xlsx"): op.join(new_obj_grids_folder, "Objective Grid - USA - Central.xlsx"),
    op.join(old_obj_grids_folder, "Objective Grid - USA - Nationalwide.xlsx"): op.join(new_obj_grids_folder, "Objective Grid - USA - Nationwide.xlsx"),
    op.join(old_obj_grids_folder, "Objective Grid - USA - Northeast.xlsx"): op.join(new_obj_grids_folder, "Objective Grid - USA - Northeast.xlsx"),
    op.join(old_obj_grids_folder, "Objective Grid - USA - Southeast.xlsx"): op.join(new_obj_grids_folder, "Objective Grid - USA - Southeast.xlsx"),
    op.join(old_obj_grids_folder, "Objective Grid - USA - West.xlsx"): op.join(new_obj_grids_folder, "Objective Grid - USA - West.xlsx"),
}

# for old_path in old_to_new_obj_grids_d:

# Load old obj_grid
for old_path in list(old_to_new_obj_grids_d.keys()):
    old = pd.read_excel(old_path, index_col=None, skiprows=21)
    print(old.columns)
    cols_to_drop = [x for x in old.columns if "Unnamed:" in x]
    old.drop(columns=cols_to_drop, inplace=True)
    d_rename = {'Target': 'old_Target', 'Plan': 'old_Plan'}
    ind_comment = False
    for c in old.columns:
        if "comment" in c.lower():
            d_rename[c] = 'Comment'
            ind_comment = True
        elif "wide" in c.lower():
            d_rename[c] = 'Site Wide Issue - Not Relevant'
    old.rename(columns=d_rename, inplace=True)
    if not ind_comment:
        old['Comment'] = ""
    # Load new obj_grid
    new_path = old_to_new_obj_grids_d[old_path]
    new = pd.read_excel(new_path, index_col=None, skiprows=21)
    cols_to_drop = [x for x in new.columns if "Unnamed:" in x]
    new.drop(columns=cols_to_drop, inplace=True)
    d_rename = {'Target': 'new_Target', 'Plan': 'new_Plan'}
    new.rename(columns=d_rename, inplace=True)

    merging_columns = ['Shop', 'Category', 'Brand', 'Product Name', 'Volume', 'Action Type']
    final_cols = ['Shop', 'Category', 'Brand', 'Product Name', 'Volume', 'Action Type', 'new_Target', 'new_Plan',
           'old_Target', 'old_Plan', 'Corrected Target', 'Site Wide Issue - Not Relevant', 'Comment', 'Indicator']

    df = pd.merge(old, new, on=merging_columns, how='outer', indicator=True)

    df['_merge'] = df['_merge'].map({"both": "In old and new obj_grids", "left_only": "In old obj_grid only",
                                     "right_only": "In new obj_grid only"})
    df.rename(columns={'_merge': 'Indicator'}, inplace=True)
    df[final_cols].to_excel('/tmp/' + "Merged_" +op.basename(old_path), index=False)
    print('/tmp/' + op.basename(new_path))