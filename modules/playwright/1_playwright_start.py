from modules.load_django import *
import asyncio
from decimal import Decimal
import re
from playwright.async_api import async_playwright, Error
from asgiref.sync import sync_to_async
from get_spec_playwr import get_spec
from parser_app.models import Phone

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


@sync_to_async
def save_phone(**data):
    """Create or update a Phone record by its link."""
    link = data.pop("link")
    obj, created = Phone.objects.update_or_create(
        link=link,
        defaults={**data, "status": "Done"},
    )
    print(f"{'Saved' if created else 'Updated'}: = {link}")


async def main():
    """Search the product on brain.com.ua, parse its page and save it to the DB."""
    product = {}
    try:
        async with async_playwright() as p:
            # Browser initialization
            try:
                browser = await p.chromium.launch(
                    headless=False,
                    args=[
                        "--start-maximized",
                        "--disable-blink-features=AutomationControlled",  # Маскируем Playwright
                    ],
                )
            except Error as nameError:
                print(f"Unable to launch browser - {nameError}")
                return

            # Creating an isolated context
            try:
                context = await browser.new_context(
                    no_viewport=True,
                    user_agent=(
                        "Mozilla/5.0 (X11; Linux x86_64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    ),
                )
            except Error as nameError:
                print(f"Failed to create context - {nameError}")
                await browser.close()
                return

            page = await context.new_page()

            await page.goto(
                "https://brain.com.ua/ukr/",
                wait_until="domcontentloaded",
                timeout=60000,
            )

            # 2. Используем точный и надежный селектор видимого поля поиска
            # На сайте brain.com.ua основной поиск доступен по класс у или placeholder
            search_input = page.locator("xpath=/html/body/header/div[2]/div/div/div[2]/form/input[1]")

            await search_input.wait_for(state="visible")
            await search_input.click()

            # 3. Последовательный ввод текста
            search_text = "Apple iPhone 15 128GB Black"
            await search_input.click()
            await search_input.press_sequentially(search_text, delay=80)  # мс
            await search_input.press("End")


            # 4. Отправка формы: сначала пробуем клик по кнопке поиска (лупе)
            submit_btn = page.locator("xpath=//input[@type='submit' and contains(@class, 'qsr-submit')]")

            await submit_btn.click()

            # Дожидаемся перехода на страницу результатов или обновления AJAX
            try:
                await page.wait_for_load_state("networkidle", timeout=10000)
            except Exception:
                pass

            # Задержка для просмотра результата
            await page.wait_for_timeout(5000)

            card = page.locator("div.product-wrapper[data-class='76']").filter(
                has_text="Apple iPhone 15 128GB Black").first

            link_element = card.locator("a").first
            link = await link_element.get_attribute("href")

            if link:
                # Формируем полный URL, если ссылка относительная
                if not link.startswith("http"):
                    link = f"https://brain.com.ua{link}"

                print(f"Переходим по ссылке: {link}")
                await page.goto(link, wait_until="domcontentloaded")

            try:
                product["link"] = link
            except AttributeError:
                product["link"] = None

            try:
                text = await page.locator("h1.desktop-only-title").text_content()
                product["full_product_name"] = re.sub(r"\s+", " ", text).strip()
            except AttributeError:
                product["full_product_name"] = None

            try:
                product["color"] = await get_spec(page, 'Колір')
            except AttributeError:
                product["color"] = None

            try:
                product["memory_size"] = await get_spec(page, "Вбудована пам'ять")
            except AttributeError:
                product["memory_size"] = None

            try:
                product["manufacturer"] = await get_spec(page, 'Виробник')
            except AttributeError:
                product["manufacturer"] = None

            try:
                product["screen_diagonal"] = await get_spec(page, "Діагональ екрану")
            except AttributeError:
                product["screen_diagonal"] = None

            try:
                product["display_resolution"] = await get_spec(page, "Роздільна здатність дисплея")
            except AttributeError:
                product["display_resolution"] = None

            try:
                price_locator = page.locator(
                    "xpath=//div[@class='br-pr-np' and @data-pid='1044347']//div[@class='price-wrapper']//span")
                if await price_locator.is_visible(timeout=1000):
                    raw_price = await price_locator.text_content()

                    if raw_price:
                        clean_price = re.sub(r"[^\d.,]", "", raw_price).replace(",", ".")

                        if clean_price:
                            product["price"] = Decimal(clean_price)
                        else:
                            product["price"] = None
                    else:
                        product["price"] = None
                else:
                    product["price"] = None
            except AttributeError:
                product["price"] = None

            try:
                d_price_locator = page.locator(
                    "xpath=//span[contains(@class, 'red-price')]").first
                if await d_price_locator.is_visible(timeout=1000):
                    raw_price = await d_price_locator.text_content()

                    if raw_price:
                        clean_price = re.sub(r"[^\d.,]", "", raw_price).replace(",", ".")

                        if clean_price:
                            product["discounted_price"] = Decimal(clean_price)
                        else:
                            product["discounted_price"] = None
                    else:
                        product["discounted_price"] = None
                else:
                    product["discounted_price"] = None
            except AttributeError:
                product["discounted_price"] = None

            try:
                product["product_code"] = await get_spec(page, "Код товару:")
            except AttributeError:
                product["product_code"] = None

            try:
                reviews_link = page.locator("a.brackets-reviews").first

                if await reviews_link.count() > 0:
                    text = await reviews_link.text_content()  # "Відгуки (1)"

                    # Извлекаем только цифры из скобок
                    match = re.search(r"\((\d+)\)", text)
                    if match:
                        reviews_count = int(match.group(1))
                    else:
                        reviews_count = 0
                else:
                    reviews_count = 0

                product["reviews_count"] = reviews_count
            except AttributeError:
                product["reviews_count"] = None

            try:
                product["photos"] = await page.locator("div.br-prs-s img.br-main-img").evaluate_all(
                    "elements => elements.map(el => el.src)")
            except AttributeError:
                product["photos"] = None

            try:
                specs = {name: await get_spec(page, name) for name in SPEC_NAMES}
                product["specifications"] = specs
            except AttributeError:
                product["specifications"] = None

            for key, value in product.items():
                print(f'{key}: {value}')

            await save_phone(**product)

            await browser.close()

    except Exception as nameError:
        print(f"Error - {nameError}")


if __name__ == "__main__":
    asyncio.run(main())