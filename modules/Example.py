from load_django import *
from parser_app.models import Tool
import requests
from bs4 import BeautifulSoup

headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:126.0) Gecko/20100101 Firefox/126.0',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Referer': 'https://www.google.com/',
    'Connection': 'keep-alive',
    'Cache-Control': 'no-cache',
    'Pragma': 'no-cache',
    'Upgrade-Insecure-Requests': '1',
    'DNT': '1',  # Do Not Track
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-User': '?1',
    'TE': 'Trailers',  # Transfer Encoding
}

url = f'https://toolup.com/products/ridgid-44923-690-i-115v-hand-held-power-drive-with-1-2-to-2-die-heads'

product = {}

tools = Tool.objects.all()
for item in tools:
    r = requests.get(item.link, headers=headers)
    soup = BeautifulSoup(r.text, 'html.parser')


    try:
        product['title'] = soup.h1.text.strip()
    except AttributeError:
        product['title'] = None


    try:
        product['vendor'] = soup.find('span', attrs={'class': 'product-vendor'}).text.strip()
    except AttributeError:
        product['vendor'] = None

    try:
        product['price'] = soup.find('strong', attrs={'class': 'price__current'}).text.strip()
    except AttributeError:
        product['price'] = None

    try:
        product['original_price'] = soup.find('s', attrs={'class': 'price__was'}).text.strip()
    except:
        product['original_price'] = None


    try:
        product['img_url'] = 'https:' + soup.find('li', attrs={'class': 'is-current-variant'}).find('img', attrs={'class': 'product-image'}).get('src')
    except AttributeError:
        product['img_url'] = None

    try:
        product['sku'] = soup.find('span', attrs={'class': 'product-sku__value'}).text.strip()
    except AttributeError:
        product['sku'] = None

    try:
        product['barcode'] = soup.find('span', attrs={'class': 'product-info__barcode-value'}).text.strip()
    except AttributeError:
        product['barcode'] = None


    try:
        specifications = soup.find('details-disclosure').find('div', attrs={'class': 'product-details-specs'}).find('table')
        product['specifications'] = specifications.text.strip().replace('\n\n', ' ')
        specifications.decompose()
    except AttributeError:
        product['specifications'] = None

    try:
        product['description'] = soup.find('div', attrs={'class': 'product-description'}).text.strip()
    except AttributeError:
        product['description'] = None

    for key, value in product.items():
        print('=' * 50)
        print(f'{key}: {value}')

    item.title = product['title']
    item.vendor = product['vendor']
    item.original_price = product['original_price']
    item.price = product['price']
    item.img_url = product['img_url']
    item.sku = product['sku']
    item.barcode = product['barcode']
    item.specifications = product['specifications']
    item.description = product['description']

    item.save()
