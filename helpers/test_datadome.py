from lxml import etree
parser = etree.HTMLParser()
from custom_browser import CustomDriver
import random
# Init variables and assets
driver = CustomDriver(headless=False, firefox=True, download_images=True)
random.choice([1,2,3])

count = 0
driver.get('https://www.leparisien.fr')
while True:
    print('Looping', count)
    elems = driver.driver.find_elements_by_xpath("//a[@href]")
    elems = [el.get_attribute('href') for el in elems]
    elems2 = [el for el in elems if "www.leparisien.fr" in el]
    elems3 = [el for el in elems if ("www.leparisien.fr" in el) and ('.php' in el)]
    if elems3:
        url = random.choice(elems3)
        count += 1
        print(count, url)
        driver.get(url)
    elif elems2:
        url = random.choice(elems2)
        count += 1
        print(count, url)
        driver.get(url)
    else:
        driver.get('https://www.leparisien.fr')
        print(count, 'https://www.leparisien.fr')

