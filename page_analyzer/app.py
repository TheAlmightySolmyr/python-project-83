import os
from datetime import datetime

import requests as req
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, url_for
from psycopg2.pool import SimpleConnectionPool
from validators import url as validate

load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
DATABASE_URL = os.getenv('DATABASE_URL')
pool = SimpleConnectionPool(1, 1, DATABASE_URL)  
MAX_URL_LENGTH = 255


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


@app.route('/')
def get_start_page():
    return render_template('start_page.html')


@app.route('/urls')
def get_urls_page():
    conn = pool.getconn()
    with conn.cursor() as curs:
        curs.execute('''
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
        ''')
        table = curs.fetchall()
    pool.putconn(conn)
    return render_template('urls.html', table=table)


@app.post('/urls')
def post_url():
    url = request.form.get('url')
    conn = pool.getconn()

    if not validate(url) or len(url) >= MAX_URL_LENGTH:
        flash('Некорректный URL', 'error')
        pool.putconn(conn)
        return render_template('start_page.html'), 422
    
    with conn.cursor() as curs:
        curs.execute('SELECT id FROM urls WHERE name = %s;', (url,))
        existing_url = curs.fetchone()
        
        if existing_url:
            flash('Страница уже существует', 'info')
            url_id = existing_url[0]
        else:
            curs.execute('''
                        INSERT INTO urls(name, created_at) 
                        VALUES (%s, %s) RETURNING id;
                        ''', (url, datetime.now()))
            url_id = curs.fetchone()[0]
            flash('Страница успешно добавлена', 'success')
        conn.commit()
    pool.putconn(conn)    
    return redirect(url_for('get_url_page', id=url_id))


@app.route('/urls/<int:id>')
def get_url_page(id):
    conn = pool.getconn()
    with conn.cursor() as curs:
        curs.execute('SELECT * FROM urls WHERE id = %s;', (id,))
        url = curs.fetchone()
        
        if not url:
            flash('Сайт не найден', 'error')
            pool.putconn(conn)
            return render_template('urls.html'), 422
        
        curs.execute('''
            SELECT * FROM url_checks 
            WHERE url_id = %s 
            ORDER BY created_at DESC;
        ''', (id,))
        checks = curs.fetchall()
    pool.putconn(conn)
    return render_template('url_detail.html', url=url, checks=checks)


@app.post('/urls/<int:id>/checks')
def check_url(id):
    conn = pool.getconn()
    with conn.cursor() as curs:
        curs.execute('''SELECT name 
                        FROM urls 
                        WHERE id = %s;''',
                        (id,))
        row = curs.fetchone()
        if not row:
            flash('Сайт не найден', 'error')
            pool.putconn(conn)
            return render_template('urls.html'), 422
        url = row[0]
    pool.putconn(conn)
    status_code = is_available(url)
    conn = pool.getconn()
    try:
        with conn.cursor() as curs:
            if status_code:
                h1 = get_h1(url)
                title = get_title(url)
                content = get_content(url)
                curs.execute('''
                INSERT INTO 
                url_checks 
                    (url_id, status_code, h1, title, description, created_at)
                VALUES (%s, %s, %s, %s, %s, %s);
                ''', (id, status_code, h1, title, content, datetime.now()))
                flash('Страница успешно проверена', 'success')
            else:
                curs.execute('''
                    INSERT INTO url_checks (url_id, status_code, created_at)
                    VALUES (%s, %s, %s);
                ''', (id, 0, datetime.now()))
                flash('Произошла ошибка при проверке', 'danger')
            
            conn.commit()
            
    except Exception:
        conn.rollback()
        flash('Произошла ошибка при сохранении проверки', 'danger')
    finally:
        pool.putconn(conn)
    
    return redirect(url_for('get_url_page', id=id))