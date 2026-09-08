from flask import Flask, request
import os
import requests

app = Flask(__name__)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Временное хранилище состояний
user_states = {}

@app.route("/", methods=["POST"])
def webhook():
    data = request.get_json(silent=True)
    if not data:
        return {"ok": True}

    # Обработка текстовых сообщений
    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "").strip()

        if str(chat_id) not in user_states:
            user_states[str(chat_id)] = {"step": "IDLE"}

        state = user_states[str(chat_id)]

        if text == "/start":
            state["step"] = "WAITING_FOR_QUERY"
            send_telegram_message(chat_id, "Привет! Что будем искать на Авито? Введи текст для поиска:")
        
        elif state["step"] == "WAITING_FOR_QUERY":
            state["query"] = text
            state["step"] = "WAITING_FOR_SORT"
            
            keyboard = {
                "inline_keyboard": [
                    [{"text": "📅 По дате (свежие)", "callback_data": "sort_date"}],
                    [{"text": "📈 По цене (возрастание)", "callback_data": "sort_price_asc"}],
                    [{"text": "📉 По цене (убывание)", "callback_data": "sort_price_desc"}]
                ]
            }
            send_telegram_message(chat_id, "Выбери сортировку:", reply_markup=keyboard)

        elif state["step"] == "WAITING_FOR_LOCATION":
            state["location"] = text
            state["step"] = "WAITING_FOR_PRICE"
            send_telegram_message(chat_id, "Введи цену (например, до 50000 или диапазон):")

        elif state["step"] == "WAITING_FOR_PRICE":
            state["price"] = text
            state["step"] = "ACTIVE_SEARCH"
            send_telegram_message(
                chat_id, 
                "✅ В активном поиске...\n\nПараметры приняты. Как только появится новое объявление, бот пришлет его сюда."
            )

    # Обработка нажатий на инлайн-кнопки
    elif "callback_query" in data:
        cb = data["callback_query"]
        chat_id = cb["message"]["chat"]["id"]
        callback_data = cb["data"]

        if str(chat_id) not in user_states:
            user_states[str(chat_id)] = {"step": "IDLE"}

        state = user_states[str(chat_id)]

        if callback_data.startswith("sort_"):
            state["sort"] = callback_data.replace("sort_", "")
            state["step"] = "WAITING_FOR_SELLER"

            keyboard = {
                "inline_keyboard": [
                    [{"text": "👤 Частные", "callback_data": "seller_private"}],
                    [{"text": "🏢 Компании", "callback_data": "seller_company"}],
                    [{"text": "🤝 Все", "callback_data": "seller_all"}]
                ]
            }
            send_telegram_message(chat_id, "Выбери тип продавца:", reply_markup=keyboard)

        elif callback_data.startswith("seller_"):
            state["seller"] = callback_data.replace("seller_", "")
            state["step"] = "WAITING_FOR_LOCATION"
            send_telegram_message(chat_id, "Введи место (город или район):")

    return {"ok": True}

def send_telegram_message(chat_id, text, reply_markup=None):
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    requests.post(f"{TELEGRAM_API_URL}/sendMessage", json=payload)
