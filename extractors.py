import re
import string
import traceback

import unidecode
from lxml import etree

# Regex loading
regex_volume = re.compile(r'(?<!\w)\d{1,2}(\.|\,)?\d*\ ?(Litre|Liter|litre|LITRE|LTR|ltr|cl|CL|Cl|ml|ML|Ml|mL|lt\.| lt|lt|l|LI|L)(?:\b|\))')
regex_volume_nb = re.compile(r'\d{1,2} ?(\.|,)? ?\d*', re.IGNORECASE)
regex_volume_unit = re.compile(r'(Litre|Liter|litre|LITRE|LTR|ltr|cl|CL|Cl|ml|ML|Ml|mL|lt\.| lt|l|LI|L)', re.IGNORECASE)
regex_price = re.compile(r'(£|\$|EUR|€)?\s?(\d*(| )?(|\.|,)\d+)?(£|\$|EUR|€)?', re.IGNORECASE)
regex_number = re.compile(r'\d+([\d,]?\d)*(\.\d+)?', re.IGNORECASE)
year_regex = r'\b(19|20)\d{2}\b'
two_digits_year = r'(?: |\')(\d{2})( |$|\n|\t|\r)(?!y|Y)'
two_digits_year_narrow = r'(\'\d{2})'
special_years = r'(?<=(RO|ro|GV|gv|WH|wh))\d{2}'


def clean_string(x):
    regex_punctuation = re.compile('[%s]' % re.escape(string.punctuation))
    x = regex_punctuation.sub('', x)
    return unidecode.unidecode(' '.join([w for w in x.split() if w])).replace(' and ', '&')


# Volume extraction
def find_volume(text):
    s = re.search(regex_volume, text)
    if s:
        return s.group()
    return ''


def calc_volume_in_ml(text):
    s = find_volume(text).replace(',', '.')
    if type(s) in [str]:
        try:
            search = re.search(regex_volume_nb, s)
            if search:
                capa_btle = float(search.group())
                capa_unit = re.search(regex_volume_unit, s).group()
                coef = (capa_unit.lower() in ['ltr', 'l', 'litre', 'liter', ' lt']) * 1000 + \
                    (capa_unit.lower() == 'cl') * 10 + (capa_unit.lower() == 'ml') * 1
                return int(capa_btle * coef)
            else:
                desc = clean_string(text).lower()
                title = clean_string(text).lower()
                d = {
                    15000: ['nebuchadnezzar', 'nabuchodonosor'],
                    9000: ['salmanazar'],
                    6000: ['mathusalem', 'methuselah', 'mathuselah'],
                    3000: ['jeroboam', 'jéroboam', ],
                    1500: ['magnum'],
                    375: ['demi-bouteille', 'demi bouteille', 'half bottle', 'half-bottle'],
                    10: ['miniature'],
                }
                for k in d:
                    if any((i in desc for i in d[k])):
                        return k
                    if any((i in title for i in d[k])):
                        return k
                if any((i in desc for i in ['bottle ', ' bottle'])):
                    return 750
                if any((i in title for i in ['bottle ', ' bottle'])):
                    return 750
        except Exception:
            print('\n\n', text, traceback.format_exc())
    return 750


def find_year_string(s):
    if s and type(s) == str:
        match = re.search(year_regex, s)
        if match:
            return match.group(0)
        else:
            match = re.search(two_digits_year_narrow, s)
            if match:
                return match.group(0)


# Extracting vintage year
def extract_year(s):
    if s and type(s) == str:
        match = re.search(year_regex, s)
        if match:
            return match.group(0)
        else:
            match = re.search(two_digits_year, s)
            if match:
                tmp = int(match.group(0).replace("'", ""))
                if 1 <= tmp <= 17 and tmp not in [10, 12]:
                    return str(2000 + tmp)
                elif 50 < tmp <= 99 and tmp not in [70, 75]:
                    return str(1900 + tmp)
            else:
                match = re.search(special_years, s)
                if match:
                    tmp = int(match.group(0))
                    if 1 <= tmp <= 17:
                        return str(2000 + tmp)
                    elif 50 < tmp <= 99 and tmp not in [70, 75]:
                        return str(1900 + tmp)
    return -1


# Finding price
def find_price_regex(text):
    text = unidecode.unidecode(' '.join([w for w in text.split() if w])).lower()
    if text and type(text) in [str]:
        pattern = re.compile('[a-zA-Z_]+')
        text = pattern.sub('', text).replace(" ", "")
        price_found = re.search(regex_price, text)
        if price_found:
            return price_found.group()
    return ''


def find_price_currency(text, default_country):
    d_currency = {'$': ['$', 'DOL'], '€': ['€', 'EUR'], '£': ['£', 'GBP']}
    d_currency_country = {'UK': '£', 'FR': '€', 'USA': '$', 'AUS': '$', 'DE': '€', 'CH': 'CHF', 'ES': '€'}
    result = {'currency': d_currency_country[default_country], 'price': None}
    if type(text) in [float, int]:
        result['price'] = text
        return result

    if type(text) in [list]:
        text = " ".join(text)

    if type(text) in [str, etree._ElementUnicodeResult, etree._ElementStringResult]:
        text = unidecode.unidecode(' '.join([w for w in text.split() if w])).lower()
        if text:
            for k in d_currency:
                for v in d_currency[k]:
                    if v in text:
                        result['currency'] = k
                        if v == "$":
                            regex_curr = '\$'
                        else:
                            regex_curr = v
                        mo = re.search("(.{0,12})" + regex_curr + "(.{0,12})", text)
                        text = mo.group()
                        break
            # print "final text", text
            pattern = re.compile('[a-zA-Z_]+')
            text = pattern.sub('', text).replace(" ", "")
            value_found = re.search(regex_number, text)
            if value_found:
                if result['currency'] == '€':
                    value_found = value_found.group().replace(',', '.')
                    result['price'] = float(value_found)
                else:
                    value_found = value_found.group().replace(',', '')
                    result['price'] = float(value_found)
    elif type(text) in [int, float]:
        result['price'] = text
    return result


if __name__ == '__main__':
    print(find_volume('Cognacs, France / Poitou-charentes, 70cl, Ref: 5733'))
    print(calc_volume_in_ml('Cognacs, France / Poitou-charentes, 70cl, Ref: 5733'))
    l = [' $2,875 ', 'Reg. $112.69', ' 20, 95 € ', '$15.97 /bottle', ' $5.49/ea ($0.92/ct)', ' Sale: $159.09 ', '1 452 €',
         ' Sale: $159.09 ', '1 115 €', ' $2,195.00 ', ' £219.95',  '[ £12.95 ,  £4.95 ]', u"$69.99",
         '15, 90 EUR', '15,90 EUR',
         'Number(19.95)'
         u"Ros\xe9 Trento DOC 0,375L in GP f\xfcr 15,90 EUR kaufen. Weingut Ferrari Spumante: Ros\xe9 Trento DOC 0,375L in GP bei Belvini.de",
         # '41,€5 041.€50',

         ]
    for t in l:
        print(t, find_price_currency(t, 'FR'))

    print(find_price_currency('Glenmorangie Grand Vintage Malt 1990 70cl£495.00', 'UK'))
    print(calc_volume_in_ml('1500mL'))
    print(calc_volume_in_ml('750.0ml Bottle'))
    print(calc_volume_in_ml('Black & White Whisky 0,7 l'))
    print(calc_volume_in_ml('Boisson brûle graisse thé vert guarana Juvamine'))
    print(calc_volume_in_ml('Pisco Cascajal Puro Quebranta, 0,5l'))
    print(calc_volume_in_ml('Johnnie Walker Black Label 5cl'))
    print('vc', calc_volume_in_ml('Veuve Clicquot - Champagne Brut Rosé Demi-Bouteille 37.5Cl'))
    print(calc_volume_in_ml('Moet Chandon Nectar Imperial Rose Half Bottle NV'))
    print("t", calc_volume_in_ml('Distillerie Beccaris - Linea Acquavite di Frutta Acquavite di Abricots 0,70 lt.'))
    print("t", calc_volume_in_ml('BELVEDERE VODKA 007 SERIES COLLECTORS EDITION POLAND 1.75LI'))
    print(extract_year("Moet & Chandon Brut Grand Vintage '08"))
    print(find_year_string("Moet & Chandon Brut Grand Vintage '08"))
