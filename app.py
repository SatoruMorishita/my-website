import requests
from flask import Flask,jsonify,request
import os

app = Flask(__name__)
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
REPO = "SatoruMorishita/my-website"

@app.route('/trigger', methods=['POST'])
def trigger():
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {
        "title": "Render Deploy Trigger",
        "body": "Triggered from about.html"
    }
    response = requests.post(f"https://api.github.com/repos/{REPO}/issues", headers=headers, json=data)
    return ("OK", 200) if response.ok else ("Failed", 500)

@app.route('/get_db')
def get_db():
    download_db()
    data = get_data()
    return jsonify(data)

DB_PATH = "data.db"
GITHUB_DB_URL = "https://raw.githubusercontent.com/SatoruMorishita/my-website/main/プラン済み.db"

def download_db():
    if not os.path.exists(DB_PATH):
        response = requests.get(GITHUB_DB_URL)
        with open(DB_PATH, "wb") as f:
            f.write(response.content)

def get_data():
    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM shipments")  # テーブル名は適宜変更
    rows = cursor.fetchall()
    conn.close()
    return rows
