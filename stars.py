import asyncio
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from aiogram import Router
from aiogram.types import CallbackQuery, Message, LabeledPrice
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
import requests
import logging
import aiohttp
from datetime import datetime, timedelta
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import F
# ========================= КОНФИГ =========================
TOKEN = "8003886936:AAH8hLax_qbdP7dQVKJyJYCBP9v-zc17Bbg"
PROVIDER_TOKEN = ""  # токен для Telegram Payments
COURSE = 1.38  # 1 звезда = 1.4 рубля
API_KEY = "ВАШ_API_KEY"  # Твой API ключ для LZT.Market
payments = {}  # словарь для хранения текущих платежей

router = Router()
import sqlite3

# ========================= БАЗА ДАННЫХ =========================
DB_PATH = "users.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            registered_at TEXT
        )
    """)
    conn.commit()
    conn.close()

def register_user(user: Message):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR IGNORE INTO users (user_id, username, first_name, last_name, registered_at)
        VALUES (?, ?, ?, ?, ?)
    """, (
        user.from_user.id,
        user.from_user.username or "",
        user.from_user.first_name or "",
        user.from_user.last_name or "",
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    conn.commit()
    conn.close()

# ========================= СОСТОЯНИЯ =========================
class BuyStars(StatesGroup):
    choose_recipient = State()
    enter_friend = State()
    enter_amount = State()

class SellStars(StatesGroup):
    choose_method = State()
    enter_requisites = State()
    enter_amount = State()

class Calculator(StatesGroup):
    rub_to_stars = State()
    stars_to_rub = State()

# ========================= ГЛАВНОЕ МЕНЮ =========================
main_menu_text = (
    "<b>💫Главное меню</b>\n"
    "<blockquote>Привет, наш бот создан для покупки Telegram Stars.\n"
    "Быстро, дешево, безопасно.</blockquote>\n<b>Выбери действие👇</b>"
)
main_menu_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="⭐ Купить Telegram Stars ⭐", callback_data="buy_stars")],
    [InlineKeyboardButton(text="💰 Продать Telegram Stars 💰", callback_data="sell_stars")],
    [
        InlineKeyboardButton(text="🛒 Мои покупки", callback_data="my_purchases"),
        InlineKeyboardButton(text="🧮 Калькулятор", callback_data="calculator"),
    ],
    [
        InlineKeyboardButton(text="🆘 Поддержка", callback_data="support"),
        InlineKeyboardButton(text="💬 Отзывы", callback_data="reviews"),
    ],
    [InlineKeyboardButton(text="ℹ️ Информация", callback_data="info")]
])
CHANNEL_USERNAME = "@aIfanews"  # Замените на ваш канал

async def check_subscription(user_id: int, bot: Bot) -> bool:
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        # Статусы, при которых пользователь считается подписанным
        if member.status in ["creator", "administrator", "member"]:
            return True
        else:
            return False
    except Exception:
        return False

# Проверка перед началом работы с ботом
async def start_cmd(message: Message, state: FSMContext = None):
    bot = message.bot

    # Регистрируем пользователя в базе
    register_user(message)

    # Проверка подписки
    subscribed = await check_subscription(message.from_user.id, bot)
    if not subscribed:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Подписаться на канал", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")]
        ])
        await message.answer(
            "<b>❌ Для использования бота необходимо подписаться на канал!</b>",
            reply_markup=kb
        )
        return

    await message.answer(main_menu_text, reply_markup=main_menu_kb)


# ========================= СТАРТ =========================

async def back_to_menu(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text(main_menu_text, reply_markup=main_menu_kb)

# ========================= ПОКУПКА =========================
async def buy_stars(call: CallbackQuery, state: FSMContext):
    text = (
        f"<b>💫 Покупка Telegram Stars</b>\n\n"
        f"<blockquote>Курс: 1 ⭐ = {COURSE} ₽\n"
        "Выберите, для кого хотите купить звезды:\n"
        "<b>Если выбираете себя, убедитесь, что у вас есть username</b></blockquote>"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 Для себя", callback_data="for_me")],
        [InlineKeyboardButton(text="🎁 Для друга", callback_data="for_friend")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_menu")]
    ])
    await call.message.edit_text(text, reply_markup=kb)
    await state.set_state(BuyStars.choose_recipient)

async def for_me(call: CallbackQuery, state: FSMContext):
    await state.update_data(recipient=call.from_user.username or call.from_user.full_name)
    text = (
        f"<b>💫 Покупка для себя</b>\n\n"
        f"<blockquote>Курс: 1 ⭐ = {COURSE} ₽\n"
        "Введите количество звёзд (от 50 до 50 000):</blockquote>"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="back_menu")]
    ])
    await call.message.edit_text(text, reply_markup=kb)
    await state.set_state(BuyStars.enter_amount)

async def for_friend(call: CallbackQuery, state: FSMContext):
    text = (
        "<b>🎁 Покупка для друга</b>\n\n"
        "<blockquote>Введите username друга (например: @username).\n"
        "Звёзды будут отправлены именно этому пользователю.</blockquote>"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="back_menu")]
    ])
    await call.message.edit_text(text, reply_markup=kb)
    await state.set_state(BuyStars.enter_friend)

async def set_friend(message: Message, state: FSMContext):
    await state.update_data(recipient=message.text.strip())
    text = (
        f"<b>🎁 Покупка для @{message.text.strip()}</b>\n\n"
        f"<blockquote>Курс: 1 ⭐ = {COURSE} ₽\n"
        "Введите количество звёзд (от 50 до 50 000):</blockquote>"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="back_menu")]
    ])
    await message.answer(text, reply_markup=kb)
    await state.set_state(BuyStars.enter_amount)

async def set_amount(message: Message, state: FSMContext):
    try:
        amount = int(message.text.strip())
        if amount < 50 or amount > 50000:
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="❌ Отмена", callback_data="back_menu")]
            ])
            await message.answer(
                "<blockquote>Количество звёзд должно быть от 50 до 50 000!</blockquote>",
                reply_markup=kb
            )
            return

        data = await state.get_data()
        recipient = data.get("recipient", "неизвестно")
        total = amount * COURSE

        # Сохраняем количество звезд
        await state.update_data(amount=amount)

        text = (
            f"<b>💳 Выберите способ оплаты</b>\n\n"
            f"<blockquote>Получатель: @{recipient}\n"
            f"Количество: {amount} ⭐\n"
            f"Сумма: {total // 1} ₽</blockquote>"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💳 Карта РФ", callback_data="create_card_payment")],
            [InlineKeyboardButton(text="🪙 Криптобот", callback_data="pay_crypto")],
            [InlineKeyboardButton(text="🇷🇺СПБ", callback_data="pay_sbp")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="back_menu")]
        ])
        await message.answer(text, reply_markup=kb)
    except ValueError:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="back_menu")]
        ])
        await message.answer(
            "<blockquote>Введите корректное число!</blockquote>",
            reply_markup=kb
        )


CRYPTO_BOT_TOKEN = "319088:AAsRs5zFKk5DRCFRsREHtde63rJDzZducjF"
# ========================= ПРОДАЖА =========================
@router.callback_query(F.data == "sell_stars")
async def sell_stars_menu(callback: CallbackQuery, state: FSMContext):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🪙 Криптокошелёк", callback_data="sell_crypto")],
        [InlineKeyboardButton(text="💳 Номер карты", callback_data="sell_card")],
        [InlineKeyboardButton(text="📱 Номер телефона", callback_data="sell_phone")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_menu")]
    ])
    text = (
        "<b>💫 Продажа Telegram Stars</b>\n\n"
        "<blockquote>Выберите метод вывода средств:\n"
        "- Опишите реквизиты максимально подробно, чтобы администрация могла правильно отправить средства.</blockquote>"
    )
    await callback.message.edit_text(text, reply_markup=kb)
    await state.set_state(SellStars.choose_method)

@router.callback_query(F.data.startswith("sell_"), SellStars.choose_method)
async def choose_sell_method(callback: CallbackQuery, state: FSMContext):
    method = callback.data.split("_")[1]
    await state.update_data(method=method)

    prompts = {
        "crypto": "💲Введите адрес вашего криптокошелька (например: USDT, ETH):",
        "card": "💳Введите номер вашей карты: (16 цифр, без пробелов.)",
        "phone": "📞Введите номер телефона: (формат +7(XXX)XXX-XX-XX)"
    }

    text = f"<b>💳 Метод: {method.upper()}</b>\n\n<blockquote>{prompts[method]}</blockquote>"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="back_menu")]
    ])
    await callback.message.edit_text(text, reply_markup=kb)
    await state.set_state(SellStars.enter_requisites)

@router.message(SellStars.enter_requisites)
async def save_requisites(message: Message, state: FSMContext):
    requisites = message.text.strip()
    await state.update_data(requisites=requisites)

    text = (
        "<b>💫 Продажа Telegram Stars</b>\n\n"
        f"<blockquote>Введите количество звёзд, которое вы хотите продать (от 50 до 50 000):</blockquote>"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="back_menu")]
    ])
    await message.answer(text, reply_markup=kb)
    await state.set_state(SellStars.enter_amount)

async def pay_with_stars(bot: Bot, user_id: int, stars: int):
    price = int(stars * 0.9 // 1)  # цена в копейках
    prices = [LabeledPrice(label=f"{stars} ⭐", amount=price)]
    await bot.send_invoice(
        chat_id=user_id,
        title="Продажа Telegram Stars",
        description=f"Вы продаёте {stars} ⭐. Оплатите счёт ниже.",
        provider_token='',
        currency="XTR",
        prices=prices,
        payload=f"stars_{user_id}_{stars}",
        start_parameter="sell_stars"
    )


@router.message(SellStars.enter_amount)
async def set_sell_amount(message: Message, state: FSMContext):
    try:
        amount = int(message.text.strip())
        if amount < 50 or amount > 50000:
            raise ValueError

        data = await state.get_data()
        method = data.get("method", "неизвестно")
        requisites = data.get("requisites", "неизвестно")

        await state.update_data(amount=amount)

        # Создаём Telegram Invoice
        await pay_with_stars(message.bot, message.from_user.id, amount)

        text = (
            f"<b>💰 Продажа {amount} ⭐</b>\n\n"
            f"<blockquote>Метод: {method}\n"
            f"Реквизиты: {requisites}\n"
            f"Сумма к получению: {amount} ₽ (1⭐ = 0.9₽)\n\n"
            "Счёт на оплату был создан автоматически. Оплатите его через Telegram.</blockquote>"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="back_menu")]
        ])

        await message.answer(text, reply_markup=kb)
        await state.clear()

    except ValueError:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="back_menu")]
        ])
        await message.answer("<blockquote>Введите корректное число (50–50 000)!</blockquote>", reply_markup=kb)


# ========================= КАЛЬКУЛЯТОР =========================
async def calculator(call: CallbackQuery):
    text = (
        "<b>🧮 Калькулятор стоимости</b>\n\n"
        "<blockquote>Выберите действие, чтобы быстро узнать стоимость или количество звёзд.</blockquote>"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐ Сколько звёзд я получу", callback_data="calc_stars")],
        [InlineKeyboardButton(text="💵 Сколько рублей мне нужно", callback_data="calc_rub")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="back_menu")]
    ])
    await call.message.edit_text(text, reply_markup=kb)

async def calc_stars(call: CallbackQuery, state: FSMContext):
    text = (
        "<b>🧮 Калькулятор: рубли → звёзды</b>\n\n"
        "<blockquote>Введите сумму в рублях, чтобы узнать, сколько звёзд вы получите.</blockquote>"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="back_menu")]
    ])
    await call.message.edit_text(text, reply_markup=kb)
    await state.set_state(Calculator.rub_to_stars)
async def calc_rub(call: CallbackQuery, state: FSMContext):
    text = (
        "<b>🧮 Калькулятор: звёзды → рубли</b>\n\n"
        "<blockquote>Введите количество звёзд, чтобы узнать, сколько это будет в рублях.</blockquote>"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="back_menu")]
    ])
    await call.message.edit_text(text, reply_markup=kb)
    await state.set_state(Calculator.stars_to_rub)


async def process_rub_to_stars(message: Message, state: FSMContext):
    try:
        rub = float(message.text.strip())
        stars = rub / COURSE
        text = f"<b>🧮 Результат</b>\n\n<blockquote>За {rub} ₽ вы получите примерно {stars:.2f} ⭐</blockquote>"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="back_menu")]
        ])
        await message.answer(text, reply_markup=kb)
        await state.clear()
    except ValueError:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="back_menu")]
        ])
        await message.answer("<blockquote>Введите корректное число!</blockquote>", reply_markup=kb)

async def process_stars_to_rub(message: Message, state: FSMContext):
    try:
        stars = float(message.text.strip())
        rub = stars * COURSE
        text = f"<b>🧮 Результат</b>\n\n<blockquote>За {stars} ⭐ вы получите примерно {rub:.2f} ₽</blockquote>"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="back_menu")]
        ])
        await message.answer(text, reply_markup=kb)
        await state.clear()
    except ValueError:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="back_menu")]
        ])
        await message.answer("<blockquote>Введите корректное число!</blockquote>", reply_markup=kb)
# ========================= ОТЗЫВЫ =========================
@router.callback_query(F.data == "reviews")
async def reviews_handler(callback: CallbackQuery):
    text = "<b>💬 Отзывы</b>\n\n<blockquote>Скоро будет!</blockquote>"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_menu")]
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")


# ========================= ПОДДЕРЖКА / ИНФО =========================
async def support(call: CallbackQuery):
    await call.message.edit_text("<b>Поддержка</b>\n\n<blockquote>По всем вопросам писать @qvvor.</blockquote>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data="back_menu")]]))

async def info(call: CallbackQuery):
    text = (
        "<b>Часто задаваемые вопросы:</b>\n\n"
        "— <b>Как происходит выдача товара?</b>\n"
        "Звёзды вы получаете прямо на указанный при оформлении заказа аккаунт, и сразу же можете использовать их так, как пожелаете.\n\n"
        "— <b>Как быстро приходят звезды?</b>\n"
        "Заказы отправляются автоматически и, как правило, приходят в течение 15 секунд.\n\n"
        "— <b>Могу ли я покупать звезды только для себя?</b>\n"
        "Нет, вы можете отправлять подарки любым пользователям, у которых есть @username.\n\n"
        "— <b>Есть ли риск блокировки моего аккаунта или рефанда звезд?</b>\n"
        "Нет, риск отсутствует, так как мы используем официальную платформу Telegram для покупки звёзд. Блокировка или потеря звёзд невозможны."
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data="back_menu")]])
    await call.message.edit_text(text, reply_markup=kb, parse_mode="HTML")



# Генерация ссылки на оплату
def generate_payment_link(amount: int, comment: str) -> str:
    return f"https://lolz.live/payment/balance/transfer?user_id=9502620&amount={amount}&currency=rub&comment={comment}&transfer_hold=false"

# Проверка платежа
async def check_payment(comment: str, amount: int) -> dict:
    url = f"https://api.lzt.market/user/payments?type=income&pmin={amount}&pmax={amount}&comment={comment}&is_hold=false"
    headers = {"authorization": f"Bearer {API_KEY}"}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            data = await response.json()
    return data.get('payments', {})

# Создание платежа
@router.callback_query(F.data == "create_card_payment")
async def create_card_payment(callback: CallbackQuery, state: FSMContext):
    # Сначала получаем данные
    data = await state.get_data()
    recipient = data.get("recipient")
    amount_stars = data.get("amount")

    if not recipient or not amount_stars:
        # Если данных нет — попросим пользователя заново ввести
        await callback.answer("❌ Данные не указаны. Пожалуйста, введите количество звёзд заново.")
        text = f"<b>💫 Покупка Telegram Stars</b>\n\n" \
               f"<blockquote>Курс: 1 ⭐ = {COURSE} ₽\nВведите количество звёзд (от 50 до 50 000):</blockquote>"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="back_menu")]
        ])
        await callback.message.answer(text, reply_markup=kb)
        await state.set_state(BuyStars.enter_amount)
        return

    # Генерация ссылки на оплату и т.д.
    comment = f"pay_{callback.from_user.id}_{datetime.now().timestamp()}"
    total_amount = int(amount_stars * COURSE)
    link = generate_payment_link(total_amount, comment)

    payments[callback.from_user.id] = {
        'amount': total_amount,
        'comment': comment,
        'created_at': datetime.now(),
        'recipient': recipient
    }

    text = (
        f"<b>💳 Оплата картой</b>\n\n"
        f"<blockquote>Получатель: @{recipient}\n"
        f"Количество: {amount_stars} ⭐\n"
        f"Сумма: {total_amount // 1} ₽</blockquote>\n\n"
        "Нажмите кнопку ниже, чтобы перейти к оплате."
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌐 Перейти к оплате", url=link)],
        [InlineKeyboardButton(text="✅ Проверить оплату", callback_data="check_card_payment")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_payment")]
    ])

    await callback.message.answer(text, parse_mode="HTML", disable_web_page_preview=True, reply_markup=kb)
    await callback.answer()



# Проверка оплаты
@router.callback_query(F.data == "check_card_payment")
async def check_card_payment_handler(callback: CallbackQuery):
    payment_info = payments.get(callback.from_user.id)

    if not payment_info:
        await callback.answer("❌ Платеж не найден")
        return

    # Проверка истечения времени
    if datetime.now() - payment_info['created_at'] > timedelta(minutes=10):
        await callback.message.answer("⌛ Время оплаты истекло")
        payments.pop(callback.from_user.id)
        return

    result = await check_payment(payment_info['comment'], payment_info['amount'])

    if result:
        await callback.message.answer(
            f"✅ Платеж подтвержден!\n"
            f"• Получатель: @{payment_info['recipient']}\n"
            f"• Количество: {payment_info['amount'] // COURSE} ⭐"
        )
        payments.pop(callback.from_user.id)

    else:
        await callback.answer("⌛ Платеж еще не поступил")

# Отмена платежа
@router.callback_query(F.data == "cancel_payment")
async def cancel_payment(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    if callback.from_user.id in payments:
        payments.pop(callback.from_user.id)
    await callback.message.delete()
    await callback.answer("❌ Платеж отменен")

@router.callback_query(F.data == "pay_crypto")
async def pay_with_crypto(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    recipient = data.get("recipient")
    amount_stars = data.get("amount")

    if amount_stars is None:
        await callback.answer("❌ Не указано количество звёзд")
        return

    try:
        headers = {
            "Crypto-Pay-API-Token": CRYPTO_BOT_TOKEN,
            "Content-Type": "application/json"
        }

        amount_usdt = round(amount_stars * COURSE / 75 // 1, 2)

        response = requests.post(
            "https://pay.crypt.bot/api/createInvoice",
            headers=headers,
            json={
                "asset": "USDT",
                "amount": f"{amount_usdt}",
                "description": f"Покупка {amount_stars} ⭐ для @{recipient}",
                "payload": f"{callback.from_user.id}_{amount_stars}",
                "paid_btn_url": "https://t.me/alfasRobot",
                "allow_anonymous": False
            }
        )

        response_data = response.json()
        if not response_data.get("ok"):
            await callback.answer("❌ Ошибка создания платежа")
            return

        invoice = response_data["result"]
        pay_url = invoice.get("pay_url") or invoice.get("invoice_url")
        if not pay_url:
            await callback.answer("❌ Не удалось получить ссылку на оплату")
            return

        await callback.message.answer(
            f"<b>💎 Оплата через Crypto Bot:</b>\n"
            f"<blockquote>• Получатель: @{recipient}\n"
            f"• Количество: {amount_stars} ⭐\n"
            f"• Сумма: {invoice['amount']} {invoice['asset']}</blockquote>\n\n"
            "<b>Нажмите кнопку «Оплатить», чтобы перейти в Crypto Bot.</b>",
            parse_mode="HTML",
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="💳 Оплатить", url=pay_url)
                ],
                [
                    InlineKeyboardButton(
                        text="✅ Проверить оплату",
                        callback_data=f"check_crypto_{callback.from_user.id}_{amount_stars}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="❌ Отмена",
                        callback_data=f"cancel_crypto_{callback.from_user.id}_{amount_stars}"
                    )
                ]
            ])
        )

        await state.clear()

    except Exception as e:
        logging.error(f"Crypto payment error: {str(e)}")
        await callback.answer("⚠️ Ошибка при создании платежа")
@router.callback_query(F.data.startswith("cancel_crypto_"))
async def cancel_crypto_payment(callback: CallbackQuery):
    order_id = callback.data.split("_")[2]  # получаем order_id

    # Удаляем заказ из словаря
   # если используешь сохранение на диск

    # Удаляем сообщение с кнопками оплаты
    await callback.message.delete()

    await callback.answer("❌ Платеж отменён")
@router.callback_query(F.data == "pay_sbp")
async def pay_sbp_handler(callback: CallbackQuery, state: FSMContext):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="back_menu")]
    ])

    await callback.message.answer(
        "<b>💸 Оплата через СПБ</b>\n\n"
        "<blockquote>Временно оплата не автоматическая <b>(через @qvvor)</b> скоро будет исправленно.</blockquote>",
        parse_mode="HTML",
        reply_markup=kb
    )
    await callback.answer()


# Словарь для хранения покупок пользователей
user_purchases = {}


# После успешного подтверждения оплаты картой или крипто, сохраняем покупку:
async def save_purchase(user_id: int, recipient: str, amount: int, method: str):
    if user_id not in user_purchases:
        user_purchases[user_id] = []
    user_purchases[user_id].append({
        "recipient": recipient,
        "amount": amount,
        "method": method,
        "date": datetime.now().strftime("%d.%m.%Y %H:%M")
    })


@router.callback_query(F.data == "my_purchases")
async def my_purchases(call: CallbackQuery):
    purchases = user_purchases.get(call.from_user.id)
    if not purchases:
        text = "<b>🛒 Мои покупки</b>\n\n<blockquote>Вы ещё ничего не покупали.</blockquote>"
    else:
        text = "<b>🛒 Мои покупки</b>\n\n<blockquote>"
        for i, p in enumerate(purchases, start=1):
            text += (f"{i}. Получатель: @{p['recipient']}\n"
                     f"   Количество: {p['amount']} ⭐\n"
                     f"   Метод оплаты: {p['method']}\n"
                     f"   Дата: {p['date']}\n\n")
        text += "</blockquote>"
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data="back_menu")]])
    await call.message.edit_text(text, reply_markup=kb, parse_mode="HTML")

# ========================= RUN =========================
async def main():
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher()
    dp.include_router(router)

    # Регистрация команд и обработчиков
    dp.message.register(start_cmd, Command("start"))
    dp.callback_query.register(back_to_menu, F.data == "back_menu")

    dp.callback_query.register(buy_stars, F.data == "buy_stars")
    dp.callback_query.register(for_me, F.data == "for_me", BuyStars.choose_recipient)
    dp.callback_query.register(for_friend, F.data == "for_friend", BuyStars.choose_recipient)
    dp.message.register(set_friend, BuyStars.enter_friend)
    dp.message.register(set_amount, BuyStars.enter_amount)

    dp.callback_query.register(calculator, F.data == "calculator")
    dp.callback_query.register(calc_stars, F.data == "calc_stars")
    dp.callback_query.register(calc_rub, F.data == "calc_rub")
    dp.message.register(process_rub_to_stars, Calculator.rub_to_stars)
    dp.message.register(process_stars_to_rub, Calculator.stars_to_rub)

    dp.callback_query.register(support, F.data == "support")
    dp.callback_query.register(info, F.data == "info")

    await dp.start_polling(bot)

if __name__ == "__main__":
    init_db()
    asyncio.run(main())
