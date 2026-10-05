"""Get links from a webpage"""



from urllib.parse import urljoin


def __get_links(page_or_element, base_url, query_selector):
    """Extracts product links from the given page or element."""
    list_links = []
    try:
        # 1. Получаем список всех найденных элементов
        search_results = page_or_element.query_selector_all(query_selector)

        # 2. Проходимся по КАЖДОМУ элементу
        for result in search_results:
            # Берём атрибут href у текущего элемента (result)
            href = result.get_attribute("href")

            if href:
                # Безопасно склеиваем base_url и href (обрабатывает относительные и абсолютные ссылки)
                full_url = urljoin(base_url, href)
                list_links.append(full_url)

    except Exception as e:
        print(f"Error extracting link: {e}")

    return list_links