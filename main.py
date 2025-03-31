from flask import Flask, request
import os
import requests
from dotenv import load_dotenv
from openai import OpenAI

# 環境変数の読み込み
load_dotenv()

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)
client = OpenAI(api_key=OPENAI_API_KEY)

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    print("📩 LINEから受信：", data)

    if data is None or "events" not in data:
        return "Bad Request", 400

    for event in data["events"]:
        if event["type"] == "message" and event["message"]["type"] == "text":
            user_text = event["message"]["text"]
            reply_token = event["replyToken"]

try:
    # GPTで返信を生成
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": "あなたは旅行とポイントに詳しい明るく親しみやすいお姉さんです。"
            },
            {"role": "user", "content": user_text}
        ]
    )
    reply_message = response.choices[0].message.content
    print("🤖 GPTの返答：", reply_message)

    send_line_reply(reply_token, reply_message)

except Exception as e:
    import traceback
    print("❌ GPTエラー：", e)
    traceback.print_exc()
    send_line_reply(reply_token, "ごめんなさい、GPTとの通信でエラーが発生しました💦")

    return "OK", 200

def send_line_reply(reply_token, text):
    headers = {
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "replyToken": reply_token,
        "messages": [{"type": "text", "text": text}]
    }

    try:
        res = requests.post("https://api.line.me/v2/bot/message/reply", headers=headers, json=payload)
        print("📤 LINE送信ステータス：", res.status_code, res.text)
    except Exception as e:
        print("❌ LINE返信エラー：", e)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
