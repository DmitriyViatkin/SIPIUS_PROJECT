from lxml import html


def get_spec(tree: html.HtmlElement, name: str) -> str | None:
    """Retrieve a specification value by its label/name from the HTML tree.

    Args:
        tree (html.HtmlElement): Parsed lxml HTML tree.
        name (str): Label/name of the specification (e.g., 'Колір').

    Returns:
        str | None: Cleaned specification text if found, otherwise None.
    """
    # XPath searches for a span containing `name` and extracts text from its sibling element
    xpath_expr = f'//span[contains(text(), "{name}")]/following-sibling::*//text()'

    result = tree.xpath(xpath_expr)

    if result:
        # Join all text fragments and strip redundant whitespaces/newlines
        full_text = "".join(result)
        return " ".join(full_text.split())

    return None