import re
from decimal import Decimal
from pprint import pprint

from bs4 import BeautifulSoup
from curl_cffi import requests
from load_django import *
from parser_app.models import Phone
from get_spec import get_spec

URL = "https://brain.com.ua/ukr/Mobilniy_telefon_Apple_iPhone_16_Pro_Max_256GB_Black_Titanium-p1145443.html"

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


def parse_product(url: str) -> dict | None:
    """
    Парсит страницу товара по переданному URL и сохраняет данные в БД.
    """
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "uk-UA,uk;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://brain.com.ua/ukr/",
    }

    session = requests.Session(impersonate="chrome120")
    response = session.get(url, headers=headers, timeout=30)

    print("STATUS:", response.status_code)

    if response.status_code != 200:
        print(f"Не удалось загрузить страницу. Статус: {response.status_code}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    product = {}

    # 1. Название товара
    title_el = soup.find("h1", class_="desktop-only-title")
    product["full_product_name"] = title_el.get_text(strip=True) if title_el else None

    # 2. Характеристики из блока get_spec
    product["color"] = get_spec(soup, "Колір")
    product["memory_size"] = get_spec(soup, "Вбудована пам'ять")
    product["manufacturer"] = get_spec(soup, "Виробник")
    product["product_code"] = get_spec(soup, "Код товару:")
    product["screen_diagonal"] = get_spec(soup, "Діагональ екрану")
    product["display_resolution"] = get_spec(soup, "Роздільна здатність дисплея")

    # 3. Парсинг цен (обычная и акционная)
    main_price_block = soup.find("div", class_="main-price-block")
    price = None
    discounted_price = None

    if main_price_block:
        # Старая цена (бывает при наличии скидки в блоке br-pr-op)
        old_price_el = main_price_block.select_one("div.br-pr-op div.price-wrapper span")
        # Красная/акционная цена
        red_price_el = main_price_block.select_one("div.br-pr-np span.red-price")

        parsed_old_price = None
        parsed_red_price = None

        if old_price_el:
            clean = re.sub(r"[^\d.,]", "", old_price_el.get_text()).replace(",", ".")
            if clean:
                parsed_old_price = Decimal(clean)

        if red_price_el:
            clean = re.sub(r"[^\d.,]", "", red_price_el.get_text()).replace(",", ".")
            if clean:
                parsed_red_price = Decimal(clean)

        if parsed_old_price and parsed_red_price:
            price = parsed_old_price
            discounted_price = parsed_red_price
        else:
            # Если скидки нет — берем стандартную цену из br-pr-np
            reg_price_el = main_price_block.select_one("div.br-pr-np div.price-wrapper span")
            if reg_price_el:
                clean = re.sub(r"[^\d.,]", "", reg_price_el.get_text()).replace(",", ".")
                if clean:
                    price = Decimal(clean)

    product["price"] = price
    product["discounted_price"] = discounted_price

    # 4. Фотографии
    slider = soup.find("div", class_="br-prs-s")
    if slider:
        photos = [img["src"] for img in slider.find_all("img", class_="br-main-img") if img.get("src")]
        product["photos"] = photos if photos else None
    else:
        product["photos"] = None

    # 5. Количество отзывов
    reviews_el = soup.find("a", class_="brackets-reviews")
    if reviews_el:
        match = re.search(r"\d+", reviews_el.get_text())
        product["reviews_count"] = int(match.group()) if match else 0
    else:
        product["reviews_count"] = 0

    # 6. Полный словарь спецификаций
    product["specifications"] = {name: get_spec(soup, name) for name in SPEC_NAMES}

    # 7. Статус обработки
    product["status"] = "Done"

    # 8. Сохранение/обновление в БД Django
    Phone.objects.update_or_create(
        link=url,
        defaults=product,
    )

    return product


def main():
    product_data = parse_product(URL)
    if product_data:
        pprint(product_data)


if __name__ == "__main__":
    main()