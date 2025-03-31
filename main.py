from flask import Flask, request
import openai
import os
import requests
from dotenv import load_dotenv

load_dotenv()
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)
openai.api_key = OPENAI_API_KEY

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json

    for event in data["events"]:
        if event["type"] == "message" and event["message"]["type"] == "text":
            user_text = event["message"]["text"]
            reply_token = event["replyToken"]

            # GPTで返信を生成
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "あなたは旅行とポイントに詳しい明るいお姉さんです。フレンドリーな口調で返答してください。"},
                    {"role": "user", "content": user_text}
                ]
            )
            reply_message = response["choices"][0]["message"]["content"]
            send_line_reply(reply_token, reply_message)

    return "OK"

def send_line_reply(reply_token, text):
    headers = {
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "replyToken": reply_token,
        "messages": [{"type": "text", "text": text}]
    }
    requests.post("https://api.line.me/v2/bot/message/reply", headers=headers, json=payload)

if __name__ == "__main__":
    app.run(port=5000)
