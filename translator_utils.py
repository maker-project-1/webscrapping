import json

from googletrans import Translator

from ers import JAPANESE_TRANSLATION_CACHE_JSON


class JapTranslator:
    def __init__(self):
        try:
            with open(JAPANESE_TRANSLATION_CACHE_JSON, 'rb') as f:
                self.d = json.load(f)
        except:
            with open(JAPANESE_TRANSLATION_CACHE_JSON, 'wb') as f:
                json.dumps({})
            self.d = {}
        self.translator = Translator()

    def translate(self, text, dest='en', src='auto', verbose=False):
        if not text:
            return None
        elif text in self.d:
            if verbose:
                print('From cache', text, self.d[text])
            return self.d[text]
        else:
            if verbose:
                print("Looking for: ", text)
            translated = self.translator.translate(text, dest=dest, src=src)
            # print(translated)
            trad = translated.text
            self.d[text] = trad
            with open(JAPANESE_TRANSLATION_CACHE_JSON, 'w') as f:
                json.dump(self.d, f)
            return trad


if __name__ == '__main__':
    japtranslator = JapTranslator()
    japtranslator.translate('アクセスが集中し、ページを閲しにくい状態になっております', verbose=True)


# from googleapiclient.discovery import build
#
# # service = build('translate', 'v2', developerKey='AIzaSyBZvP5tnYgFpax6NOR-WEDcMXCS1Y7EbIg')
# # print(service.translations().list(
# #       source='en',
# #       target='fr',
# #       q=['flower', 'car']).execute())
