
import asyncio
import logging

from aiogram import Bot, Dispatcher


from app.handlers import router
from app.database.models import async_main
from app.middlewares import SubscriptionMiddleware
TOKEN = '8442407027:AAGvxbLeWbzSjNIuVXHL-iFuUG05gViU8bs'
crypto_bot_token = '319088:AAsRs5zFKk5DRCFRsREHtde63rJDzZducjF'
CHANNEL_ID = "@aIfanews"

bot = Bot(token=TOKEN)
dp = Dispatcher(bot=bot)
# После создания Dispatcher
dp = Dispatcher()

# Регистрируем middleware
dp.message.middleware.register(SubscriptionMiddleware(bot))
dp.callback_query.middleware.register(SubscriptionMiddleware(bot))
# Добавьте для других типов событий при необходимости
dp.inline_query.middleware.register(SubscriptionMiddleware(bot))
async def main():
    await async_main()
    dp.include_router(router)
    await dp.start_polling(bot)


from aiogram import F, Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, LabeledPrice, PreCheckoutQuery
import app.keyboards as kb
from aiogram.fsm.context import FSMContext
import app.database.requests as rq
from aiogram import types
import requests
from aiogram.fsm.state import State, StatesGroup
import aiohttp
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime, timedelta
from config import crypto_bot_token
import logging
from aiogram import Bot
import re
import os
import json
from aiogram.utils.markdown import bold
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import uuid
from typing import Dict, Any
import random
from aiogram.fsm.state import State, StatesGroup

CHANNEL_ID = "@aIfanews"
PROMO_CODE = "ильяпидор.ком"  # Действующий промокод
PROMO_DISCOUNT = 0.1


class InfoStates(StatesGroup):
    waiting_info = State()


# Добавляем состояние для капчи
class CaptchaStates(StatesGroup):
    waiting_captcha = State()


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
    await callback.answer()
    new_media = types.InputMediaPhoto(
        media="AgACAgQAAxkBAAMEaJvAKelwUJ3FyF2K28N4LVSPrpcAAiTKMRuGWOFQ-eq_9D5tqiQBAAMCAAN5AAM2BA",
        caption='🔐 Добро пожаловать в магазин Telegram-аккаунтов!'
    )
    await callback.bot.edit_message_media(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        media=new_media,
        reply_markup=kb.settings()  # Добавьте скобки здесь
    )


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    # Сбрасываем текущее состояние
    await state.clear()
    correct_emoji = random.choice(EMOJIS)
    # Создаем список из 6 уникальных эмодзи (1 правильный + 5 случайных)
    emojis = [correct_emoji] + random.sample([e for e in EMOJIS if e != correct_emoji], 5)
    random.shuffle(emojis)  # Перемешиваем

    # Сохраняем правильный ответ в состоянии
    await state.update_data(correct_emoji=correct_emoji)
    await state.set_state(CaptchaStates.waiting_captcha)

    # Регистрируем/обновляем пользователя
    await rq.set_user(message.from_user.id)

    # Отправляем приветственное сообщение
    await message.answer_photo(
        photo="AgACAgQAAxkBAAMEaJvAKelwUJ3FyF2K28N4LVSPrpcAAiTKMRuGWOFQ-eq_9D5tqiQBAAMCAAN5AAM2BA",
        caption='🔐 Добро пожаловать в магазин Telegram-аккаунтов!',
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
    await message.answer_photo(
        photo='AgACAgQAAxkBAAIC1WiaWTTPLv32vXQonLP_qIj_eUE6AAJGyTEbjW_ZUJTFjk9SE2QNAQADAgADeAADNgQ', caption="Swag?")


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
    # Получаем список категорий из БД
    categories = await rq.get_catigories()

    # Создаем медиа-объект с фото
    new_media = types.InputMediaPhoto(
        media="AgACAgQAAxkBAAMGaJvAZVJl0uPuo4MnZwOMNL9VJIQAAubKMRvHC-BQt7_NPHm8ypEBAAMCAAN5AAM2BA",
        caption="🌐Выберите тип аккаунта:"
    )

    # Редактируем сообщение с новой клавиатурой
    await callback.bot.edit_message_media(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        media=new_media,
        reply_markup=await kb.catigories()  # Используем клавиатуру категорий
    )


@router.callback_query(F.data == "check_subscription")
async def check_subscription(callback: CallbackQuery, bot: Bot):
    user_id = callback.from_user.id

    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        if member.status in ["member", "administrator", "creator"]:
            # Удаляем сообщение с просьбой подписаться
            await callback.message.delete()
            await callback.answer("✅ Спасибо за подписку! Теперь вы можете пользоваться ботом.", show_alert=True)
        else:
            await callback.answer("❌ Вы всё ещё не подписаны на канал!", show_alert=True)
    except Exception as e:
        logging.error(f"Subscription check error: {e}")
        await callback.answer("⚠️ Ошибка проверки подписки, попробуйте позже", show_alert=True)


@router.callback_query(F.data.startswith("category_"))
async def show_category_items(callback: CallbackQuery):
    category_id = callback.data.split('_')[1]
    items = await rq.get_item(category_id)

    new_media = types.InputMediaPhoto(
        media="AgACAgQAAxkBAAMIaJvAg9fcyDTi1JYZZU-2xrcc2IgAAujKMRvHC-BQ3WBtyqsmTucBAAMCAAN5AAM2BA",
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
async def category(callback: CallbackQuery):
    await callback.answer('')
    await callback.message.edit_media(
        photo="AgACAgQAAxkBAAMKaJvBQ13h8QTp60mHxebmH-Ojw3IAAj_LMRsPPeBQZlOYypQoU4sBAAMCAAN5AAM2BA",
        caption="Выберете аккаунт:", reply_markup=await kb.items(callback.data.split('_')[1]))


@router.callback_query(F.data.startswith("item_"))
async def show_item(callback: CallbackQuery):
    item_id = callback.data.split('_')[1]
    item_data = await rq.get_item_by_id(item_id)

    if not item_data:
        await callback.answer("Товар не найден!")
        return

    category_id = item_data.category
    category_name = await rq.get_category_name(category_id)

    new_media = types.InputMediaPhoto(
        media="AgACAgQAAxkBAAMMaJvBVw5xMUj1oc6kPPaHRIjnzhsAAm3LMRtzVOBQqtd_8MzFFMQBAAMCAAN5AAM2BA",
        caption='💈Информация об аккаунте:'
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
        reply_markup=await kb.payment_methods(item_id, category_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("pay_stars_"))
async def pay_with_stars(callback: CallbackQuery, state: FSMContext):
    try:
        item_id = callback.data.split('_')[2]
        item = await rq.get_item_by_id(item_id)

        # Сохраняем данные в состоянии
        await state.update_data(item_id=item_id, user_id=callback.from_user.id)

        # Конвертируем рубли в Stars (1 Star = ~6.5 руб)
        stars_amount = int(item.price // 1.15)

        prices = [LabeledPrice(label=item.name, amount=stars_amount)]  # В копейках

        await callback.bot.send_invoice(
            chat_id=callback.from_user.id,
            title=f"Покупка: {item.name}",
            description="Оплата через Stars\nОплатите счет ниже\n👇👇👇",
            provider_token="",  # Замените на ваш токен
            currency="XTR",
            prices=prices,
            payload=f"stars_{item_id}_{callback.from_user.id}",
            start_parameter="create_invoice_stars",
            reply_markup=kb.stars_payment_keyboard()
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
        history_text = "📜 <b>История покупок</b>\n\n"
        history_text += "У вас пока нет покупок."
    else:
        history_text = "📜 <b>Последние 5 покупок:</b>\n\n"
        for purchase in purchases[:5]:
            item = await rq.get_item_by_id(purchase.item_id)
            history_text += f"• {item.name} - {purchase.date.strftime('%d.%m.%Y')}\n"

    new_media = types.InputMediaPhoto(
        media="AgACAgQAAxkBAAMMaJvBVw5xMUj1oc6kPPaHRIjnzhsAAm3LMRtzVOBQqtd_8MzFFMQBAAMCAAN5AAM2BA",
        # Замените на ID фото для истории
        caption=history_text,
        parse_mode="HTML"
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
    user = await rq.get_user(user_id)

    referral_text = (
        "🎁 <b>Реферальная система</b>\n\n"
        f"👥 Приглашено пользователей: {user.referrals}\n"
        f"💰 Заработано: {user.referrals * 50} RUB\n\n"
        "Приглашайте друзей и получайте 10% с их покупки\n"
        f"Ваша реферальная ссылка:\nhttps://t.me/@alfasRobot?start={user_id}"
    )

    new_media = types.InputMediaPhoto(
        media="AgACAgQAAxkBAAMOaJvBgKPQzZfGA4HEV3NnW1KZ8vQAAufKMRvHC-BQWNf-qW3dZlgBAAMCAAN5AAM2BA",
        # Замените на ID фото для рефералов
        caption=referral_text,
        parse_mode="HTML"
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


@router.callback_query(F.data == "profile")
async def show_profile(callback: CallbackQuery):
    user_id = callback.from_user.id

    try:
        user = await rq.get_user(user_id)
        purchases = await rq.get_user_purchases(user_id)

        profile_text = (
            f"👤 <b>Ваш профиль</b>\n\n"
            f"🆔 ID: <code>{user_id}</code>\n"
            f"📅 Регистрация: {user.registered_at.strftime('%d.%m.%Y %H:%M')}\n"
            f"🛒 Покупок: {len(purchases)}\n"
            f"👥 Рефералов: {user.referrals}\n"
            f"💸 Баланс: {user.balance} RUB\n\n"
            f"🔗 Реферальная ссылка: https://t.me/alfasRobot?start={user_id}"
        )

        # Создаем новое медиа для профиля
        new_media = types.InputMediaPhoto(
            media="AgACAgQAAxkBAAMEaJvAKelwUJ3FyF2K28N4LVSPrpcAAiTKMRuGWOFQ-eq_9D5tqiQBAAMCAAN5AAM2BA",
            # Замените на ID фото для профиля
            caption=profile_text,
            parse_mode="HTML"
        )

        # Редактируем сообщение, заменяя медиа
        await callback.message.edit_media(
            media=new_media,
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Назад", callback_data="main")
                     ]
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
                "amount": f"{item.price // 75:.2f}",
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

        await callback.message.answer(
            f"💎 Оплата через Crypto Bot:\n"
            f"• Сумма: {invoice['amount']} {invoice['asset']}\n"
            f"• Ссылка: {invoice['pay_url']}\n"
            f"• ID заказа: {order_id}\n\n"
            f"Или отправьте {invoice['amount']} USDT по адрессу (сеть Trc-20):\n"
            f"<code>TQFosX3FGMoxs2jCS2EG84wALZgfqLx6yK</code>\n\n"
            f"Проверка оплаты этим способом {bold('автоматическая')}",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
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
        "❗️ Рекомендации на первый день после покупки:\n\n"
        "● Не начинайте переписку, не вступайте в группы/каналы/беседы.\n"
        "● Не меняйте настройки: НИКНЕЙМ, ЮЗЕРНЕЙМ, АВАТАРКУ\n"
        "● Дайте аккаунту «отлежаться» — это поможет избежать блокировок и создать надежный аккаунт.\n\n"
        "📚 Информация о нашем магазине:\n\n"
        "• Мы продаем Telegram-аккаунты БЕЗ спам-блока\n"
        "• Поддержка 24/7: @qvvor\n"
        "💬 По вопросам сотрудничества: @qvvor\n\n"
        "Возврат средств при слете аккаунта не предусмотрен."
    )

    # Создаем медиа-объект с информацией
    new_media = types.InputMediaPhoto(
        media="AgACAgQAAxkBAAMMaJvBVw5xMUj1oc6kPPaHRIjnzhsAAm3LMRtzVOBQqtd_8MzFFMQBAAMCAAN5AAM2BA",
        caption=predefined_text
    )

    back_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="info_back")]
        ]
    )

    # Редактируем текущее сообщение с новым медиа
    await callback.message.edit_media(
        media=new_media,
        reply_markup=back_keyboard
    )
    await callback.answer()


@router.callback_query(F.data == "dogovor")
async def dogovor_callback(callback: CallbackQuery):
    predefined_text = (
        "Настоящее пользовательское соглашение (далее — \"Соглашение\") регулирует порядок использования сервиса, предоставляемого ботом @alfasRobot (далее — \"Сервис\").\n"
        "Используя Сервис, you подтверждаете своё согласие с условиями данного Соглашения.\n\n\n"
        "1. Стоимость услуг.\n\n"
        "1.1. Стоимость активаций списывается в соответствии с действующим прейскурантом, который отображается перед покупкой номера.\n"
        "1.2. Средства списываются с вашего баланса по завершению операции, как указано в пунктах 1.4 и 1.5 регламента.\n\n"
        "2. Отмена операций.\n\n"
        "2.1. Если номер был выделен, но вы не получили код из SMS, вы вправе отменить операцию в любой момент без какого-либо штрафа.\n\n"
        "3. Согласие на получение рекламы.\n"
        "3.1. Используя Сервис, вы даёте согласие на получение рекламных материалов от @alfasRobot.\n\n"
        "4. Запрещённые действия.\n\n"
        "4.2. Запрещено использование номеров с целями, нарушающими положения Уголовного кодекса РФ или любой другой страны.\n\n"
        "4.3. Возврат средств при слете аккаунта не предусмотрен."
    )

    # Создаем медиа-объект с договором
    new_media = types.InputMediaPhoto(
        media="AgACAgQAAxkBAAMMaJvBVw5xMUj1oc6kPPaHRIjnzhsAAm3LMRtzVOBQqtd_8MzFFMQBAAMCAAN5AAM2BA",
        caption=predefined_text
    )

    back_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="info_back")]
        ]
    )

    # Редактируем текущее сообщение с новым медиа
    await callback.message.edit_media(
        media=new_media,
        reply_markup=back_keyboard
    )
    await callback.answer()


# Обработчик кнопки "Назад" в информационном сообщении
@router.callback_query(F.data == "info_back")
async def info_back(callback: CallbackQuery):
    # Восстанавливаем главное меню с фотографией
    new_media = types.InputMediaPhoto(
        media="AgACAgQAAxkBAAMEaJvAKelwUJ3FyF2K28N4LVSPrpcAAiTKMRuGWOFQ-eq_9D5tqiQBAAMCAAN5AAM2BA",
        caption='🔐 Добро пожаловать в магазин Telegram-аккаунтов!'
    )

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
            [InlineKeyboardButton(text="🔙 Назад", callback_data="info_back")]
        ]
    )

    # Отправляем информацию с кнопкой "Назад"
    await message.answer(
        f"ℹ️ Информация:\n\n{info_text}",
        reply_markup=back_keyboard
    )

    await state.clear()


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
    await callback.message.answer(
        f"💳 Оплата картой РФ\n"
        f"Сумма: {item.price} RUB\n"
        f"Нажмите кнопку ниже чтобы создать платеж",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Создать платеж", callback_data="create_card_payment")]
        ]
        )
    )
    await callback.answer()

    @router.callback_query(F.data == "create_card_payment")
    async def create_card_payment(callback: CallbackQuery, state: FSMContext):
        data = await state.get_data()
        item = await rq.get_item_by_id(data['item_id'])

        comment = f"pay_{callback.from_user.id}_{datetime.now().timestamp()}"
        link = generate_payment_link(item.price, comment)

        payments[callback.from_user.id] = {
            'amount': item.price,
            'comment': comment,
            'created_at': datetime.now(),
            'item_id': data['item_id']
        }

        await callback.message.answer(
            f"🔗 Ссылка для оплаты: {link}\n"

            "После оплаты нажмите кнопку проверки",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✅ Проверить оплату", callback_data="check_card_payment")],
                [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_payment")]
            ]
            )
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
    await callback.message.answer("Введите промокод:")
    await state.set_state(PromoStates.waiting_promo)
    await callback.answer()


# Обработчик ввода промокода
@router.message(PromoStates.waiting_promo)
async def check_promo(message: Message, state: FSMContext):
    user_input = message.text.strip().lower()
    if user_input == PROMO_CODE.lower() or user_input == 'alfastars':
        # Сохраняем информацию о примененном промокоде
        await state.update_data(promo_applied=True)
        await message.answer("✅ Промокод применен! Вы получите 10% скидку на следующую покупку.")
    else:
        await message.answer("❌ Неверный промокод. Попробуйте еще раз.")
    await state.clear()


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

from aiogram import BaseMiddleware, Bot, types
from aiogram.types import TelegramObject
from typing import Callable, Dict, Awaitable, Any
from config import CHANNEL_ID  # ID вашего канала
import logging


class SubscriptionMiddleware(BaseMiddleware):
    def __init__(self, bot: Bot):
        self.bot = bot
        super().__init__()

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]
    ) -> Any:
        user = data.get("event_from_user")

        # Проверяем подписку для всех событий, кроме команды /start
        if not isinstance(event, types.Message) or (hasattr(event, "text") and event.text != '/start'):
            if user and not await self.check_subscription(user.id):
                await self.ask_for_subscription(event)
                return  # Прерываем обработку события

        return await handler(event, data)

    async def check_subscription(self, user_id: int) -> bool:
        try:
            member = await self.bot.get_chat_member(CHANNEL_ID, user_id)
            return member.status in ["member", "administrator", "creator"]
        except Exception as e:
            logging.error(f"Subscription check error: {e}")
            return True  # В случае ошибки разрешаем действие

    async def ask_for_subscription(self, event):
        text = (
            "📢В нашем боте самые низкие цены! По этому для использования бота необходимо подписаться на наш канал!\n"
            "После подписки нажмите кнопку 'Проверить подписку'."
        )
        markup = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="🔔 Подписаться", url=f"https://t.me/aIfanews")],
            [types.InlineKeyboardButton(text="✅ Проверить подписку", callback_data="check_subscription")]
        ])

        if isinstance(event, types.CallbackQuery):
            await event.message.answer(text, reply_markup=markup)
        elif isinstance(event, types.Message):
            await event.answer(text, reply_markup=markup)
        else:
            # Для других типов событий (например, inline-запросов)
            chat_id = event.from_user.id
            await self.bot.send_message(chat_id, text, reply_markup=markup)

from app.database.models import async_session, User, Category, Item
from sqlalchemy import select, update, delete
from datetime import datetime
from aiogram.types import Message  # Добавьте это в начале файла
from app.database.models import async_session, User, Category, Item, Order  # Добавьте Order
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

async def get_catigories():
    async with async_session() as session:
        result = await session.scalars(select(Category))
        return result.all()

async def get_item(category_id):
    async with async_session() as session:
        return await session.scalars(select(Item).where(Item.category == category_id))

async def get_category_name(category_id):
    async with async_session() as session:
        return await session.scalar(select(Category.name).where(Category.id == category_id))

async def get_items_by_category(category_id):
    async with async_session() as session:
        result = await session.scalars(select(Item).where(Item.category == category_id))
        return result.all()
async def get_all_users():
    async with async_session() as session:
        result = await session.execute(select(User))
        return result.scalars().all()
# requests.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.database.requests import get_catigories, get_item
from aiogram.types import LabeledPrice, Message


main_keyboard = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text = 'Профиль')],
], resize_keyboard=True, input_field_placeholder='Выбери')


# В начало файла добавим новое состояние