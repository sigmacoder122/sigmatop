import os

# Структура папок и файлов
structure = {
    "database": ["db.py"],
    "handlers": ["user.py"],
    "keyboards": ["inline.py"],
}

files_content = {
    ".env": "BOT_TOKEN=8730929027:AAFvBfgHiDZSpUh1ybh2A5hQXPDdVPWMTxM\nADMIN_ID=ТВОЙ_ID\nPROXY_URL=http://181.41.201.85:3128",

    "config.py": """import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID', 0))
PROXY_URL = os.getenv('PROXY_URL')
""",

    "database/db.py": """import aiosqlite

DB_NAME = "bot_database.db"

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                balance INTEGER DEFAULT 0,
                invites_count INTEGER DEFAULT 0,
                invited_by INTEGER
            )
        ''')
        await db.commit()
""",

    "keyboards/inline.py": """from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💼 Личный кабинет", callback_data="profile")],
        [InlineKeyboardButton(text="💸 Заработать", callback_data="earn"),
         InlineKeyboardButton(text="📊 Статистика", callback_data="stats")]
    ])

def get_back_button():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
    ])
""",

    "handlers/user.py": """from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from keyboards.inline import get_main_menu, get_back_button

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    text = "👋 <b>Привет!</b> Добро пожаловать в бота.\n\nВыбирай нужный раздел 👇"
    await message.answer(text, reply_markup=get_main_menu(), parse_mode="HTML")

@router.callback_query(F.data == "profile")
async def show_profile(callback: CallbackQuery):
    text = f"💼 <b>Твой Личный кабинет</b>\n\nID: <code>{callback.from_user.id}</code>\nБаланс: <b>0</b> ₽"
    await callback.message.edit_text(text, reply_markup=get_back_button(), parse_mode="HTML")

@router.callback_query(F.data == "earn")
async def show_earn(callback: CallbackQuery):
    bot_info = await callback.bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={callback.from_user.id}"
    text = f"💸 <b>Как заработать?</b>\n\nТвоя ссылка: <code>{ref_link}</code>"
    await callback.message.edit_text(text, reply_markup=get_back_button(), parse_mode="HTML")

@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery):
    text = "👋 <b>Главное меню</b>\n\nВыбирай нужный раздел 👇"
    await callback.message.edit_text(text, reply_markup=get_main_menu(), parse_mode="HTML")
""",

    "main.py": """import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from config import BOT_TOKEN, PROXY_URL
from database.db import init_db
from handlers import user

async def main():
    logging.basicConfig(level=logging.INFO)

    # Твой рабочий прокси
    session = AiohttpSession(proxy=PROXY_URL)
    bot = Bot(token=BOT_TOKEN, session=session)
    dp = Dispatcher()

    dp.include_router(user.router)

    await init_db()

    print(f"Бот запущен через прокси: {PROXY_URL}")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот выключен")
"""
}


def create_project():
    for folder, files in structure.items():
        os.makedirs(folder, exist_ok=True)
        for file in files:
            path = os.path.join(folder, file)
            if not os.path.exists(path):
                with open(path, "w", encoding="utf-8") as f:
                    f.write(files_content.get(path, ""))

    for file, content in files_content.items():
        if "/" not in file:
            with open(file, "w", encoding="utf-8") as f:
                f.write(content)

    print("✅ Проект успешно создан!")


if __name__ == "__main__":
    create_project()
