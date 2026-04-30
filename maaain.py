import asyncio
import logging
import os
from datetime import datetime, timedelta

import aiosqlite
import uvicorn
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

# === НАСТРОЙКИ ===
BOT_TOKEN = "8311389856:AAGp1Cdb8Yejr8yPgNfH9YBiGOeT-CKr9-A"
ADMIN_ID = 7658738825
CHANNEL_ID = "@eelge"
RENDER_URL = "https://sigmatop.onrender.com"  # Проверь, что это твой URL в Render

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
app = FastAPI()

# Разрешаем запросы от твоего React-приложения
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# === БАЗА ДАННЫХ ===
async def init_db():
    async with aiosqlite.connect('database.db') as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                sub_deadline TIMESTAMP
            )
        ''')
        await db.commit()


# === ЛОГИКА БОТА ===

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    async with aiosqlite.connect('database.db') as db:
        await db.execute(
            'INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)',
            (message.from_user.id, message.from_user.username)
        )
        await db.commit()
    await message.answer("Бот и приложение готовы к работе!")


@dp.message(Command("stats"), F.from_user.id == ADMIN_ID)
async def admin_stats(message: types.Message):
    async with aiosqlite.connect('database.db') as db:
        async with db.execute('SELECT COUNT(*) FROM users') as cursor:
            count = await cursor.fetchone()
    await message.answer(f"📊 Юзеров в базе: {count[0]}")


@dp.message(Command("add"), F.from_user.id == ADMIN_ID)
async def admin_add_sub(message: types.Message):
    args = message.text.split()
    if len(args) != 3:
        return await message.answer("Формат: /add @username 6")
    target_username = args[1].replace("@", "")
    hours = int(args[2])
    deadline = (datetime.now() + timedelta(hours=hours)).isoformat()
    async with aiosqlite.connect('database.db') as db:
        await db.execute('UPDATE users SET sub_deadline = ? WHERE username = ?', (deadline, target_username))
        await db.commit()
    await message.answer(f"✅ Ограничение для @{target_username} установлено.")


# === API И САМОПИНГ ===

@app.get("/")
async def root():
    return {"status": "working", "info": "Habit Tracker Backend"}


@app.post("/api/check_access")
async def check_access(request: Request):
    data = await request.json()
    user_id = data.get("user_id")
    async with aiosqlite.connect('database.db') as db:
        async with db.execute('SELECT sub_deadline FROM users WHERE user_id = ?', (user_id,)) as cursor:
            user = await cursor.fetchone()
    if not user or not user[0]:
        return {"status": "ok"}

    deadline = datetime.fromisoformat(user[0])
    if datetime.now() < deadline:
        try:
            member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
            if member.status in ["left", "kicked"]:
                return {"status": "error", "message": "unsubscribed", "channel": CHANNEL_ID}
        except:
            pass
    return {"status": "ok"}


async def self_ping():
    import aiohttp
    await asyncio.sleep(10)  # Даем серверу загрузиться
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(RENDER_URL) as resp:
                    logging.info(f"Ping status: {resp.status}")
        except Exception as e:
            logging.error(f"Ping failed: {e}")
        await asyncio.sleep(600)  # 10 минут


# === ЗАПУСК ===
async def main():
    await init_db()
    port = int(os.environ.get("PORT", 8000))
    config = uvicorn.Config(app, host="0.0.0.0", port=port)
    server = uvicorn.Server(config)

    asyncio.create_task(server.serve())
    asyncio.create_task(self_ping())

    print("Бот и сервер запущены!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())