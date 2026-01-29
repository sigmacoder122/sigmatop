import requests

# Конфигурационные данные
API_TOKEN = "GnwNIBe5n8TLdTDrIbjd"  # Замените на ваш API-ключ из ЛК
SERVICE_ID = 1  # ID сервиса (например: 1 - Telegram)
COUNTRY_ID = 1  # ID страны (например: 1 - Россия)
ACCOUNTS_COUNT = 1  # Количество аккаунтов для покупки

# Формируем запрос
url = "https://api.helper20sms.ru/api/v1/accounts/buy"
headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}
payload = {
    "service_id": SERVICE_ID,
    "country_id": COUNTRY_ID,
    "count": ACCOUNTS_COUNT
}

try:
    # Отправка запроса
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()

    # Обработка успешного ответа
    if response.status_code == 200:
        accounts = response.json()
        print(f"Успешно куплено {len(accounts)} аккаунтов:")
        for account in accounts:
            print(f"ID: {account['id']}")
            print(f"Телефон: {account['phone']}")
            print(f"Сервис: {account['service']}")
            print(f"Страна: {account['country']}")
            print(f"Дата создания: {account['created_at']}")
            print("-" * 30)
    else:
        print(f"Ошибка: {response.status_code}")
        print(response.json())

except requests.exceptions.RequestException as e:
    print(f"Ошибка соединения: {str(e)}")
except Exception as e:
    print(f"Неизвестная ошибка: {str(e)}")