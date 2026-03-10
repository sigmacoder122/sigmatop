import asyncio
import uuid
import aiohttp
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

# --- КОНФИГУРАЦИЯ ---
BOT_TOKEN = "8730929027:AAFvBfgHiDZSpUh1ybh2A5hQXPDdVPWMTxM"  # Токен бота от @BotFather
CACTUS_TOKEN = "4abbe943eeead14e06bb2821"  # Ваш секретный ключ магазина CactusPay

# Предполагаемый URL для создания платежа.
# Сверьтесь с вашей документацией, возможно там просто https://lk.cactuspay.pro/api/
CACTUS_API_URL = "https://lk.cactuspay.pro/api/?method=create"
# --------------------

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()


@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "👋 Привет! Я бот для оплаты.\n\n"
        "Просто отправь мне сумму (числом), на которую хочешь пополнить баланс или совершить покупку."
    )


@dp.message(F.text)
async def process_amount(message: Message):
    # 1. Проверяем, ввел ли пользователь корректное число
    try:
        amount = float(message.text.replace(",", "."))
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer("⚠️ Пожалуйста, отправьте корректную сумму (например: 150 или 150.50).")
        return

    # 2. Генерируем уникальный order_id для нашей системы
    order_id = str(uuid.uuid4())

    # 3. Подготавливаем данные для CactusPay API
    payload = {
        "token": CACTUS_TOKEN,
        "order_id": order_id,
        "amount": amount,
        "description": f"Оплата от пользователя {message.from_user.id}"
        # "method": "sbp" # Раскомментируйте и укажите метод, если хотите зафиксировать способ оплаты
    }

    # 4. Отправляем запрос на создание платежа
    msg = await message.answer("⏳ Создаю ссылку на оплату...")

    async with aiohttp.ClientSession() as session:
        try:
            # Используем JSON для отправки данных (или data=payload, если API требует form-data)
            async with session.post(CACTUS_API_URL, json=payload) as response:
                result = await response.json()

                # 5. Обрабатываем ответ от API
                if result.get("status") == "success":
                    payment_url = result["response"]["url"]

                    # Создаем инлайн-кнопку с ссылкой
                    keyboard = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="💳 Оплатить", url=payment_url)]
                    ])

                    await msg.edit_text(
                        f"✅ <b>Счет успешно создан!</b>\n\n"
                        f"<b>Сумма:</b> {amount} руб.\n"
                        f"<b>Номер заказа:</b> <code>{order_id}</code>\n\n"
                        f"Нажмите на кнопку ниже, чтобы перейти к оплате.",
                        reply_markup=keyboard
                    )
                else:
                    await msg.edit_text(
                        "❌ Произошла ошибка на стороне платежной системы.\n"
                        f"Детали: {result.get('message', 'Неизвестная ошибка')}"
                    )
        except Exception as e:
            await msg.edit_text(f"❌ Ошибка соединения с платежным шлюзом: {e}")


async def main():
    print("Бот запущен!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())