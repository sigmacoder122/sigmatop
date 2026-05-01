import asyncio
import logging
import os
from datetime import datetime, timedelta, timezone

import aiosqlite
import uvicorn
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, FSInputFile
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

# === НАСТРОЙКИ ===
BOT_TOKEN = "8311389856:AAEbCn9AxcX56LFQg1Fv97l5v_IuvnlbWU0"
ADMIN_ID = 7658738825

# Ссылка для поддержания активности бэкенда (Render)
RENDER_URL = "https://sigmatop-7.onrender.com"
# Ссылка на само приложение (Vercel)
WEB_APP_URL = "https://my-tracker-plum.vercel.app/"

# Дефолтное фото (пока админ не установит свое)
DEFAULT_PHOTO_URL = "https://images.unsplash.com/photo-1552508744-1696d4464960?auto=format&fit=crop&w=800&q=80"

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


# === СОСТОЯНИЯ FSM ===
class BroadcastState(StatesGroup):
    waiting_for_message = State()


class DataState(StatesGroup):
    waiting_for_db = State()


class SettingsState(StatesGroup):
    waiting_for_photo = State()


# === БАЗА ДАННЫХ ===
async def init_db():
    async with aiosqlite.connect('database.db') as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                habits_count INTEGER DEFAULT 0,
                joined_date DATE DEFAULT CURRENT_DATE
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS sponsors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_username TEXT,
                expires_at TIMESTAMP
            )
        ''')
        # Таблица для настроек (в том числе для сохранения приветственного фото)
        await db.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')

        # Вставляем дефолтное фото, если еще нет
        await db.execute('INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)',
                         ('welcome_photo', DEFAULT_PHOTO_URL))

        # Безопасное добавление новых колонок для старой базы
        try:
            await db.execute('ALTER TABLE users ADD COLUMN uncompleted_count INTEGER DEFAULT 0')
        except Exception:
            pass

        try:
            await db.execute('ALTER TABLE users ADD COLUMN notifications_enabled INTEGER DEFAULT 1')
        except Exception:
            pass

        await db.commit()


# === ЛОГИКА БОТА ===

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    async with aiosqlite.connect('database.db') as db:
        await db.execute(
            'INSERT OR IGNORE INTO users (user_id, username, joined_date, notifications_enabled) VALUES (?, ?, CURRENT_DATE, 1)',
            (message.from_user.id, message.from_user.username)
        )
        async with db.execute('SELECT value FROM settings WHERE key = ?', ('welcome_photo',)) as cursor:
            photo_row = await cursor.fetchone()
            photo_url_or_id = photo_row[0] if photo_row else DEFAULT_PHOTO_URL
        await db.commit()

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔥 Открыть трекер", web_app=WebAppInfo(url=WEB_APP_URL))],
        [InlineKeyboardButton(text="🔔 Настроить уведомления", callback_data="toggle_notifs")]
    ])

    # ИСПРАВЛЕНО: Правильные закрывающиеся теги
    text = (
        "<b>Привет!</b>\n\n"
        "Добро пожаловать в твой личный трекер привычек. "
        "Здесь мы куем дисциплину и достигаем целей.\n\n"
        "<i>Дисциплина — это решение делать то, чего очень не хочется делать, "
        "чтобы достичь того, чего очень хочется.</i>"
    )

    try:
        await message.answer_photo(
            photo=photo_url_or_id,
            caption=text,
            reply_markup=keyboard
        )
    except Exception as e:
        logging.error(f"Ошибка отправки фото: {e}")
        await message.answer(text, reply_markup=keyboard)


@dp.callback_query(F.data == "toggle_notifs")
async def toggle_notifs(call: types.CallbackQuery):
    async with aiosqlite.connect('database.db') as db:
        async with db.execute('SELECT notifications_enabled FROM users WHERE user_id = ?',
                              (call.from_user.id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                new_state = 0 if row[0] == 1 else 1
                await db.execute('UPDATE users SET notifications_enabled = ? WHERE user_id = ?',
                                 (new_state, call.from_user.id))
                await db.commit()
                status = "ВКЛЮЧЕНЫ ✅" if new_state == 1 else "ВЫКЛЮЧЕНЫ 🔕"
                await call.answer(f"Ежедневные уведомления (в 20:00 МСК): {status}", show_alert=True)
            else:
                await call.answer("Произошла ошибка. Напиши /start", show_alert=True)


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


# Объединенная команда /add (фото и спонсоры)
@dp.message(Command("add"), F.from_user.id == ADMIN_ID)
async def admin_add(message: types.Message, state: FSMContext):
    args = message.text.split()

    # 1. Если это смена фото: /add photo
    if len(args) == 2 and args[1].lower() == "photo":
        await message.answer(
            "🖼 <b>Смена приветственного фото</b>\n\n"
            "Отправь мне новую картинку обычным сообщением.\n"
            "Для отмены напиши <code>отмена</code>."
        )
        await state.set_state(SettingsState.waiting_for_photo)
        return

    # 2. Если это спонсор: /add @channel 24
    if len(args) != 3:
        return await message.answer(
            "⚠️ <b>Доступные команды:</b>\n"
            "1) Спонсор: <code>/add @channel_name 24</code> (где 24 - часы)\n"
            "2) Фото: <code>/add photo</code>"
        )

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
        f"✅ <b>Спонсор добавлен!</b>\nТеперь юзеры должны подписаться на {channel} в течение {hours} ч.")


# --- СМЕНА ФОТО ---

@dp.message(SettingsState.waiting_for_photo, F.from_user.id == ADMIN_ID, F.photo)
async def process_new_photo(message: types.Message, state: FSMContext):
    # Берем самое большое качество фото
    photo_file_id = message.photo[-1].file_id

    async with aiosqlite.connect('database.db') as db:
        await db.execute('UPDATE settings SET value = ? WHERE key = ?', (photo_file_id, 'welcome_photo'))
        await db.commit()

    await state.clear()
    await message.answer("✅ <b>Приветственное фото успешно обновлено!</b>\nОтправь /start чтобы проверить.")


@dp.message(SettingsState.waiting_for_photo, F.from_user.id == ADMIN_ID)
async def process_new_photo_invalid(message: types.Message, state: FSMContext):
    if message.text and message.text.lower() == "отмена":
        await state.clear()
        return await message.answer("❌ Смена фото отменена.")
    await message.answer("❌ Это не картинка! Пожалуйста, отправь фото (или напиши <code>отмена</code>).")


# --- УПРАВЛЕНИЕ БАЗОЙ ДАННЫХ ---

@dp.message(Command("data"), F.from_user.id == ADMIN_ID)
async def export_data(message: types.Message):
    file = FSInputFile("database.db")
    await message.answer_document(file,
                                  caption="📦 <b>Дамп базы данных (SQLite)</b>\nЗдесь все пользователи, настройки и спонсоры.")


@dp.message(Command("adddata"), F.from_user.id == ADMIN_ID)
async def import_data_start(message: types.Message, state: FSMContext):
    await message.answer(
        "⚠️ <b>Внимание!</b> Это действие полностью перезапишет текущую базу данных.\n\n"
        "Отправь мне файл <code>database.db</code> в ответ на это сообщение.\n"
        "Для отмены напиши <code>отмена</code>."
    )
    await state.set_state(DataState.waiting_for_db)


@dp.message(DataState.waiting_for_db, F.from_user.id == ADMIN_ID)
async def import_data_process(message: types.Message, state: FSMContext):
    if message.text and message.text.lower() == "отмена":
        await state.clear()
        return await message.answer("❌ Загрузка отменена.")

    if not message.document or message.document.file_name != "database.db":
        return await message.answer("❌ Пожалуйста, отправь файл с точным названием: <code>database.db</code>")

    await message.answer("⏳ Скачиваю и обновляю базу...")

    file_id = message.document.file_id
    file = await bot.get_file(file_id)
    await bot.download_file(file.file_path, "database.db")

    await state.clear()
    await message.answer("✅ <b>Успех!</b> Новая база данных загружена и установлена.")


# --- РАССЫЛКА (/all) ---

@dp.message(Command("all"), F.from_user.id == ADMIN_ID)
async def cmd_all_start(message: types.Message, state: FSMContext):
    await message.answer("📢 Отправь сообщение для рассылки (или 'отмена').")
    await state.set_state(BroadcastState.waiting_for_message)


@dp.message(BroadcastState.waiting_for_message, F.from_user.id == ADMIN_ID)
async def process_broadcast(message: types.Message, state: FSMContext):
    if message.text and message.text.lower() == "отмена":
        await state.clear()
        return await message.answer("❌ Рассылка отменена.")

    await message.answer("⏳ Начинаю рассылку...")
    success, blocked = 0, 0

    async with aiosqlite.connect('database.db') as db:
        async with db.execute('SELECT user_id FROM users') as cursor:
            users = await cursor.fetchall()

    for (user_id,) in users:
        try:
            await message.copy_to(chat_id=user_id)
            success += 1
        except Exception:
            blocked += 1
        await asyncio.sleep(0.05)

    await state.clear()
    await message.answer(f"✅ <b>Рассылка завершена!</b>\nОтправлено: {success}\nЗаблокировали: {blocked}")


# === API ЭНДПОИНТЫ ===

@app.get("/")
async def root():
    return {"status": "working", "info": "Habit Tracker Backend"}


@app.post("/api/sync_stats")
async def sync_stats(request: Request):
    try:
        data = await request.json()
        user_id = data.get("user_id")
        habits_count = data.get("habits_count", 0)
        uncompleted_count = data.get("uncompleted_count", 0)

        if user_id:
            async with aiosqlite.connect('database.db') as db:
                await db.execute('''
                    UPDATE users 
                    SET habits_count = ?, uncompleted_count = ? 
                    WHERE user_id = ?
                ''', (habits_count, uncompleted_count, user_id))
                await db.commit()
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/api/check_access")
async def check_access(request: Request):
    try:
        data = await request.json()
        user_id = data.get("user_id")
        now = datetime.now().isoformat()

        async with aiosqlite.connect('database.db') as db:
            await db.execute('DELETE FROM sponsors WHERE expires_at < ?', (now,))
            await db.commit()
            async with db.execute('SELECT channel_username FROM sponsors') as cursor:
                sponsors = await cursor.fetchall()

        for (channel,) in sponsors:
            try:
                member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
                if member.status in ["left", "kicked"]:
                    return {"status": "error", "message": "unsubscribed", "channel": channel}
            except Exception:
                pass
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# === ФОНОВЫЕ ЗАДАЧИ ===

async def self_ping():
    import aiohttp
    await asyncio.sleep(10)
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(RENDER_URL) as resp:
                    pass
        except:
            pass
        await asyncio.sleep(600)


async def notification_scheduler():
    last_sent_date = None
    while True:
        now_utc = datetime.now(timezone.utc)
        now_msk = now_utc + timedelta(hours=3)

        if now_msk.hour == 20 and now_msk.minute == 0 and last_sent_date != now_msk.date():
            last_sent_date = now_msk.date()

            async with aiosqlite.connect('database.db') as db:
                async with db.execute(
                        'SELECT user_id FROM users WHERE notifications_enabled = 1 AND uncompleted_count > 0') as cursor:
                    users = await cursor.fetchall()

            for (uid,) in users:
                try:
                    await bot.send_message(
                        uid,
                        "🔔 <b>Напоминание!</b>\n\n"
                        "У тебя остались невыполненные привычки на сегодня. Зайди в трекер и закрой день как истинный Сигма! 🗿",
                        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                            [InlineKeyboardButton(text="🔥 Открыть", web_app=WebAppInfo(url=WEB_APP_URL))]])
                    )
                except Exception:
                    pass
                await asyncio.sleep(0.05)

        await asyncio.sleep(30)


async def main():
    await init_db()
    port = int(os.environ.get("PORT", 8000))
    config = uvicorn.Config(app, host="0.0.0.0", port=port)
    server = uvicorn.Server(config)

    await asyncio.gather(
        server.serve(),
        self_ping(),
        notification_scheduler(),
        dp.start_polling(bot)
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Stopped")