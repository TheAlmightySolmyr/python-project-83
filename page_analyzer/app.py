import os
from datetime import datetime

from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, url_for

from page_analyzer.service import DbManager
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
pool = DbManager(DATABASE_URL)  


@app.route('/')
def get_start_page():
    return render_template('start_page.html')


@app.route('/urls')
def get_urls_page():
    query = '''
            SELECT 
                u.id, 
                u.name, 
                MAX(uc.created_at) as last_check_date,
                (SELECT status_code 
                 FROM url_checks 
                 WHERE url_id = u.id 
                 ORDER BY created_at DESC 
                 LIMIT 1) as last_status_code
            FROM urls u
            LEFT JOIN url_checks uc ON u.id = uc.url_id
            GROUP BY u.id, u.name
            ORDER BY u.id DESC;
        '''
    table = pool.fetch_all(query)
    return render_template('urls.html', table=table)


@app.post('/urls')
def post_url():
    url = request.form.get('url')
    normalized_url = normalize_url(url)

    if not validator(normalized_url):
        flash('Некорректный URL', 'error')
        return render_template('start_page.html'), 422
    
    query_url = 'SELECT id FROM urls WHERE name =%s;'

    existing_url = pool.fetch_one(query_url, (normalized_url,))
        
    if existing_url:
        flash('Страница уже существует', 'info')
        url_id = existing_url[0]
    else:
        time = datetime.now()
        query_insert = '''
                    INSERT INTO urls(name, created_at) 
                    VALUES (%s, %s) RETURNING id;
                    '''
        url_id = pool.fetch_one(query_insert, (normalized_url, time))[0]
        flash('Страница успешно добавлена', 'success')
    return redirect(url_for('get_url_page', id=url_id))


@app.route('/urls/<int:id>')
def get_url_page(id):
    query = 'SELECT * FROM urls WHERE id = %s;'
    url = pool.fetch_one(query, (id,))
    
    if not url:
        flash('Сайт не найден', 'error')
        return render_template('urls.html'), 422
    
    query_checks = '''
        SELECT * FROM url_checks 
        WHERE url_id = %s 
        ORDER BY created_at DESC;
    '''
    checks = pool.fetch_all(query_checks, (id,))
    return render_template('url_detail.html', url=url, checks=checks)


@app.post('/urls/<int:id>/checks')
def check_url(id):
    query_id = '''
                SELECT name 
                FROM urls 
                WHERE id = %s;'''

    row = pool.fetch_one(query_id, (id,))
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
        query_insert = '''
        INSERT INTO 
        url_checks 
            (url_id, status_code, h1, title, description, created_at)
        VALUES (%s, %s, %s, %s, %s, %s);
        '''
        pool.execute(query_insert, (id, status_code, h1, title, content, time))
        flash('Страница успешно проверена', 'success')
    else:
        query_error = '''
            INSERT INTO url_checks (url_id, status_code, created_at)
            VALUES (%s, %s, %s);
        '''
        pool.execute(query_error, (id, 0, time))
        flash('Произошла ошибка при проверке', 'danger')
        
    return redirect(url_for('get_url_page', id=id))