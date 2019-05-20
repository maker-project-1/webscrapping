import random
import time

import ahocorasick

from ers import brands

ljpbrands = list(brands.loc[brands.brnd_jp.notnull(), 'brnd_jp_clean'])
random.shuffle(ljpbrands)

candidate = 'グレンマレイ8年 700 ml'
candidate = 'テラザス レゼルヴァ トロンテス / テラザス(TERRAZAS RESERVA TORRONTES)'
candidate = 'グレンモーレンジィ ラサンタ 12年(Glenmorangie Lasanta 12Years)'


t = time.time()
br = None
for br in ljpbrands:
    if br in candidate:
       break
print(time.time() - t, br)


A = ahocorasick.Automaton()
for idx, br in enumerate(ljpbrands):
    A.add_word(br, (idx, br))

A.make_automaton()

t = time.time()
for item in A.iter(candidate):
    pass
print(time.time() - t, item)
