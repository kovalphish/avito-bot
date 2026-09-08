import os
import json
import base64
import requests
from fastapi import FastAPI, Request
from pydantic import BaseModel

app = FastAPI()

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TOKEN}"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")  # Токен GitHub для сохранения подписок в репозиторий
REPO_NAME = os.environ.get("GITHUB_REPO", "kovalphish/avito-bot-plq2") # Твой репозиторий

# Простая временная память состояний пользователей в памяти (или можно хранить в файле)
user_states = {}

class WebhookUpdate(BaseModel):
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
async def webhook(update: WebhookUpdate):
    if update.message:
        message = update.message
        chat_id = message["chat"]["id"]
        text = message.get("text", "").strip()
        
        # Команда /start
        if text == "/start":
            user_states[chat_id] = {"step": "waiting_query"}
            send_message(
                chat_id, 
                "👋 Привет! Я бот для мониторинга Авито.\n\n"
                "Что ты хочешь найти? (Например: <i>айфон</i>, <i>видеокарта rtx 3080</i>)"
            )
            return {"ok": True}
            
        # Логика пошагового ввода
        state = user_states.get(chat_id, {})
        step = state.get("step")
        
        if step == "waiting_query":
            state["query"] = text
            state["step"] = "waiting_max_price"
            send_message(chat_id, f"Отлично, ищем: <b>{text}</b>.\n\nТеперь введи <b>максимальную сумму</b> в рублях (только число, например: <i>50000</i>):")
            
        elif step == "waiting_max_price":
            state["max_price"] = text
            state["step"] = "waiting_location"
            send_message(chat_id, "Принято. Теперь укажи <b>место / город</b> (например: <i>Москва</i>):")
            
        elif step == "waiting_location":
            state["location"] = text
            state["step"] = None
            
            # Сохраняем подписку
            save_subscription(chat_id, state["query"], state["max_price"], state["location"])
            
            send_message(
                chat_id, 
                f"✅ <b>Подписка успешно создана!</b>\n\n"
                f"🔍 Товар: {state['query']}\n"
                f"💰 До: {state['max_price']} ₽\n"
                f"📍 Место: {state['location']}\n\n"
                f"Я жду новое объявление и пришлю его сразу, как только оно появится!"
            )
            
    return {"ok": True}

def save_subscription(chat_id, query, max_price, location):
    """Сохраняет подписку пользователя в JSON-файл на GitHub"""
    if not GITHUB_TOKEN:
        print("GitHub token missing!")
        return

    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }
    
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/subscriptions.json"
    
    # Получаем текущий файл
    res = requests.get(url, headers=headers)
    subs = []
    sha = None
    
    if res.status_code == 200:
        file_data = res.json()
        sha = file_data["sha"]
        content = base64.b64decode(file_data["content"]).decode("utf-8")
        try:
            subs = json.loads(content)
        except:
            subs = []
            
    # Добавляем новую подписку (или обновляем старую для этого chat_id)
    # Удаляем старую для чистоты
    subs = [s for s in subs if s.get("chat_id") != chat_id]
    subs.append({
        "chat_id": chat_id,
        "query": query,
        "max_price": max_price,
        "location": location,
        "notified_ads": [] # Список уже отправленных ID объявлений, чтобы не спамить повторами
    })
    
    new_content = base64.b64encode(json.dumps(subs, ensure_ascii=False, indent=2).encode("utf-8")).decode("utf-8")
    
    data = {
        "message": f"Update subscription for {chat_id}",
        "content": new_content,
        "sha": sha
    }
    requests.put(url, headers=headers, json=data)

# Эндпоинт, который вызывает GitHub Actions, когда находит подходящее объявление для конкретного пользователя
class NotificationPayload(BaseModel):
    chat_id: int
    title: str
    price: str
    location: str
    url: str
    photo_url: str

@app.post("/api/notify-user")
async def notify_user(payload: NotificationPayload):
    caption = (
        f"🚨 <b>Найдено новое объявление!</b>\n\n"
        f"<b>{payload.title}</b>\n\n"
        f"💰 <b>Цена:</b> {payload.price}\n"
        f"📍 <b>Место:</b> {payload.location}\n\n"
        f"<a href='{payload.url}'>Открыть объявление на Авито</a>"
    )
    send_photo(payload.chat_id, payload.photo_url, caption)
    return {"status": "notified"}
