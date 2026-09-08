import os
import requests
from fastapi import FastAPI, Request
from pydantic import BaseModel

app = FastAPI()

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TOKEN}"

# Временное хранилище пользовательских фильтров (в реальном проекте лучше использовать БД вроде Supabase/Firebase)
user_filters = {}

class TelegramUpdate(BaseModel):
    update_id: int
    message: dict = None
    callback_query: dict = None

def send_message(chat_id: int, text: str, reply_markup: dict = None):
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    requests.post(f"{TELEGRAM_API_URL}/sendMessage", json=payload)

def send_photo(chat_id: int, photo_url: str, caption: str, reply_markup: dict = None):
    payload = {"chat_id": chat_id, "photo": photo_url, "caption": caption, "parse_mode": "HTML"}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    requests.post(f"{TELEGRAM_API_URL}/sendPhoto", json=payload)

@app.post("/")
async def webhook(update: TelegramUpdate):
    # Обработка нажатий на инлайн-кнопки
    if update.callback_query:
        callback = update.callback_query
        chat_id = callback["message"]["chat"]["id"]
        data = callback["data"]
        
        if data == "set_query":
            send_message(chat_id, "Введите ключевое слово для поиска (например: <code>Lada Priora</code>):")
        elif data == "set_price":
            send_message(chat_id, "Введите максимальную сумму (например: <code>350000</code>):")
        elif data == "set_location":
            send_message(chat_id, "Введите город или регион (например: <code>Челябинск</code>):")
        return {"ok": True}

    # Обработка обычных текстовых сообщений
    if update.message:
        message = update.message
        chat_id = message["chat"]["id"]
        text = message.get("text", "")
        
        if text == "/start":
            keyboard = {
                "inline_keyboard": [
                    [{"text": "🔍 Что искать", "callback_data": "set_query"}],
                    [{"text": "💰 Макс. сумма", "callback_data": "set_price"}],
                    [{"text": "📍 Место", "callback_data": "set_location"}]
                ]
            }
            send_message(
                chat_id, 
                "Привет! Это бот мониторинга Авито.\nНастрой параметры поиска с помощью кнопок ниже:", 
                reply_markup=keyboard
            )
        else:
            # Логика сохранения введенных пользователем данных
            # Здесь можно определить, что именно ввёл пользователь (сумму, категорию или место) и записать в user_filters[chat_id]
            send_message(chat_id, f"Параметр сохранен: <b>{text}</b>. Поиск активирован!")
            
    return {"ok": True}

# Функция-триггер (можно вызывать по расписанию через внешние сервисы вроде Cron-job.org)
@app.get("/api/check-avito")
async def check_avito():
    # Сдесь реализуется запрос к поисковой выдаче Авито по сохраненным фильтрам пользователей.
    # Если найдено новое объявление, оно отправляется в Telegram:
    
    # Пример отправки карточки объявления:
    # sample_chat_id = 123456789
    # photo = "https://avatars.mds.yandex.net/get-altay/..."
    # caption = "<b>Название:</b> Lada Priora Люкс\n<b>Цена:</b> 350 000 ₽\n<b>Место:</b> Челябинск\n<a href='https://avito.ru/...'>Ссылка на объявление</a>"
    # send_photo(sample_chat_id, photo, caption)
    
    return {"status": "checked"}