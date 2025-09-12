from urllib.parse import urlparse

import requests as req
from validators import url as validate
from bs4 import BeautifulSoup

MAX_URL_LENGTH = 255


def normalize_url(url):
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    parsed = urlparse(url)
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower().strip('/')
    result = f'{scheme}://{netloc}'
    return result


def is_available(link):
    try:
        url = req.get(link)
        url.raise_for_status()
        return url.status_code
    except req.RequestException:
        return None
    

def get_h1(url):
    html = req.get(url).text
    soup = BeautifulSoup(html, 'html.parser')
    h1 = soup.find('h1')
    if h1:
        return h1.get_text()


def get_title(url):
    html = req.get(url).text
    soup = BeautifulSoup(html, 'html.parser')
    title = soup.find('title')
    if title:
        return title.get_text()
    

def get_content(url):
    html = req.get(url).text
    soup = BeautifulSoup(html, 'html.parser')
    content = soup.find('meta', attrs={'name': 'description'})
    if content:
        return content.get('content')
    

def validator(url):
    return validate(url) and len(url) < MAX_URL_LENGTH
