from http.server import BaseHTTPRequestHandler
import json
import os
import requests

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Простое хранилище в памяти (для примера; на Vercel может сбрасываться при перезапуске инстанса)
user_states = {}

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8'))
        except Exception:
            self.send_response(400)
            self.end_headers()
            return

        # Обработка текстовых сообщений
        if "message" in data:
            chat_id = data["message"]["chat"]["id"]
            text = data["message"].get("text", "").strip()

            if str(chat_id) not in user_states:
                user_states[str(chat_id)] = {"step": "IDLE"}

            state = user_states[str(chat_id)]

            if text == "/start":
                state["step"] = "WAITING_FOR_QUERY"
                self.send_telegram_message(chat_id, "Привет! Что будем искать на Авито? Введи текст для поиска:")
            
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
                self.send_telegram_message(chat_id, "Выбери сортировку:", reply_markup=keyboard)

            elif state["step"] == "WAITING_FOR_LOCATION":
                state["location"] = text
                state["step"] = "WAITING_FOR_PRICE"
                self.send_telegram_message(chat_id, "Введи цену (например, до 50000 или диапазон):")

            elif state["step"] == "WAITING_FOR_PRICE":
                state["price"] = text
                state["step"] = "ACTIVE_SEARCH"
                
                # Сохраняем параметры поиска куда-нибудь или в файл/бд, чтобы парсер их видел
                self.save_user_config(chat_id, state)
                
                self.send_telegram_message(
                    chat_id, 
                    "✅ В активном поиске...\n\nПараметры сохранены. Как только появится новое объявление, бот пришлет его сюда."
                )

        # Обработка нажатий на кнопки (Callback Query)
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
                self.send_telegram_message(chat_id, "Выбери тип продавца:", reply_markup=keyboard)

            elif callback_data.startswith("seller_"):
                state["seller"] = callback_data.replace("seller_", "")
                state["step"] = "WAITING_FOR_LOCATION"
                self.send_telegram_message(chat_id, "Введи место (город или район):")

        self.send_response(200)
        self.end_headers()
        self.wfile.write(json.dumps({"ok": True}).encode('utf-8'))

    def send_telegram_message(self, chat_id, text, reply_markup=None):
        payload = {
            "chat_id": chat_id,
            "text": text
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup
        requests.post(f"{TELEGRAM_API_URL}/sendMessage", json=payload)

    def save_user_config(self, chat_id, state):
        # Здесь можно сохранять настройки пользователя в JSON-файл или базу данных,
        # чтобы скрипт парсинга на GitHub Actions мог их оттуда читать.
        os.makedirs("data", exist_ok=True)
        with open(f"data/user_{chat_id}.json", "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=4)
