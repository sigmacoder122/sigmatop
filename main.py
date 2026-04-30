import asyncio
import logging
import os
from datetime import datetime, timedelta

import aiosqlite
import uvicorn
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

# === НАСТРОЙКИ ===
BOT_TOKEN = "8311389856:AAGp1Cdb8Yejr8yPgNfH9YBiGOeT-CKr9-A"
ADMIN_ID = 7658738825
RENDER_URL = "https://sigmatop-7.onrender.com"

# Включаем HTML-разметку по умолчанию для красивого текста
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# === СОСТОЯНИЯ ДЛЯ РАССЫЛКИ ===
class BroadcastState(StatesGroup):
    waiting_for_message = State()


# === БАЗА ДАННЫХ ===
async def init_db():
    async with aiosqlite.connect('database.db') as db:
        # Таблица юзеров
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                habits_count INTEGER DEFAULT 0,
                joined_date DATE DEFAULT CURRENT_DATE
            )
        ''')
        # Таблица каналов для проверки подписки
        await db.execute('''
            CREATE TABLE IF NOT EXISTS sponsors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_username TEXT,
                expires_at TIMESTAMP
            )
        ''')
        await db.commit()


# === ЛОГИКА БОТА ===

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    # Добавляем юзера в БД
    async with aiosqlite.connect('database.db') as db:
        await db.execute(
            'INSERT OR IGNORE INTO users (user_id, username, joined_date) VALUES (?, ?, CURRENT_DATE)',
            (message.from_user.id, message.from_user.username)
        )
        await db.commit()

    # Красивая клавиатура
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔥 Открыть трекер", web_app=WebAppInfo(url=RENDER_URL))]
    ])

    text = (
        "<b>Салют, Сигма!</b> 🗿\n\n"
        "Добро пожаловать в твой личный трекер привычек. "
        "Здесь мы куем дисциплину и достигаем целей.\n\n"
        "<i>Дисциплина — это решение делать то, чего очень не хочется делать, "
        "чтобы достичь того, чего очень хочется.</i>\n\n"
        "👇 <b>Жми кнопку ниже, чтобы начать:</b>"
    )
    await message.answer(text, reply_markup=keyboard)


@dp.message(Command("stats"), F.from_user.id == ADMIN_ID)
async def admin_stats(message: types.Message):
    async with aiosqlite.connect('database.db') as db:
        async with db.execute('SELECT COUNT(*) FROM users') as cursor:
            total_users = (await cursor.fetchone())[0]

        async with db.execute('SELECT COUNT(*) FROM users WHERE habits_count > 0') as cursor:
            active_users = (await cursor.fetchone())[0]

        async with db.execute('SELECT SUM(habits_count) FROM users') as cursor:
            total_habits = (await cursor.fetchone())[0] or 0

        async with db.execute('SELECT COUNT(*) FROM users WHERE joined_date = CURRENT_DATE') as cursor:
            today_users = (await cursor.fetchone())[0]

    text = (
        "📊 <b>Статистика трекера:</b>\n\n"
        f"👥 <b>Всего юзеров:</b> {total_users}\n"
        f"⚡️ <b>Новых сегодня:</b> {today_users}\n"
        f"🔥 <b>Активных (1+ привычка):</b> {active_users}\n"
        f"🎯 <b>Всего привычек создано:</b> {total_habits}\n"
    )
    await message.answer(text)


@dp.message(Command("add"), F.from_user.id == ADMIN_ID)
async def admin_add_sponsor(message: types.Message):
    args = message.text.split()
    if len(args) != 3:
        return await message.answer("⚠️ <b>Формат:</b> <code>/add @channel_name 24</code> (где 24 - часы)")

    channel = args[1]
    if not channel.startswith("@"):
        return await message.answer("❌ Укажи юзернейм канала с @ (например, @mychannel)")

    try:
        hours = int(args[2])
    except ValueError:
        return await message.answer("❌ Время должно быть числом!")

    expires_at = (datetime.now() + timedelta(hours=hours)).isoformat()

    async with aiosqlite.connect('database.db') as db:
        await db.execute('INSERT INTO sponsors (channel_username, expires_at) VALUES (?, ?)', (channel, expires_at))
        await db.commit()

    await message.answer(
        f"✅ <b>Спонсор добавлен!</b>\nТеперь юзеры должны подписаться на {channel} в течение {hours} ч.\n<i>(Не забудь сделать бота админом в этом канале!)</i>")


# --- РАССЫЛКА (/all) ---

@dp.message(Command("all"), F.from_user.id == ADMIN_ID)
async def cmd_all_start(message: types.Message, state: FSMContext):
    await message.answer(
        "📢 <b>Режим рассылки</b>\n\n"
        "Отправь следующим сообщением то, что хочешь разослать.\n"
        "<i>Поддерживаются фото, видео, гифки, кнопки и любой текст.</i>\n\n"
        "Для отмены напиши <code>отмена</code>."
    )
    await state.set_state(BroadcastState.waiting_for_message)


@dp.message(BroadcastState.waiting_for_message, F.from_user.id == ADMIN_ID)
async def process_broadcast(message: types.Message, state: FSMContext):
    if message.text and message.text.lower() == "отмена":
        await state.clear()
        return await message.answer("❌ Рассылка отменена.")

    await message.answer("⏳ Начинаю рассылку...")
    success = 0
    blocked = 0

    async with aiosqlite.connect('database.db') as db:
        async with db.execute('SELECT user_id FROM users') as cursor:
            users = await cursor.fetchall()

    for (user_id,) in users:
        try:
            # copy_to копирует сообщение 1 в 1 с медиа и форматированием
            await message.copy_to(chat_id=user_id)
            success += 1
        except Exception:
            blocked += 1
        await asyncio.sleep(0.05)  # Защита от спам-блока Телеграма

    await state.clear()
    await message.answer(
        f"✅ <b>Рассылка завершена!</b>\n\n"
        f"✉️ Успешно отправлено: {success}\n"
        f"🚫 Заблокировали бота: {blocked}"
    )


# === API ЭНДПОИНТЫ ===

@app.get("/")
async def root():
    return {"status": "working", "info": "Habit Tracker Backend"}


@app.get("/api/ping")
async def ping_test():
    return {"message": "Связь с Python установлена! Сервер SigmaTop активен. 🚀"}


# Эндпоинт для обновления статистики из React
@app.post("/api/sync_stats")
async def sync_stats(request: Request):
    try:
        data = await request.json()
        user_id = data.get("user_id")
        habits_count = data.get("habits_count", 0)

        if user_id:
            async with aiosqlite.connect('database.db') as db:
                await db.execute('UPDATE users SET habits_count = ? WHERE user_id = ?', (habits_count, user_id))
                await db.commit()
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/api/check_access")
async def check_access(request: Request):
    try:
        data = await request.json()
        user_id = data.get("user_id")

        # Удаляем просроченных спонсоров
        now = datetime.now().isoformat()
        async with aiosqlite.connect('database.db') as db:
            await db.execute('DELETE FROM sponsors WHERE expires_at < ?', (now,))
            await db.commit()

            # Получаем актуальных спонсоров
            async with db.execute('SELECT channel_username FROM sponsors') as cursor:
                sponsors = await cursor.fetchall()

        # Проверяем подписку на каждого спонсора
        for (channel,) in sponsors:
            try:
                member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
                if member.status in ["left", "kicked"]:
                    return {"status": "error", "message": "unsubscribed", "channel": channel}
            except Exception as e:
                logging.error(f"TG API Error checking {channel}: {e}")
                # Если бот не админ, он не сможет проверить. Пропускаем.
                pass

        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


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