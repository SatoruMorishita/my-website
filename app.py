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
DB_CONFIG = {
    "planned": {
        "filename": "プラン済み.db",
        "url": "https://raw.githubusercontent.com/SatoruMorishita/my-website/main/プラン済み.db",
        "table": "shipments",
        "template": "planned.html",
        "xlsx_name": "planned_shipments.xlsx"
    },
    "unplanned": {
        "filename": "未プラン.db",
        "url": "https://raw.githubusercontent.com/SatoruMorishita/my-website/main/未プラン.db",
        "table": "orders",
        "template": "unplanned.html",
        "xlsx_name": "unplanned_orders.xlsx"
    }
}

# DBダウンロード関数
def download_db(db_path, github_url):
    if not os.path.exists(db_path):
        response = requests.get(github_url)
        with open(db_path, "wb") as f:
            f.write(response.content)

# DBデータ取得関数
def fetch_data(db_path, table_name):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()
    conn.close()
    return rows

# Excelダウンロードエンドポイント（planned固定）
@app.route('/download_xlsx')
def download_xlsx():
    config = DB_CONFIG["planned"]
    download_db(config["filename"], config["url"])
    data = fetch_data(config["filename"], config["table"])
    df = pd.DataFrame(data, columns=[
        "ID", "キャリア名", "出荷日", "名前", "宛先", "カートン数", "重量",
        "トラッキングナンバー", "商品名", "商品カテゴリー", "着日"
    ])
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Planned')
    output.seek(0)
    return send_file(output,
                     download_name=config["xlsx_name"],
                     as_attachment=True,
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


#未プラン
@app.route('/download_xlsx_unplanned')
def download_xlsx_unplanned():
    config = DB_CONFIG["unplanned"]
    download_db(config["filename"], config["url"])
    data = fetch_data(config["filename"], config["table"])
#当日出荷表
@app.route('/download_today-shippments_xlsx')
def download_today_xlsx():
    config = DB_CONFIG["today-shippments"]
    download_db(config["filename"], config["url"])
    conn = sqlite3.connect(config["filename"])
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {config['table']} WHERE 出荷日 = '2025-08-01'")
    rows = cursor.fetchall()
    conn.close()

    df = pd.DataFrame(rows, columns=[
        "ID", "キャリア名", "出荷日", "名前", "宛先", "カートン数", "重量",
        "トラッキングナンバー", "商品名", "商品カテゴリー", "着日"
    ])
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Today')
    output.seek(0)
    return send_file(output,
                     download_name="today_shipments.xlsx",
                     as_attachment=True,
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
#翌日出荷表
@app.route('/download_tommorrow-shippments_xlsx')
def download_tommorrow_xlsx():
    config = DB_CONFIG["planned"]
    download_db(config["filename"], config["url"])
    conn = sqlite3.connect(config["filename"])
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {config['table']} WHERE 出荷日 = '2025-08-02'")
    rows = cursor.fetchall()
    conn.close()

    df = pd.DataFrame(rows, columns=[
        "ID", "キャリア名", "出荷日", "名前", "宛先", "カートン数", "重量",
        "トラッキングナンバー", "商品名", "商品カテゴリー", "着日"
    ])
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Tommorrow')
    output.seek(0)
    return send_file(output,
                     download_name="tommorrow_shipments.xlsx",
                     as_attachment=True,
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    # 必要に応じてカラム名を調整
    df = pd.DataFrame(data, columns=[
        "ID", "キャリア名", "出荷日", "名前", "宛先", "カートン数", "重量", "商品名","商品カテゴリー","着日","電話番号"
    ])

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Unplanned')
    output.seek(0)
    return send_file(output,
                     download_name=config["xlsx_name"],
                     as_attachment=True,
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


# ルート：プラン済み
@app.route('/')
def index():
    config = DB_CONFIG["planned"]
    download_db(config["filename"], config["url"])
    data = fetch_data(config["filename"], config["table"])
    return render_template(config["template"], shipments=data)

# ルート：未プラン
@app.route('/unplanned')
def unplanned():
    config = DB_CONFIG["unplanned"]
    download_db(config["filename"], config["url"])
    data = fetch_data(config["filename"], config["table"])
    return render_template(config["template"], shipments=data)

#ルート:当日出荷表
@app.route('/today-shipping')
def today_shipping():
    config = DB_CONFIG["planned"]
    download_db(config["filename"], config["url"])
    conn = sqlite3.connect(config["filename"])
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {config['table']} WHERE 出荷日 = '2025-08-01'")
    rows = cursor.fetchall()
    conn.close()
    return render_template("today-shipping.html", shipments=rows)

#ルート:翌日出荷表
@app.route('/tommorrow-shipping')
def tommorrow_shipping():
    config = DB_CONFIG["planned"]
    download_db(config["filename"], config["url"])
    conn = sqlite3.connect(config["filename"])
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {config['table']} WHERE 出荷日 = '2025-08-02'")
    rows = cursor.fetchall()
    conn.close()
    return render_template("tommorrow-shipping.html", shipments=rows)
    
# ローカル実行
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
