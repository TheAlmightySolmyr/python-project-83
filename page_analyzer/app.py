import os
import psycopg2
import datetime

from validators import url as validate
from dotenv import load_dotenv
from flask import Flask, render_template, request, flash, redirect, url_for

load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
DATABASE_URL = os.getenv('DATABASE_URL')

def get_db_connection():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        return conn
    except psycopg2.Error as e:
        print(f"Ошибка подключения к базе данных: {e}")
        return None
    
connect = get_db_connection()

@app.route('/')
def get_start_page():
    return render_template('start_page.html')

@app.route('/urls')
def get_url():
    return render_template('urls.html')

@app.post('/')
def post_url():
    formed = request.form.to_dict()
    url = formed.get('url')
    if validate(url):
        with connect.cursor() as curs:
            curs.execute('INSERT INTO urls(name, created_at) VALUES (%s, %s);', (url, datetime.datetime.now()))
            flash('Your url was successfully added', 'success')
    else:
        flash('url has mistakes', 'error')
        return redirect('/')
