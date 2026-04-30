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
RENDER_URL = "https://sigmatop-7.onrender.com"  # Твой актуальный URL

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
app = FastAPI()

# Разрешаем CORS для React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
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


# === API ЭНДПОИНТЫ ===

@app.get("/")
async def root():
    return {"status": "working", "info": "Habit Tracker Backend"}


# Тот самый эндпоинт для проверки связи из профиля
@app.get("/api/ping")
async def ping_test():
    return {"message": "Связь с Python установлена! Сервер SigmaTop активен. 🚀"}


@app.post("/api/check_access")
async def check_access(request: Request):
    try:
        data = await request.json()
        user_id = data.get("user_id")

        # 1. Проверяем подписку на канал обязательно
        try:
            member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
            if member.status in ["left", "kicked"]:
                return {"status": "error", "message": "unsubscribed"}
        except Exception as e:
            logging.error(f"TG API Error: {e}")
            # Если не можем проверить (бот не админ), пропускаем
            pass

        # 2. Проверяем временные ограничения из БД (если есть)
        async with aiosqlite.connect('database.db') as db:
            async with db.execute('SELECT sub_deadline FROM users WHERE user_id = ?', (user_id,)) as cursor:
                user = await cursor.fetchone()

        if user and user[0]:
            deadline = datetime.fromisoformat(user[0])
            if datetime.now() > deadline:
                return {"status": "error", "message": "expired"}

        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# === ЛОГИКА БОТА ===

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    async with aiosqlite.connect('database.db') as db:
        await db.execute(
            'INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)',
            (message.from_user.id, message.from_user.username)
        )
        await db.commit()
    await message.answer("✅ Бот SigmaTop подключен к приложению!")


# === ЗАПУСК ===

async def self_ping():
    import aiohttp
    await asyncio.sleep(10)
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(RENDER_URL) as resp:
                    logging.info(f"Self-ping: {resp.status}")
        except:
            pass
        await asyncio.sleep(600)


async def main():
    await init_db()
    port = int(os.environ.get("PORT", 8000))
    config = uvicorn.Config(app, host="0.0.0.0", port=port)
    server = uvicorn.Server(config)

    # Запускаем сервер, самопинг и бота параллельно
    await asyncio.gather(
        server.serve(),
        self_ping(),
        dp.start_polling(bot)
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Stopped")