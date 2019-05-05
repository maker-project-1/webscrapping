# -*- coding: utf-8 -*
import re
import string
import unidecode
from operator import itemgetter

import regex
import unicodedata
from fuzzyset import FuzzySet
from fuzzywuzzy import fuzz
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel

from ers import brands

pattern_japanese_chinese_caracters = regex.compile(r'([\p{IsHan}\p{IsBopo}\p{IsHira}\p{IsKatakana}【】]+)', re.UNICODE)


def clean_string(x):
    if bool(pattern_japanese_chinese_caracters.search(x)):
        x = unicodedata.normalize('NFKC', x)
    x = x.replace('-', ' ').replace('_', ' ')
    regex_punctuation = re.compile('[%s]' % re.escape(string.punctuation))
    x = regex_punctuation.sub('', x)
    return unidecode.unidecode(' '.join([w for w in x.split() if w]).lower()).replace(' and ', ' & ').replace(' et ', ' & ')


def simple_processor(x):
    return clean_string(x).lower().strip()


class BrandMatcher:
    def __init__(self, ngram_range=(1, 3)):
        """
        :param choices_corpus: should be a list of texts
        :param preprocess_func: is a str->str function
        """
        self.ngram_range = ngram_range
        choices_corpus = [str(x) for x in list(brands['brnd'].dropna().unique())]

        l = brands[['brnd', 'equivalents']].dropna().to_dict('records')
        self.equivalents = {}
        for el in l:
            for eq in el['equivalents'].split(';'):
                self.equivalents[eq.strip()] = el['brnd']

        choices_corpus.extend(self.equivalents.keys())

        self.initial_choices_corpus = choices_corpus
        self.cleaned_choices_corpus = self.cleaner(choices_corpus)

        self.tfidf = TfidfVectorizer(analyzer='word', sublinear_tf=True,  # strip_accents='ascii',
                                     lowercase=True, ngram_range=self.ngram_range, min_df=0).fit(self.cleaned_choices_corpus)

        self.initial_corpus_tf_idf = self.tfidf.transform(choices_corpus)
        self.initial_corpus_tf_idf_dict = {}
        for k in range(len(choices_corpus)):
            self.initial_corpus_tf_idf_dict[choices_corpus[k]] = self.initial_corpus_tf_idf[k]

        # Creating fuzzy set
        self.fset_brands = FuzzySet()
        for token in [str(x) for x in list(brands['brnd'].dropna().unique())]:
            self.fset_brands.add(token)

        self.fset_tokens = FuzzySet()
        for token in list(self.tfidf.vocabulary_):
            self.fset_tokens.add(token)

        # Prepare the japanese matching
        jp_brands = brands[['brnd', 'brnd_jp_clean']]
        jp_brands = jp_brands[jp_brands.brnd_jp_clean.notnull()]
        jp_brands['brnd_jp_clean'] = jp_brands['brnd_jp_clean'].apply(lambda x: unicodedata.normalize('NFKC', x.replace('・', '').replace(' ', '')))
        jp_brands['brnd_jp_size'] = jp_brands['brnd_jp_clean'].apply(lambda x: len(x))
        jp_brands.sort_values(['brnd_jp_size', 'brnd'], ascending=[False, False], inplace=True)
        self.jp_brands = jp_brands
        # jp_brands.to_excel('/tmp/jp_brands.xlsx')

    def cleaner(self, x, verbose=False):
        if verbose:
            print("Before cleaning", type(x), x)

        def cleaning_function(x):
            return clean_string(x).lower()

        if type(x) == list:
            x = [cleaning_function(str(el)) for el in x]
        if type(x) in [str]:
            x = cleaning_function(x)
        if verbose:
            print("After cleaning", type(x), x)
        return x

    def extract(self, query, verbose=False):
        """
        :param choices should be a list of texts
        :param query: TODO add an input type checker
        :param processor: TODO : add a cleaning process
        :param scorer: TODO : Add other distances
        :return:
        """
        initial_choices = self.initial_choices_corpus
        choices_corpus = self.initial_choices_corpus
        corpus_tf_idf = self.initial_corpus_tf_idf
        query = self.cleaner(query)

        # building fuzzy query
        new_query = []

        for q in query.split():
            if verbose:
                print(q)
            fset_get = self.fset_tokens.get(q)
            if fset_get:
                tmp_score, new_q = fset_get[0]
                if verbose:
                    print("Modified", q, new_q, tmp_score)
                if tmp_score > 0.80:
                    new_query.append(new_q)
        query = " ".join(new_query)
        if verbose:
            print("NEW QUERY", query)

        x = self.tfidf.transform([query])

        cosine_similarities = linear_kernel(x, corpus_tf_idf).flatten()
        related_docs_indices = cosine_similarities.argsort().flatten()
        result = [(choices_corpus[k], cosine_similarities[k].flatten()[0]) for k in related_docs_indices]
        result = [(initial_choices[choices_corpus.index(k[0])], k[1]) for k in result]
        # correcting with fuzzyratio score between result and query
        # result = [(k[0], k[1] * 0.01 * 0.5 * (fuzz.token_set_ratio(k[0], query) + fuzz.ratio(k[0], query))) for k in result]
        # result = [(k[0], k[1]) for k in result]
        result.sort(key=lambda tup: tup[1], reverse=True)  # sorts in place

        if verbose:
            print("Query", query, "\nResult", result)
        max_score = max(result, key=itemgetter(1))[1]
        result = [k for k in result if k[1] == max_score]
        return result

    def find_brand(self, pdct_name_on_eretailer, special_country=None, verbose=False):

        if not pdct_name_on_eretailer:
            return {'brand': None, 'score': 0}
        assert special_country in ['JP', None]

        if bool(pattern_japanese_chinese_caracters.search(pdct_name_on_eretailer)) or special_country == 'JP':
            clean_jp_str = lambda x: unicodedata.normalize('NFKC', x.replace('・', '').replace(' ', '').replace('･', ''))
            clean_jp_name = clean_jp_str(pdct_name_on_eretailer)

            # Forbidden words:
            japanese_forbidden_words = [" shoulder ", ' bag ', '【CD】', "【SHM-CD】", 'dvd', 'helmet', 'rucksack',
                                        'daypack', 'daiken', 'ダイケン', "スリープスパ", 'リンゴビール', 'パターソン', 'ヘネシー澄子',
                                        ]
            clean_japanese_forbidden_words = [clean_jp_str(x).lower() for x in japanese_forbidden_words]
            # print(clean_jp_name, clean_japanese_forbidden_words)
            if any(x in clean_jp_name.lower() for x in clean_japanese_forbidden_words):
                return {'brand': None, 'score': 0}

            for br in self.jp_brands.to_dict(orient='records'):
                if br['brnd_jp_clean'] in clean_jp_name:
                    # print("clean_jp_name :", clean_jp_name, "candidate", br['brnd_jp_clean'])
                    return {'brand': br['brnd'], "score": 98.765}
            if "モエ " in pdct_name_on_eretailer and any(x in clean_jp_name for x in ["750", 'ml', 'cl']):
                return {'brand': "Moët & Chandon", "score": 98.765}
        # Ad-hoc rules
        if any([x in pdct_name_on_eretailer.lower() for x in ["moet ", "moët"]]) and 'dom p' in pdct_name_on_eretailer.lower():
            return {'brand': 'Dom Pérignon', 'score': 99}
        if any([x in pdct_name_on_eretailer.lower() for x in ["moet ", "moët"]]):
            return {'brand': 'Moët & Chandon', 'score': 99}
        if any([x in pdct_name_on_eretailer.lower() for x in ["clicquot"]]):
            return {'brand': 'Veuve Clicquot', 'score': 99}
        if any([x in pdct_name_on_eretailer.lower() for x in ["ruinart"]]):
            return {'brand': 'Ruinart', 'score': 99}

        # # Forbidden words:
        # forbidden_words = ['leinwand', "hamper ", ' hamper', ' poster', 'poster ', 'chocolates ', ' chocolates',
        #                    'truffle ', ' truffle', 'birthday cake', ' cake', 'candle', 'poplin', ' sheet ', ' bed ',
        #                    ' cover ', ' kimono', 'towel', 'dvd']
        # if any(x in pdct_name_on_eretailer.lower() for x in forbidden_words):
        #     return {'brand': None, 'score': 0}

        # Cleaning
        pdct_name_on_eretailer = pdct_name_on_eretailer.replace('–', ' ')
        pdct_name_on_eretailer = pdct_name_on_eretailer.replace('-', ' ')
        pdct_name_on_eretailer = pdct_name_on_eretailer.replace('_', ' ')
        pdct_name_on_eretailer = ' '.join(w for w in pdct_name_on_eretailer.split() if w)
        pdct_name_on_eretailer = pdct_name_on_eretailer.replace("'", "").replace('Ã©', 'e').replace('Â', '').replace(
            'Ã«', 'e')
        # print(pdct_name_on_eretailer)
        candidates = self.extract(pdct_name_on_eretailer, verbose=verbose)
        if not candidates:
            return {'brand': None, 'score': 0}
        # print(candidates)
        # print("FIRST SCORE :", brand, score)
        # Post treatment
        clean_tokens = clean_string(pdct_name_on_eretailer).split()
        # s = FuzzySet()
        # s.add(candidate)
        # l = [deepcopy(s.get(ngram, candidate)) for ngram in ngrams]
        # l = [x[0][0] for x in l if type(x) == list]
        brand, score = candidates[0], 0
        for candidate in candidates:
            candidate_str = self.cleaner(candidate[0])
            candidate_str = " ".join(candidate_str.split()[:9])
            nb_token_candidate = len(candidate_str.split())
            ngrams = [" ".join(clean_tokens[start:start + length]) for start in range(len(clean_tokens))
                      for length in range(max(nb_token_candidate, min(4, len(clean_tokens) - start + 1)))]
            # print([("'" + ngram + "'", "'" + candidate + "'", fuzz.ratio(ngram, candidate)) for ngram in ngrams])
            l = [fuzz.ratio(ngram, candidate_str) for ngram in list(set(ngrams))]
            max_score = (max(l + [0])*0.01) ** 2
            if max_score > score:
                score = max_score
                brand = candidate[0]

        if brand in self.equivalents:
            brand = self.equivalents[brand]
        score = round(100 * score, 2)
        # print("SECOND SCORE :", brand, score)

        # Forbidden words
        if any([x in pdct_name_on_eretailer.lower() for x in ["poster", 'dvd']]):
            return {'brand': None, 'score': 0}

        if score >= 80:
            if brand in ['Mercier']:  # Add Krug ???
                if 'hampagne' in pdct_name_on_eretailer.lower():
                    return {'brand': brand, 'score': score}
            if brand in ["Krug"] and any([x.lower() in pdct_name_on_eretailer.lower() for x in ['butler']]):
                return {'brand': None, 'score': 0}
            elif brand == "Belvedere":
                if not any([x in pdct_name_on_eretailer.lower() for x in
                            ['zinfandel', 'chardonnay', 'sauvignon', 'pinot', 'merlot', 'syrah']]):
                    return {'brand': brand, 'score': score}
            else:
                return {'brand': brand, 'score': score}
        elif verbose:
            print("Score is too low for: ", pdct_name_on_eretailer, {'brand': brand, 'score': score})
        return {'brand': None, 'score': 0}


def find_brnd_jp(name_jp):
    for br in brands[['brnd', 'brnd_jp']].to_dict(orient='records'):
        if br['brnd_jp'] == br['brnd_jp'] and br['brnd_jp'] in name_jp:
            return br['brnd']


if __name__ == '__main__':
    from tqdm import tqdm
    tqdm.pandas(tqdm())
    brm = BrandMatcher()

    if False:
        orig = '/data/eretail/w7_code_and_data_archives/raw_data_csv/raw_kws_searches_extracts.csv'
        df = pd.read_csv(orig, sep=';', index_col=False).sample(2000)
        df['brnd'] = df['pdct_name_on_eretailer'].dropna().progress_apply(lambda x: brm.find_brand(x)['brand'])
        df['score'] = df['pdct_name_on_eretailer'].dropna().progress_apply(lambda x: brm.find_brand(x)['score'])
        df[["pdct_name_on_eretailer", "brnd", "ctg", "score"]].to_excel(
            '/data/datascience/textmining/classification/brand_classification.xlsx')
        print('/data/datascience/textmining/classification/brand_classification.xlsx')

    name_jp = 'ラフロイグ Möet Chandion 700ml 【スコッチ／シングルモルト】【並行品】'
    print(find_brnd_jp(name_jp))
    print(brm.find_brand(name_jp))

    l = [
        u'Corton "Maréchaudes" Grand Cru, Chandon de Briailles - 2014',
         u'Corton Blanc Grand Cru, Chandon de Briailles (slightly damaged label) - 2006',
         u'Corton Blanc Grand Cru, Chandon de Briailles - 2001',
         u'Savigny-lès-Beaune "Les Lavières", Chandon de Briailles - 2012',
         u'Aloxe-Corton "Les Valoizières", Chandon de Briailles - 2014',
         u' Chandon Brut Classic 750 ml ',
         u' Chandon Blanc De Noirs 750 ml ',
         u' Moet & Chandon Imperial 375 ml ',
         u' Moet & Chandon Imperial',
         u'Moet et Chandon',
         u'Moet and Chandon',
         u"veuve",
         u"Moet Ice Imperial",
        "Veuve Clicquot La Grande Dame Champagne 750 ml  • 2006 •",
        'LEGO Friends:Snow Resort Hot Chocolate Van 41319 (Age 6 Yrs+)',
        "GLENMORANGIE 12 ans Nectar d'Or 46%",
        "ARDBEG 10 ans Ten Warehouse 46%",
        'Charles Krug Chardonnay',
        'Numanthia-Termes - Termanthia 2010 (750ml)',
        'Dom Perignon',
        'Belvedere Chardonnay',
        'Moët Nectar',
        "Champagne MoÃ«t & Chandon ImpÃ©rial 75 cl  ",
        'Ruinart, Dom Ruinart Rosé, avec étui, 2002 - Champagne - 0,75L',
        'AO YUN CABERNET SAUVIGNON CHINA 2013',
        'ArdbegÂ Supernova Scotch Whisky 700mL',
        "Hennessey, Paradis Cognac",
        'Moët Nectar Imperial Rosé',
        'The barvenie 15 years Sherry cask Single barrel 47.8 degrees 700 ml ■ Cask number varies for each arrival. [Parallel import goods]',
        'Charles Krug Vintage',
        'Montana Ciderworks Newtown Pippin'
        'Anowi: Plymouth Belvedere 1954, Produkt:Poster. gerollt, Größe (HxB):30x40 cm / Poster',
        "Ca'Belvedere DOC Valpolicella Classico Superiore Ripasso 2013 - Ca'Belvedere",
        'Krug Grande Cuvée NV (12 x 375mL half bottle), Champagne, France.',
        '2006 Roederer Cristal 750 ml',
        'Bird In Hand Blackbird Chardonnay 2016',
        'Château Cheval Blanc - St.-Emilion 2014 (750ml)',
        'WHYTE&MACKAY',
        'ニュートン (青リンゴビール) 1瓶(330ml)',
        "Champagne Moët & Chandon 'Dom Pérignon' Vintage 2009"
    ]

    import numpy as np
    import time

    print(brm.find_brand('ChampagneCHARLES HEIDSIECKBlanc Des Millenaires 1995'))
    calculation_durations = []
    for k in l:
        print("\n\n\n")
        t = time.time()
        print(k, brm.find_brand(k, verbose=True))
        calculation_durations.append(time.time() - t)
    print("Mean time for brand computation", np.mean(calculation_durations))
