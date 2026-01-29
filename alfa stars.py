import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime, timedelta
import json

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Токен бота (замените на свой)
BOT_TOKEN = "8003886936:AAH8hLax_qbdP7dQVKJyJYCBP9v-zc17Bbg"
# ID администратора для уведомлений
ADMIN_ID = "YOUR_ADMIN_ID"

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# Состояния FSM
class PurchaseStars(StatesGroup):
    choosing_recipient = State()
    entering_amount = State()
    confirmation = State()
    payment = State()


class SellStars(StatesGroup):
    choosing_method = State()
    entering_details = State()
    entering_amount = State()
    confirmation = State()


# Клавиатуры
def main_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Купить Telegram Stars 💡")],
            [KeyboardButton(text="Продать Telegram Stars 💸")],
            [KeyboardButton(text="Мои покупки 💼"), KeyboardButton(text="Поддержка 🆘")],
            [KeyboardButton(text="Калькулятор 🔢"), KeyboardButton(text="Отзывы 📝")],
            [KeyboardButton(text="Информация ℹ️")]
        ],
        resize_keyboard=True
    )
    return keyboard


def back_next_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="<< Назад", callback_data="back"),
                InlineKeyboardButton(text="Далее >>", callback_data="next")
            ]
        ]
    )
    return keyboard


def payment_methods_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Банковская карта 💳", callback_data="card")],
            [InlineKeyboardButton(text="Криптокошелек ₿", callback_data="crypto")],
            [InlineKeyboardButton(text="P2P перевод 👤", callback_data="p2p")],
            [InlineKeyboardButton(text="<< Назад", callback_data="back_main")]
        ]
    )
    return keyboard


def confirm_cancel_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm")],
            [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel")]
        ]
    )
    return keyboard


# Обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    welcome_text = (
        "Главное меню\n"
        "Привет! Наш бот создан для покупки\n"
        "Telegram Stars 💡 быстро, дешево и безопасно.\n\n"
    )
    await message.answer(welcome_text, reply_markup=main_keyboard())


# Обработчик кнопки "Купить Telegram Stars"
@dp.message(F.text == "Купить Telegram Stars 💡")
async def purchase_stars(message: types.Message, state: FSMContext):
    # Запрос имени пользователя
    user_info = f"- Имя пользователя: @{message.from_user.username}\n" if message.from_user.username else ""
    purchase_text = (
        "Покупка Telegram Stars\n"
        f"{user_info}"
        "- Количество звёзд: 50 ➤ = 70.0P\n\n"
        "Количество звёзд можно ввести «/»\n"
        "вручную через сообщение нажав на кнопку \"Ввести количество\".\n"
        "Число может быть не кратным десяти!"
    )

    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Ввести количество", callback_data="enter_amount"))
    builder.add(InlineKeyboardButton(text="<< Назад", callback_data="back_main"))
    builder.adjust(1)

    await message.answer(purchase_text, reply_markup=builder.as_markup())
    await state.set_state(PurchaseStars.entering_amount)


# Обработчик ввода количества звезд
@dp.callback_query(F.data == "enter_amount", PurchaseStars.entering_amount)
async def enter_amount(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите количество звезд, которое хотите купить:")
    await state.set_state(PurchaseStars.entering_amount)


@dp.message(PurchaseStars.entering_amount)
async def process_amount(message: types.Message, state: FSMContext):
    try:
        amount = int(message.text)
        if amount <= 0:
            await message.answer("Пожалуйста, введите положительное число:")
            return

        await state.update_data(amount=amount)

        # Расчет стоимости (пример: 1 звезда = 0.017898 USDT)
        cost = round(amount * 0.017898, 3)
        await state.update_data(cost=cost)

        purchase_text = (
            "Покупка Telegram Stars\n"
            f"- Имя пользователя: @{message.from_user.username}\n"
            f"- Количество звёзд: {amount} ➤ = {cost} USDT\n\n"
            "- Выбери кому ты хочешь отправить «/» звезды. Себе или другому пользователю. "
            "Если выбираешь отправить себе убедись что у тебя установлен username"
        )

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Себе!!!", callback_data="self")],
                [InlineKeyboardButton(text="Другому пользователю 🟢", callback_data="other")],
                [InlineKeyboardButton(text="<< Назад", callback_data="back"),
                 InlineKeyboardButton(text="Далее >>", callback_data="next")]
            ]
        )

        await message.answer(purchase_text, reply_markup=keyboard)
        await state.set_state(PurchaseStars.choosing_recipient)

    except ValueError:
        await message.answer("Пожалуйста, введите корректное число:")


# Обработчик выбора получателя
@dp.callback_query(F.data.in_(["self", "other"]), PurchaseStars.choosing_recipient)
async def choose_recipient(callback: types.CallbackQuery, state: FSMContext):
    recipient = "себе" if callback.data == "self" else "другому пользователю"
    await state.update_data(recipient=recipient)

    data = await state.get_data()
    amount = data.get('amount', 0)
    cost = data.get('cost', 0)

    confirmation_text = (
        "Подтверждение покупки\n"
        f"- Получатель: {recipient}\n"
        f"- Количество звезд: {amount}\n"
        f"- Сумма к оплате: {cost} USDT\n\n"
        "Для продолжения нажмите \"Подтвердить\""
    )

    await callback.message.answer(confirmation_text, reply_markup=confirm_cancel_keyboard())
    await state.set_state(PurchaseStars.confirmation)


# Обработчик подтверждения покупки
@dp.callback_query(F.data == "confirm", PurchaseStars.confirmation)
async def confirm_purchase(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    amount = data.get('amount', 0)
    cost = data.get('cost', 0)
    recipient = data.get('recipient', '')

    payment_text = (
        "Оплата через CryptoBot\n"
        f"- Получатель – @usercursor\n"
        f"- Звезд будет отправлено – {amount}\n"
        f"- Сумма к оплате – {cost} USDT\n\n"
        "---\n\n"
        "Для оплаты нажмите кнопку \"Оплатить\"\n"
        "- [ ] платеж должен быть совершен в течении 10 минут\n"
    )

    # Создаем таймер
    expiration_time = datetime.now() + timedelta(minutes=10)
    timer_text = f"{expiration_time.minute:02d}:{expiration_time.second:02d}"

    payment_text += f"  {timer_text}\n\n"

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Оплатить", callback_data="pay")],
            [InlineKeyboardButton(text="Отменить покупку", callback_data="cancel")]
        ]
    )

    await callback.message.answer(payment_text, reply_markup=keyboard)
    await state.set_state(PurchaseStars.payment)


# Обработчик оплаты
@dp.callback_query(F.data == "pay", PurchaseStars.payment)
async def process_payment(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    amount = data.get('amount', 0)
    cost = data.get('cost', 0)
    recipient = data.get('recipient', '')

    # Имитация успешной оплаты
    success_text = (
        f"Сделка на сумму {cost} USDT подтверждена. Спасибо за покупку!\n\n"
        "Покупка звезд может занимать от 1 до 5/2 минут 💬. Пожалуйста ожидайте\n\n"
        "---\n\n"
        f"{amount} звезд было отправлено пользователю (@usercursor)\n\n"
        "Если вам понравилась работа бот вык/э можете оставить отзыв"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Оставить отзыв 💬", callback_data="feedback")],
            [InlineKeyboardButton(text="Пропустить 💬", callback_data="skip")]
        ]
    )

    await callback.message.answer(success_text, reply_markup=keyboard)

    # Отправляем уведомление администратору
    admin_text = (
        "🛒 Новая покупка!\n"
        f"Пользователь: @{callback.from_user.username}\n"
        f"Количество звезд: {amount}\n"
        f"Сумма: {cost} USDT\n"
        f"Получатель: {recipient}"
    )

    try:
        await bot.send_message(ADMIN_ID, admin_text)
    except Exception as e:
        logger.error(f"Не удалось отправить уведомление администратору: {e}")

    await state.clear()


# Обработчик кнопки "Продать Telegram Stars"
@dp.message(F.text == "Продать Telegram Stars 💸")
async def sell_stars(message: types.Message, state: FSMContext):
    sell_text = (
        "Продажа Telegram Stars\n\n"
        "Выберите способ вывода средств:"
    )

    await message.answer(sell_text, reply_markup=payment_methods_keyboard())
    await state.set_state(SellStars.choosing_method)


# Обработчик выбора способа вывода
@dp.callback_query(F.data.in_(["card", "crypto", "p2p"]), SellStars.choosing_method)
async def choose_payment_method(callback: types.CallbackQuery, state: FSMContext):
    method_map = {
        "card": "Банковская карта",
        "crypto": "Криптокошелек",
        "p2p": "P2P перевод"
    }

    method = method_map[callback.data]
    await state.update_data(method=method)

    await callback.message.answer(f"Вы выбрали: {method}\n\nВведите реквизиты для получения средств:")
    await state.set_state(SellStars.entering_details)


# Обработчик ввода реквизитов
@dp.message(SellStars.entering_details)
async def enter_payment_details(message: types.Message, state: FSMContext):
    details = message.text
    await state.update_data(details=details)

    await message.answer("Введите количество звезд, которое хотите продать:")
    await state.set_state(SellStars.entering_amount)


# Обработчик ввода количества звезд для продажи
@dp.message(SellStars.entering_amount)
async def enter_sell_amount(message: types.Message, state: FSMContext):
    try:
        amount = int(message.text)
        if amount <= 0:
            await message.answer("Пожалуйста, введите положительное число:")
            return

        await state.update_data(amount=amount)

        # Расчет стоимости (пример: 1 звезда = 0.015 USDT)
        cost = round(amount * 0.015, 2)
        await state.update_data(cost=cost)

        data = await state.get_data()
        method = data.get('method', '')
        details = data.get('details', '')

        confirmation_text = (
            "Подтверждение продажи\n"
            f"- Способ вывода: {method}\n"
            f"- Реквизиты: {details}\n"
            f"- Количество звезд: {amount}\n"
            f"- Сумма к получению: {cost} USDT\n\n"
            "Для продолжения нажмите \"Подтвердить\""
        )

        await message.answer(confirmation_text, reply_markup=confirm_cancel_keyboard())
        await state.set_state(SellStars.confirmation)

    except ValueError:
        await message.answer("Пожалуйста, введите корректное число:")


# Обработчик подтверждения продажи
@dp.callback_query(F.data == "confirm", SellStars.confirmation)
async def confirm_sale(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    amount = data.get('amount', 0)
    cost = data.get('cost', 0)
    method = data.get('method', '')
    details = data.get('details', '')

    success_text = (
        "Заявка на продажу принята!\n\n"
        f"Отправьте {amount} звезд на аккаунт @starstobuybot\n"
        "После получения средств мы переведем деньги на указанные реквизиты."
    )

    await callback.message.answer(success_text)

    # Отправляем уведомление администратору
    admin_text = (
        "💰 Новая продажа!\n"
        f"Пользователь: @{callback.from_user.username}\n"
        f"Количество звезд: {amount}\n"
        f"Сумма: {cost} USDT\n"
        f"Способ вывода: {method}\n"
        f"Реквизиты: {details}"
    )

    try:
        await bot.send_message(ADMIN_ID, admin_text)
    except Exception as e:
        logger.error(f"Не удалось отправить уведомление администратору: {e}")

    await state.clear()


# Обработчик кнопки "Назад"
@dp.callback_query(F.data == "back_main")
async def back_to_main(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    welcome_text = (
        "Главное меню\n"
        "Привет! Наш бот создан для покупки\n"
        "Telegram Stars 💡 быстро, дешево и безопасно.\n\n"
    )
    await callback.message.answer(welcome_text, reply_markup=main_keyboard())


# Обработчик отмены
@dp.callback_query(F.data == "cancel")
async def cancel_operation(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer("Операция отменена.", reply_markup=main_keyboard())


# Запуск бота
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())