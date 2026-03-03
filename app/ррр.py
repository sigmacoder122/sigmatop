import telebot
import requests

# --- НАСТРОЙКИ (Замените на свои данные) ---
BOT_TOKEN = '8730929027:AAFvBfgHiDZSpUh1ybh2A5hQXPDdVPWMTxM'
MERCHANT_ID = 'de2ca737-2c78-4f6b-b213-8179c25ea4bf'
API_SECRET = 'u5jYRfAaWUGs2lxibMm3ostWyAiMFpEgKTGIw7xuA46lATQBEqIw5EUldTiqBg2K23S3gys8dbBlqQzb6YIEzfJ5hgX7oocyNGFI'

PLATEGA_API_URL = 'https://app.platega.io/transaction/process'

bot = telebot.TeleBot(BOT_TOKEN)


def create_platega_invoice(amount, chat_id):
    """
    Создает транзакцию в Platega API и возвращает ссылку на оплату.
    """
    headers = {
        'X-MerchantId': MERCHANT_ID,
        'X-Secret': API_SECRET,
        'Content-Type': 'application/json'
    }

    # Формируем тело запроса строго по документации Platega
    payload = {
        "paymentMethod": 2,  # 2 - оплата по QR СБП
        "paymentDetails": {
            "amount": amount,
            "currency": "RUB"
        },
        "description": f"Оплата заказа через Telegram бота. Чат ID: {chat_id}",
        # Опционально: куда вернуть пользователя после оплаты
        # "return": "https://t.me/ТвойЮзернеймБота",
        "payload": str(chat_id)  # Доп. информация, например, ID пользователя
    }

    try:
        response = requests.post(PLATEGA_API_URL, json=payload, headers=headers)
        response.raise_for_status()  # Бросит ошибку, если статус не 200 ОК

        data = response.json()

        # Согласно документации, ссылка для оплаты лежит в поле "redirect"
        payment_url = data.get('redirect')

        return payment_url

    except requests.exceptions.RequestException as e:
        print(f"Ошибка при обращении к API Platega: {e}")
        if e.response is not None:
            print(f"Ответ сервера: {e.response.text}")  # Для отладки в консоли
        return None


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Отправь мне сумму числом, и я пришлю тебе чек (ссылку на оплату через СБП).")


@bot.message_handler(func=lambda message: True)
def handle_amount_input(message):
    try:
        # Меняем запятую на точку, если юзер ввел дробное число (например, 150,50)
        amount = float(message.text.replace(',', '.'))

        if amount <= 0:
            bot.reply_to(message, "Сумма должна быть больше нуля.")
            return

        bot.reply_to(message, "⏳ Создаю транзакцию...")

        # Вызываем функцию создания платежа
        payment_link = create_platega_invoice(amount, message.chat.id)

        if payment_link:
            bot.reply_to(message, f"✅ Ссылка на оплату успешно создана!\n\n💳 Оплатить: {payment_link}")
        else:
            bot.reply_to(message, "❌ Произошла ошибка на стороне платежной системы. Попробуй позже.")

    except ValueError:
        # Если юзер ввел текст вместо числа
        bot.reply_to(message, "Пожалуйста, введи корректную сумму числом (например, 500 или 1500.50).")


if __name__ == '__main__':
    print("Бот запущен и ждет сообщений...")
    bot.infinity_polling()