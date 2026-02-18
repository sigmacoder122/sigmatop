from aiogram import F, Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
import app.keyboards as kb
from aiogram.fsm.context import FSMContext
from typing import Union
from aiogram.types import PreCheckoutQuery
from aiogram import types
import requests
import aiohttp
from datetime import datetime, timedelta
from config import crypto_bot_token
import logging
from aiogram import Bot
import os
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import uuid
from typing import Dict, Any
import random
from aiogram.fsm.state import State, StatesGroup
CHANNEL_ID = "@eelge"
PROMO_CODE = "ильяпидор.ком"  # Действующий промокод
PROMO_DISCOUNT = 0.1
API_TOKEN = '8442407027:AAGvxbLeWbzSjNIuVXHL-iFuUG05gViU8bs'
bot = Bot(token=API_TOKEN)

class InfoStates(StatesGroup):
    waiting_info = State()
# Добавляем состояние для капчи
class CaptchaStates(StatesGroup):
    waiting_captcha = State()
class StarGameStates(StatesGroup):
    selecting_item = State()
    choosing_mode = State()
    placing_bet = State()
# Список эмодзи для капчи
EMOJIS = ["😀", "😂", "😍", "🥰", "😎", "🤩", "🥳", "😭", "😡", "🤯", "🥶", "🤢", "👻", "💩", "👾"]
router = Router()
class PaymentStates(StatesGroup):
    waiting_for_card_amount = State()

API_KEY = '774774'  # Ваш ключ от LZT Market
payments = {}  # Временное хранилище платежей

def generate_payment_link(amount: int, comment: str) -> str:
    return f"https://lolz.live/payment/balance/transfer?user_id=9502620&amount={amount}&currency=rub&comment={comment}&transfer_hold=false"

async def check_payment(comment: str, amount: int) -> dict:
    url = f"https://api.lzt.market/user/payments?type=income&pmin={amount}&pmax={amount}&comment={comment}&is_hold=false"
    headers = {"authorization": f"Bearer {API_KEY}"}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            data = await response.json()
    return data.get('payments', {})

@router.callback_query(F.data == "cancel_payment")
async def cancel_payment(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Платеж отменен")
    await callback.answer()

@router.callback_query(F.data == "main")
async def main_menu(callback: CallbackQuery):
    try:
        # Форматируем текст в новом стиле
        main_text = (
            "<b>🔐 добро пожаловать!</b>\n"
            "<blockquote>Лучшие Telegram-аккаунты для ваших целей.\n"
            "Выбирайте нужную категорию в меню ниже.</blockquote>\n\n"
            "<b>📢 Новости:</b>@eelge\n"
            "<b>🛡 Гарантия качества:</b> 24/7"
        )

        new_media = types.InputMediaPhoto(
            media="AgACAgQAAxkBAAIReGmBBY8-2iXa7erdW74PztiMWiRTAAJTEGsb3gYIUEricwettX1qAQADAgADeQADOAQ",
            caption=main_text,
            parse_mode="HTML"
        )

        # Используем edit_message_media через callback.message — это лаконичнее
        await callback.message.edit_media(
            media=new_media,
            reply_markup=kb.settings()
        )
        await callback.answer()

    except Exception as e:
        logging.error(f"Main menu error: {str(e)}")
        # Если сообщение не изменилось, просто гасим уведомление
        await callback.answer()


# Инициализируем пустое множество для хранения ID проверенных пользователей
verified_users = set()
class BonusStates(StatesGroup):
    waiting_for_bonus = State()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    # 1. Проверяем, есть ли пользователь в списке проверенных
    if message.from_user.id in verified_users:
        await state.clear()
        return await show_main_menu(message)

    await state.clear()

    correct_emoji = random.choice(EMOJIS)
    other_emojis = random.sample([e for e in EMOJIS if e != correct_emoji], 5)
    all_emojis = [correct_emoji] + other_emojis
    random.shuffle(all_emojis)

    await state.update_data(correct_emoji=correct_emoji)
    await state.set_state(CaptchaStates.waiting_captcha)

    captcha_text = (
        "<b>🛡 ВЕРИФИКАЦИЯ</b>\n\n"
        "<blockquote>Для доступа к магазину подтвердите, что вы человек.</blockquote>\n"
        f"🎯 <b>НАЖМИТЕ НА:</b> {correct_emoji}"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=e, callback_data=f"check_{e}") for e in all_emojis]
    ])

    await message.answer_photo(
        photo="AgACAgQAAxkBAAIReGmBBY8-2iXa7erdW74PztiMWiRTAAJTEGsb3gYIUEricwettX1qAQADAgADeQADOAQ",
        caption=captcha_text,
        reply_markup=keyboard
    )


@router.callback_query(CaptchaStates.waiting_captcha, F.data.startswith("check_"))
async def process_captcha(callback: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    correct_emoji = user_data.get("correct_emoji")
    selected_emoji = callback.data.split("_")[1]

    if selected_emoji == correct_emoji:
        # 1. Сразу убираем загрузку и мигание
        await callback.answer("Успешно!")

        # 2. Добавляем в белый список
        verified_users.add(callback.from_user.id)

        # 3. Отправляем нижнюю клавиатуру
        await callback.message.answer(
            text="✅ <b>Верификация успешно пройдена!</b>\nМеню доступно внизу.",
            reply_markup=kb.main_reply_keyboard(),
            parse_mode="HTML"
        )

        # 4. Переходим к бонусной игре
        await state.set_state(BonusStates.waiting_for_bonus)

        # Генерируем сетку 3х3
        keyboard = []
        for i in range(3):
            row = []
            for j in range(3):
                row.append(InlineKeyboardButton(text="🎁", callback_data=f"bonus_{i * 3 + j}"))
            keyboard.append(row)

        bonus_kb = InlineKeyboardMarkup(inline_keyboard=keyboard)

        bonus_text = (
            "<b>🎉 СЮРПРИЗ!</b>\n\n"
            "<blockquote>В честь знакомства мы дарим вам <b>бонус</b>!\n"
            "Выберите один из квадратов, чтобы получить приз на баланс:</blockquote>"
        )

        # 5. Меняем сообщение
        await callback.message.edit_caption(
            caption=bonus_text,
            reply_markup=bonus_kb,
            parse_mode="HTML"
        )
    else:
        # Для неверного ответа answer уже есть, он уберет загрузку и покажет алерт
        await callback.answer("⚠️ Неверно! Попробуйте еще раз.", show_alert=True)


# Обрабатываем текст кнопки "🎁 Испытать удачу"
@router.message(F.text == "🎁 Бесплатный аккаунт")
async def gamble_start(message: Message, state: FSMContext):
    # Твой код запуска игры (который мы писали выше)
    # ...
    items = await rq.get_items_by_category_paginated(category_id=1, limit=5)

    if not items:
        await message.answer("Товаров пока нет.")
        return

    keyboard = []
    for item in items:
        keyboard.append([InlineKeyboardButton(
            text=f"{item.name} | 💎 {int(item.price)} руб",
            callback_data=f"gamble_item_{item.id}"
        )])

    text = "<b>🎰 ХАЛЯВА / РОЗЫГРЫШ</b>\nВыберите товар:"

    await message.answer_photo(
        photo="AgACAgQAAxkBAAIRhmmBCKVgYQUdGJR1w487TY2Ow5pHAAJsEGsb3gYIULDY1Wk8kLn4AQADAgADeAADOAQ",
        caption=text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode="HTML"
    )
    await state.set_state(StarGameStates.selecting_item)
@router.callback_query(BonusStates.waiting_for_bonus, F.data.startswith("bonus_"))
async def get_bonus_result(callback: CallbackQuery, state: FSMContext):
    # Список возможных призов
    prizes = [
        "💰 30 RUB на баланс",
        "🎫 Скидка 10% на первый заказ",
        "🔥 Скидка 5% на любой товар",
        "💸 Кешбэк 15% на следующую покупку",
        "💰 15 RUB на баланс",
        "📦 Бесплатный тестовый аккаунт после покупки первого",
        "🍀 Удача! Скидка 20%"
    ]

    # Выбираем случайный приз
    won_prize = random.choice(prizes)

    await state.clear()
    await callback.answer(f"🎁 Вы выиграли: {won_prize}", show_alert=True)

    # Итоговый текст после выигрыша
    main_text = (
        f"<b>🔐 ГЛАВНОЕ МЕНЮ</b>\n\n"
        f"🎁 <b>Ваш бонус:</b> {won_prize}\n"
        "<blockquote>Лучшие Telegram-аккаунты для ваших целей.\n"
        "Выбирайте нужную категорию в меню ниже.</blockquote>\n\n"
        "<b>📢 Новости:</b> @eelge"
    )

    # Переходим в главное меню
    await callback.message.edit_caption(
        caption=main_text,
        reply_markup=kb.settings(),
        parse_mode="HTML"
    )


# Вспомогательная функция для показа меню (чтобы не дублировать код в Start)
async def show_main_menu(message: Message):
    main_text = (
        "<b>🔐 ДОБРО ПОЖАЛОВАТЬ</b>\n\n"
        "<blockquote>Лучшие Telegram-аккаунты для ваших целей.\n"
        "Выбирайте нужную категорию в меню ниже.</blockquote>\n\n"
        "<b>📢 Новости:</b> @eelge"
    )

    await message.answer_photo(
        photo="AgACAgQAAxkBAAIReGmBBY8-2iXa7erdW74PztiMWiRTAAJTEGsb3gYIUEricwettX1qAQADAgADeQADOAQ",
        caption=main_text,
        reply_markup=kb.settings()
    )
@router.callback_query(F.data == "send_start_command")
async def send_start_command(callback: CallbackQuery):
    # Создаем искусственное сообщение с командой /start
    fake_message = types.Message(
        message_id=callback.message.message_id + 1,
        date=datetime.now(),
        chat=callback.message.chat,
        from_user=callback.from_user,
        text="/start"
    )

    # Вызываем обработчик команды /start
    await cmd_start(fake_message)

    # Удаляем предыдущее сообщение
    try:
        await callback.message.delete()
    except:
        pass

    await callback.answer("🔄 Бот перезапущен!")

@router.message(F.photo)
async def photoid(message: Message):
    await message.answer(f"ID photo: {message.photo[-1].file_id}")

@router.message(Command("get_photo"))
async def send_photo(message: Message):
    await message.answer_photo(photo = 'AgACAgQAAxkBAAIC1WiaWTTPLv32vXQonLP_qIj_eUE6AAJGyTEbjW_ZUJTFjk9SE2QNAQADAgADeAADNgQ', caption = "Swag?")


@router.callback_query(F.data == "sigma")
async def sigma(callback: CallbackQuery):
    await callback.answer('')
    await callback.message.edit_text('Sigma', reply_markup=kb.menu)


@router.callback_query(F.data == "check_subscription")
async def check_subscription(callback: CallbackQuery, bot: Bot):
    user_id = callback.from_user.id

    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        if member.status in ["member", "administrator", "creator"]:
            await callback.message.delete()
            await callback.answer("✅ Спасибо за подписку! Теперь вы можете пользоваться ботом.", show_alert=True)
        else:
            await callback.answer("❌ Вы всё ещё не подписаны на канал!", show_alert=True)
    except Exception as e:
        logging.error(f"Subscription check error: {e}")
        await callback.answer("⚠️ Ошибка проверки подписки, попробуйте позже", show_alert=True)


@router.callback_query(F.data == 'buyacc')
async def buy_account(callback: CallbackQuery):
    await callback.answer()

    # Форматируем текст с использованием HTML-тегов
    # 🛒 - эмодзи в заголовке добавляет акцент
    # <blockquote> - создает стильную вертикальную черту слева
    caption_text = (
        "<b>🛒 КАТАЛОГ ТОВАРОВ</b>\n\n"
        "<blockquote>Выберите интересующую категорию аккаунтов из списка ниже:</blockquote>"
    )

    new_media = types.InputMediaPhoto(
        media="AgACAgQAAxkBAAIRgGmBByXL43m-mbTb4IqPfsKQGLZTAAJWEGsb3gYIUI2k2p5oBI0PAQADAgADeAADOAQ",
        caption=caption_text,
        parse_mode="HTML"  # Убедитесь, что parse_mode указан, если он не стоит по умолчанию
    )

    await callback.message.edit_media(
        media=new_media,
        reply_markup=await kb.catigories()
    )



@router.callback_query(F.data.startswith("category_"))
async def show_category_items(callback: CallbackQuery):
    category_id = callback.data.split('_')[1]
    items = await rq.get_item(category_id)

    new_media = types.InputMediaPhoto(
        media="AgACAgQAAxkBAAIRgmmBB9az2LR3mZzyyLrqvt1EKrLXAAJrEGsb3gYIUEPJvAPCt0XpAQADAgADeAADOAQ",
        caption="🌏Выберите страну:"
    )

    await callback.bot.edit_message_media(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        media=new_media,
        reply_markup=await kb.items(category_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("category_"))
async def show_category_items(callback: CallbackQuery):
    category_id = int(callback.data.split('_')[1])

    new_media = types.InputMediaPhoto(
        media="AgACAgQAAxkBAAMKaJvBQ13h8QTp60mHxebmH-Ojw3IAAj_LMRsPPeBQZlOYypQoU4sBAAMCAAN5AAM2BA",
        caption="Выберете аккаунт:"
    )

    keyboard = await kb.items(category_id, 0)

    await callback.bot.edit_message_media(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        media=new_media,
        reply_markup=keyboard
    )
    await callback.answer()


from aiogram.exceptions import TelegramBadRequest
from contextlib import suppress


@router.callback_query(F.data.startswith('items_'))
async def items_pagination(callback: CallbackQuery):
    data = callback.data.split('_')
    category_id = int(data[1])
    page = int(data[2])
    sort_mode = data[3] if len(data) > 3 else "asc"

    keyboard = await kb.items(category_id, page, sort_mode)

    # Используем suppress, чтобы бот не падал при "пустых" обновлениях
    with suppress(TelegramBadRequest):
        await callback.message.edit_reply_markup(reply_markup=keyboard)

    await callback.answer()


@router.callback_query(F.data == "ignore")
async def ignore_callback(callback: CallbackQuery):
    await callback.answer()

@router.callback_query(F.data.startswith("item_"))
async def show_item(callback: CallbackQuery):
    item_id = callback.data.split('_')[1]
    item_data = await rq.get_item_by_id(item_id)

    if not item_data:
        await callback.answer("Товар не найден!")
        return

    category_id = item_data.category
    category_name = await rq.get_category_name(category_id)

    # Форматируем текст с использованием жирного шрифта и блока цитаты
    caption_text = (
        "<b>💈 ИНФОРМАЦИЯ ОБ АККАУНТЕ</b>\n"
        f"<blockquote><b>🏳️ Страна:</b> {item_data.name}\n"
        f"<b>📡 Оператор:</b> любой\n"
        f"<b>💵 Цена:</b> {item_data.price} RUB</blockquote>\n"
        "➖➖➖➖➖➖➖➖➖➖\n"
        "<b>💳 Выберите способ оплаты:</b>"
    )

    new_media = types.InputMediaPhoto(
        media="AgACAgQAAxkBAAIRhmmBCKVgYQUdGJR1w487TY2Ow5pHAAJsEGsb3gYIULDY1Wk8kLn4AQADAgADeAADOAQ",
        caption=caption_text,
        parse_mode="HTML" # Убедись, что parse_mode указан, чтобы теги работали
    )

    await callback.bot.edit_message_media(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        media=new_media,
        reply_markup=await kb.payment_methods(item_id, category_id)
    )
    await callback.answer()


from aiogram.filters import Command
from sqlalchemy import func, select
from datetime import datetime, timedelta
from database.models import async_session, User, Order  # Импортируем из твоего models.py


@router.message(Command("stat"))
async def show_stats(message: Message):
    """Показывает простую статистику бота"""

    # Проверка на админа (замени на свой ID)
    ADMIN_ID = 7658738825  # Укажи свой Telegram ID

    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Эта команда только для администратора")
        return

    try:
        async with async_session() as session:
            # Основные метрики
            total_users = await session.scalar(select(func.count(User.id))) or 0

            # Пользователи за сегодня
            today_start = datetime.now().replace(hour=0, minute=0, second=0)
            today_users = await session.scalar(
                select(func.count(User.id)).where(User.registered_at >= today_start)
            ) or 0

            # Заказы
            total_orders = await session.scalar(select(func.count(Order.id))) or 0
            today_orders = await session.scalar(
                select(func.count(Order.id)).where(Order.date >= today_start)
            ) or 0

            # Балансы
            total_balance = await session.scalar(select(func.sum(User.balance))) or 0

        # Формируем ответ
        stat_text = (
            f"📊 <b>СТАТИСТИКА БОТА</b>\n\n"
            f"👥 <b>Пользователи:</b>\n"
            f"├ Всего: <code>{total_users}</code>\n"
            f"└ Новых сегодня: <code>{today_users}</code>\n\n"

            f"📦 <b>Заказы:</b>\n"
            f"├ Всего: <code>{total_orders}</code>\n"
            f"└ Сегодня: <code>{today_orders}</code>\n\n"

            f"💰 <b>Балансы:</b>\n"
            f"└ Сумма на счетах: <code>{total_balance} ₽</code>\n\n"

            f"🕒 <i>Обновлено: {datetime.now().strftime('%d.%m.%Y %H:%M')}</i>"
        )

        await message.answer(stat_text, parse_mode="HTML")

    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")
# --- 1. НАЖАТИЕ НА КНОПКУ "ПОЛУЧИТЬ БЕСПЛАТНО" ---
# Если используешь Inline кнопку:
@router.callback_query(F.data == "gamble_select_item")
# Если используешь Reply кнопку (внизу экрана):
# @router.message(F.text == "🎁 Получить аккаунт бесплатно")
async def gamble_start(event: Union[CallbackQuery, Message], state: FSMContext):
    # Получаем товары (например, 5 штук из первой категории)
    # Можно сделать выборку рандомных товаров: items = await rq.get_random_items(5)
    items = await rq.get_items_by_category_paginated(category_id=1, limit=5)

    if not items:
        # Универсальный ответ и для callback и для message
        if isinstance(event, CallbackQuery):
            await event.answer("Товаров нет", show_alert=True)
        else:
            await event.answer("Товаров нет")
        return

    # Генерируем список товаров для игры
    keyboard = []
    for item in items:
        # Кнопка для каждого товара
        keyboard.append([InlineKeyboardButton(
            text=f"{item.name} | 💎 {int(item.price)} руб",
            callback_data=f"gamble_item_{item.id}"
        )])

    # Кнопка назад
    keyboard.append([InlineKeyboardButton(text="🔙 В меню", callback_data="main")])

    text = (
        "<b>🎰 ХАЛЯВА / РОЗЫГРЫШ</b>\n\n"
        "<blockquote>Выберите товар, который хотите забрать почти даром.\n"
        "Испытайте удачу за Telegram Stars!</blockquote>\n\n"
        "👇 <b>На какой товар играем?</b>"
    )

    # Отправляем ответ (универсально для Call/Message)
    if isinstance(event, CallbackQuery):
        await event.message.edit_media(
            media=types.InputMediaPhoto(
                media="AgACAgQAAxkBAAIRhmmBCKVgYQUdGJR1w487TY2Ow5pHAAJsEGsb3gYIULDY1Wk8kLn4AQADAgADeAADOAQ",
                # Твоя картинка "Казино"
                caption=text,
                parse_mode="HTML"
            ),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
    else:
        await event.answer_photo(
            photo="AgACAgQAAxkBAAIRhmmBCKVgYQUdGJR1w487TY2Ow5pHAAJsEGsb3gYIULDY1Wk8kLn4AQADAgADeAADOAQ",
            caption=text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
            parse_mode="HTML"
        )

    await state.set_state(StarGameStates.selecting_item)


# --- 2. ВЫБРАЛИ ТОВАР -> ВЫБИРАЕМ РЕЖИМ РИСКА ---
@router.callback_query(StarGameStates.selecting_item, F.data.startswith("gamble_item_"))
async def gamble_mode_select(callback: CallbackQuery, state: FSMContext):
    item_id = int(callback.data.split("_")[2])
    item = await rq.get_item_by_id(item_id)

    # Цены в звездах
    full_price = int(item.price)
    price_50 = max(1, int(full_price * 0.5))  # 50%
    price_15 = max(1, int(full_price * 0.15))  # 15%

    await state.update_data(item_id=item_id, item_name=item.name, p50=price_50, p15=price_15)

    text = (
        f"<b>🎲 ИГРА ЗА: {item.name}</b>\n"
        f"💰 Рыночная цена: {full_price} RUB\n\n"
        "<b>Выберите свои шансы:</b>\n\n"
        f"1️⃣ <b>50/50 (Половина цены)</b>\n"
        f"💳 Стоимость: <b>{price_50} 🌟</b>\n"
        f"🎯 Угадай: Чётное или Нечётное\n\n"
        f"2️⃣ <b>ДЖЕКПОТ (За копейки)</b>\n"
        f"💳 Стоимость: <b>{price_15} 🌟</b>\n"
        f"🎯 Угадай: Число (1 из 6)"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"⚖️ Шанс 50% ({price_50} ⭐️)", callback_data="starmode_50")],
        [InlineKeyboardButton(text=f"🔥 Шанс 16% ({price_15} ⭐️)", callback_data="starmode_15")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="gamble_select_item")]
    ])

    await callback.message.edit_caption(caption=text, reply_markup=kb, parse_mode="HTML")
    await state.set_state(StarGameStates.choosing_mode)


# --- 3. ВЫБИРАЕМ НА ЧТО СТАВИТЬ (ЧИСЛО ИЛИ ЧЕТ/НЕЧЕТ) ---
@router.callback_query(StarGameStates.choosing_mode)
async def gamble_bet_select(callback: CallbackQuery, state: FSMContext):
    mode = callback.data
    data = await state.get_data()
    keyboard = []

    if mode == "starmode_50":
        pay_amount = data['p50']
        task_text = "🔮 <b>На что ставим? (Чет / Нечет)</b>"
        keyboard.append([InlineKeyboardButton(text="2️⃣ ЧЁТНОЕ", callback_data="pay_bet_even")])
        keyboard.append([InlineKeyboardButton(text="1️⃣ НЕЧЁТНОЕ", callback_data="pay_bet_odd")])

    elif mode == "starmode_15":
        pay_amount = data['p15']
        task_text = "🔮 <b>Угадайте число на кубике:</b>"
        keyboard.append([InlineKeyboardButton(text=f"{i} 🎲", callback_data=f"pay_bet_num_{i}") for i in range(1, 4)])
        keyboard.append([InlineKeyboardButton(text=f"{i} 🎲", callback_data=f"pay_bet_num_{i}") for i in range(4, 7)])

    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data=f"gamble_item_{data['item_id']}")])

    await state.update_data(pay_amount=pay_amount)

    text = (
        f"<b>⭐️ ПОДТВЕРЖДЕНИЕ</b>\n\n"
        f"🎁 Приз: <b>{data['item_name']}</b>\n"
        f"💳 Спишется: <b>{pay_amount} Stars</b>\n\n"
        f"{task_text}"
    )

    await callback.message.edit_caption(caption=text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
    await state.set_state(StarGameStates.placing_bet)


# --- 4. ВЫСТАВЛЯЕМ СЧЕТ (INVOICE) ---
@router.callback_query(StarGameStates.placing_bet)
async def send_gamble_invoice(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    # ФОРМИРУЕМ КОРОТКИЙ PAYLOAD (до 128 байт)
    # Мы убрали 'item_name', так как он занимал слишком много места
    payload_data = {
        "t": "g",  # t = type (gamble)
        "id": data['item_id'],  # id товара
        "b": callback.data  # b = bet (ставка)
    }

    await callback.message.answer_invoice(
        title=f"Розыгрыш: {data['item_name']}",
        description="Оплата участия в лотерее. Победа = Автовыдача товара.",
        payload=json.dumps(payload_data),  # Теперь это короткая строка
        currency="XTR",
        prices=[LabeledPrice(label="Ставка", amount=data['pay_amount'])],
        provider_token=""
    )
    await callback.answer()
    await callback.message.delete()


# --- 5. ПРОВЕРКА И БРОСОК (ЭТАПЫ ОПЛАТЫ) ---
@router.pre_checkout_query()
async def gamble_pre_checkout(query: PreCheckoutQuery):
    await query.answer(ok=True)


@router.message(F.successful_payment)
async def gamble_payment_success(message: Message):
    try:
        data = json.loads(message.successful_payment.invoice_payload)
    except:
        return

    # Проверяем, что это оплата именно игры
    if data.get("type") != "gamble": return

    await message.answer("✅ <b>Ставка принята!</b> Бросаем кости...", parse_mode="HTML")

    dice_msg = await message.answer_dice(emoji="🎲")
    result = dice_msg.dice.value
    await asyncio.sleep(4)  # Интрига

    # Логика победы
    bet = data['bet']
    is_win = False

    if "even" in bet and result % 2 == 0:
        is_win = True
    elif "odd" in bet and result % 2 != 0:
        is_win = True
    elif "num" in bet:
        target = int(bet.split("_")[-1])
        if target == result: is_win = True

    if is_win:
        await dice_msg.reply(
            f"🎉 <b>ПОБЕДА! Выпало {result}!</b>\n\n"
            f"🎁 Товар: <b>{data['item_name']}</b>\n"
            f"<i>Данные отправлены ниже...</i>",
            parse_mode="HTML"
        )
        # --- ТУТ ФУНКЦИЯ ВЫДАЧИ ТОВАРА ---
        # await rq.issue_item(message.from_user.id, data['item_id'])
    else:
        # Предлагаем попробовать снова
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Попробовать еще раз", callback_data="gamble_select_item")],
            [InlineKeyboardButton(text="🏠 В меню", callback_data="main")]
        ])

        await dice_msg.reply(
            f"❌ <b>Выпало {result}. Не повезло.</b>\n"
            f"Звезды списаны, товара нет. Попробуем снова?",
            reply_markup=kb,
            parse_mode="HTML"
        )

@router.callback_query(F.data.startswith("pay_stars_"))
async def pay_with_stars(callback: CallbackQuery, state: FSMContext):
    try:
        # 1. Извлекаем данные из callback_data
        # Предполагаем формат pay_stars_{item_id}_{category_id}
        data = callback.data.split('_')
        item_id = data[2]

        item = await rq.get_item_by_id(item_id)
        category_id = item.category  # Получаем категорию из данных товара

        await state.update_data(item_id=item_id, user_id=callback.from_user.id)
        stars_amount = int(item.price // 1.15)

        # ... (код с обновлением caption) ...

        # 2. Передаем аргументы в функцию клавиатуры
        await callback.bot.send_invoice(
            chat_id=callback.from_user.id,
            title=f"Оплата заказа",
            description=f"Товар: {item.name}",
            provider_token="",
            currency="XTR",
            prices=[LabeledPrice(label=f"Оплата {item.name}", amount=stars_amount)],
            payload=f"stars_{item_id}_{callback.from_user.id}",
            start_parameter="create_invoice_stars",
            # ВОТ ТУТ ПЕРЕДАЕМ АРГУМЕНТЫ:
            reply_markup=kb.stars_payment_keyboard(item_id, category_id)
        )

        await callback.answer()

    except Exception as e:
        logging.error(f"Stars payment error: {str(e)}")
        await callback.answer("⚠️ Ошибка при создании платежа")


@router.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)


@router.callback_query(F.data == "purchase_history")
async def purchase_history(callback: CallbackQuery):
    user_id = callback.from_user.id
    purchases = await rq.get_user_purchases(user_id)

    if not purchases:
        history_text = (
            "📜 <b>ИСТОРИЯ ПОКУПОК</b>\n\n"
            "<blockquote>У вас пока нет совершенных заказов.\n"
            "Самое время что-нибудь выбрать!</blockquote>"
        )
    else:
        history_text = "📜 <b>ПОСЛЕДНИЕ ЗАКАЗЫ</b>\n\n"
        # Перебираем последние 5 покупок
        for purchase in purchases[:5]:
            item = await rq.get_item_by_id(purchase.item_id)
            # Проверка: если товар удален из БД, пишем "Товар удален"
            item_name = item.name if item else "📦 Товар удален"
            date_str = purchase.date.strftime('%d.%m.%Y')

            history_text += f"▫️ <b>{item_name}</b>\n"
            history_text += f"└ 📅 <i>{date_str}</i>\n\n"

    # Создаем объект медиа
    new_media = types.InputMediaPhoto(
        media="AgACAgQAAxkBAAIRhmmBCKVgYQUdGJR1w487TY2Ow5pHAAJsEGsb3gYIULDY1Wk8kLn4AQADAgADeAADOAQ",
        caption=history_text,
        parse_mode="HTML"
    )

    # Кнопка возврата в профиль
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад в профиль", callback_data="main")]
        ]
    )

    try:
        await callback.message.edit_media(
            media=new_media,
            reply_markup=keyboard
        )
    except Exception as e:
        logging.error(f"Error in purchase history: {e}")
        # Если фото не грузится или сообщение то же самое
        await callback.answer("Ошибка при загрузке истории", show_alert=True)

    await callback.answer()


@router.callback_query(F.data == "referral")
async def referral_system(callback: CallbackQuery):
    user_id = callback.from_user.id
    user = await rq.get_user(user_id)

    # Заменяем на реальный юзернейм твоего бота без @
    bot_username = "alfasRobot"

    referral_text = (
        "🎁 <b>РЕФЕРАЛЬНАЯ ПРОГРАММА</b>\n\n"
        "<blockquote>Приглашайте друзей и зарабатывайте вместе! \n"
        "Вы получаете <b>50 RUB</b> за каждого активного друга + <b>10%</b> с их покупок.</blockquote>\n\n"
        f"👥 Приглашено друзей: <b>{user.referrals}</b>\n"
        f"💰 Ваш бонус: <b>{user.referrals * 50} RUB</b>\n\n"
        f"🔗 <b>Ваша ссылка для приглашения:</b>\n"
        f"<code>https://t.me/{bot_username}?start={user_id}</code>"
    )

    new_media = types.InputMediaPhoto(
        media="AgACAgQAAxkBAAIRhmmBCKVgYQUdGJR1w487TY2Ow5pHAAJsEGsb3gYIULDY1Wk8kLn4AQADAgADeAADOAQ",
        caption=referral_text,
        parse_mode="HTML"
    )

    # Добавим кнопку "Поделиться", чтобы юзеру было проще переслать ссылку
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📢 Пригласить друга",
                                  switch_inline_query=f"\nЗаходи в лучший магазин аккаунтов! Моя ссылка: https://t.me/{bot_username}?start={user_id}")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="main")]
        ]
    )

    await callback.message.edit_media(
        media=new_media,
        reply_markup=keyboard
    )
    await callback.answer()


# --- 1. ЗАПУСК ИГРЫ: ВЫБОР ТОВАРА ---
@router.callback_query(F.data == "stars_game")
async def stars_game_start(callback: CallbackQuery, state: FSMContext):
    # Берем товары (например, первые 5 из категории 1)
    items = await rq.get_items_by_category_paginated(category_id=1, limit=5)

    if not items:
        await callback.answer("😔 Товаров пока нет", show_alert=True)
        return

    keyboard = []
    for item in items:
        # Для примера: 1 рубль = 1 звезда (или настрой свой курс)
        price_in_stars = int(item.price)
        btn_text = f"{item.name} | ⭐️ {price_in_stars}"
        keyboard.append([InlineKeyboardButton(text=btn_text, callback_data=f"star_item_{item.id}")])

    keyboard.append([InlineKeyboardButton(text="🔙 В меню", callback_data="main")])

    text = (
        "<b>🌟 ЗВЁЗДНАЯ РУЛЕТКА</b>\n\n"
        "<blockquote>Хотите получить топовый аккаунт за копейки?\n"
        "Оплатите часть стоимости Звездами (Telegram Stars) и испытайте удачу!</blockquote>\n\n"
        "👇 <b>Выберите приз, за который будем играть:</b>"
    )

    await callback.message.edit_media(
        media=types.InputMediaPhoto(
            media="AgACAgQAAxkBAAIReGmBBY8-2iXa7erdW74PztiMWiRTAAJTEGsb3gYIUEricwettX1qAQADAgADeQADOAQ",
            # Твоя картинка
            caption=text,
            parse_mode="HTML"
        ),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await state.set_state(StarGameStates.selecting_item)


# --- 2. ВЫБОР РИСКА ---
@router.callback_query(StarGameStates.selecting_item, F.data.startswith("star_item_"))
async def stars_mode_select(callback: CallbackQuery, state: FSMContext):
    item_id = int(callback.data.split("_")[2])
    item = await rq.get_item_by_id(item_id)

    # Расчет цены в звездах (округляем до целого, так как Stars - это целые числа)
    full_price = int(item.price)
    price_50 = max(1, int(full_price * 0.5))  # 50% цены
    price_15 = max(1, int(full_price * 0.15))  # 15% цены

    # Сохраняем данные во временное хранилище
    await state.update_data(item_id=item_id, item_name=item.name, p50=price_50, p15=price_15)

    text = (
        f"<b>🎲 ИГРА ЗА: {item.name}</b>\n"
        f"💎 Полная цена: <s>{full_price} ⭐️</s>\n\n"
        "<b>Выберите стратегию:</b>\n\n"
        f"1️⃣ <b>ШАНС 50/50</b>\n"
        f"├ 💳 Стоимость: <b>{price_50} ⭐️</b>\n"
        f"└ 🎯 Задача: Угадать Чёт или Нечёт\n\n"
        f"2️⃣ <b>ДЖЕКПОТ (1 к 6)</b>\n"
        f"├ 💳 Стоимость: <b>{price_15} ⭐️</b>\n"
        f"└ 🎯 Задача: Угадать точное число кубика"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"⚖️ 50% (Цена: {price_50} ⭐️)", callback_data="starmode_50")],
        [InlineKeyboardButton(text=f"🔥 Риск (Цена: {price_15} ⭐️)", callback_data="starmode_15")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="stars_game")]
    ])

    await callback.message.edit_caption(caption=text, reply_markup=kb, parse_mode="HTML")
    await state.set_state(StarGameStates.choosing_mode)


# --- 3. ВЫБОР КОНКРЕТНОЙ СТАВКИ ---
@router.callback_query(StarGameStates.choosing_mode)
async def stars_bet_select(callback: CallbackQuery, state: FSMContext):
    mode = callback.data
    data = await state.get_data()
    keyboard = []

    if mode == "starmode_50":
        pay_amount = data['p50']
        task_text = "🔮 На что ставите?"
        keyboard.append([InlineKeyboardButton(text="2️⃣ ЧЁТНОЕ (2, 4, 6)", callback_data="pay_bet_even")])
        keyboard.append([InlineKeyboardButton(text="1️⃣ НЕЧЁТНОЕ (1, 3, 5)", callback_data="pay_bet_odd")])

    elif mode == "starmode_15":
        pay_amount = data['p15']
        task_text = "🔮 Какое число выпадет?"
        # Кнопки 1-6
        row1 = [InlineKeyboardButton(text=f"{i} 🎲", callback_data=f"pay_bet_num_{i}") for i in range(1, 4)]
        row2 = [InlineKeyboardButton(text=f"{i} 🎲", callback_data=f"pay_bet_num_{i}") for i in range(4, 7)]
        keyboard.append(row1)
        keyboard.append(row2)

    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="stars_game")])

    # Сохраняем сумму к оплате
    await state.update_data(pay_amount=pay_amount)

    text = (
        f"<b>⭐️ ПОЧТИ ГОТОВО</b>\n\n"
        f"📦 Товар: <b>{data['item_name']}</b>\n"
        f"💳 К оплате: <b>{pay_amount} XTR</b>\n\n"
        f"{task_text}\n"
        "<i>Нажмите на кнопку с прогнозом, чтобы перейти к оплате.</i>"
    )

    await callback.message.edit_caption(caption=text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
    await state.set_state(StarGameStates.placing_bet)


# --- 4. ОТПРАВКА СЧЕТА НА ОПЛАТУ ---
@router.callback_query(StarGameStates.placing_bet)
async def send_stars_invoice(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    bet_type = callback.data  # pay_bet_even, pay_bet_num_6 и т.д.
    amount = data['pay_amount']
    item_id = data['item_id']

    # Формируем payload (скрытые данные чека)
    # Это позволит нам понять, что делать ПОСЛЕ оплаты
    payload_data = {
        "type": "game_bet",
        "user_id": callback.from_user.id,
        "item_id": item_id,
        "bet": bet_type,
        "item_name": data['item_name']
    }

    # Отправляем инвойс
    await callback.message.answer_invoice(
        title=f"Игра за {data['item_name']}",
        description=f"Ставка: {bet_type}. Если выиграете - товар ваш!",
        payload=json.dumps(payload_data),  # Упаковываем данные в строку
        currency="XTR",  # ВАЖНО: Валюта Telegram Stars
        prices=[LabeledPrice(label="Участие", amount=amount)],  # Сумма
        provider_token=""  # Для Stars токен оставляем пустым!
    )
    await callback.answer()


# --- 5. ПОДТВЕРЖДЕНИЕ ПЕРЕД ОПЛАТОЙ (Pre-Checkout) ---
@router.pre_checkout_query()
async def on_pre_checkout(pre_checkout_query: PreCheckoutQuery):
    # Всегда отвечаем OK, если готовы принять оплату
    await pre_checkout_query.answer(ok=True)
import json
import asyncio
from aiogram.types import LabeledPrice, PreCheckoutQuery, ContentType

# --- 6. ФИНАЛ: ОПЛАТА ПРОШЛА -> КИДАЕМ КУБИК ---
from datetime import datetime


# Убедись, что notify_admin и orders импортированы или доступны в этом файле

@router.message(F.successful_payment)
async def payment_handler(message: Message, state: FSMContext):
    # 1. Пытаемся понять, что это за оплата (Рулетка или Обычная)
    payload_str = message.successful_payment.invoice_payload

    try:
        data = json.loads(payload_str)  # Пробуем прочитать как JSON
    except:
        data = None

    # ==============================
    # ВАРИАНТ 1: ЭТО РУЛЕТКА (JSON)
    # ==============================
    if data and data.get("t") == "g":

        # Сразу кидаем сообщение и кубик
        await message.answer("✅ <b>Ставка принята!</b> Испытываем удачу...", parse_mode="HTML")
        dice_msg = await message.answer_dice(emoji="🎲")
        result = dice_msg.dice.value
        await asyncio.sleep(4)  # Пауза для интриги

        # Логика победы
        bet = data['b']
        is_win = False

        if "even" in bet and result % 2 == 0:
            is_win = True
        elif "odd" in bet and result % 2 != 0:
            is_win = True
        elif "num" in bet:
            target = int(bet.split("_")[-1])
            if target == result: is_win = True

        # --- ЕСЛИ ВЫИГРАЛ ---
        if is_win:
            item_id = data['id']
            item = await rq.get_item_by_id(item_id)
            user_id = message.from_user.id

            # --- ТВОЙ КОД СОЗДАНИЯ ЗАКАЗА ---
            order_id = int(datetime.now().timestamp())

            orders[order_id] = {
                'user_id': user_id,
                'item_id': item_id,
                'status': 'waiting_number',
                'payment_method': 'Stars (Win)'
            }

            # Уведомление админу
            try:
                await notify_admin(
                    bot=message.bot,
                    order_id=order_id,
                    user_id=user_id,
                    item_name=item.name,
                    payment_method='Stars (Win)'
                )
            except Exception as e:
                logging.error(f"Ошибка уведомления админа: {e}")

            # Сообщение пользователю (Твой текст)
            await dice_msg.reply(
                f"🎉 <b>ПОБЕДА! Выпало число {result}!</b>\n\n"
                "✅ Оплата прошла успешно! Ожидайте номер, Администрация пришлет его вам в течение 5 минут⌛.",
                reply_markup=kb.settings(),  # Или kb.main_reply_keyboard()
                parse_mode="HTML"
            )

        # --- ЕСЛИ ПРОИГРАЛ ---
        else:
            kb_loss = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Попробовать еще раз", callback_data="gamble_select_item")],
                [InlineKeyboardButton(text="🏠 В меню", callback_data="main")]
            ])
            await dice_msg.reply(
                f"❌ <b>Выпало {result}. Не повезло.</b>\n"
                f"Звезды списаны, товар не получен. Попробуйте снова!",
                reply_markup=kb_loss,
                parse_mode="HTML"
            )

        await state.clear()
        return

    # ==========================================
    # ВАРИАНТ 2: ОБЫЧНАЯ ПОКУПКА (Твой старый код)
    # Если это не JSON рулетки, значит это обычный платеж
    # ==========================================
    try:
        # Тут твой старый метод разбора через split
        # payload_str выглядит как "type_itemId_userId"
        parts = payload_str.split('_')
        if len(parts) >= 3:
            _, item_id, user_id = parts  # Игнорируем префикс, берем ID

            item = await rq.get_item_by_id(int(item_id))
            order_id = int(datetime.now().timestamp())

            orders[order_id] = {
                'user_id': int(user_id),
                'item_id': int(item_id),
                'status': 'waiting_number',
                'payment_method': 'Stars'
            }

            await message.answer(
                "✅ Оплата прошла успешно! Ожидайте номер, Администрация пришлет его вам в течение 5 минут⌛.",
                reply_markup=kb.settings()
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



@router.callback_query(F.data == "profile")
async def show_profile(callback: CallbackQuery):
    user_id = callback.from_user.id

    try:
        user = await rq.get_user(user_id)
        purchases = await rq.get_user_purchases(user_id)

        # Форматируем текст: Заголовок + Цитата + Моноширинный текст для копирования
        profile_text = (
            "<b>👤 ЛИЧНЫЙ КАБИНЕТ</b>\n\n"
            f"<blockquote><b>🆔 Мой ID:</b> <code>{user_id}</code>\n"
            f"<b>🗓 Регистрация:</b> {user.registered_at.strftime('%d.%m.%Y')}\n"
            f"<b>🛒 Покупок:</b> {len(purchases)}\n"
            f"<b>👥 Рефералов:</b> {user.referrals}\n"
            f"<b>💸 Баланс:</b> {user.balance} RUB</blockquote>\n\n"
            f"<b>🔗 Реферальная ссылка:</b>\n"
            f"<code>https://t.me/alfasRobot?start={user_id}</code>"
        )

        new_media = types.InputMediaPhoto(
            media="AgACAgQAAxkBAAIRhmmBCKVgYQUdGJR1w487TY2Ow5pHAAJsEGsb3gYIULDY1Wk8kLn4AQADAgADeAADOAQ",
            caption=profile_text,
            parse_mode="HTML"
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
@router.message(F.successful_payment)
async def process_successful_payment(message: Message, state: FSMContext):
    try:
        payload = message.successful_payment.invoice_payload
        _, item_id, user_id = payload.split('_')

        # Получаем данные о товаре
        item = await rq.get_item_by_id(int(item_id))

        # Генерируем order_id
        order_id = int(datetime.now().timestamp())

        # Сохраняем заказ
        orders[order_id] = {
            'user_id': int(user_id),
            'item_id': int(item_id),
            'status': 'waiting_number',
            'payment_method': 'Stars'
        }

        # Уведомление пользователя
        await message.answer(
            "✅ Оплата прошла успешно! Ожидайте номер, Администрация пришлет его вам в течение 5 минут⌛.",
            reply_markup=kb.settings()
        )

        # Уведомление админу (ИСПРАВЛЕННАЯ СТРОКА)
        await notify_admin(
            bot=message.bot,  # Передаем бота из контекста
            order_id=order_id,
            user_id=int(user_id),
            item_name=item.name,
            payment_method='Stars'
        )

        await state.clear()

    except Exception as e:
        logging.error(f"Payment processing error: {str(e)}")
        await message.answer("⚠️ Произошла ошибка при обработке платежа")


# Клавиатура для оплаты Stars
def stars_payment_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отменить платеж", callback_data="cancel_stars_payment")]
    ])


@router.callback_query(F.data == "cancel_stars_payment")
async def cancel_stars_payment(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.message.delete()
        await callback.answer("❌ Платеж отменен")
        await state.clear()
    except Exception as e:
        logging.error(f"Cancel stars error: {str(e)}")
        await callback.answer("⚠️ Ошибка при отмене")

ORDERS_FILE = "orders.json"
# Обновленная функция уведомления админа
if os.path.exists(ORDERS_FILE):
    with open(ORDERS_FILE, "r") as f:
        orders = json.load(f)
else:
    orders = {}


# Функция сохранения заказов
def save_orders():
    with open(ORDERS_FILE, "w") as f:
        json.dump(orders, f, indent=4)


# Модифицируем функцию создания заказа
ORDERS_FILE = "orders.json"
orders: Dict[str, Dict[str, Any]] = {}

# Загрузка заказов при старте
if os.path.exists(ORDERS_FILE):
    with open(ORDERS_FILE, "r") as f:
        orders = json.load(f)

def save_orders():
    with open(ORDERS_FILE, "w") as f:
        json.dump(orders, f, indent=4, ensure_ascii=False)

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


@router.callback_query(F.data.startswith("pay_crypto_"))
async def pay_with_crypto(callback: CallbackQuery, state: FSMContext):
    item_id = callback.data.split('_')[2]
    item = await rq.get_item_by_id(item_id)
    user_id = callback.from_user.id

    try:
        # Создаем заказ ДО оплаты
        order_id = await create_order(user_id, item.id, "Crypto")

        headers = {
            "Crypto-Pay-API-Token": "319088:AAsRs5zFKk5DRCFRsREHtde63rJDzZducjF",
            "Content-Type": "application/json"
        }

        response = requests.post(
            "https://pay.crypt.bot/api/createInvoice",
            headers=headers,
            json={
                "asset": "USDT",
                "amount": f"{item.price//68:.2f}",
                "description": f"Order #{order_id}",
                "payload": order_id,
                "paid_btn_url": "https://t.me/alfasRobot",
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

        # Получаем прямую ссылку на оплату через Crypto Bot
        crypto_bot_link = f"https://t.me/CryptoBot?start={invoice['bot_invoice_url'].split('=')[-1]}"

        # ОФОРМЛЕНИЕ ТЕКСТА
        payment_text = (
            f"<b>💎 ОПЛАТА ЧЕРЕЗ CRYPTO BOT</b>\n\n"
            f"<blockquote><b>💰 Сумма:</b> {invoice['amount']} {invoice['asset']}\n"
            f"<b>🧾 Заказ:</b> #{order_id}</blockquote>\n"
            "➖➖➖➖➖➖➖➖➖➖➖➖➖\n"
            "<b>📥 Прямой перевод (Сеть TRC-20):</b>\n"
            f"<code>TQFosX3FGMoxs2jCS2EG84wALZgfqLx6yK</code>\n\n"
            "<i>⚠️ После оплаты нажмите кнопку ниже для проверки транзакции.</i>"
        )

        await callback.message.answer(
            text=payment_text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="💳 Оплатить через Crypto Bot",
                        url=crypto_bot_link
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📋 Копировать адрес",
                        callback_data="copy_address"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="✅ Проверить оплату",
                        callback_data=f"check_crypto_{order_id}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="❌ Отмена",
                        callback_data=f"cancel_crypto_{order_id}"
                    )
                ]
            ])
        )

    except Exception as e:
        logging.error(f"Crypto payment error: {str(e)}")
        await callback.answer("⚠️ Ошибка при создании платежа")


@router.callback_query(F.data.startswith("cancel_crypto_"))
async def cancel_crypto_payment(callback: CallbackQuery):
    # Извлекаем order_id из callback_data
    order_id = callback.data.split('_')[2]

    # Здесь можно добавить логику удаления заказа из БД, если это необходимо:
    # await rq.delete_order(order_id)

    try:
        # Редактируем старое сообщение, чтобы пользователь видел статус отмены
        await callback.message.edit_text(
            "<b>❌ ОПЛАТА ОТМЕНЕНА</b>\n\n"
            f"<blockquote>Заказ <b>#{order_id}</b> был успешно аннулирован.</blockquote>\n"
            "Вы можете выбрать другой товар или способ оплаты.",
            parse_mode="HTML"
        )
    except Exception:
        # Если редактирование невозможно (например, сообщение старое), просто удаляем
        await callback.message.delete()
        await callback.answer("Заказ отменен", show_alert=True)

    await callback.answer()
# Обработчик проверки оплаты
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

            # Уведомление админа
            item = await rq.get_item_by_id(order["item_id"])
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


# Обработчик кнопки "Инфо"
@router.callback_query(F.data == "info")
async def info_callback(callback: CallbackQuery):
    predefined_text = (
        "<b>ℹ️ ИНФОРМАЦИЯ И РЕКОМЕНДАЦИИ</b>\n\n"
        "<b>⚠️ ПРАВИЛА ПОСЛЕ ПОКУПКИ:</b>\n"
        "<blockquote>• Не начинайте переписки сразу\n"
        "• Не вступайте в группы и каналы\n"
        "• <b>ЗАПРЕЩЕНО:</b> менять ник, юзернейм и аватарку в первый день\n"
        "• Дайте аккаунту «отлежаться» 24 часа</blockquote>\n\n"
        "<b>📚 О НАШЕМ МАГАЗИНЕ:</b>\n"
        "• Аккаунты строго <b>БЕЗ спам-блока</b>\n"
        "• Поддержка 24/7: @qvvor\n"
        "• Сотрудничество: @qvvor\n\n"
        "<i>⛔️ Возврат средств при слете аккаунта не предусмотрен.</i>"
    )

    new_media = types.InputMediaPhoto(
        media="AgACAgQAAxkBAAIRhmmBCKVgYQUdGJR1w487TY2Ow5pHAAJsEGsb3gYIULDY1Wk8kLn4AQADAgADeAADOAQ",
        caption=predefined_text,
        parse_mode="HTML"
    )

    await callback.message.edit_media(
        media=new_media,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="main")]
        ])
    )
    await callback.answer()


@router.callback_query(F.data == "dogovor")
async def dogovor_callback(callback: CallbackQuery):
    predefined_text = (
        "<b>📜 ПОЛЬЗОВАТЕЛЬСКОЕ СОГЛАШЕНИЕ</b>\n\n"
        "Используя сервис <b>@alfasRobot</b>, вы подтверждаете согласие с условиями:\n\n"
        "<b>1️⃣ СТОИМОСТЬ УСЛУГ</b>\n"
        "<blockquote>Списание средств происходит согласно прейскуранту по завершению операции.</blockquote>\n"
        "<b>2️⃣ ОТМЕНА ОПЕРАЦИЙ</b>\n"
        "<blockquote>Если код из SMS не пришел, вы можете отменить операцию без штрафа.</blockquote>\n"
        "<b>3️⃣ РЕКЛАМА</b>\n"
        "<blockquote>Вы соглашаетесь на получение рассылок от сервиса.</blockquote>\n"
        "<b>4️⃣ ЗАПРЕТЫ</b>\n"
        "<blockquote>Запрещено нарушение законов РФ и других стран.\n"
        "<b>Возврат при слете аккаунта не предусмотрен.</b></blockquote>"
    )

    new_media = types.InputMediaPhoto(
        media="AgACAgQAAxkBAAIRhmmBCKVgYQUdGJR1w487TY2Ow5pHAAJsEGsb3gYIULDY1Wk8kLn4AQADAgADeAADOAQ",
        caption=predefined_text,
        parse_mode="HTML"
    )

    await callback.message.edit_media(
        media=new_media,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="main")]
        ])
    )
    await callback.answer()


# Обработчик кнопки "Назад" в информационном сообщении
from aiogram.exceptions import TelegramBadRequest
from contextlib import suppress


@router.callback_query(F.data == "info_back")
async def info_back(callback: CallbackQuery):
    # Улучшенный текст главного меню
    main_text = (
        "<b>🔐 ДОБРО ПОЖАЛОВАТЬ В МАГАЗИН</b>\n"
        "<blockquote>Лучшие Telegram аккаунты для ваших целей:\n"
        "• Высокая отлега\n"
        "• Низкая цена\n"
        "<b>⚡️ Выберите нужный раздел ниже:</b>"
    )

    new_media = types.InputMediaPhoto(
        media="AgACAgQAAxkBAAIRhmmBCKVgYQUdGJR1w487TY2Ow5pHAAJsEGsb3gYIULDY1Wk8kLn4AQADAgADeAADOAQ",
        caption=main_text,
        parse_mode="HTML"  # Обязательно для работы тегов
    )

    # Используем suppress, чтобы избежать ошибок при повторном нажатии
    with suppress(TelegramBadRequest):
        await callback.message.edit_media(
            media=new_media,
            reply_markup=kb.settings()
        )

    await callback.answer()

# Обработчик ввода текста информации
@router.message(InfoStates.waiting_info)
async def process_info_text(message: Message, state: FSMContext):
    # Сохраняем введенный текст
    info_text = message.text

    # Создаем клавиатуру с кнопкой "Назад"
    back_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="main")]
        ]
    )

    # Отправляем информацию с кнопкой "Назад"
    await message.answer(
        f"ℹ️ Информация:\n\n{info_text}",
        reply_markup=back_keyboard
    )

    await state.clear()


@router.callback_query(F.data.startswith("cancel_pay_"))
async def cancel_stars_payment(callback: CallbackQuery):
    data = callback.data.split('_')
    item_id = data[2]
    category_id = data[3]

    item_data = await rq.get_item_by_id(item_id)

    if not item_data:
        await callback.answer("Ошибка: товар не найден")
        return

    # 1. Удаляем сообщение с инвойсом
    await callback.message.delete()

    # 2. Восстанавливаем текст первого сообщения (информация об аккаунте)
    # ПРИМЕЧАНИЕ: Чтобы восстановить текст в ПРЕДЫДУЩЕМ сообщении,
    # нам нужно знать его ID. Но проще всего отредактировать текущее или
    # отправить заново. Если мы хотим «вернуть» вид выбора оплаты:

    caption_text = (
        "<b>💈 ИНФОРМАЦИЯ ОБ АККАУНТЕ</b>\n"
        f"<blockquote><b>🏳️ Страна:</b> {item_data.name}\n"
        f"<b>📡 Оператор:</b> любой\n"
        f"<b>💵 Цена:</b> {item_data.price} RUB</blockquote>\n"
        "➖➖➖➖➖➖➖➖➖➖\n"
        "<b>💳 Выберите способ оплаты:</b>"
    )

    # Отправляем пользователю сообщение с выбором оплаты заново
    # (так как инвойс был отдельным сообщением)
    await callback.message.answer_photo(
        photo="AgACAgQAAxkBAAIRhmmBCKVgYQUdGJR1w487TY2Ow5pHAAJsEGsb3gYIULDY1Wk8kLn4AQADAgADeAADOAQ",
        caption=caption_text,
        reply_markup=await kb.payment_methods(item_id, category_id),
        parse_mode="HTML"
    )

    await callback.answer("Оплата отменена")

@router.callback_query(F.data == "cancel_payment")
async def cancel_payment(callback: CallbackQuery, state: FSMContext):
    await state.clear()

    # Удаляем сообщение с инвойсом
    try:
        await callback.message.delete()
    except Exception as e:
        logging.error(f"Ошибка при удалении сообщения: {str(e)}")

    # Отправляем подтверждение отмены
    await callback.answer("❌ Платеж отменен")
@router.callback_query(F.data == "cancel_stars_payment")
async def cancel_stars_payment(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.answer()


@router.callback_query(F.data.startswith("pay_card_"))
async def pay_with_card(callback: CallbackQuery, state: FSMContext):
    item_id = callback.data.split('_')[2]
    item = await rq.get_item_by_id(item_id)

    await state.update_data(item_id=item_id, amount=item.price)

    # Красивое пре-превью оплаты
    text = (
        "<b>💳 ОПЛАТА БАНКОВСКОЙ КАРТОЙ</b>\n\n"
        f"<blockquote><b>📦 Товар:</b> {item.name}\n"
        f"<b>💰 Сумма:</b> {item.price} RUB</blockquote>\n"
        "Для генерации персональной ссылки нажмите кнопку ниже 👇"
    )

    await callback.message.answer(
        text=text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💎 Создать платеж", callback_data="create_card_payment")]
        ])
    )
    await callback.answer()


@router.callback_query(F.data == "create_card_payment")
async def create_card_payment(callback: CallbackQuery, state: FSMContext):
    try:
        data = await state.get_data()
        item = await rq.get_item_by_id(data['item_id'])

        comment = f"pay_{callback.from_user.id}_{int(datetime.now().timestamp())}"
        link = generate_payment_link(item.price, comment)

        payments[callback.from_user.id] = {
            'amount': item.price,
            'comment': comment,
            'created_at': datetime.now(),
            'item_id': data['item_id']
        }

        # Красивый текст со ссылкой внутри слова
        payment_ready_text = (
            "<b>🔗 СЧЕТ СФОРМИРОВАН</b>\n\n"
            f"<blockquote><b>💰 К оплате:</b> {item.price} RUB\n"
            f"<b>📝 Комментарий:</b> <code>{comment}</code></blockquote>\n\n"
            f"👉 Оплатите по <b><a href='{link}'>ссылке</a></b> (нажмите на слово)\n"
            "<i>После оплаты обязательно нажмите кнопку проверки.</i>"
        )

        await callback.message.answer(
            text=payment_ready_text,
            parse_mode="HTML",
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="💳 Перейти к оплате", url=link)],
                [InlineKeyboardButton(text="✅ Проверить оплату", callback_data="check_card_payment")],
                [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_payment")]
            ])
        )
        await callback.answer()

    except Exception as e:
        logging.error(f"Card payment creation error: {str(e)}")
        await callback.answer("⚠️ Ошибка при создании платежа", show_alert=True)


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
        item = await rq.get_item_by_id(payment_info['item_id'])
        await callback.message.answer(
            f"✅ Платеж подтвержден!\n"
            f"Данные аккаунта:\n"
            f"Логин: {item.login}\n"
            f"Пароль: {item.password}"
        )
        payments.pop(callback.from_user.id)
        await process_successful_payment(callback.from_user.id, item)

    else:
        await callback.answer("⌛ Платеж еще не поступил")


@router.callback_query(F.data == "cancel_payment")
async def cancel_payment(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    if callback.from_user.id in payments:
        payments.pop(callback.from_user.id)
    await callback.message.delete()
    await callback.answer("❌ Платеж отменен")


orders = {}


ADMIN_ID = 7658738825


async def notify_admin(
        bot: Bot,
        order_id: str,  # Изменено на строковый тип
        user_id: int,
        item_name: str,
        payment_method: str
):
    message = await bot.send_message(
        ADMIN_ID,
        f"🛎 Новый заказ\n"
        f"ID: `{order_id}`\n"  # Добавляем ID в markdown-формате
        f"👤 Пользователь: {user_id}\n"
        f"🛒 Товар: {item_name}\n"
        f"💳 Способ оплаты: {payment_method}\n\n"
        "➖➖➖➖➖➖➖➖➖\n"
        "📨 Для отправки данных ответьте на это сообщение",
        parse_mode="Markdown"
    )

    # Сохраняем ID сообщения с заказом
    orders[order_id]["admin_message_id"] = message.message_id
    save_orders()
from aiogram.filters import CommandObject

user_balances = {}  # словарь: user_id -> баланс stars

def save_balances():
    with open("balances.json", "w") as f:
        json.dump(user_balances, f, indent=4)

# Пример команды для возврата


from aiogram.methods.refund_star_payment import RefundStarPayment

@router.message(Command("ref"))
async def refund(message: types.Message):
    args = message.text.split()[1:]  # Получаем аргументы после команды
    if not args:
        await message.answer("❌ Укажите ID транзакции для возврата Stars.")
        return

    charge_id = args[0]  # ID платежа Stars
    user_id = message.from_user.id  # ID пользователя, который совершил оплату

    try:
        # Вызываем метод RefundStarPayment
        result: bool = await message.bot(RefundStarPayment(
            user_id=user_id,
            telegram_payment_charge_id=charge_id
        ))

        if result:
            await message.answer("✅ Stars успешно возвращены.")
        else:
            await message.answer("❌ Не удалось вернуть Stars. Проверьте ID транзакции.")
    except Exception as e:
        await message.answer(f"⚠️ Ошибка при возврате Stars: {e}")



def load_balances():
    global user_balances
    try:
        with open("balances.json", "r") as f:
            user_balances = json.load(f)
    except FileNotFoundError:
        user_balances = {}





@router.message(F.reply_to_message, F.from_user.id == ADMIN_ID)
async def handle_admin_reply(message: Message):
    try:
        if not message.reply_to_message:
            await message.answer("❌ Ответьте на сообщение с заказом")
            return

        # Получаем ID сообщения, на которое ответили
        admin_message_id = message.reply_to_message.message_id

        # Ищем заказ по ID сообщения
        order_id = next((
            oid for oid, order in orders.items()
            if order.get("admin_message_id") == admin_message_id
        ), None)

        if not order_id:
            await message.answer("❌ Заказ не найден")


        order = orders[order_id]

        # Определяем тип данных для отправки
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




class PromoStates(StatesGroup):
    waiting_promo = State()

# Обработчик кнопки "Промокод"
@router.callback_query(F.data == "promo_code")
async def promo_code(callback: CallbackQuery, state: FSMContext):
    text = (
        "<b>🎫 АКТИВАЦИЯ ПРОМОКОДА</b>\n\n"
        "<blockquote>Введите ваш секретный код в чат.\n"
        "Бонусы будут зачислены мгновенно!</blockquote>"
    )

    # Создаем кнопку отмены
    # Убедись, что callback_data "info_back" у тебя обрабатывается для возврата в меню
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_promo")]
    ])

    await callback.message.edit_caption(
        caption=text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await state.set_state(PromoStates.waiting_promo)
    await callback.answer()


@router.callback_query(F.data == "cancel_promo")
async def cancel_promo(callback: CallbackQuery, state: FSMContext):
    await state.clear()  # Сбрасываем ожидание ввода промокода

    # Возвращаем вид главного меню
    main_text = (
        "<b>🔐 ДОБРО ПОЖАЛОВАТЬ В МАГАЗИН</b>\n\n"
        "<blockquote>Лучшие Telegram аккаунты для ваших целей:\n"
        "• Высокая отлежка\n"
        "• Чистые прокси\n"
        "• Форматы Session + TData</blockquote>\n\n"
        "<b>⚡️ Выберите нужный раздел ниже:</b>"
    )

    with suppress(TelegramBadRequest):
        await callback.message.edit_caption(
            caption=main_text,
            reply_markup=kb.settings(),  # Твоя клавиатура главного меню
            parse_mode="HTML"
        )

    await callback.answer("Действие отменено")

# Обработчик ввода промокода
@router.message(PromoStates.waiting_promo)
async def check_promo(message: Message, state: FSMContext):
    user_input = message.text.strip().lower()

    # Список доступных промокодов
    valid_promos = [PROMO_CODE.lower(), 'alfastars']

    if user_input in valid_promos:
        await state.update_data(promo_applied=True)

        success_text = (
            "<b>✅ ПРОМОКОД АКТИВИРОВАН</b>\n\n"
            "<blockquote>💳 Ваша скидка: <b>10%</b>\n"
            "📌 Статус: <b>Применится при следующей оплате</b></blockquote>\n"
            "<i>Удачных покупок в Alfas Shop!</i>"
        )
        await message.answer(success_text)
        await state.clear()
    else:
        error_text = (
            "<b>❌ ОШИБКА АКТИВАЦИИ</b>\n\n"
            "Такого промокода не существует или его срок действия истек.\n"
            "<i>Попробуйте ввести другой или вернитесь в меню.</i>"
        )
        await message.answer(error_text)
        # Состояние НЕ сбрасываем (state.clear не пишем), чтобы юзер мог попробовать еще раз
        # Либо добавь кнопку "Отмена"

from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import app.database.requests as rq


# Добавляем состояние для рассылки
class BroadcastStates(StatesGroup):
    waiting_broadcast_text = State()


# Обработчик команды /all (только для админа)
@router.message(Command("all"), F.from_user.id == ADMIN_ID)
async def broadcast_command(message: Message, state: FSMContext):
    await message.answer("Введите текст для рассылки:")
    await state.set_state(BroadcastStates.waiting_broadcast_text)


@router.message(BroadcastStates.waiting_broadcast_text, F.from_user.id == ADMIN_ID)
async def process_broadcast_text(message: Message, state: FSMContext):
    broadcast_text = message.text
    users = await rq.get_all_users()  # Получаем всех пользователей из базы

    success_count = 0
    fail_count = 0

    for user in users:
        try:
            # Используем user.tg_id вместо user.id
            await message.bot.send_message(user.tg_id, broadcast_text)
            success_count += 1
        except Exception as e:
            print(f"Ошибка отправки пользователю {user.tg_id}: {e}")
            fail_count += 1

    await message.answer(
        f"✅ Рассылка завершена\n"
        f"▪️ Успешно: {success_count}\n"
        f"▪️ Не удалось: {fail_count}"
    )
    await state.clear()

