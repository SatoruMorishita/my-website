from flask import Flask, jsonify, render_template

import sqlite3
import requests
import os

app = Flask(__name__)
DB_PATH = "data.db"
GITHUB_DB_URL = "https://raw.githubusercontent.com/SatoruMorishita/my-website/main/プラン済み.db"

def download_db():
    if not os.path.exists(DB_PATH):
        response = requests.get(GITHUB_DB_URL)
        with open(DB_PATH, "wb") as f:
            f.write(response.content)

def get_data():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM shipments")  # 任意のテーブル名
    rows = cursor.fetchall()
    conn.close()
    return rows

#@app.route('/get_db')
#def get_db():
 #   download_db()
  #  data = get_data()
   # return jsonify(data)
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run()

@app.route('/shipments')
def shipments():
    download_db()
    data = get_data()
    return render_template('shipments.html', shipments=data)
