from flask import Flask, request
import os
import requests
from dotenv import load_dotenv
from openai import OpenAI

# .envを読み込む
load_dotenv()

# 環境変数の読み込み
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# FlaskアプリとOpenAIクライアントの初期化
app = Flask(__name__)
client = OpenAI(api_key=OPENAI_API_KEY)

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    print("📩 受信データ:", data)

    if data is None or "events" not in data:
        return "Bad Request", 400

    for event in data["events"]:
        if event["type"] == "message" and event["message"]["type"] == "text":
            user_text = event["message"]["text"]
            reply_token = event["replyToken"]

            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
    {
        "role": "system",
        "content": (
            "あなたは旅行とクレジットカードに詳しい専門家です。\n"
            "旅行（国内・海外）やポイント、マイル、クレジットカードに関する質問のみに答えてください。\n"
            "それ以外の話題（芸能、政治、医療、時事、雑談など）には、\n"
            "『申し訳ありません、その話題にはお答えできません』とだけ返答してください。\n"
            "絶対にルールを破らず、他の話題には絶対に答えないでください。"
        )
    },
    {"role": "user", "content": user_text}
]
                )
                reply_message = response.choices[0].message.content
                print("🤖 GPTの返答:", reply_message)

                send_line_reply(reply_token, reply_message)

            except Exception as e:
                import traceback
                print("❌ GPTエラー:", e)
                traceback.print_exc()
                send_line_reply(reply_token, "ごめんなさい、GPTとの通信でエラーが発生しました💦")

    return "OK", 200  # ← この位置が正解！

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
        print("📤 LINE送信ステータス:", res.status_code, res.text)
    except Exception as e:
        print("❌ LINE返信エラー:", e)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
