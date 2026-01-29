import asyncio
import contextvars
import inspect
import json
import logging
import os
from sqlalchemy import select
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import partial
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

import aiohttp
import requests
from aiogram import Bot, Dispatcher, F, Router, types
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (CallbackQuery, InlineKeyboardButton,
                           InlineKeyboardMarkup, KeyboardButton, LabeledPrice,
                           Message, PreCheckoutQuery, ReplyKeyboardMarkup)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from magic_filter.magic import MagicFilter as OriginalMagicFilter
from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.ext.asyncio import (AsyncAttrs, async_sessionmaker,
                                    create_async_engine)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Конфигурация
TOKEN = '8442407027:AAGvxbLeWbzSjNIuVXHL-iFuUG05gViU8bs'
crypto_bot_token = '319088:AAsRs5zFKk5DRCFRsREHtde63rJDzZducjF'
API_KEY = '774774'
ADMIN_ID = 7658738825

# Инициализация бота
bot = Bot(token=TOKEN)
dp = Dispatcher(bot=bot)
router = Router()
dp.include_router(router)

# База данных
engine = create_async_engine(url='sqlite+aiosqlite:///db.sqlite3')
async_session = async_sessionmaker(engine)

class Base(AsyncAttrs, DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    registered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    referrals: Mapped[int] = mapped_column(Integer, default=0)
    balance: Mapped[float] = mapped_column(default=0.0)

class Category(Base):
    __tablename__ = 'categories'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(25))

class Item(Base):
    __tablename__ = 'items'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150))
    description: Mapped[str] = mapped_column(String(500))
    price: Mapped[float] = mapped_column()
    category: Mapped[int] = mapped_column(ForeignKey('categories.id'))
    login: Mapped[Optional[str]] = mapped_column(String(100))
    password: Mapped[Optional[str]] = mapped_column(String(100))

class Order(Base):
    __tablename__ = 'orders'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger)
    item_id: Mapped[int] = mapped_column(Integer)
    date: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    status: Mapped[str] = mapped_column(String(50), default='pending')

async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Database requests
async def set_user(tg_id: int):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if not user:
            # Создаем пользователя с текущей датой регистрации
            session.add(User(tg_id=tg_id, registered_at=datetime.now()))
            await session.commit()

async def get_user(tg_id: int):
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.tg_id == tg_id)
        )
        return result.scalar()

async def get_user_purchases(tg_id: int):
    async with async_session() as session:
        result = await session.execute(
            select(Order).where(Order.user_id == tg_id)
        )
        return result.scalars().all()

async def get_opr(item_id):
    async with async_session() as session:
        return await session.scalar(select(Item).where(Item.id == item_id))

async def get_item_by_id(item_id):
    async with async_session() as session:
        return await session.scalar(select(Item).where(Item.id == item_id))

async def get_categories():
    async with async_session() as session:
        result = await session.scalars(select(Category))
        return result.all()

async def get_items(category_id):
    async with async_session() as session:
        return await session.scalars(select(Item).where(Item.category == category_id))

async def get_category_name(category_id):
    async with async_session() as session:
        return await session.scalar(select(Category.name).where(Category.id == category_id))

# Keyboards
def settings():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🛒 Купить аккаунт", callback_data="buyacc")],
            [
                InlineKeyboardButton(text="👤 Профиль", callback_data="profile"),
                InlineKeyboardButton(text="📜 История", callback_data="purchase_history")
            ],
            [InlineKeyboardButton(text="🎁 Рефералы", callback_data="referral")],
            [InlineKeyboardButton(text="🔄 Перезапустить", callback_data="send_start_command")]
        ]
    )


async def categories_kb():
    all_categories = await get_categories()
    keyboard = InlineKeyboardBuilder()
    for category in all_categories:
        keyboard.add(InlineKeyboardButton(
            text=category.name,
            callback_data=f'category_{category.id}'
        ))
    keyboard.row(InlineKeyboardButton(text='Назад', callback_data='main'))
    return keyboard.adjust(2).as_markup()

async def items_kb(category_id):
    all_items = await get_items(category_id)
    keyboard = InlineKeyboardBuilder()
    for item in all_items:
        keyboard.add(InlineKeyboardButton(
            text=f"{item.name} ({item.price} RUB)",
            callback_data=f'item_{item.id}'
        ))
    keyboard.row(InlineKeyboardButton(
        text='Назад',
        callback_data='buyacc'
    ))
    return keyboard.adjust(2).as_markup()

async def payment_methods_kb(item_id, category_id):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(
        InlineKeyboardButton(text='Telegram Stars 🌟', callback_data=f'pay_stars_{item_id}'),
        InlineKeyboardButton(text='Crypto Bot', callback_data=f'pay_crypto_{item_id}'),
        InlineKeyboardButton(text='Карта РФ 💳', callback_data=f'pay_card_{item_id}')
    )
    keyboard.row(InlineKeyboardButton(
        text='Назад к товарам',
        callback_data=f'category_{category_id}'
    ))
    return keyboard.adjust(1).as_markup()

def stars_payment_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Оплатить", pay=True)
    builder.button(text="❌ Отмена", callback_data="cancel_stars_payment")
    return builder.as_markup()

# States
class PaymentStates(StatesGroup):
    waiting_for_card_amount = State()

class CaptchaStates(StatesGroup):
    waiting_captcha = State()

# Payments
EMOJIS = ["😀", "😂", "😍", "🥰", "😎", "🤩", "🥳", "😭", "😡", "🤯", "🥶", "🤢", "👻", "💩", "👾"]
ORDERS_FILE = "orders.json"
payments = {}
orders = {}

if os.path.exists(ORDERS_FILE):
    with open(ORDERS_FILE, "r") as f:
        orders = json.load(f)

def save_orders():
    with open(ORDERS_FILE, "w") as f:
        json.dump(orders, f, indent=4, ensure_ascii=False)

def generate_payment_link(amount: int, comment: str) -> str:
    return f"https://lolz.live/payment/balance/transfer?user_id=8389422&amount={amount}&currency=rub&comment={comment}&transfer_hold=false"

async def check_payment(comment: str, amount: int) -> dict:
    url = f"https://api.lzt.market/user/payments?type=income&pmin={amount}&pmax={amount}&comment={comment}&is_hold=false"
    headers = {"authorization": f"Bearer {API_KEY}"}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            data = await response.json()
    return data.get('payments', {})

async def create_order(user_id: int, item_id: int, payment_method: str) -> str:
    order_id = str(uuid.uuid4())
    orders[order_id] = {
        "user_id": user_id,
        "item_id": item_id,
        "payment_method": payment_method,
        "status": "waiting_payment",
        "created_at": datetime.now().isoformat(),
        "number": None,
        "code": None
    }
    save_orders()
    return order_id

async def notify_admin(
        bot: Bot,
        order_id: str,
        user_id: int,
        item_name: str,
        payment_method: str
):
    message = await bot.send_message(
        ADMIN_ID,
        f"🛎 Новый заказ\n"
        f"ID: `{order_id}`\n"
        f"👤 Пользователь: {user_id}\n"
        f"🛒 Товар: {item_name}\n"
        f"💳 Способ оплаты: {payment_method}\n\n"
        "➖➖➖➖➖➖➖➖➖\n"
        "📨 Для отправки данных ответьте на это сообщение",
        parse_mode=ParseMode.MARKDOWN
    )
    orders[order_id]["admin_message_id"] = message.message_id
    save_orders()

# Handlers
@router.callback_query(F.data == "main")
async def main_menu(callback: CallbackQuery):
    new_media = types.InputMediaPhoto(
        media="AgACAgQAAxkBAAMEaJvAKelwUJ3FyF2K28N4LVSPrpcAAiTKMRuGWOFQ-eq_9D5tqiQBAAMCAAN5AAM2BA",
        caption='🔐 Добро пожаловать в магазин Telegram-аккаунтов!'
    )
    await callback.bot.edit_message_media(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        media=new_media,
        reply_markup=settings()
    )

@router.callback_query(F.data == "send_start_command")
async def send_start_command(callback: CallbackQuery):
    fake_message = types.Message(
        message_id=callback.message.message_id + 1,
        date=datetime.now(),
        chat=callback.message.chat,
        from_user=callback.from_user,
        text="/start"
    )
    await cmd_start(fake_message)
    try:
        await callback.message.delete()
    except:
        pass
    await callback.answer("🔄 Бот перезапущен!")

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()

    await set_user(message.from_user.id)
    await message.answer_photo(
        photo="AgACAgQAAxkBAAMEaJvAKelwUJ3FyF2K28N4LVSPrpcAAiTKMRuGWOFQ-eq_9D5tqiQBAAMCAAN5AAM2BA",
        caption='🔐 Добро пожаловать в магазин Telegram-аккаунтов!',
        reply_markup=settings()
    )

@router.callback_query(F.data == 'buyacc')
async def buy_account(callback: CallbackQuery):
    new_media = types.InputMediaPhoto(
        media="AgACAgQAAxkBAAMGaJvAZVJl0uPuo4MnZwOMNL9VJIQAAubKMRvHC-BQt7_NPHm8ypEBAAMCAAN5AAM2BA",
        caption="🌐Выберите тип аккаунта:"
    )
    await callback.bot.edit_message_media(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        media=new_media,
        reply_markup=await categories_kb()
    )

@router.callback_query(F.data.startswith("category_"))
async def show_category_items(callback: CallbackQuery):
    category_id = callback.data.split('_')[1]
    new_media = types.InputMediaPhoto(
        media="AgACAgQAAxkBAAMIaJvAg9fcyDTi1JYZZU-2xrcc2IgAAujKMRvHC-BQ3WBtyqsmTucBAAMCAAN5AAM2BA",
        caption="🌏Выберите страну:"
    )
    await callback.bot.edit_message_media(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        media=new_media,
        reply_markup=await items_kb(category_id)
    )

@router.callback_query(F.data.startswith("item_"))
async def show_item(callback: CallbackQuery):
    item_id = callback.data.split('_')[1]
    item_data = await get_item_by_id(item_id)
    if not item_data:
        await callback.answer("Товар не найден!")
        return
    category_name = await get_category_name(item_data.category)
    new_media = types.InputMediaPhoto(
        media="AgACAgQAAxkBAAMMaJvBVw5xMUj1oc6kPPaHRIjnzhsAAm3LMRtzVOBQqtd_8MzFFMQBAAMCAAN5AAM2BA",
        caption=f'💈Информация об аккаунте:\n'
                f"Страна:🏷 {item_data.name}\n"
                "Оператор: любой\n"
                f"💵 Цена: {item_data.price} RUB\n"
                f"➖➖➖➖➖➖➖➖➖➖\n"
                f"Выберите способ оплаты:"
    )
    await callback.bot.edit_message_media(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        media=new_media,
        reply_markup=await payment_methods_kb(item_id, item_data.category)
    )

@router.callback_query(F.data.startswith("pay_stars_"))
async def pay_with_stars(callback: CallbackQuery, state: FSMContext):
    try:
        item_id = callback.data.split('_')[2]
        item = await get_item_by_id(item_id)
        await state.update_data(item_id=item_id, user_id=callback.from_user.id)
        stars_amount = int(item.price // 1.5)
        prices = [LabeledPrice(label=item.name, amount=stars_amount)]
        await callback.bot.send_invoice(
            chat_id=callback.from_user.id,
            title=f"Покупка: {item.name}",
            description="Оплата через Stars\nОплатите счет ниже\n👇👇👇",
            provider_token="",  # Ваш токен Stars
            currency="XTR",
            prices=prices,
            payload=f"stars_{item_id}_{callback.from_user.id}",
            start_parameter="create_invoice_stars",
            reply_markup=stars_payment_kb()
        )
        await callback.answer()
    except Exception as e:
        logging.error(f"Stars payment error: {str(e)}")
        await callback.answer("⚠️ Ошибка при создании платежа")

@router.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)

@router.message(F.successful_payment)
async def process_successful_payment(message: Message, state: FSMContext):
    try:
        payload = message.successful_payment.invoice_payload
        _, item_id, user_id = payload.split('_')
        item = await get_item_by_id(int(item_id))
        order_id = int(datetime.now().timestamp())
        orders[order_id] = {
            'user_id': int(user_id),
            'item_id': int(item_id),
            'status': 'waiting_number',
            'payment_method': 'Stars'
        }
        await message.answer(
            "✅ Оплата прошла успешно! Ожидайте номер, Администрация пришлет его вам в течение 5 минут⌛.",
            reply_markup=settings()
        )
        await notify_admin(
            bot=message.bot,
            order_id=order_id,
            user_id=int(user_id),
            item_name=item.name,
            payment_method='Stars'
        )
        await state.clear()
    except Exception as e:
        logging.error(f"Payment processing error: {str(e)}")
        await message.answer("⚠️ Произошла ошибка при обработке платежа")

@router.callback_query(F.data.startswith("pay_crypto_"))
async def pay_with_crypto(callback: CallbackQuery, state: FSMContext):
    item_id = callback.data.split('_')[2]
    item = await get_item_by_id(item_id)
    user_id = callback.from_user.id
    try:
        order_id = await create_order(user_id, item.id, "Crypto")
        headers = {
            "Crypto-Pay-API-Token": crypto_bot_token,
            "Content-Type": "application/json"
        }
        response = requests.post(
            "https://pay.crypt.bot/api/createInvoice",
            headers=headers,
            json={
                "asset": "USDT",
                "amount": f"{item.price//75:.2f}",
                "description": f"Order #{order_id}",
                "payload": order_id,
                "paid_btn_url": "https://t.me/alfah0st",
                "allow_anonymous": False
            }
        )
        response_data = response.json()
        if not response_data.get("ok"):
            await callback.answer("❌ Ошибка создания платежа")
            return
        invoice = response_data["result"]
        orders[order_id]["invoice_id"] = invoice["invoice_id"]
        save_orders()
        await callback.message.answer(
            f"💎 Оплата через Crypto Bot:\n"
            f"• Сумма: {invoice['amount']} {invoice['asset']}\n"
            f"• Ссылка: {invoice['pay_url']}\n"
            f"ID заказа: {order_id}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✅ Проверить оплату", callback_data=f"check_crypto_{order_id}")],
                [InlineKeyboardButton(text="❌ Отмена", callback_data=f"cancel_crypto_{order_id}")]
            ])
        )
    except Exception as e:
        logging.error(f"Crypto payment error: {str(e)}")
        await callback.answer("⚠️ Ошибка при создании платежа")

@router.callback_query(F.data.startswith("check_crypto_"))
async def check_crypto_payment(callback: CallbackQuery):
    order_id = callback.data.split('_')[2]
    try:
        order = orders.get(order_id)
        if not order:
            await callback.answer("❌ Заказ не найден")
            return
        headers = {"Crypto-Pay-API-Token": crypto_bot_token}
        response = requests.get(
            "https://pay.crypt.bot/api/getInvoices",
            params={"invoice_ids": order["invoice_id"]},
            headers=headers
        )
        response_data = response.json()
        if not response_data.get("ok"):
            await callback.answer("❌ Ошибка проверки платежа")
            return
        invoice = response_data["result"]["items"][0]
        if invoice["status"] == "paid":
            orders[order_id]["status"] = "waiting_number"
            save_orders()
            item = await get_item_by_id(order["item_id"])
            await notify_admin(
                bot=callback.bot,
                order_id=order_id,
                user_id=order["user_id"],
                item_name=item.name,
                payment_method="Crypto"
            )
            await callback.message.edit_text("✅ Платеж подтвержден! Ожидайте данные.")
        elif invoice["status"] in ["active", "pending"]:
            await callback.answer("⌛ Платеж еще не получен")
        else:
            await callback.answer("❌ Платеж отменен")
            del orders[order_id]
            save_orders()
    except Exception as e:
        logging.error(f"Check crypto error: {str(e)}")
        await callback.answer("⚠️ Ошибка проверки")

@router.callback_query(F.data.startswith("cancel_crypto_"))
async def cancel_crypto_payment(callback: CallbackQuery):
    order_id = callback.data.split('_')[2]
    if order_id in orders:
        del orders[order_id]
        save_orders()
    await callback.message.delete()
    await callback.answer("❌ Платеж отменен")

@router.callback_query(F.data.startswith("pay_card_"))
async def pay_with_card(callback: CallbackQuery, state: FSMContext):
    item_id = callback.data.split('_')[2]
    item = await get_item_by_id(item_id)
    await state.update_data(item_id=item_id, amount=item.price)
    await callback.message.answer(
        f"💳 Оплата картой РФ\nСумма: {item.price} RUB\nНажмите кнопку ниже чтобы создать платеж",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Создать платеж", callback_data="create_card_payment")]
        ])
    )
    await callback.answer()

@router.callback_query(F.data == "create_card_payment")
async def create_card_payment(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    item = await get_item_by_id(data['item_id'])
    comment = f"pay_{callback.from_user.id}_{datetime.now().timestamp()}"
    link = generate_payment_link(item.price, comment)
    payments[callback.from_user.id] = {
        'amount': item.price,
        'comment': comment,
        'created_at': datetime.now(),
        'item_id': data['item_id']
    }
    await callback.message.answer(
        f"🔗 Ссылка для оплаты: {link}\nПосле оплаты нажмите кнопку проверки",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Проверить оплату", callback_data="check_card_payment")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_payment")]
        ])
    )
    await callback.answer()

@router.callback_query(F.data == "check_card_payment")
async def check_card_payment_handler(callback: CallbackQuery):
    payment_info = payments.get(callback.from_user.id)
    if not payment_info:
        await callback.answer("❌ Платеж не найден")
        return
    if datetime.now() - payment_info['created_at'] > timedelta(minutes=10):
        await callback.message.answer("⌛ Время оплаты истекло")
        payments.pop(callback.from_user.id)
        return
    result = await check_payment(payment_info['comment'], payment_info['amount'])
    if result:
        item = await get_item_by_id(payment_info['item_id'])
        await callback.message.answer(
            f"✅ Платеж подтвержден!\nДанные аккаунта:\n"
            f"Логин: {item.login}\nПароль: {item.password}"
        )
        payments.pop(callback.from_user.id)
    else:
        await callback.answer("⌛ Платеж еще не поступил")

@router.callback_query(F.data == "cancel_payment")
async def cancel_payment(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    if callback.from_user.id in payments:
        payments.pop(callback.from_user.id)
    await callback.message.delete()
    await callback.answer("❌ Платеж отменен")

@router.callback_query(F.data == "profile")
async def show_profile(callback: CallbackQuery):
    user_id = callback.from_user.id
    try:
        user = await get_user(user_id)
        purchases = await get_user_purchases(user_id)
        profile_text = (
            f"👤 <b>Ваш профиль</b>\n\n"
            f"🆔 ID: <code>{user_id}</code>\n"
            f"📅 Регистрация: {user.registered_at.strftime('%d.%m.%Y %H:%M')}\n"
            f"🛒 Покупок: {len(purchases)}\n"
            f"👥 Рефералов: {user.referrals}\n"
            f"💸 Баланс: {user.balance} RUB\n\n"
            f"🔗 Реферальная ссылка: https://t.me/alfah0stbot?start={user_id}"
        )
        new_media = types.InputMediaPhoto(
            media="AgACAgQAAxkBAAMEaJvAKelwUJ3FyF2K28N4LVSPrpcAAiTKMRuGWOFQ-eq_9D5tqiQBAAMCAAN5AAM2BA",
            caption=profile_text,
            parse_mode=ParseMode.HTML
        )
        await callback.message.edit_media(
            media=new_media,
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Назад", callback_data="main")]
                ]
            )
        )
        await callback.answer()
    except Exception as e:
        logging.error(f"Profile error: {str(e)}")
        await callback.answer("⚠️ Ошибка загрузки профиля")

@router.callback_query(F.data == "purchase_history")
async def purchase_history(callback: CallbackQuery):
    user_id = callback.from_user.id
    purchases = await get_user_purchases(user_id)
    if not purchases:
        history_text = "📜 <b>История покупок</b>\n\nУ вас пока нет покупок."
    else:
        history_text = "📜 <b>Последние 5 покупок:</b>\n\n"
        for purchase in purchases[:5]:
            item = await get_item_by_id(purchase.item_id)
            history_text += f"• {item.name} - {purchase.date.strftime('%d.%m.%Y')}\n"
    new_media = types.InputMediaPhoto(
        media="AgACAgQAAxkBAAMMaJvBVw5xMUj1oc6kPPaHRIjnzhsAAm3LMRtzVOBQqtd_8MzFFMQBAAMCAAN5AAM2BA",
        caption=history_text,
        parse_mode=ParseMode.HTML
    )
    await callback.message.edit_media(
        media=new_media,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="profile")]
            ]
        )
    )
    await callback.answer()

@router.callback_query(F.data == "referral")
async def referral_system(callback: CallbackQuery):
    user_id = callback.from_user.id
    user = await get_user(user_id)
    referral_text = (
        "🎁 <b>Реферальная система</b>\n\n"
        f"👥 Приглашено пользователей: {user.referrals}\n"
        f"💰 Заработано: {user.referrals * 50} RUB\n\n"
        "Приглашайте друзей и получайте 10% с их покупки\n"
        f"Ваша реферальная ссылка:\nhttps://t.me/alfah0st?start={user_id}"
    )
    new_media = types.InputMediaPhoto(
        media="AgACAgQAAxkBAAMOaJvBgKPQzZfGA4HEV3NnW1KZ8vQAAufKMRvHC-BQWNf-qW3dZlgBAAMCAAN5AAM2BA",
        caption=referral_text,
        parse_mode=ParseMode.HTML
    )
    await callback.message.edit_media(
        media=new_media,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="profile")]
            ]
        )
    )
    await callback.answer()

@router.message(F.reply_to_message, F.from_user.id == ADMIN_ID)
async def handle_admin_reply(message: Message):
    try:
        if not message.reply_to_message:
            await message.answer("❌ Ответьте на сообщение с заказом")
            return
        admin_message_id = message.reply_to_message.message_id
        order_id = next((
            oid for oid, order in orders.items()
            if order.get("admin_message_id") == admin_message_id
        ), None)
        if not order_id:
            await message.answer("❌ Заказ не найден")
            return
        order = orders[order_id]
        if order["status"] == "waiting_number":
            order["number"] = message.text
            order["status"] = "number_sent"
            await message.bot.send_message(
                order["user_id"],
                f"🔢 Ваш номер: {message.text}\nОжидайте код активации!"
            )
            await message.answer(f"✅ Номер для заказа {order_id} отправлен!")
        elif order["status"] == "number_sent":
            order["code"] = message.text
            order["status"] = "completed"
            await message.bot.send_message(
                order["user_id"],
                f"🔐 Ваш код активации: {message.text}\nСпасибо за покупку! 🛍️"
            )
            await message.answer(f"✅ Код для заказа {order_id} отправлен!")
        else:
            await message.answer(f"⚠️ Заказ {order_id} уже завершен")
        save_orders()
    except Exception as e:
        logging.error(f"Admin reply error: {str(e)}")
        await message.answer(f"⚠️ Ошибка: {str(e)}")

# Main function
async def main():
    await async_main()
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Exit")