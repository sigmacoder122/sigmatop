import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.client.default import DefaultBotProperties
from telethon import TelegramClient, errors
from telethon.sessions import StringSession

# --------------------------
API_TOKEN = "7098307410:AAH-Q4q8emT5QCnWFVVRxRfV4TxIJtUM-wE"
API_ID = 123456
API_HASH = "ВАШ_API_HASH"
# --------------------------

bot = Bot(API_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

# FSM состояния
class ConnectAccount(StatesGroup):
    waiting_for_phone = State()
    waiting_for_code = State()
    waiting_for_password = State()

# Хранилище сессий
user_sessions = {}  # user_id -> list of dict {session_str, username, id}

# --------------------------
# Клавиатуры
def main_menu():
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="➕ Подключить\nсессию", callback_data="connect"),
                InlineKeyboardButton(text="📂 Мои\nсессии", callback_data="my_accounts")
            ],
            [
                InlineKeyboardButton(text="⚙️ Управление\nсессиями", callback_data="manage"),
                InlineKeyboardButton(text="💳 Купить\nаккаунт/подписку", callback_data="buy")
            ],
            [
                InlineKeyboardButton(text="ℹ️ Что делает\nбот?", callback_data="about"),
                InlineKeyboardButton(text="📖 Руководство", callback_data="guide")
            ],
            [
                InlineKeyboardButton(text="📜 Команды\nбота", callback_data="commands")
            ]
        ]
    )
    return kb
def cancel_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel")]
        ]
    )

def back_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="back")]
        ]
    )

# --------------------------
# Старт
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer("👋 Привет! Выбери действие:", reply_markup=main_menu())

# --------------------------
# Подключение аккаунта
# --------------------------
# Подключение аккаунта
@dp.callback_query(lambda c: c.data == "connect")
async def connect_begin(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()  # отвечаем на callback, чтобы кнопка не висела

    # Отправляем новое сообщение с кнопкой отмены
    await callback.message.answer(
        "📱 Введите номер телефона для новой сессии:",
        reply_markup=cancel_keyboard()
    )

    await state.set_state(ConnectAccount.waiting_for_phone)


@dp.message(ConnectAccount.waiting_for_phone)
async def phone_input(message: types.Message, state: FSMContext):
    phone = message.text.strip()
    await state.update_data(phone=phone)

    client = TelegramClient(StringSession(), API_ID, API_HASH)
    await client.connect()

    try:
        sent = await client.send_code_request(phone)
    except Exception as e:
        await message.answer(f"❗ Ошибка при отправке кода: {e}")
        await client.disconnect()
        await state.clear()
        return

    await state.update_data(phone_code_hash=sent.phone_code_hash, temp_client=client)

    await message.answer(
        "📩 Код отправлен! Введите его:",
        reply_markup=cancel_keyboard()
    )
    await state.set_state(ConnectAccount.waiting_for_code)


@dp.message(ConnectAccount.waiting_for_code)
async def code_input(message: types.Message, state: FSMContext):
    code = message.text.strip()
    data = await state.get_data()
    phone = data.get("phone")
    phone_code_hash = data.get("phone_code_hash")
    client: TelegramClient = data.get("temp_client")

    try:
        me = await client.sign_in(phone=phone, code=code, phone_code_hash=phone_code_hash)
    except errors.SessionPasswordNeededError:
        await message.answer(
            "🔒 У аккаунта включена двухфакторная защита. Введите пароль:",
            reply_markup=cancel_keyboard()
        )
        await state.set_state(ConnectAccount.waiting_for_password)
        return
    except Exception as e:
        await message.answer(f"❗ Ошибка авторизации: {e}")
        await client.disconnect()
        await state.clear()
        return

    # Сохраняем сессию
    user_id = message.from_user.id
    session_str = client.session.save()
    username = me.username or "(нет username)"
    uid = me.id
    user_sessions.setdefault(user_id, []).append({
        "session_str": session_str,
        "username": username,
        "id": uid
    })

    await message.answer(f"✅ Аккаунт @{username} (id {uid}) подключён!")
    await client.disconnect()
    await state.clear()


@dp.message(ConnectAccount.waiting_for_password)
async def password_input(message: types.Message, state: FSMContext):
    password = message.text.strip()
    data = await state.get_data()
    client: TelegramClient = data.get("temp_client")

    try:
        me = await client.sign_in(password=password)
    except Exception as e:
        await message.answer(f"❗ Ошибка пароля: {e}")
        await client.disconnect()
        await state.clear()
        return

    user_id = message.from_user.id
    session_str = client.session.save()
    username = me.username or "(нет username)"
    uid = me.id
    user_sessions.setdefault(user_id, []).append({
        "session_str": session_str,
        "username": username,
        "id": uid
    })

    await message.answer(f"✅ Аккаунт @{username} (id {uid}) подключён!")
    await client.disconnect()
    await state.clear()


# --------------------------
# Обработчик кнопки "Отмена" на всех шагах
@dp.callback_query(lambda c: c.data == "cancel")
async def cancel_handler(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    client: TelegramClient | None = data.get("temp_client")

    if client:
        await client.disconnect()

    await state.clear()

    await callback.message.answer(
        "🚫 Действие отменено.\n\n👋 Выбери действие:",
        reply_markup=main_menu()
    )
    await callback.answer()


# --------------------------
# Мои сессии
@dp.callback_query(lambda c: c.data == "my_accounts")
async def my_accounts_handler(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    sessions = user_sessions.get(user_id, [])
    if not sessions:
        await callback.message.edit_text("> ❌ У вас нет подключённых сессий.", reply_markup=back_keyboard())
    else:
        kb = InlineKeyboardMarkup(row_width=1)
        for idx, sess in enumerate(sessions, 1):
            kb.add(InlineKeyboardButton(f"Аккаунт {idx} @{sess['username']}", callback_data=f"session:{idx}"))
        kb.add(InlineKeyboardButton("⬅️ Главное меню", callback_data="main_menu"))
        await callback.message.edit_text("> 📂 Ваши сессии:", reply_markup=kb)
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith("session:"))
async def session_info_handler(callback: types.CallbackQuery):
    idx = int(callback.data.split(":")[1])
    user_id = callback.from_user.id
    session = user_sessions.get(user_id, [])[idx-1]

    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("❌ Отвязать", callback_data=f"unlink:{idx}"),
        InlineKeyboardButton("⬅️ Главное меню", callback_data="main_menu")
    )
    await callback.message.edit_text(
        f"> 📌 Аккаунт {idx}\n"
        f"🆔 ID: <code>{session.get('id')}</code>\n"
        f"👤 Username: @{session.get('username')}",
        reply_markup=kb
    )

@dp.callback_query(lambda c: c.data.startswith("unlink:"))
async def unlink_handler(callback: types.CallbackQuery):
    idx = int(callback.data.split(":")[1])
    user_id = callback.from_user.id
    if user_id in user_sessions and len(user_sessions[user_id]) >= idx:
        removed = user_sessions[user_id].pop(idx-1)
        await callback.message.edit_text(f"> ✅ Аккаунт @{removed.get('username')} отвязан.", reply_markup=main_menu())
    else:
        await callback.message.edit_text("> ⚠️ Ошибка. Аккаунт не найден.")

# --------------------------
# Управление сессиями
@dp.callback_query(lambda c: c.data == "manage")
async def manage_sessions(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    sessions = user_sessions.get(user_id, [])
    if not sessions:
        await callback.message.edit_text("> ❌ У вас нет подключённых сессий.", reply_markup=back_keyboard())
    else:
        kb = InlineKeyboardMarkup(row_width=1)
        for idx, sess in enumerate(sessions, 1):
            kb.add(InlineKeyboardButton(f"Аккаунт {idx} @{sess['username']}", callback_data=f"session:{idx}"))
        kb.add(InlineKeyboardButton("⬅️ Главное меню", callback_data="main_menu"))
        await callback.message.edit_text("> 📂 Выберите сессию:", reply_markup=kb)
    await callback.answer()
def cancel_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel")]
        ]
    )

# --------------------------
# Главное меню
@dp.callback_query(lambda c: c.data == "main_menu")
async def show_main_menu(callback: types.CallbackQuery, state: FSMContext):
    # чистим temp_client, если остался
    data = await state.get_data()
    client: TelegramClient | None = data.get("temp_client")
    if client:
        await client.disconnect()
    await state.clear()

    await callback.message.edit_text("👋 Привет! Выбери действие:", reply_markup=main_menu())
    await callback.answer()

# --------------------------
# Кнопка Назад
@dp.callback_query(lambda c: c.data == "back")
async def go_back(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    client: TelegramClient | None = data.get("temp_client")
    if client:
        await client.disconnect()
    await state.clear()

    await callback.message.edit_text("👋 Привет! Выбери действие:", reply_markup=main_menu())
    await callback.answer()

# --------------------------
# Информационные разделы
@dp.callback_query(F.data == "about")
async def about_bot(callback: types.CallbackQuery):
    text = (
        "ℹ️ <b>Что делает бот?</b>\n"
        "Бот позволяет подключать ваши аккаунты Telegram, "
        "управлять сессиями, запускать массовые рассылки, "
        "следить за сессиями и многое другое."
    )
    await callback.message.edit_text(text, reply_markup=back_keyboard())
    await callback.answer()

@dp.callback_query(F.data == "guide")
async def guide_bot(callback: types.CallbackQuery):
    text = (
        "📖 <b>Руководство использования</b>\n"
        "1. Подключи аккаунт.\n"
        "2. Выбери нужную сессию.\n"
        "3. Настраивай рассылку или другие функции.\n"
        "4. Пользуйся безопасно и не передавай коды."
    )
    await callback.message.edit_text(text, reply_markup=back_keyboard())
    await callback.answer()




# --------------------------
# Покупка подписки
@dp.callback_query(F.data == "buy")
async def buy_subscription(callback: types.CallbackQuery):
    text = "💳 <b>Купить подписку</b>\nВыберите тариф для покупки или узнайте подробнее:"
    kb = InlineKeyboardMarkup(row_width=1)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💎 Полный ⭐⭐⭐ (60⭐, 1 неделя)", callback_data="tariff_full")],
            [InlineKeyboardButton(text="🌟 Начинающий ⭐⭐ (30⭐, 1 неделя)", callback_data="tariff_beginner")],
            [InlineKeyboardButton(text="🆓 Пробный ⭐ (10⭐, 2 дня)", callback_data="tariff_trial")],
            [InlineKeyboardButton(text="ℹ️ Подробнее о тарифах", callback_data="tariff_info")],
            [InlineKeyboardButton(text="⬅️ Главное меню", callback_data="main_menu")]
        ]
    )

    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()

# --------------------------
# Команды бота
@dp.callback_query(F.data == "commands")
async def bot_commands(callback: types.CallbackQuery):
    text = (
        "📜 <b>Команды бота</b>\n"
        "/start - Главное меню\n"
        "/help - Помощь по функциям\n"
        "Все действия можно выполнять через кнопки."
    )
    await callback.message.edit_text(text, reply_markup=back_keyboard())
    await callback.answer()

# --------------------------
async def main():
    # Убираем все старые вебхуки, если были
    await bot.delete_webhook(drop_pending_updates=True)

    # Запуск бота через polling (только один экземпляр!)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
