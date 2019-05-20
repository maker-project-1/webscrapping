fr_paths = ['/code/mhers/amazon/fr_0_kw_search.py',
			'/code/mhers/amazon/fr_00_ctg_scrap.py',
			'/code/mhers/amazon/fr_000_g_primenow.py',
			'/code/mhers/amazon/fr_1_create_data.py',
			'/code/mhers/amazon/fr_2_g_compliance_score.py',
			'/code/mhers/amazon/fr_3_ctg_pages_sos.py',
			'/code/mhers/amazon/fr_3_kws_sos.py',
			'/code/mhers/amazon/fr_4_gen_graphs.py',
			'/code/mhers/amazon/fr_5_sellers.py',
			'/code/mhers/amazon/fr_6_gen_data_for_pivot.py']

for p in fr_paths:
	dest = p.replace('amazon/fr', 'amazon/uk')
	print(dest)
	with open(p, 'r') as f:
		txt = f.read()
	txt = txt.replace('_FR', '_UK').replace('_fr', '_uk')
	with open(dest, 'w') as f:
		f.write(txt)
