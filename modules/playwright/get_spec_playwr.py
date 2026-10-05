import re
from playwright.async_api import Page, TimeoutError


async def get_spec(page: Page, name: str) -> str | None:
    """Извлекает значение характеристики по её названию прямо со страницы."""
    try:
        # 1. Находим span, содержащий точное имя характеристики
        # exact=True помогает избежать ложных срабатываний, если названия похожи
        label = page.get_by_text(name, exact=True).first

        # Проверяем, существует ли элемент и виден ли он
        if await label.count() == 0:
            return None

        # 2. Находим следующий соседний span (find_next_sibling -> xpath=following-sibling::span[1])
        value_locator = label.locator("xpath=following-sibling::span[1]").first

        if await value_locator.count() > 0:
            text = await value_locator.inner_text()

            # Удаляем абсолютно все пробельные символы (аналог "".join(text.split()))
            return re.sub(r"\s+", "", text)

        return None

    except TimeoutError:
        return None
    except Exception as e:
        print(f"Ошибка при получении характеристики '{name}': {e}")
        return None