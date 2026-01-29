import sqlite3
import asyncio
import logging
import os
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
import requests
from math import ceil

from aiogram import Bot, Dispatcher, Router, F, types
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message, CallbackQuery, LabeledPrice, InputMediaPhoto, InputFile,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from sqlalchemy import String, Integer, DateTime, select
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# =========================
# Настройки
# =========================
TOKEN = os.getenv("TOKEN", "ВАШ_TOKEN")
PROVIDER_TOKEN = os.getenv("STARS_PROVIDER_TOKEN", "")
CRYPTO_BOT_TOKEN = os.getenv("CRYPTO_BOT_TOKEN", "")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))
STARS_RATE_RUB = float(os.getenv("STARS_RATE_RUB", "1.15"))
PROMO_CODE = os.getenv("PROMO_CODE", "PROMO")
PROMO_DISCOUNT = float(os.getenv("PROMO_DISCOUNT", "0.10"))
ORDERS_FILE = "orders.json"
MAIN_PHOTO_PATH = "photo.jpg"  # локальный файл для главного изображения

SERVICES: List[str] = [
    "Телега", "163COM", "1688", "1and1", "1xbet", "2dehands", "2ГИС", "32red", "360Kredi",
    "3Fun", "4Fun", "7-Eleven", "888casino", "99acres", "99app", "A23", "A9A", "AaHIRA Fashion",
    "Abastece-aí", "Abbott", "Ace2Three"
]

REGIONS: List[dict] = [
    {"id": "1", "name": "Россия", "flag": "🇷🇺", "price_rub": 50},
    {"id": "2", "name": "Казахстан", "flag": "🇰🇿", "price_rub": 60},
    {"id": "3", "name": "Украина", "flag": "🇺🇦", "price_rub": 70},
    {"id": "4", "name": "Европа", "flag": "🇪🇺", "price_rub": 100},
]

SERVICES_PER_PAGE = 15
ROWS_PER_PAGE = 5
COLS_PER_ROW = 3

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bot")

bot = Bot(token=TOKEN)
dp = Dispatcher()
router = Router()
dp.include_router(router)

DATABASE_URL = "sqlite+aiosqlite:///./bot.db"

# =========================
# ORM
# =========================
class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tg_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    registered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    referrals: Mapped[int] = mapped_column(Integer, default=0)
    balance: Mapped[int] = mapped_column(Integer, default=0)
    promo_available: Mapped[int] = mapped_column(Integer, default=0)

class Purchase(Base):
    __tablename__ = "purchases"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    service: Mapped[str] = mapped_column(String(64))
    region_label: Mapped[str] = mapped_column(String(128))
    price_rub: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

engine = create_async_engine(DATABASE_URL, echo=False, future=True)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# =========================
# FSM States
# =========================
class PromoStates(StatesGroup):
    waiting_promo = State()

class BroadcastStates(StatesGroup):
    waiting_broadcast_text = State()

# =========================
# Orders
# =========================
def load_orders() -> Dict[str, Dict[str, Any]]:
    if os.path.exists(ORDERS_FILE):
        try:
            with open(ORDERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_orders():
    with open(ORDERS_FILE, "w", encoding="utf-8") as f:
        json.dump(orders, f, indent=4, ensure_ascii=False)

orders: Dict[str, Dict[str, Any]] = load_orders()

# =========================
# Клавиатуры
# =========================
def kb_main() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Купить номер", callback_data="buyacc")],
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile")],
        [InlineKeyboardButton(text="📜 История", callback_data="purchase_history"),
         InlineKeyboardButton(text="🎁 Рефералы", callback_data="referral")],
        [InlineKeyboardButton(text="ℹ️ Инфо", callback_data="info"),
         InlineKeyboardButton(text="📄 Договор", callback_data="dogovor")],
        [InlineKeyboardButton(text="🎁 Промокод", callback_data="promo_code")]
    ])

def kb_services_page(page: int = 0) -> InlineKeyboardMarkup:
    start = page * SERVICES_PER_PAGE
    end = start + SERVICES_PER_PAGE
    page_services = SERVICES[start:end]

    keyboard = []
    for i in range(0, len(page_services), COLS_PER_ROW):
        row = [InlineKeyboardButton(text=srv, callback_data=f"service|{srv}") for srv in page_services[i:i+COLS_PER_ROW]]
        keyboard.append(row)

    total_pages = ceil(len(SERVICES) / SERVICES_PER_PAGE)
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton("⬅️", callback_data=f"page|{page-1}"))
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton("➡️", callback_data=f"page|{page+1}"))
    if nav_row:
        keyboard.append(nav_row)

    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="main")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def kb_regions() -> InlineKeyboardMarkup:
    rows: List[List[InlineKeyboardButton]] = []
    for r in REGIONS:
        label = f"{r['name']} {r['flag']} ({r['price_rub']}₽)"
        rows.append([InlineKeyboardButton(text=label, callback_data=f"region|{r['id']}")])
    rows.append([InlineKeyboardButton(text="🔙 Назад", callback_data="buyacc")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def kb_confirm(service: str, region_label: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐️ Оплатить через Stars", callback_data=f"paystars|{service}|{region_label}")],
        [InlineKeyboardButton(text="💎 Оплатить через Crypto", callback_data=f"pay_crypto_{region_label}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="buyacc")]
    ])

# =========================
# База
# =========================
async def db_init():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def set_user(tg_id: int):
    async with async_session() as session:
        user = (await session.execute(select(User).where(User.tg_id == tg_id))).scalar_one_or_none()
        if not user:
            session.add(User(tg_id=tg_id))
            await session.commit()

async def get_user(tg_id: int) -> Optional[User]:
    async with async_session() as session:
        return (await session.execute(select(User).where(User.tg_id == tg_id))).scalar_one_or_none()

async def get_all_users() -> List[User]:
    async with async_session() as session:
        return (await session.execute(select(User))).scalars().all()

async def get_user_purchases(tg_id: int) -> List[Purchase]:
    async with async_session() as session:
        return (await session.execute(select(Purchase).where(Purchase.user_id == tg_id).order_by(Purchase.created_at.desc()))).scalars().all()

async def add_purchase(tg_id: int, service: str, region_label: str, price_rub: int):
    async with async_session() as session:
        session.add(Purchase(user_id=tg_id, service=service, region_label=region_label, price_rub=price_rub))
        await session.commit()

# =========================
# Утилиты
# =========================
def rub_to_stars(price_rub: int) -> int:
    return max(1, int(price_rub / STARS_RATE_RUB))

async def notify_admin(order_id: str, user_id: int, service: str, region_label: str, price_rub: int, stars: int):
    msg = await bot.send_message(
        ADMIN_ID,
        f"🛎 Новый заказ\nID: {order_id}\nПользователь: {user_id}\nСервис: {service}\nРегион: {region_label}\nЦена: {price_rub} RUB (~{stars}⭐️)"
    )
    orders[order_id]["admin_message_id"] = msg.message_id
    save_orders()

async def notify_admin_crypto(order_id: str, user_id: int, service: str, region_label: str):
    msg = await bot.send_message(
        ADMIN_ID,
        f"🛎 Новый заказ через Crypto\nID: {order_id}\nПользователь: {user_id}\nСервис: {service}\nРегион: {region_label}"
    )
    orders[order_id]["admin_message_id"] = msg.message_id
    save_orders()

# =========================
# Хэндлеры
# =========================
@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await set_user(message.from_user.id)
    await message.answer_photo(
        photo=InputFile(MAIN_PHOTO_PATH),
        caption='🔐 Добро пожаловать в магазин Telegram-номеров!',
        reply_markup=kb_main()
    )

@router.callback_query(F.data == "main")
async def cb_main(callback: CallbackQuery):
    await callback.answer()
    new_media = InputMediaPhoto(media=InputFile(MAIN_PHOTO_PATH), caption='🔐 Добро пожаловать в магазин Telegram-номеров!')
    await callback.bot.edit_message_media(chat_id=callback.message.chat.id, message_id=callback.message.message_id, media=new_media, reply_markup=kb_main())


# =========================
# Хэндлер покупки аккаунта
# =========================
@router.callback_query(F.data == 'buyacc')
async def buy_account(callback: CallbackQuery, state: FSMContext):
    await state.update_data(selected_service=None, selected_region=None)
    await callback.answer()
    new_media = InputMediaPhoto(media=InputFile(MAIN_PHOTO_PATH), caption="🧩 Выберите сервис:")
    await callback.bot.edit_message_media(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        media=new_media,
        reply_markup=kb_services_page(0)
    )

@router.callback_query(F.data.startswith("page|"))
async def change_service_page(callback: CallbackQuery):
    page = int(callback.data.split("|")[1])
    await callback.answer()
    new_media = InputMediaPhoto(media=InputFile(MAIN_PHOTO_PATH), caption="🧩 Выберите сервис:")
    await callback.bot.edit_message_media(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        media=new_media,
        reply_markup=kb_services_page(page)
    )

@router.callback_query(F.data.startswith("service|"))
async def choose_service(callback: CallbackQuery, state: FSMContext):
    _, service = callback.data.split("|", 1)
    await state.update_data(selected_service=service, selected_region=None)
    await callback.answer()
    new_media = InputMediaPhoto(media=InputFile(MAIN_PHOTO_PATH), caption=f"🌍 Сервис: {service}\nВыберите регион:")
    await callback.bot.edit_message_media(chat_id=callback.message.chat.id, message_id=callback.message.message_id, media=new_media, reply_markup=kb_regions())

@router.callback_query(F.data.startswith("region|"))
async def choose_region(callback: CallbackQuery, state: FSMContext):
    _, region_id = callback.data.split("|", 1)
    data = await state.get_data()
    service = data.get("selected_service")
    if not service:
        await callback.answer("Сначала выберите сервис")
        return

    region = next((r for r in REGIONS if r["id"] == region_id), None)
    if not region:
        await callback.answer("Регион не найден")
        return

    region_label = f"{region['name']} {region['flag']} ({region['price_rub']}₽)"
    await state.update_data(selected_region=region_label)
    caption = f"💈 Детали заказа:\n• Сервис: {service}\n• Регион: {region_label}\n• Стоимость: {region['price_rub']} RUB"
    new_media = InputMediaPhoto(media=InputFile(MAIN_PHOTO_PATH), caption=caption)
    await callback.bot.edit_message_media(chat_id=callback.message.chat.id, message_id=callback.message.message_id, media=new_media, reply_markup=kb_confirm(service, region_label))
    await callback.answer()

# =========================
# Оплата через Stars
# =========================
@router.callback_query(F.data.startswith("paystars|"))
async def pay_with_stars(callback: CallbackQuery, state: FSMContext):
    _, service, region_label = callback.data.split("|", 2)
    try:
        price_str = region_label.split("(")[-1].split("₽)")[0]
        price_rub = int(price_str)
    except:
        await callback.answer("Ошибка цены")
        return

    user = await get_user(callback.from_user.id)
    effective_price = price_rub
    if user and user.promo_available:
        discount = int(round(price_rub * PROMO_DISCOUNT))
        effective_price = max(1, price_rub - discount)
    stars_amount = max(1, int(effective_price / STARS_RATE_RUB))

    if not PROVIDER_TOKEN:
        await callback.answer("Stars провайдер не настроен. Свяжитесь с админом.")
        return

    await callback.bot.send_invoice(
        chat_id=callback.from_user.id,
        title=f"Покупка: {service} — {region_label}",
        description="Оплата через Stars. После оплаты ожидание данных.",
        provider_token=PROVIDER_TOKEN,
        currency="XTR",
        prices=[LabeledPrice(label=f"{service} {region_label}", amount=stars_amount)],
        payload=f"stars|{service}|{region_label}|{callback.from_user.id}",
        start_parameter="stars_invoice",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Отменить платеж", callback_data="cancel_stars_payment")]])
    )
    await callback.answer()

# =========================
# Оплата через Crypto
# =========================
@router.callback_query(F.data.startswith("pay_crypto_"))
async def pay_with_crypto(callback: CallbackQuery, state: FSMContext):
    region_label = callback.data[len("pay_crypto_"):]
    user_id = callback.from_user.id
    order_id = str(uuid.uuid4())
    orders[order_id] = {"user_id": user_id, "region_label": region_label, "status": "pending", "payment_method": "Crypto"}
    save_orders()

    try:
        headers = {"Crypto-Pay-API-Token": CRYPTO_BOT_TOKEN, "Content-Type": "application/json"}
        response = requests.post(
            "https://pay.crypt.bot/api/createInvoice",
            headers=headers,
            json={"asset": "USDT", "amount": "1.00", "description": f"Order #{order_id}", "payload": order_id}
        )
        data = response.json()
        if not data.get("ok"):
            await callback.answer("❌ Ошибка создания платежа")
            return
        invoice = data["result"]
        orders[order_id]["invoice_id"] = invoice["invoice_id"]
        save_orders()
        await callback.message.answer(
            f"💎 Оплата через Crypto Bot:\nСумма: {invoice['amount']} {invoice['asset']}\nСсылка: {invoice['pay_url']}\nID заказа: {order_id}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✅ Проверить оплату", callback_data=f"check_crypto_{order_id}")],
                [InlineKeyboardButton(text="❌ Отмена", callback_data=f"cancel_crypto_{order_id}")]
            ])
        )
        await notify_admin_crypto(order_id, user_id, "CryptoService", region_label)
    except Exception as e:
        logger.error(f"Crypto error: {e}")
        await callback.answer("⚠️ Ошибка при создании платежа")

# Остальные хэндлеры buyacc, pagination, choose_service, choose_region, paystars, pay_crypto
# остаются аналогичными вашему коду, с заменой MAIN_PHOTO_ID на InputFile(MAIN_PHOTO_PATH)

# =========================
# Запуск
# =========================
async def main():
    await db_init()
    logger.info("Bot started.")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped.")
