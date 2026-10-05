from bs4 import BeautifulSoup
from curl_cffi import requests
from load_django import *
from parser_app.models import Phone
from pprint import pprint
from get_spec import get_spec
import re



url = "https://brain.com.ua/ukr/Mobilniy_telefon_Apple_iPhone_16_Pro_Max_256GB_Black_Titanium-p1145443.html"

SPEC_NAMES = [
    "Форм-фактор", "Кількість SIM-карт", "Формат SIM-карти","Покоління зв'язку (2G /3G/4G/5G)",
    "Тип дисплея","Діагональ екрану","Роздільна здатність екрану", "Частота оновлення екрану",
    "Матеріал екрану","Процесор","Кількість ядер","Відеоядро","Вбудована пам'ять",
    "Кількість модулів основної камери","Основна камера", "Діафрагма основної камери",
    "Метод стабілізації","Запис відео основної камери","Кількість модулів фронтальної камери",
    "Фронтальна камера","Діафрагма фронтальної камери", "Запис відео фронтальної камери",
    "Функції камери","Операційна система", "Мультимедіа", "Органайзер","Бездротові технології",
    "Навігація","Інтерфейси і підключення", "Особливості", "Вбудовані датчики",
    "Безпека","Оснащення","Матеріал корпуса", "Розміри (мм)", "Вага",  "Колір",
    "Особливості корпусу", "Виробник","Країна виробництва", "Штрихкод", "Примітка",
]

# impersonate="chrome120" повністю імітує TLS-відбиток браузера Chrome
session = requests.Session(impersonate="chrome120")

headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "uk-UA,uk;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://brain.com.ua/ukr/",
}

r = session.get(url, headers=headers, timeout=30)

product={}

print("STATUS:", r.status_code)

if r.status_code == 200:
    soup = BeautifulSoup(r.text, "html.parser")

    # Полное название товара
    try:
        product["full_product_name"] =  soup.find("h1", {"class": "desktop-only-title"}).text.strip()
    except AttributeError:
        product["full_product_name"] = None
        # Color
    try:
        product["color"] = get_spec(soup, "Колір")
    except AttributeError:
        product["color"] = None
        #memmory_size
    try:
       product["memory_size"] = get_spec(soup, "Вбудована пам'ять")
    except AttributeError:
        product["memory_size"] = None
    #Manufacturer
    try:
        product["manufacturer"] = get_spec(soup, "Виробник")
    except AttributeError:
        product["manufacturer"] = None
        #price
    try:
        product["price"] = get_spec(soup, "Цена")
    except AttributeError:
        product["price"] = None
    #discounted_price
    try:
        product["discounted_price"] = get_spec(soup, "Цена по акции")
    except AttributeError:
        product["discounted_price"] = None
    #photos
    try:
        slider = soup.find("div", class_="br-prs-s")
        product["photos"] =   [img["src"] for img in slider.find_all("img", class_="br-main-img") if img.get("src")
] if slider else []
    except AttributeError:
        product["photos"] = None
    #Code product
    try:
        product["product_code"] = get_spec(soup, "Код товару:")
    except AttributeError:
        product["product_code"] = None
    try:
        a = soup.find("a", class_="brackets-reviews")
        m = re.search(r"\d+", a.get_text()) if a else None
        product["reviews_count"] = int(m.group()) if m else None
    except AttributeError:
        product["reviews_count"] = None

    try:
        product["screen_diagonal"] = get_spec(soup, "Діагональ екрану")
    except AttributeError:
        product["screen_diagonal"] = None
    try:
        product["display_resolution"] = get_spec(soup, "Роздільна здатність дисплея")
    except AttributeError:
        product["display_resolution"] = None

    try:
        specs={name: get_spec(soup, name) for name in SPEC_NAMES}
        product["specifications"] =  specs
    except AttributeError:
        specs = None
    try:
        product["status"] = "Done"
    except AttributeError:
        product["status"] = "Failed"
pprint(product)

Phone.objects.get_or_create(
    link=url,

    defaults=product,
)