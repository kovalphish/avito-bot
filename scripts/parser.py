import os
import json
import requests

VERCEL_NOTIFY_URL = "https://avito-bot-plq2.vercel.app/api/notify-user"

def run_parser():
    # Путь к файлу подписок в репозитории (или скачиваем его через raw.githubusercontent.com)
    subs_url = "https://raw.githubusercontent.com/kovalphish/avito-bot-plq2/main/subscriptions.json"
    
    try:
        res = requests.get(subs_url)
        if res.status_code != 200:
            print("No subscriptions file found.")
            return
        subscriptions = res.json()
    except Exception as e:
        print(f"Error loading subscriptions: {e}")
        return

    for sub in subscriptions:
        chat_id = sub["chat_id"]
        query = sub["query"]
        max_price = sub["max_price"]
        location = sub["location"]
        
        print(f"Checking for user {chat_id}: query='{query}', max_price={max_price}, location={location}")
        
        # --- ЗДЕСЬ БУДЕТ ЛОГИКА ПОИСКА ПО АВИТО ---
        # (Скрипт делает запрос к поиску Авито по параметрам query, max_price, location)
        # Если найдено новое объявление, которого нет в sub["notified_ads"], отправляем его:
        
        # Пример найденного объявления (тест):
        # found_ad = {
        #     "chat_id": chat_id,
        #     "title": f"Айфон по вашему запросу ({query})",
        #     "price": f"{max_price} ₽",
        #     "location": location,
        #     "url": "https://www.avito.ru",
        #     "photo_url": "https://avatars.mds.yandex.net/get-altay/237406/2a0000015afa3fde5bc803e1e69b5e39486c/orig"
        # }
        # requests.post(VERCEL_NOTIFY_URL, json=found_ad)

if __name__ == "__main__":
    run_parser()