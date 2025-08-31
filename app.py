import os
import requests
import sqlite3
import io
import pandas as pd
from flask import Flask, jsonify, request, render_template, send_file
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

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

@app.route('/unplanned')
def unplanned():
    data = get_data_from("未プラン.db")
    return render_template('unplanned.html', shipments=data)
    
# ローカル実行用
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
