import time

import requests
from bs4 import BeautifulSoup


def get_data_by_name(name_document: str):
    url = f'https://www.consultant.ru/search/?q={name_document}'
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/29.0.1547.65 Chrome/29.0.1547.65 Safari/537.36',
    }
    time.sleep(1)
    page = requests.get(url, headers=headers)
    soup = BeautifulSoup(page.text, 'html.parser')
    search_data = soup.findAll('li', class_='search-results__item search-results__item_default')
    all_data = []
    words = ['вопрос', 'путеводитель']
    point = False
    for data in search_data:
        link = ''
        name = data.text.replace('<', '').replace('>', '').split('\n')
        name = [i for i in name if i]
        for word in words:
            if word.lower() in name[1].lower():
                point = True
        if point:
            point = False
            continue
        if not data.a['href'].startswith('https'):
            link = f'https://www.consultant.ru{data.a['href']}' if 'www.consultant.ru' not in data.a['href'] else f'https:{data.a['href']}'
        else:
            link = data.a['href']

        all_data.append({
            'name': name,
            'link': link
        })

    return all_data
