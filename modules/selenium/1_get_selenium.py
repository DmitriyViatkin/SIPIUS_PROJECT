from modules.load_django import *
from time import sleep
import re
from pprint import pprint

import undetected_chromedriver as uc
from lxml import html
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


from get_spec_selenium import get_spec
from parser_app.models import Phone

URL = "https://brain.com.ua/ukr"
SEARCH_QUERY = "Apple iPhone 15 128GB Black"

SPEC_NAMES = [
    "Форм-фактор", "Кількість SIM-карт", "Формат SIM-карти", "Покоління зв'язку (2G /3G/4G/5G)",
    "Тип дисплея", "Діагональ екрану", "Роздільна здатність екрану", "Частота оновлення екрану",
    "Матеріал екрану", "Процесор", "Кількість ядер", "Відеоядро", "Вбудована пам'ять",
    "Кількість модулів основної камери", "Основна камера", "Діафрагма основної камери",
    "Метод стабілізації", "Запис відео основної камери", "Кількість модулів фронтальної камери",
    "Фронтальна камера", "Діафрагма фронтальної камери", "Запис відео фронтальної камери",
    "Функції камери", "Операційна система", "Мультимедіа", "Органайзер", "Бездротові технології",
    "Навігація", "Інтерфейси і підключення", "Особливості", "Вбудовані датчики",
    "Безпека", "Оснащення", "Матеріал корпуса", "Розміри (мм)", "Вага", "Колір",
    "Особливості корпусу", "Виробник", "Країна виробництва", "Штрихкод", "Примітка",
]


def quit_driver(driver):
    driver.quit()


def get_url(driver, url):
    driver.get(url)
    sleep(5)


def search_product(driver, query):
    try:
        search = driver.find_element(By.XPATH, "/html/body/header/div[2]/div/div/div[2]/form/input[1]")
        search.clear()
        search.send_keys(query)
        sleep(5)
    except NoSuchElementException:
        print('There is no search input')
        return

    try:
        button = driver.find_element(By.XPATH, "//input[@type='submit' and contains(@class, 'qsr-submit')]")
        button.click()
        sleep(5)
    except NoSuchElementException:
        print('There is no search button')


def go_to_product_page(driver):
    """Клікає по першому товару в видачі, повертає його посилання."""
    try:
        product_link = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, "(//div[contains(@class, 'br-pp-img')]//a)[1]"))
        )
    except TimeoutException:
        print('There is no product in search results')
        return None

    link = product_link.get_attribute("href")
    product_link.click()
    sleep(5)
    WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.XPATH, "//h1")))
    return link


def get_first(tree, xpath):
    result = tree.xpath(xpath)
    return result[0].strip() if result else None


def get_data_from_the_page(driver, link):
    tree = html.fromstring(driver.page_source)
    product = {'link': link}

    product['full_product_name'] = get_first(tree, "//h1[contains(@class, 'desktop-only-title')]/text()")
    product['color'] = get_spec(tree, "Колір")
    product['memory_size'] = get_spec(tree, "Вбудована пам'ять")
    product['manufacturer'] = get_spec(tree, "Виробник")
    product['screen_diagonal'] = get_spec(tree, "Діагональ екрану")
    product['display_resolution'] = get_spec(tree, "Роздільна здатність дисплея")
    product['discounted_price'] = get_spec(tree, "Цена по акции")

    price_text = get_first(
        tree,
        "//div[@class='br-pr-np' and @data-pid='1044347']//div[@class='price-wrapper']//span//text()"
    )
    product['price'] = int(re.sub(r"\D", "", price_text)) if price_text else None

    slider = tree.xpath("//div[contains(@class, 'br-prs-s')]")
    product['photos'] = [
        img.get("src")
        for img in slider[0].xpath(".//img[contains(@class, 'br-main-img')]")
        if img.get("src")
    ] if slider else []

    product['product_code'] = get_first(
        tree, "//span[normalize-space()='Код товару:']/following-sibling::span[1]/text()"
    )

    reviews_text = get_first(tree, "//a[contains(@class, 'brackets-reviews')]/text()")
    match = re.search(r"\d+", reviews_text) if reviews_text else None
    product['reviews_count'] = int(match.group()) if match else None

    product['specifications'] = {name: get_spec(tree, name) for name in SPEC_NAMES}
    product['status'] = 'Done'

    for key, value in product.items():
        print(f'{key}: {value}')

    return product


def save_data(product):
    link = product.pop('link')
    Phone.objects.update_or_create(link=link, defaults=product)


def get_data(driver):
    get_url(driver, URL)
    search_product(driver, SEARCH_QUERY)

    link = go_to_product_page(driver)
    if not link:
        return

    try:
        product = get_data_from_the_page(driver, link)
    except Exception as e:
        print(f'Failed: {e}')
        Phone.objects.update_or_create(link=link, defaults={'status': 'Failed'})
        return

    save_data(product)


if __name__ == '__main__':
    driver = uc.Chrome()
    try:
        get_data(driver)
    finally:
        quit_driver(driver)