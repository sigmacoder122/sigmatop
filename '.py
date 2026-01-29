import requests

API_KEY = '01973541-27b6-7000-a9cb-a62d42a6a9df'
URL_BUY_NUMBER = 'https://api.greedy-sms.com/v1/number/buy'

def buy_number(country: str, operator: str = None):
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }

    payload = {
        'country': country
    }

    # Если нужно указать оператора, добавляем в payload
    if operator:
        payload['operator'] = operator

    response = requests.post(URL_BUY_NUMBER, json=payload, headers=headers)

    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            print('Номер успешно куплен!')
            print('Данные номера:', data.get('number'))
            return data.get('number')
        else:
            print('Ошибка API:', data.get('error'))
    else:
        print(f'HTTP ошибка {response.status_code}:', response.text)

if __name__ == '__main__':
    # Пример: покупка номера в России
    country_code = 'RU'  # Код страны в формате ISO 3166-1 alpha-2
    operator_name = None  # Можно указать оператор, если нужно

    buy_number(country_code, operator_name)
