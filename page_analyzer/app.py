import os
from datetime import datetime

from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, url_for

from page_analyzer.db import DbManager
from page_analyzer.service import UrlService as us
from page_analyzer.url import (
    get_content,
    get_h1,
    get_title,
    is_available,
    normalize_url,
    validator,
)

load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
DATABASE_URL = os.getenv('DATABASE_URL')
db = DbManager(DATABASE_URL)  


@app.route('/')
def get_start_page():
    return render_template('start_page.html')


@app.route('/urls')
def get_urls_page():
    table = us.get_urls_list(db)
    return render_template('urls.html', table=table)


@app.post('/urls')
def post_url():
    url = request.form.get('url')
    normalized_url = normalize_url(url)

    if not validator(normalized_url):
        flash('Некорректный URL', 'error')
        return render_template('start_page.html'), 422
    
    existing_url = us.get_id_by_name(db, normalized_url)
        
    if existing_url:
        flash('Страница уже существует', 'info')
        url_id = existing_url[0]
    else:
        time = datetime.now()
        url_id = us.insert_name_time(db, normalized_url, time)
        flash('Страница успешно добавлена', 'success')
    return redirect(url_for('get_url_page', id=url_id))


@app.route('/urls/<int:id>')
def get_url_page(id):
    url = us.get_all_by_id(db, id)
    
    if not url:
        flash('Сайт не найден', 'error')
        return render_template('urls.html'), 422
    
    checks = us.get_all_by_id_ordered(db, id)
    return render_template('url_detail.html', url=url, checks=checks)


@app.post('/urls/<int:id>/checks')
def check_url(id):
    row = us.get_name_by_id(db, id)

    if not row:
        flash('Сайт не найден', 'error')
        return render_template('urls.html'), 422
    url = row[0]
    status_code = is_available(url)
    time = datetime.now()
    if status_code:
        h1 = get_h1(url)
        title = get_title(url)
        content = get_content(url)
        us.insert_url_checks(db, id, status_code, h1, title, content, time)
        flash('Страница успешно проверена', 'success')
    else:
        us.insert_error(db, id, time)
        flash('Произошла ошибка при проверке', 'danger')
        
    return redirect(url_for('get_url_page', id=id))