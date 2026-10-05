"""Get product specifications"""


def get_spec(soup, name):
    """Get product specifications from the soup object."""
    try:
         label=soup.find('span', string=name)
         if not label:
                return None
         value = label.find_next_sibling("span")
         text = value.get_text(strip=True) if value else None
         return "".join(text.split())
    except AttributeError:
        return None