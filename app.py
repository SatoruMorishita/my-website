import os
import requests
import sqlite3
import io
import pandas as pd
from flask import Flask, jsonify, request, render_template, send_file
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# GitHub連携
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
REPO = "SatoruMorishita/my-website"

# DB設定
DB_PATH = "data.db"
GITHUB_DB_URL = "https://raw.githubusercontent.com/SatoruMorishita/my-website/main/プラン済み.db"

# DB操作関数
def download_db():
    if not os.path.exists(DB_PATH):
        response = requests.get(GITHUB_DB_URL)
        with open(DB_PATH, "wb") as f:
            f.write(response.content)

def get_data():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM shipments")
    rows = cursor.fetchall()
    conn.close()
    return rows

# Excelダウンロード用エンドポイント
@app.route('/download_xlsx')
def download_xlsx():
    download_db()
    data = get_data()
    df = pd.DataFrame(data, columns=[
        "ID", "キャリア名", "出荷日", "名前", "宛先", "カートン数", "重量",
        "トラッキングナンバー", "商品名", "商品カテゴリー", "着日"
    ])
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Planned')
    output.seek(0)
    return send_file(output,
                     download_name="planned_shipments.xlsx",
                     as_attachment=True,
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

# ルート定義
@app.route('/')
def index():
    download_db()
    data = get_data()
    return render_template('planned.html', shipments=data)

@app.route('/api/plan')
@app.route('/api/plan/')
def api_plan():
    download_db()
    data = get_data()
    return render_template('planned.html', shipments=data)

@app.route('/get_db')
def get_db():
    download_db()
    data = get_data()
    return jsonify(data)

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

# ローカル実行用
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
