import os

import psycopg2
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request
from validators import url as validate

load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
DATABASE_URL = os.getenv('DATABASE_URL')
conn = psycopg2.connect(DATABASE_URL)
conn.autocommit = True


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
        with conn.cursor() as curs:
            curs.execute('INSERT INTO urls(name, created_at) VALUES (%s, %s);', (url, datetime.now()))
            flash('Your url was successfully added', 'success')
    else:
        flash('url has mistakes', 'error')
        return redirect('/')
