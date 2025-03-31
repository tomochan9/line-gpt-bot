from flask import Flask, request
import os
import requests
from dotenv import load_dotenv
from openai import OpenAI
import pickle
import numpy as np
import faiss

# .envを読み込む
load_dotenv()

# 環境変数の読み込み
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# FlaskアプリとOpenAIクライアントの初期化
app = Flask(__name__)
client = OpenAI(api_key=OPENAI_API_KEY)

# ベクトルデータの読み込み
with open("vector_store.pkl", "rb") as f:
    vector_data = pickle.load(f)
    index = vector_data["index"]
    texts = vector_data["texts"]

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
                # ユーザーの質問をベクトル化
                embedding_response = client.embeddings.create(
                    input=user_text,
                    model="text-embedding-3-small"
                )
                query_vector = np.array(embedding_response.data[0].embedding).astype("float32")

                # ベクトル検索（類似度の高い情報を1件取得）
                D, I = index.search(np.array([query_vector]), k=1)
                similar_text = texts[I[0][0]] if I[0][0] < len(texts) else ""

                print("🔍 類似した知識:", similar_text)  # ← 追加

                # GPTに質問 + 検索結果を渡す
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "あなたは旅行とクレジットカードに詳しい専門家です。\n"
                                "以下の参考知識のみを元に、絶対にその内容に基づいて回答してください。\n"
                                "その他の知識や想像では一切答えないでください。\n"
                                "参考知識:\n" + similar_text
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
        print("📤 LINE送信ステータス:", res.status_code, res.text)
    except Exception as e:
        print("❌ LINE返信エラー:", e)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)