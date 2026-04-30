import asyncio
import logging
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
import aiosqlite
from fastapi import FastAPI, HTTPException, Request
import uvicorn

# === НАСТРОЙКИ ===
BOT_TOKEN = "8311389856:AAGp1Cdb8Yejr8yPgNfH9YBiGOeT-CKr9-A"
ADMIN_ID = 7658738825 # Твой личный ID в Telegram (можно узнать через @userinfobot)
CHANNEL_ID = "@eelge"  # Канал, на который нужно подписаться

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
app = FastAPI()

# === БАЗА ДАННЫХ ===
async def init_db():
    async with aiosqlite.connect('database.db') as db:
        # Таблица пользователей
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                sub_deadline TIMESTAMP
            )
        ''')
        await db.commit()

# === ЛОГИКА БОТА (aiogram) ===

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    # Записываем юзера в базу, когда он жмет /start
    async with aiosqlite.connect('database.db') as db:
        await db.execute(
            'INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)',
            (message.from_user.id, message.from_user.username)
        )
        await db.commit()

    await message.answer("Привет! Открой приложение, чтобы трекать привычки.",
                         reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                             [types.InlineKeyboardButton(text="Открыть App", web_app=types.WebAppInfo(url="https://tvoi-sayt.com"))]
                         ]))

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Разрешаем запросы с любых сайтов (твоего React-аппа)
    allow_methods=["*"],
    allow_headers=["*"],
)
# Команда админа: /stats (Статистика)
@dp.message(Command("stats"), F.from_user.id == ADMIN_ID)
async def admin_stats(message: types.Message):
    async with aiosqlite.connect('database.db') as db:
        async with db.execute('SELECT COUNT(*) FROM users') as cursor:
            count = await cursor.fetchone()
    await message.answer(f"📊 Всего пользователей в базе: {count[0]}")

# Команда админа: /broadcast Текст (Рассылка)
@dp.message(Command("broadcast"), F.from_user.id == ADMIN_ID)
async def admin_broadcast(message: types.Message):
    text = message.text.replace("/broadcast ", "")
    if not text or text == "/broadcast":
        return await message.answer("Напиши текст: /broadcast Привет всем!")

    async with aiosqlite.connect('database.db') as db:
        async with db.execute('SELECT user_id FROM users') as cursor:
            users = await cursor.fetchall()

    count = 0
    for row in users:
        try:
            await bot.send_message(chat_id=row[0], text=text)
            count += 1
        except Exception:
            pass # Если юзер заблокировал бота

    await message.answer(f"✅ Рассылка завершена. Доставлено: {count} чел.")

# Команда админа: /add @username 6 (Обязательная подписка)
@dp.message(Command("add"), F.from_user.id == ADMIN_ID)
async def admin_add_sub(message: types.Message):
    args = message.text.split()
    if len(args) != 3:
        return await message.answer("Формат: /add @username 6")

    target_username = args[1].replace("@", "")
    hours = int(args[2])
    deadline = datetime.now() + timedelta(hours=hours)

    async with aiosqlite.connect('database.db') as db:
        await db.execute('UPDATE users SET sub_deadline = ? WHERE username = ?', (deadline, target_username))
        await db.commit()

    await message.answer(f"🔒 Пользователь @{target_username} должен быть подписан на {CHANNEL_ID} до {deadline.strftime('%Y-%m-%d %H:%M')}")

# === ЛОГИКА СЕРВЕРА ДЛЯ REACT (FastAPI) ===

@app.post("/api/check_access")
async def check_access(request: Request):
    data = await request.json()
    user_id = data.get("user_id")

    async with aiosqlite.connect('database.db') as db:
        async with db.execute('SELECT sub_deadline FROM users WHERE user_id = ?', (user_id,)) as cursor:
            user = await cursor.fetchone()

    if not user or not user[0]:
        return {"status": "ok"} # Нет ограничений

    deadline = datetime.fromisoformat(user[0])
    if datetime.now() < deadline:
        # Время еще есть, проверяем подписку через бота
        try:
            member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
            if member.status in ["left", "kicked"]:
                return {"status": "error", "message": "unsubscribed", "channel": CHANNEL_ID}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    return {"status": "ok"}

# === ЗАПУСК ===
async def main():
    await init_db()
    # Запускаем FastAPI сервер (для React) в фоне
    config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(config)
    asyncio.create_task(server.serve())

    # Запускаем бота
    print("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())