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

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)

#追加
@app.route('/api/plan')
def api_plan():
    download_db()
    data = get_data()
    return render_template('planned.html', shipments=data)

@app.route('/')
def index():
    download_db()
    data = get_data()
    return render_template('プラン済み.html', shipments=data)

