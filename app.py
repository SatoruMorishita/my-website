import os
import requests
import sqlite3
import io
import pandas as pd
from flask import Flask, jsonify, request, render_template, send_file, abort
from flask_cors import CORS
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import japanize_matplotlib
###################################################################
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
####################################################################
app = Flask(__name__)
CORS(app)
#####勤怠管理用コード###############################################################
# Renderの環境変数から復元
json_str = base64.b64decode(os.environ["GOOGLE_CREDENTIALS"]).decode("utf-8")
with open("credentials.json", "w") as f:
    f.write(json_str)
    
#勤怠管理用
# 認証スコープ
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

# 認証情報の読み込み（JSONファイルは.gitignore推奨）
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)

# スプレッドシートとシートに接続
sheet = client.open("勤怠管理").worksheet("勤怠")

# 出勤打刻
def record_clock_in(name):
    now = datetime.now().strftime("%Y/%m/%d %H:%M")
    sheet.append_row([now.split()[0], name, now.split()[1], "", "", "出勤"])

# 退勤打刻（最後の出勤行を更新）
def record_clock_out(name):
    records = sheet.get_all_records()
    for i in reversed(range(len(records))):
        if records[i]["名前"] == name and records[i]["退勤時間"] == "":
            row_index = i + 2  # ヘッダー分オフセット
            now = datetime.now().strftime("%H:%M")
            sheet.update_cell(row_index, 4, now)
            sheet.update_cell(row_index, 6, "退勤")
            break

def get_work_summary(name):
    records = sheet.get_all_records()
    total_minutes = 0
    for row in records:
        if row["名前"] == name and row["出勤時間"] and row["退勤時間"]:
            in_time = datetime.strptime(row["出勤時間"], "%H:%M")
            out_time = datetime.strptime(row["退勤時間"], "%H:%M")
            total_minutes += int((out_time - in_time).total_seconds() / 60)
    hours = total_minutes // 60
    minutes = total_minutes % 60
    return f"{name}さんの今月の勤務時間は {hours}時間{minutes}分 です"
@app.route("/line_webhook", methods=["POST"])
def line_webhook():
    # LINEからのイベント処理
    return "OK"

# 環境変数から認証情報を取得（Renderで設定）
CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")
CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")

# LINE APIインスタンス化
line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# Flaskアプリ初期化
app = Flask(__name__)

# Webhook受信エンドポイント
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

# メッセージイベントの処理（オウム返し）
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    reply_text = f"「{event.message.text}」ですね！了解です🦊"
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )
#####################################################################
#HP
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
    },
    
    "inventory": {
    "filename": "inventory.db",
    "url": "https://raw.githubusercontent.com/SatoruMorishita/my-website/main/inventory.db",
    "table": "inventory",  # ← 実際のテーブル名に合わせてね
    "template": "inventory.html",
    "xlsx_name": "inventory_summary.xlsx"
    },

    "unplanned-item": {
    "filename": "unplanned_item.db",
    "url": "https://raw.githubusercontent.com/SatoruMorishita/my-website/main/unplanned_item.db",
    "table": "unplanned",  # ← ここが元のテーブル名
    "template": "unplanned-item.html",
    "xlsx_name": "unplanned_item.xlsx"
    },

    
    "today-shipping": {
        "filename": "プラン済み.db",
        "url": "https://raw.githubusercontent.com/SatoruMorishita/my-website/main/プラン済み.db",
        "table": "shipments",
        "template": "today-shipping.html",
        "xlsx_name": "today-shipping.xlsx"
    },
    "tommorrow-shipping": {
        "filename": "プラン済み.db",
        "url": "https://raw.githubusercontent.com/SatoruMorishita/my-website/main/プラン済み.db",
        "table": "shipments",
        "template": "tommorrow-shipping.html",
        "xlsx_name": "tommorrow-shipping.xlsx"
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

#inventory
def fetch_inventory_summary(db_path, table_name):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    query = f"""
        SELECT 商品名, 商品カテゴリー, SUM(unit数) as 合計unit数
        FROM {table_name}
        GROUP BY 商品名, 商品カテゴリー
    """
    cursor.execute(query)
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

    df = pd.DataFrame(data, columns=[
        "ID", "キャリア名", "出荷日", "名前", "宛先", "カートン数", "重量",
        "商品名", "商品カテゴリー", "着日", "電話番号"
    ])

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Unplanned')
    output.seek(0)
    return send_file(output,
                     download_name=config["xlsx_name"],
                     as_attachment=True,
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

#在庫
@app.route('/download_inventory_xlsx')
def download_inventory_xlsx():
    config = DB_CONFIG["inventory"]
    download_db(config["filename"], config["url"])
    summary = fetch_inventory_summary(config["filename"], config["table"])

    df = pd.DataFrame(summary, columns=["商品名", "商品カテゴリー", "unit数合計"])
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Inventory Summary')
    output.seek(0)
    return send_file(output,
                     download_name=config["xlsx_name"],
                     as_attachment=True,
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

#未プラン在庫
@app.route('/download_unplanned_item_xlsx')
def download_unplanned_item_xlsx():
    config = DB_CONFIG["unplanned-item"]
    download_db(config["filename"], config["url"])
    data = fetch_data(config["filename"], config["table"])

    df = pd.DataFrame(data, columns=[
        "ID","出荷日", "名前","商品名", "商品カテゴリー","unit数","着日","電話番号"
    ])

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Unplanned Item')
    output.seek(0)
    return send_file(output,
                     download_name=config["xlsx_name"],
                     as_attachment=True,
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

#short
@app.route('/download_shortage_xlsx')
def download_shortage_xlsx():
    # DB設定
    inventory_config = DB_CONFIG["inventory"]
    unplanned_config = DB_CONFIG["unplanned-item"]

    # DBダウンロード
    download_db(inventory_config["filename"], inventory_config["url"])
    download_db(unplanned_config["filename"], unplanned_config["url"])

    # 在庫データ取得
    conn_inv = sqlite3.connect(inventory_config["filename"])
    cursor_inv = conn_inv.cursor()
    cursor_inv.execute("""
        SELECT 商品名, SUM(unit数) as 在庫unit数
        FROM inventory
        GROUP BY 商品名
    """)
    inventory_data = cursor_inv.fetchall()
    conn_inv.close()

    # 未プラン出荷データ取得
    conn_unp = sqlite3.connect(unplanned_config["filename"])
    cursor_unp = conn_unp.cursor()
    cursor_unp.execute("""
        SELECT 商品名, SUM(unit数) as 未プランunit数
        FROM unplanned
        GROUP BY 商品名
    """)
    unplanned_data = cursor_unp.fetchall()
    conn_unp.close()

    # 辞書化
    inventory_dict = {name: units for name, units in inventory_data}
    unplanned_dict = {name: units for name, units in unplanned_data}

    # 差分計算
    shortage_list = []
    for name, unplanned_units in unplanned_dict.items():
        inventory_units = inventory_dict.get(name, 0)
        diff = inventory_units - unplanned_units
        if diff < 0:
            shortage_list.append({
                "商品名": name,
                "在庫unit数": inventory_units,
                "未プランunit数": unplanned_units,
                "差分": diff
            })

    # Excel出力
    df = pd.DataFrame(shortage_list, columns=["商品名", "在庫unit数", "未プランunit数", "差分"])
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Shortage')
    output.seek(0)

    return send_file(output,
                     download_name="shortage_summary.xlsx",
                     as_attachment=True,
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

#当日出荷表
@app.route('/download_today-shipping_xlsx')
def download_today_xlsx():
    config = DB_CONFIG["today-shipping"]
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
                     download_name="today_shipping.xlsx",
                     as_attachment=True,
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
#翌日出荷表
@app.route('/download_tommorrow-shipping_xlsx')
def download_tommorrow_xlsx():
    config = DB_CONFIG["tommorrow-shipping"]
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
                     download_name="tommorrow-shipping.xlsx",
                     as_attachment=True,
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

#空きロケーション
@app.route('/download_empty-slot_xlsx')
def download_empty_slot_xlsx():
    config = DB_CONFIG["inventory"]
    download_db(config["filename"], config["url"])
    conn = sqlite3.connect(config["filename"])
    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT Location
        FROM {config['table']}
        WHERE 商品名 IS NULL OR TRIM(商品名) = ''
    """)
    rows = cursor.fetchall()
    conn.close()

    df = pd.DataFrame(rows, columns=["空きロケーション"])
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='EmptySlot')
    output.seek(0)
    return send_file(output,
                     download_name="empty_slot.xlsx",
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

#ルート:在庫
@app.route('/inventory')
def inventory():
    config = DB_CONFIG["inventory"]
    download_db(config["filename"], config["url"])
    summary = fetch_inventory_summary(config["filename"], config["table"])
    return render_template(config["template"], shipments=summary)

#未プラン在庫
@app.route('/unplanned-item')
def unplanned_item():
    config = DB_CONFIG["unplanned-item"]
    download_db(config["filename"], config["url"])
    data = fetch_data(config["filename"], config["table"])
    return render_template(config["template"], shipments=data)

#short
@app.route('/shortage')
def shortage():
    # DB設定
    inventory_config = DB_CONFIG["inventory"]
    unplanned_config = DB_CONFIG["unplanned-item"]

    # DBダウンロード
    download_db(inventory_config["filename"], inventory_config["url"])
    download_db(unplanned_config["filename"], unplanned_config["url"])

    # 在庫データ取得（商品名単位で合計）
    conn_inv = sqlite3.connect(inventory_config["filename"])
    cursor_inv = conn_inv.cursor()
    cursor_inv.execute("""
        SELECT 商品名, SUM(unit数) as 在庫unit数
        FROM inventory
        GROUP BY 商品名
    """)
    inventory_data = cursor_inv.fetchall()
    conn_inv.close()

    # 未プラン出荷データ取得（商品名単位で合計）
    conn_unp = sqlite3.connect(unplanned_config["filename"])
    cursor_unp = conn_unp.cursor()
    cursor_unp.execute("""
        SELECT 商品名, SUM(unit数) as 未プランunit数
        FROM unplanned
        GROUP BY 商品名
    """)
    unplanned_data = cursor_unp.fetchall()
    conn_unp.close()

    # データを辞書化
    inventory_dict = {name: units for name, units in inventory_data}
    unplanned_dict = {name: units for name, units in unplanned_data}

    # 差分計算（在庫 - 未プラン）でマイナスのものを抽出
    shortage_list = []
    for name, unplanned_units in unplanned_dict.items():
        inventory_units = inventory_dict.get(name, 0)
        diff = inventory_units - unplanned_units
        if diff < 0:
            shortage_list.append({
                "商品名": name,
                "在庫unit数": inventory_units,
                "未プランunit数": unplanned_units,
                "差分": diff
            })

    return render_template("short.html", shipments=shortage_list)
    
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

#空きロケーション
@app.route('/empty-slot')
def empty_slot():
    config = DB_CONFIG["inventory"]
    download_db(config["filename"], config["url"])
    conn = sqlite3.connect(config["filename"])
    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT Location AS 空きロケーション
        FROM {config['table']}
        WHERE 商品名 IS NULL OR TRIM(商品名) = ''
    """)
    rows = cursor.fetchall()
    conn.close()
    return render_template("empty_slot.html", shipments=[{"空きロケーション": r[0]} for r in rows])

#注文と注文商品ランキング
@app.route('/order_summary')
def order_summary():
    db_path = "注文.db"
    github_url = "https://raw.githubusercontent.com/SatoruMorishita/my-website/main/注文.db"
    table_name = "orders"

    # DBダウンロード
    download_db(db_path, github_url)

    # データ取得（表用）
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query(f"SELECT 商品カテゴリ, 注文時間, 商品名, Unit FROM {table_name}", conn)
    conn.close()

    # 注文集計表の処理
    df["注文日"] = pd.to_datetime(df["注文時間"]).dt.date
    pivot = pd.pivot_table(df, index="商品カテゴリ", columns="注文日", aggfunc="size", fill_value=0)
    table_html = pivot.to_html(classes="table table-bordered", border=0, index_names=False)

    # 売上ランキングの処理
    summary = df.groupby("商品名")["Unit"].sum().sort_values(ascending=True)
    top10 = summary.tail(10)

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(top10.index, top10.values, color="#4a90e2")
    ax.set_xlabel("Unit")
    ax.set_title("商品別売上ランキング（トップ10）")
    plt.tight_layout()

    buf = BytesIO()
    fig.savefig(buf, format="png")
    buf.seek(0)
    encoded = base64.b64encode(buf.getvalue()).decode("utf-8")
    graph_url = f"data:image/png;base64,{encoded}"

    # 両方渡す！
    return render_template("orders.html", table_html=table_html, graph_url=graph_url)

# ローカル実行
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
