import os
from datetime import datetime

import psycopg2
from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request
from validators import url as validate

load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
DATABASE_URL = os.getenv('DATABASE_URL')
conn = psycopg2.connect(DATABASE_URL)
conn.autocommit = True
MAX_URL_LENGTH = 255


@app.route('/')
def get_start_page():
    return render_template('start_page.html')


@app.route('/urls')
def get_urls_page():
    return render_template('urls.html')


@app.post('/urls')
def post_url():
    url = request.form.get('url')
    
    if not validate(url) or len(url) >= MAX_URL_LENGTH:
        flash('URL has mistakes', 'error')
        return redirect('/')
    
    with conn.cursor() as curs:
        curs.execute('SELECT id FROM urls WHERE name = %s;', (url,))
        existing_url = curs.fetchone()
        
        if existing_url:
            flash('URL already exists in database', 'info')
        else:
            curs.execute('''
                        INSERT INTO urls(name, created_at) 
                        VALUES (%s, %s);
                        ''', (url, datetime.now()))
            flash('URL was successfully added', 'success')
    
    return redirect('/urls')