# -*- coding: utf-8 -*
import csv
import re
from operator import itemgetter

import pandas as pd
import regex
import string
import unidecode
from fuzzyset import FuzzySet
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel

from ers import rose_kws
from extractors import find_year_string, extract_year
from translator_utils import JapTranslator


def clean_string(x):
    regex_punctuation = re.compile('[%s]' % re.escape(string.punctuation))
    x = regex_punctuation.sub('', x)
    return unidecode.unidecode(' '.join([w for w in x.split() if w]).lower()).replace(' and ', ' & ')


def simple_processor(x):
    return clean_string(x).lower().strip()


class TFIDFmatcher:
    def __init__(self, choices_corpus, ngram_range=(1, 2), use_cleaner=True, preprocess_func=None):
        """
        :param choices_corpus: should be a list of texts
        :param preprocess_func: is a str->str function
        """
        self.ngram_range = ngram_range
        self.use_cleaner = use_cleaner
        self.preprocess_func = preprocess_func

        self.initial_choices_corpus = choices_corpus
        if self.use_cleaner:
            choices_corpus = self.cleaner(choices_corpus)
        if self.preprocess_func:
            choices_corpus = [self.preprocess_func(k) for k in choices_corpus]

        self.tfidf = TfidfVectorizer(analyzer='word', sublinear_tf=True,  # strip_accents='ascii',
                                     lowercase=True, ngram_range=self.ngram_range, min_df=0).fit(choices_corpus)

        self.initial_corpus_tf_idf = self.tfidf.transform(choices_corpus)
        self.initial_corpus_tf_idf_dict = {}
        for k in range(len(choices_corpus)):
            self.initial_corpus_tf_idf_dict[choices_corpus[k]] = self.initial_corpus_tf_idf[k]
        self.vocabulary = self.tfidf.vocabulary_.keys()
        self.fset_vocabulary = FuzzySet()
        for brnd in self.vocabulary:
            self.fset_vocabulary.add(brnd)


    def cleaner(self, x, verbose=False):
        if verbose:
            print("Before cleaning", type(x), x)

        def cleaning_function(x):
            return clean_string(x).lower()

        if type(x) == list:
            x = [cleaning_function(el) for el in x]
        if type(x) in [str]:
            x = cleaning_function(x)
        if verbose:
            print("After cleaning", type(x), x)
        return x

    def extract(self, query, choices=None, limit=5, verbose=False):
        """
        :param choices should be a list of texts
        :param query: TODO add an input type checker
        :param processor: TODO : add a cleaning process
        :param scorer: TODO : Add other distances
        :return:
        """
        # print("---------------------------\n"
        # Get rid of this case
        if choices == []:
            return []

        if choices:
            choices = list(set(choices))

            # Clean the choices corpus
            initial_choices = choices
            if self.use_cleaner:
                choices = self.cleaner(choices)
            if self.preprocess_func:
                choices = [self.preprocess_func(elk) for elk in choices]
            choices_corpus = choices

            corpus_tf_idf = self.tfidf.transform(choices_corpus)
        else:
            initial_choices = self.initial_choices_corpus
            choices_corpus = self.initial_choices_corpus
            corpus_tf_idf = self.initial_corpus_tf_idf
            # print("Defaulting"

        if self.use_cleaner:
            query = self.cleaner(query)
        if self.preprocess_func:
            query = self.preprocess_func(query)

        # building fuzzy query
        new_query = []
        # print("Vocabulary", vocabulary)
        for q in query.split():
            if q in self.vocabulary:
                new_query.append(q)
            else:
                fset_get = self.fset_vocabulary.get(q)
                if fset_get:
                    tmp_score, new_q = fset_get[0]
                    if verbose:
                        print("Modified", q, new_q, tmp_score)
                    if tmp_score >= 0.80:
                        new_query.append(new_q)
        query = " ".join(new_query)
        if verbose:
            print("NEW QUERY", query)
        x = self.tfidf.transform([query])

        cosine_similarities = linear_kernel(x, corpus_tf_idf).flatten()
        related_docs_indices = cosine_similarities.argsort().flatten()
        if choices:
            result = [(choices_corpus[k], cosine_similarities[k].flatten()[0]) for k in related_docs_indices if choices_corpus[k]]
        else:
            result = [(choices_corpus[k], cosine_similarities[k].flatten()[0]) for k in related_docs_indices]
        result.sort(key=lambda tup: tup[1], reverse=True)  # sorts in place
        # print("Query", query, "\nChoices", choices, "\nResult", result
        result = [(initial_choices[choices_corpus.index(k[0])], k[1]) for k in result]
        # print("Query", query, "\nChoices", choices, "\nResult", result
        if limit:
            return result[0:limit]
        return result

    def export_vocabulary(self, vocabulary_csv_destination, choices_corpus=None):
        if not choices_corpus:
            choices_corpus = self.initial_choices_corpus

        if self.use_cleaner:
            choices_corpus = [clean_string(x).lower() for x in choices_corpus]

        cnt_vec = CountVectorizer(ngram_range=self.ngram_range)
        transformed_data = cnt_vec.fit_transform(choices_corpus)
        l = [{'word':k, 'freq':v} for k, v in zip(cnt_vec.get_feature_names(), np.ravel(transformed_data.sum(axis=0)))]
        df = pd.DataFrame(l)
        df = df[['word', 'freq']]
        df.sort_values('freq', ascending=False, inplace=True)
        df.to_csv(vocabulary_csv_destination, encoding='utf-8', index=False, sep=";", doublequote=True, quoting=csv.QUOTE_ALL)
        print('The vocabulary was exported at : ', vocabulary_csv_destination)


japtranslator = JapTranslator()
pattern_japanese_chinese_caracters = regex.compile(r'([\p{IsHan}\p{IsBopo}\p{IsHira}\p{IsKatakana}【】]+)', re.UNICODE)


def pdct_matching_function(row, ref, tfmatcher, pdcts_other=None, verbose=False, countrywise=True, return_res_list=False, thresh=0.375):
    if verbose:
        print('\n\nMatching : ', row['pdct_name_on_eretailer'])

    pdct_name_on_eretailer = str(row["pdct_name_on_eretailer"])

    pdct_name_on_eretailer_has_japanese = False
    if countrywise and row['country'] == 'JP' and bool(pattern_japanese_chinese_caracters.search(pdct_name_on_eretailer)):
        pdct_name_on_eretailer = japtranslator.translate(pdct_name_on_eretailer, verbose=False)
        thresh = 0.28
        pdct_name_on_eretailer_has_japanese = True

    # Post year cleaning
    pdct_name_on_eretailer = pdct_name_on_eretailer.replace('2016', '')
    pdct_name_on_eretailer = pdct_name_on_eretailer.replace('2017', '')
    pdct_name_on_eretailer = pdct_name_on_eretailer.replace('2018', '')
    pdct_name_on_eretailer = pdct_name_on_eretailer.replace('2019', '')

    if verbose:
        print("Initial pdct_name_on_eretailer ", pdct_name_on_eretailer)

    rf = pd.DataFrame(ref.copy(deep=True))
    if isinstance(pdcts_other, pd.DataFrame):
        rf = rf.append(pdcts_other)
    rf_brnd = rf[(rf['brnd'] == row['brnd'])]
    rf = rf[(rf['brnd'] == row['brnd'])]

    if countrywise:
        rf = rf[((rf['country'] == row['country']) & (rf['segment'] == row['segment']))]
    else:
        rf = rf.copy()

    if "volume_in_ml" in row:
        rf = rf[(0.9 * row["volume_in_ml"] < rf["volume_in_ml"]) & (rf["volume_in_ml"] < 1.1 * row["volume_in_ml"])]
        if verbose:
            print("Candidates size after volume_in_ml selection", rf.shape[0], list(rf['pdct_name'].unique()))

    if pdct_name_on_eretailer_has_japanese:
        row["dtctd_rose"] = any(k in pdct_name_on_eretailer.lower() for k in rose_kws)

    brand_has_rose = ref[(ref['brnd'] == row["brnd"]) & (ref['rose'])].shape[0] > 0

    if "dtctd_rose" in list(row.index) and row['dtctd_rose'] == row["dtctd_rose"] and (brand_has_rose or not pdct_name_on_eretailer_has_japanese):
        rf = rf[rf['rose'] == row['dtctd_rose']]
        rf_brnd = rf_brnd[rf_brnd['rose'] == row['dtctd_rose']]
        if verbose:
            print("Candidates size after rose selection", rf.shape[0], list(rf['pdct_name'].unique()))

    brand_has_vintages = ref[(ref['brnd'] == row["brnd"]) & (ref['vintage'] != -1) &
                             ~(ref['ctg'].isin(['Still Wine', 'Vodka']))].shape[0] > 0 and row["brnd"] != 'Glenmorangie'
    if pdct_name_on_eretailer_has_japanese:
        row["dtctd_vintage"] = int(extract_year(pdct_name_on_eretailer))

    if "dtctd_vintage" in list(row.index) and row['dtctd_vintage'] == row["dtctd_vintage"] and brand_has_vintages:
        rf = rf[rf['vintage'] == row["dtctd_vintage"]]
        if verbose:
            print("Candidates size after vintage selection", rf.shape[0], """row['dtctd_vintage']""", row['dtctd_vintage'], )

    if verbose:
        print("After segmentation", rf.shape)

    # Clean years
    year_str = find_year_string(pdct_name_on_eretailer)
    vintage_year = extract_year(year_str)
    if year_str and vintage_year:
        pdct_name_on_eretailer = pdct_name_on_eretailer.replace(str(year_str), str(vintage_year))

    if verbose:
        print("Lower pdct_name_on_eretailer, correct year :", pdct_name_on_eretailer)

    # Standard cleaning
    pdct_name_on_eretailer = pdct_name_on_eretailer.replace("'", "").replace('Ã©', 'e').replace('Â', '').replace('Ã«', 'e')
    pdct_name_on_eretailer = pdct_name_on_eretailer.replace('"', "").replace('`', "")
    pdct_name_on_eretailer = pdct_name_on_eretailer.lower()

    # Custom cleaning
    pdct_name_on_eretailer = pdct_name_on_eretailer.replace('champagner', '').replace('  ', ' ')
    pdct_name_on_eretailer = pdct_name_on_eretailer.replace('champagne', '').replace('  ', ' ')
    pdct_name_on_eretailer = pdct_name_on_eretailer.replace('extra brut', 'brut')
    pdct_name_on_eretailer = pdct_name_on_eretailer.replace('carte jaune', 'yellow label')
    if not any([x in pdct_name_on_eretailer for x in ['rich ', 'grande dame', "demi-sec", 'demi ', 'arrow', 'along', 'message', 'call']]):
        pdct_name_on_eretailer = pdct_name_on_eretailer.replace('veuve clicquot ponsardin brut', 'veuve clicquot yellow label')
        pdct_name_on_eretailer = pdct_name_on_eretailer.replace('veuve clicquot ponsardin champagne brut', 'veuve clicquot yellow label')
        pdct_name_on_eretailer = pdct_name_on_eretailer.replace('veuve clicquot ponsardin vintage', 'veuve clicquot yellow label')
        pdct_name_on_eretailer = pdct_name_on_eretailer.replace('veuve clicquot ponsardin champagne', 'veuve clicquot yellow label')
        pdct_name_on_eretailer = pdct_name_on_eretailer.replace('veuve clicquot ponsardin champagne', 'veuve clicquot yellow label')
        pdct_name_on_eretailer = 'veuve clicquot yellow label' if pdct_name_on_eretailer == 'veuve clicquot ponsardin' else pdct_name_on_eretailer
        pdct_name_on_eretailer = pdct_name_on_eretailer.replace('veuve clicquot champagne brut', 'veuve clicquot yellow label')
        pdct_name_on_eretailer = pdct_name_on_eretailer.replace('veuve clicquot - brut', 'veuve clicquot yellow label')
        pdct_name_on_eretailer = pdct_name_on_eretailer.replace('brut veuve clicquot', 'veuve clicquot yellow label')
        pdct_name_on_eretailer = pdct_name_on_eretailer.replace('quot brut', 'quot yellow label brut')
    pdct_name_on_eretailer = pdct_name_on_eretailer.replace('10 yo', 'ten years')
    pdct_name_on_eretailer = pdct_name_on_eretailer.replace('10 y.o.', 'ten years')
    pdct_name_on_eretailer = pdct_name_on_eretailer.replace('10y.o.', 'ten years')
    pdct_name_on_eretailer = pdct_name_on_eretailer.replace('10yo', 'ten years')
    pdct_name_on_eretailer = pdct_name_on_eretailer.replace('10yr', 'ten years')
    pdct_name_on_eretailer = pdct_name_on_eretailer.replace('10 yr.', 'ten years')
    pdct_name_on_eretailer = pdct_name_on_eretailer.replace('10 yr', 'ten years')
    pdct_name_on_eretailer = pdct_name_on_eretailer.replace('10y ', 'ten years')
    pdct_name_on_eretailer = pdct_name_on_eretailer.replace('ten year ', 'ten years ')
    pdct_name_on_eretailer = pdct_name_on_eretailer.replace('10 year', 'ten years')
    pdct_name_on_eretailer = pdct_name_on_eretailer.replace('10 ans', 'ten years')
    pdct_name_on_eretailer = pdct_name_on_eretailer.replace('10ans', 'ten years')
    pdct_name_on_eretailer = pdct_name_on_eretailer.replace('10 jahre', 'ten years')
    pdct_name_on_eretailer = pdct_name_on_eretailer.replace('10jahre', 'ten years')
    pdct_name_on_eretailer = pdct_name_on_eretailer.replace('10 anos', 'ten years')
    pdct_name_on_eretailer = pdct_name_on_eretailer.replace('10anos', 'ten years')
    pdct_name_on_eretailer = pdct_name_on_eretailer.replace('10 años', 'ten years')
    pdct_name_on_eretailer = pdct_name_on_eretailer.replace('10años', 'ten years')
    pdct_name_on_eretailer = pdct_name_on_eretailer.replace('ardbeg 10 ', 'ardbeg ten years ')
    pdct_name_on_eretailer = pdct_name_on_eretailer.replace('don ruinard', 'dom ruinart')
    pdct_name_on_eretailer = pdct_name_on_eretailer.replace('trondes', 'torrontes')
    pdct_name_on_eretailer = pdct_name_on_eretailer.replace('cricot', 'clicquot')
    pdct_name_on_eretailer = pdct_name_on_eretailer.replace('domisek', 'demi sec')
    pdct_name_on_eretailer = pdct_name_on_eretailer.replace('dumisek', 'demi sec')
    pdct_name_on_eretailer = pdct_name_on_eretailer.replace('dummisek', 'demi sec')
    pdct_name_on_eretailer = pdct_name_on_eretailer.replace('dommisek', 'demi sec')
    pdct_name_on_eretailer = pdct_name_on_eretailer.replace('domisec', 'demi sec')
    pdct_name_on_eretailer = pdct_name_on_eretailer.replace('dumisec', 'demi sec')
    pdct_name_on_eretailer = pdct_name_on_eretailer.replace('dummisec', 'demi sec')
    pdct_name_on_eretailer = pdct_name_on_eretailer.replace('dommisec', 'demi sec')

    pdct_name_on_eretailer = pdct_name_on_eretailer.replace('very superior old pale', 'v.s.o.p')
    pdct_name_on_eretailer = pdct_name_on_eretailer.replace('very special old pale', 'v.s.o.p')
    pdct_name_on_eretailer = pdct_name_on_eretailer.replace('very special old product', 'v.s.o.p')
    pdct_name_on_eretailer = pdct_name_on_eretailer.replace('very special', 'v.s.')
    pdct_name_on_eretailer = pdct_name_on_eretailer.replace('pamplemousse rose', 'pink grapefruit')
    pdct_name_on_eretailer = pdct_name_on_eretailer.replace(' - ', ' ').replace('- ', ' ').replace(' -', ' ').replace('-', ' ')
    pdct_name_on_eretailer = pdct_name_on_eretailer.replace('18yr', '18 years').replace('18 yr.', '18 years').replace('18 yr', '18 years')
    pdct_name_on_eretailer = pdct_name_on_eretailer.replace('25yr', '25 years').replace('25 yr.', '25 years').replace('25 yr', '25 years')
    pdct_name_on_eretailer = pdct_name_on_eretailer.replace('glenmorangie pride', 'glenmorangie pride 1978')
    pdct_name_on_eretailer = pdct_name_on_eretailer.replace('glenmorangie 34', 'glenmorangie pride 1978')
    pdct_name_on_eretailer = pdct_name_on_eretailer.replace('glenmorangie ten years old ', 'glenmorangie the original ')
    pdct_name_on_eretailer = pdct_name_on_eretailer.replace('glenmorangie ten years ', 'glenmorangie the original ')
    pdct_name_on_eretailer = pdct_name_on_eretailer.replace('glenmorangie ten year ', 'glenmorangie the original ')
    pdct_name_on_eretailer = pdct_name_on_eretailer.replace('glenmorangie ten yrs. ', 'glenmorangie the original ')
    pdct_name_on_eretailer = pdct_name_on_eretailer.replace('glenmorangie ten yrs ', 'glenmorangie the original ')
    pdct_name_on_eretailer = pdct_name_on_eretailer.replace('glenmorangie ten yr. ', 'glenmorangie the original ')
    pdct_name_on_eretailer = pdct_name_on_eretailer.replace('glenmorangie ten yr ', 'glenmorangie the original ')
    pdct_name_on_eretailer = pdct_name_on_eretailer.replace(' la santa', ' lasanta')
    pdct_name_on_eretailer = pdct_name_on_eretailer.replace('krug brut champagne', 'krug grande cuvée')
    pdct_name_on_eretailer = pdct_name_on_eretailer.replace(' d or', " dor")
    pdct_name_on_eretailer = pdct_name_on_eretailer.replace(" d'or", " dor")
    pdct_name_on_eretailer = pdct_name_on_eretailer.replace('minkoff ', 'minkoff eoy ')
    if "glenmorangie" in pdct_name_on_eretailer and ' ten y' in pdct_name_on_eretailer:
        pdct_name_on_eretailer = pdct_name_on_eretailer.replace('glenmorangie', 'glenmorangie the original ')
    if "rignon" in pdct_name_on_eretailer and not "p2" in pdct_name_on_eretailer:
        pdct_name_on_eretailer = pdct_name_on_eretailer.replace('plénitude', 'plénitude p2')
    if "hennessy" in pdct_name_on_eretailer:
        pdct_name_on_eretailer = pdct_name_on_eretailer.replace(' de ', ' ')

    pdct_name_on_eretailer = pdct_name_on_eretailer.replace('blanc de noir ', 'blanc de noirs ')
    pdct_name_on_eretailer = pdct_name_on_eretailer.replace('', '')

    # Japanese replaces
    pdct_name_on_eretailer = pdct_name_on_eretailer.replace('grancuvee', ' grande cuvée ')
    pdct_name_on_eretailer = pdct_name_on_eretailer.replace('grancuve', ' grande cuvée ')

    if "very special" in pdct_name_on_eretailer:
        pdct_name_on_eretailer = pdct_name_on_eretailer.replace(' cognac', '')
        pdct_name_on_eretailer = pdct_name_on_eretailer.replace(' de', '')

    if not 'dom' in pdct_name_on_eretailer.lower():
        pdct_name_on_eretailer = pdct_name_on_eretailer.replace('ruinart brut', 'r de ruinart')
        pdct_name_on_eretailer = pdct_name_on_eretailer.replace('ruinart champagne brut', 'r de ruinart')

    if "ruinart" in pdct_name_on_eretailer and 'blanc de blancs' in pdct_name_on_eretailer and '2004' in pdct_name_on_eretailer:
        pdct_name_on_eretailer = pdct_name_on_eretailer.replace(' blanc de blancs', '')

    # German years
    for k in range(1950, 2017):
        pdct_name_on_eretailer = pdct_name_on_eretailer.replace(str(k) + 'er', str(k))

    if verbose:
        print("pdct_name_on_eretailer after cleaning : ", pdct_name_on_eretailer)

    pdcts_name_candidates = list(set(rf_brnd['pdct_name']))
    if verbose:
        print("pdcts_name_candidates", pdcts_name_candidates)

    if pdcts_name_candidates:
        res = tfmatcher.extract(pdct_name_on_eretailer, choices=pdcts_name_candidates, verbose=verbose)

        if verbose:
            print("TFIDF extract: ", res)
        res_max = [k for k in res if k[1] == max(res, key=itemgetter(1))[1]]

        if pdct_name_on_eretailer_has_japanese:
            if verbose:
                for x in res_max:
                    print(x, row["dtctd_vintage"], extract_year(x[0]), type(row["dtctd_vintage"]), type(extract_year(x)))
            res_max = [x for x in res_max if row["dtctd_vintage"] == int(extract_year(x[0]))]

        if return_res_list:
            return res_max

        # Forbidden words:
        forbidden_words = ['leinwand', "hamper ", ' hamper', ' poster', 'poster', 'chocolates ', ' chocolates',
                           'truffle ', ' truffle', 'birthday cake', ' cake', 'candle', 'poplin', ' sheet ', ' bed ', ' cover '
                           ' kimono', 'towel', 'rosenthal']
        if any(x in pdct_name_on_eretailer.lower() for x in forbidden_words):
            print('Forbidden word detected in : ', pdct_name_on_eretailer)
            return {'dtctd_pdct_name': None, 'dtctd_pdct_score': 0}

        if res_max:
            if res_max[0][1] > thresh:
                if res_max[0][0] in rf['pdct_name'].unique():
                    if verbose:
                        print("Score above threshold : ", res_max[0][1], "thresh :", thresh)
                    return {'dtctd_pdct_name': res_max[0][0], 'dtctd_pdct_score': res_max[0][1]}
                else:
                    if verbose:
                        print("Closer name :", res_max[0][0], 'not in', rf['pdct_name'].unique())
                return {'dtctd_pdct_name': None, 'dtctd_pdct_score': -1}
            else:
                if verbose:
                    print("Score below threshold : ", res_max[0][1], "thresh :", thresh)
                return {'dtctd_pdct_name': None, 'dtctd_pdct_score': res_max[0][1]}
        else:
            if verbose:
                print("2 - No candidates for : ", pdct_name_on_eretailer)
    if verbose:
        print("No candidates for : ", pdct_name_on_eretailer)
    return {'dtctd_pdct_name': None, 'dtctd_pdct_score': 0}


if __name__ == '__main__':
    if False:
        import time, itertools
        print("TF-IDF testing")
        ngram_range = (1, 2)

        arbitrarily_large_corpus = ["".join(k) for k in itertools.combinations('abcdefghijklmnopqrstuvwzyz', 6)]
        # print(arbitrarily_large_corpus
        print("len(arbitrarily_large_corpus)", len(arbitrarily_large_corpus))
        t = time.time()
        tfidf = TfidfVectorizer(analyzer='word', sublinear_tf=True,  # strip_accents='ascii',
                                     lowercase=True, ngram_range=ngram_range).fit(arbitrarily_large_corpus)
        print("Time for arbitrarily_large_corpus tfidf init", time.time() - t)
        t = time.time()
        tfidf.transform(arbitrarily_large_corpus)
        print("Time for arbitrarily_large_corpus tfidf transform", time.time() - t)

    if True:
        testing_list = ['Moët Chandon demi-sec',
                        'Moët & Chandon demi-sec',
                        'Moët & Chandon rich', 'Moët & Chandon rosé',
                        'Moët Chandon rich rosé',
                        'Krug rich 2006 Impérial', 'Moët & Chandon Impérial Brut Rosé',
                        "Veuve Clicquot Vintage 2008 150cl",
                        "Dom Perignon Blanc",
                        "Dom Perignon Rose",
                        "Glenmorangie Sco Bacalta",
                        "Numanthia Termes 2011",
                        "Steele Chardonnay California",
                        ]
        testing_list = ['Dom Ruinart', 'R de Ruinart', 'Ruinart Blanc de Blancs']

        tfmatcher = TFIDFmatcher(testing_list, ngram_range=(1, 1))
        tfmatcher.export_vocabulary('/tmp/small_voc.csv')
        l = ['Moët & Chandon demi-sec', 'Moët Chandon rosé', 'Moët & Chandon Impérial', 'Moët & Chandon Rich rosé']
        l = ['R de Ruinart']

        choices = testing_list

        for m in l:
            print("--------------------------------------------------------------\n\n")
            print(m, tfmatcher.extract(m, choices))

    if True:
        import numpy as np
        import time
        from ers import pdcts

        tfmatcher = TFIDFmatcher(testing_list, ngram_range=(1, 1))
        l = ['Moët & Chandon demi-sec', 'Moët Chandon rosé', 'Moët & Chandon Impérial', 'Moët & Chandon Rich rosé']

        calculation_durations = []
        for k in l:
            t = time.time()
            print('\n\n------------\n')
            print(k, tfmatcher.extract(m, list(pdcts['pdct_name'].unique())))
            calculation_durations.append(time.time() - t)
        print("Mean time for pdct computation", np.mean(calculation_durations))

