import tldextract

from ers import shops

# Testing
urls_test_list = ["https://www.auchandrive.fr/drive/Roissy-Aeroville-542/",
"http://www.binnys.com/",
"bodeboca.com",
"https://www.cellarmasters.com.au/",
"https://courses-en-ligne.carrefour.fr/",
"http://shop.davidjones.com.au/djs/en/davidjones",
"elcorteingles.es/supermercado/",
"elcorteingles.es/clubdelgourmet/",
"https://fd4-www.leclercdrive.fr/default.aspx",
"leshop.ch",
]
url = urls_test_list[3]


def extract_domains(url):
    ext_url = tldextract.extract(url)
    return ".".join([ext_url.domain, ext_url.suffix])


for url in urls_test_list:
    print(extract_domains(url))

shops['domain'] = shops['shop_url'].apply(lambda x: extract_domains(x))

shops = shops[['shop_computer_id', 'shop_id', 'continent', 'country', 'region',
       'segment', 'shop_url', "domain", 'delivery_adress', 'pushed_advertising_module',
       'pushed_advertising_module_comments', 'prmptd_search_on_site',
       'prmptd_search_on_site_comments', 'prmptd_search_on_site_with_image',
       'prmptd_search_on_site_with_image_comments',
       'prmptd_search_on_site_with_text',
       'prmptd_search_on_site_with_text_comments']]

shops.to_excel('/tmp/ERS-referential-shops-alt.xlsx', index=None)
