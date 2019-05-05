# -*- coding: utf-8 -*
import time
import traceback
from time import sleep

import selenium.webdriver.support.ui as ui
from lxml import etree
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import Firefox, FirefoxProfile
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options

parser = etree.HTMLParser()


class CustomDriver:
    def __init__(self, headless=False, download_images=False, proxy_host=None, proxy_port=None, timeout=10, firefox=False,
                 user_agent=None):
        self.headless = headless
        self.driver = None
        self.proxy_host = proxy_host
        self.proxy_port = int(proxy_port) if proxy_port else None
        self.timeout = timeout
        self.download_images = download_images
        if not user_agent:
            self.user_agent = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:60.0) Gecko/20100101 Firefox/60.0'
        else:
            self.user_agent = user_agent

        # Lazy-loading params
        self.firefox = firefox
        self.driver_exists = False

    def create_driver_if_needed(self):
        if not self.driver_exists:
            if self.firefox:
                self.init_driver_firefox()
            else:
                self.init_driver_chrome()
            self.driver_exists = True

    def init_driver_chrome(self, total_width=1600, total_height=900):
        print('Initing Chrome Driver')
        chrome_options = Options()
        chrome_options.add_argument("user-agent=" + self.user_agent)
        # username = os.getenv("USERNAME")
        userProfile = "C:\\Users\\" + 'renaud' + "\\AppData\\Local\\Google\\Chrome\\User Data\\Default"
        options = webdriver.ChromeOptions()
        options.add_argument("user-data-dir={}".format(userProfile))
        options.add_experimental_option("excludeSwitches",
                                        ["ignore-certificate-errors", "safebrowsing-disable-download-protection",
                                         "safebrowsing-disable-auto-update", "disable-client-side-phishing-detection"])
        if self.headless:
            chrome_options.add_argument("--headless")
            # chrome_options.binary_location = '/usr/bin/google-chrome'

        if self.proxy_host and self.proxy_port:
            print("Using proxy", self.proxy_host + ':' + str(self.proxy_port))
            chrome_options.add_argument('--proxy-server=https://%s' % self.proxy_host + ':' + str(self.proxy_port))

        chrome_options.add_argument("--window-size={total_width},{total_height}".format(total_width=total_width, total_height=total_height))
        chrome_options.add_argument("--disable-extensions")
        # if not self.download_images:
        #     prefs = {"profile.managed_default_content_settings.images": 2}
        #     chrome_options.add_experimental_option("prefs", prefs)
        self.driver = webdriver.Chrome(executable_path="/home/pierre/Documents/chromedriver", chrome_options=chrome_options)

    def init_driver_firefox(self, total_width=1600, total_height=900):
        options = Options()
        fp = FirefoxProfile()

        if self.headless:
            options.add_argument("--headless")

        if not self.download_images:
            fp.set_preference('permissions.default.image', 2)
            fp.set_preference('dom.ipc.plugins.enabled.libflashplayer.so', 'false')

        if self.proxy_host and self.proxy_port:
            fp = webdriver.FirefoxProfile()
            # network.proxy.type:  Direct = 0, Manual = 1, PAC = 2, AUTODETECT = 4, SYSTEM = 5
            fp.set_preference("network.proxy.type", 1)
            fp.set_preference("network.proxy.http", self.proxy_host)
            fp.set_preference("network.proxy.http_port", int(self.proxy_port))  # WARNING ! proxy_port should be int
            fp.set_preference("general.useragent.override", self.user_agent)
            fp.update_preferences()
        elif self.proxy_port or self.proxy_host:
            raise(Exception('If you want to use a proxy, please provide proxy_host and proxy_port'))
        self.driver = Firefox(firefox_options=options, firefox_profile=fp)
        self.driver.set_window_size(total_width, total_height)

    def __del__(self):
        # self.quit()
        pass

    def quit(self):
        try:
            self.driver.quit()
        except Exception:
            pass

    def respawn(self, lazyload=True):
        self.quit()
        if not lazyload:
            self.create_driver_if_needed()
            self.driver_exists = False
        else:
            self.driver_exists = False

    def waitclick(self, xpath, ctrl=False, timeout=None, silent=False):
        try:
            timeout = timeout if timeout else self.timeout
            if not ctrl:
                ui.WebDriverWait(self.driver, timeout * 1).until(lambda browser: browser.find_elements_by_xpath(xpath))
                self.driver.find_element_by_xpath(xpath).click()
            else:
                ui.WebDriverWait(self.driver, self.timeout * 1).until(lambda browser: browser.find_elements_by_xpath(xpath))
                actions = ActionChains(self.driver)
                actions.key_down(Keys.CONTROL)
                self.driver.find_element_by_xpath(xpath).click()
                actions.key_up(Keys.CONTROL)
                actions.perform()
        except Exception:
            if not silent:
                print('ERROR waitclick', xpath)
                print(traceback.format_exc())
            return False
        return True

    def text_input(self, text, xpath, enter=False, clear=True, timeout=2):
        timeout = timeout if timeout else self.timeout
        ui.WebDriverWait(self.driver, timeout).until(lambda browser: browser.find_elements_by_xpath(xpath))
        if clear:
            self.driver.find_element_by_xpath(xpath).clear()
        self.driver.find_element_by_xpath(xpath).send_keys(text)
        if enter:
            self.driver.find_element_by_xpath(xpath).send_keys(Keys.ENTER)

    def wait_for_xpath(self, xpath, timeout=None, is_enabled=False):
        timeout = timeout if timeout else self.timeout
        if is_enabled:
            try:
                ui.WebDriverWait(self.driver, timeout * 1).until(lambda browser: browser.find_elements_by_xpath(xpath).is_enabled())
                return True
            except:
                return False
        else:
            try:
                ui.WebDriverWait(self.driver, timeout * 1).until(lambda browser: browser.find_elements_by_xpath(xpath))
                return True
            except:
                return False

    def save_page(self, destination, scroll_to_bottom=False):
        if scroll_to_bottom:
            self.scroll_to_bottom()
        page = self.driver.page_source
        file_ = open(destination, 'w')
        file_.write(page)
        file_.close()

    def scroll_to_bottom(self, next_button_click_xpath=None):
        # Get scroll height
        last_height = self.driver.execute_script("return document.body.scrollHeight")

        while True:
            # Scroll down to bottom
            # self.driver.execute_script("window.scrollTo(0, 9*document.body.scrollHeight)/10;")
            time.sleep(1)
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
            if next_button_click_xpath and self.wait_for_xpath(next_button_click_xpath, timeout=3):
                print('Clicking next', next_button_click_xpath)
                self.waitclick(next_button_click_xpath)
            # Wait to load page
            time.sleep(1.5)

            # Calculate new scroll height and compare with last scroll height
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

    def click_to_bottom(self, next_button_click_xpath):
        # Get scroll height
        last_height = self.driver.execute_script("return document.body.scrollHeight")

        while True:
            self.smooth_scroll()
            print("Sleeping", sleep(5))
            if self.wait_for_xpath(next_button_click_xpath, timeout=5):
                button_to_click = self.driver.find_element_by_xpath(next_button_click_xpath)
                action = ActionChains(self.driver)
                action.move_to_element(button_to_click).click().perform()
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

    def smooth_scroll(self, step=10, sleep_time=0.5):
        last_height = self.driver.execute_script("return document.body.scrollHeight")

        while True:
            for k in range(step):
                print((k+1)/step)
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight*%s);" % ((k+1)/step))
                sleep(sleep_time)
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            sleep(sleep_time*5)
            if new_height == last_height:
                break
            last_height = new_height

    def get(self, url, verbose=False):
        # Lazy-loading
        self.create_driver_if_needed()

        if verbose:
            print("GET: ", url)

        self.driver.get(url)
        return self

    def check_exists_by_xpath(self, xpath):
        try:
            self.driver.find_element_by_xpath(xpath)
        except NoSuchElementException:
            return False
        except Exception:
            print("check_exists_by_xpath error raised", traceback.format_exc())
            return False
        return True


if __name__ == '__main__':
    # if True:
    #     chromedriver = CustomDriver(headless=False)

    if False:
        url = "http://api.ipify.org"
        proxy = "178.33.76.75:8080"
        chromedriver = CustomDriver(headless=False, proxy=proxy)
        chromedriver.get(url)
        time.sleep(2)
        chromedriver.save_page('/tmp/null.html')

    if False:
        # Prompted search text
        url = "https://www.sherry-lehmann.com/"
        text = "champagne"
        input_box_path = '//*[@id="search_box_id"]'
        waiting_xpath = "//div[@class='termsHeader']"
        destination = '/tmp/test_headless.html'
        chromedriver = CustomDriver(headless=False)
        chromedriver.get(url)
        chromedriver.text_input(text, input_box_path, clear=True)
        chromedriver.wait_for_xpath(waiting_xpath)
        chromedriver.save_page(destination)

    if False:
        url = "https://fd7-courses.leclercdrive.fr/magasin-159301-Blanc-Mesnil/recherche.aspx?TexteRecherche=whisky"
        destination = "/tmp/leclerc.html"
        chromedriver = CustomDriver(headless=True)
        chromedriver.get(url)
        time.sleep(5)
        chromedriver.save_page(destination)
        print(destination)

    if False:
        chromedriver = CustomDriver(headless=False)
        url = "https://www.boozebud.com/"
        kw = "champagne"
        input_box_xpath = '//*[@id="reactContent"]/div/div[2]/nav/nav/div[2]/div[1]/div[1]/input'
        chromedriver.get(url)
        chromedriver.text_input(kw, input_box_xpath, enter=True)
        time.sleep(15)

    if False:
        chromedriver = CustomDriver(headless=False)
        chromedriver.get('https://www.wine.com/list/wine/champagne-and-sparkling/7155-123/2?pagelength=100')
        # chromedriver.driver.execute_script("window.scrollTo(0, 8*document.body.scrollHeight)/10;")
        chromedriver.save_page('/tmp/test.html', scroll_to_bottom=True)
        time.sleep(5)

    if False:
        cdriver = CustomDriver(firefox=True, proxy_host="151.80.140.233", proxy_port=54566, headless=True)
        cdriver.get("http://icanhazip.com/")
        print(cdriver.driver.page_source)

    if False:
        fpath = '/tmp/free-proxy-list.net.html'
        if not os.path.exists(fpath):
            cdriver = CustomDriver(firefox=True, proxy_host="151.80.140.233", proxy_port=54566, headless=True)
            cdriver.get("https://free-proxy-list.net/")
            cdriver.save_page(fpath, scroll_to_bottom=True)
        tree = etree.parse(open(fpath), parser=parser)
        for li in tree.xpath('//*[@id="proxylisttable"]//tr'):
            print(":".join(li.xpath('./td//text()')[:2]))

    if False:
        fpath = '/tmp/enfants_riches.html'
        cdriver = CustomDriver(firefox=True, proxy_host="52.15.102.68", proxy_port=3128, headless=False)
        cdriver.get("http://icanhazip.com/")
        sleep(2)
        print(cdriver.driver.page_source)
        cdriver.get('https://whatismyipaddress.com/fr/mon-ip')
        sleep(5)
        cdriver.get("https://www.ssense.com/en-fr/men/product/enfants-riches-deprimes/white-self-destructive-enfant-t-shirt/2676158")
        cdriver.save_page(fpath, scroll_to_bottom=True)
        sleep(100)
    if True:
        cdriver = CustomDriver(firefox=True, proxy_host="52.15.102.68", proxy_port=3128, headless=False)
        url = 'https://translate.google.fr/m/translate?hl=fr#ja/en/'
        cdriver.get(url)
        text = """B00FJSAWAQ;;感謝の風船セット ギフトセット　ウイスキーセット ハート風船付( ボウモア 43% 700ml(スコットランド）)メッセージカード付;;
                B00LA279LA;;誕生日祝い　名入れ彫刻　ジャックダニエル ブラック　デザインA　nck-jackdnl;;
                B00KBOE72W;;スミノフ ウォッカ 40° 750ml ［並行輸入品;;
                B00JZXK1SY;;ルーチェ グラッパ 40度 500ml 並行輸入品;;
                """
        cdriver.text_input(text, xpath='//textarea[@id="source"]')
        sleep(200)
