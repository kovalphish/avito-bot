import os
import requests
import json
from glob import glob

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

def send_item(chat_id, item):
    # Отправка карточки товара пользователю: фото, название, описание, место, цена
    caption = (
        f"<b>{item.get('title')}</b>\n\n"
        f"💰 Цена: {item.get('price')}\n"
        f"📍 Место: {item.get('location')}\n\n"
        f"{item.get('description')}"
    )
    
    payload = {
        "chat_id": chat_id,
        "caption": caption,
        "parse_mode": "HTML"
    }
    
    image_url = item.get('image')
    if image_url:
        payload["photo"] = image_url
        requests.post(f"{TELEGRAM_API_URL}/sendPhoto", json=payload)
    else:
        payload["text"] = caption
        requests.post(f"{TELEGRAM_API_URL}/sendMessage", json=payload)

def main():
    print("Запуск проверки объявлений...")
    
    # Ищем сохраненные настройки пользователей
    user_files = glob("data/user_*.json")
    if not user_files:
        print("Активных поисков не найдено.")
        return

    for file_path in user_files:
        with open(file_path, "r", encoding="utf-8") as f:
            user_data = json.load(f)
            
        if user_data.get("step") == "ACTIVE_SEARCH":
            chat_id = file_path.split("_")[-1].replace(".json", "")
            
            # Твоя логика запроса к Авито по параметрам:
            # user_data["query"], user_data["sort"], user_data["seller"], user_data["location"], user_data["price"]
            
            # Пример имитации найденного нового объявления:
            # new_item = parse_avito(user_data)
            # if new_item:
            #     send_item(chat_id, new_item)

if __name__ == "__main__":
    main()
