from flask import Flask
from threading import Thread
import os
import json
import logging
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

app = Flask('')

@app.route('/')
def home():
    return "✅ Bixx همیشه بیداره :)"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

BOT_TOKEN = os.environ.get("BOT_TOKEN")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

CONV_FILE = "conversations.json"

def load_conversations():
    if os.path.exists(CONV_FILE):
        with open(CONV_FILE, "r") as f:
            return json.load(f)
    return {}

def save_conversations(data):
    with open(CONV_FILE, "w") as f:
        json.dump(data, f)

def ask_openrouter(user_id, prompt, history):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://render.com",
        "X-Title": "BixxBot"
    }

    system_msg = {
        "role": "system",
        "content": (
            "تو Bixx هستی. یه دوست واقعی، صمیمی، مهربون و همیشه در دسترس. "
            "مثل یه رفیق نزدیک حرف بزن، انسانی، همدل، و دلگرم‌کننده. "
            "همیشه یادته کاربر چی گفته و مکالمه‌ها رو ادامه می‌دی."
        )
    }

    messages = [system_msg] + history + [{"role": "user", "content": prompt}]
    data = {
        "model": "openai/gpt-3.5-turbo",
        "messages": messages
    }

    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return f"🥺 متأسفم، مشکلی پیش اومده. (کد خطا: {response.status_code})"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    user_id = str(update.message.chat_id)

    conversations = load_conversations()
    user_history = conversations.get(user_id, [])

    reply = ask_openrouter(user_id, user_text, user_history)

    user_history.append({"role": "user", "content": user_text})
    user_history.append({"role": "assistant", "content": reply})
    conversations[user_id] = user_history
    save_conversations(conversations)

    await update.message.reply_text(reply)

if __name__ == '__main__':
    keep_alive()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
