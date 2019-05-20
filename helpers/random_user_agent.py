# author Anka Yip <ankayip@gmail.com>
# credit Python Random User-Agent Generator <http://pastebin.com/zYPWHnc6#>
import random


def randomua():
    platform = get_platform()
    os = get_os(platform)
    browser = get_browser()

    if browser == 'Chrome':
        webkit = str(random.randint(500, 599))
        version = "%s.0%s.%s" % (str(random.randint(0, 24)), str(
            random.randint(0, 1500)), str(random.randint(0, 999)))
        return "Mozilla/5.0 (%s) AppleWebKit/%s.0 (KHTML, live Gecko) Chrome/%s Safari/%s" % (os, webkit, version, webkit)
    elif browser == 'Firefox':
        year = str(random.randint(2000, 2015))
        month = str(random.randint(1, 12)).zfill(2)
        day = str(random.randint(1, 28)).zfill(2)
        gecko = "%s%s%s" % (year, month, day)
        version = "%s.0" % (str(random.randint(1, 15)))
        return "Mozillia/5.0 (%s; rv:%s) Gecko/%s Firefox/%s" % (os, version, gecko, version)
    elif browser == 'IE':
        version = "%s.0" % (str(random.randint(1, 10)))
        engine = "%s.0" % (str(random.randint(1, 5)))
        option = random.choice([True, False])
        if option:
            token = "%s;" % (random.choice(
                ['.NET CLR', 'SV1', 'Tablet PC', 'Win64; IA64', 'Win64; x64', 'WOW64']))
        else:
            token = ''
        return "Mozilla/5.0 (compatible; MSIE %s; %s; %sTrident/%s)" % (version, os, token, engine)


def get_os(platform):
    if platform == 'Machintosh':
        return random.choice(['68K', 'PPC'])
    elif platform == 'Windows':
        return random.choice(['Win3.11', 'WinNT3.51', 'WinNT4.0', 'Windows NT 5.0', 'Windows NT 5.1', 'Windows NT 5.2', 'Windows NT 6.0', 'Windows NT 6.1', 'Windows NT 6.2', 'Win95', 'Win98', 'Win 9x 4.90', 'WindowsCE'])
    elif platform == 'X11':
        return random.choice(['Linux i686', 'Linux x86_64'])


def get_browser():
    return random.choice(['Chrome', 'Firefox', 'IE'])


def get_platform():
    return random.choice(['Machintosh', 'Windows', 'X11'])


if __name__ == '__main__':
    while 1:
        print(randomua())
