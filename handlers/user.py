from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, CommandObject
from keyboards.inline import get_main_menu, get_back_button
import database.db as db

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject):
    # Ловим реферальный ID (то, что идет после /start ...)
    invited_by = None
    if command.args and command.args.isdigit():
        invited_by = int(command.args)
        if invited_by == message.from_user.id:
            invited_by = None  # Запрещаем приглашать самого себя :)

    # Пробуем добавить пользователя в базу
    username = message.from_user.username or message.from_user.first_name
    await db.add_user(message.from_user.id, username, invited_by)

    text = (
        f"👋 <b>Привет, {message.from_user.first_name}!</b>\n\n"
        "Добро пожаловать в наш проект 🚀\n"
        "Здесь ты можешь зарабатывать реальные деньги, просто приглашая друзей!\n\n"
        "Выбирай нужный раздел в меню ниже 👇"
    )
    await message.answer(text, reply_markup=get_main_menu(), parse_mode="HTML")


@router.callback_query(F.data == "profile")
async def show_profile(callback: CallbackQuery):
    # Достаем данные из базы
    user_data = await db.get_user(callback.from_user.id)

    # Если данные есть (а они должны быть), берем их, иначе ставим нули
    balance = user_data["balance"] if user_data else 0
    invites = user_data["invites_count"] if user_data else 0

    text = (
        "💼 <b>Твой Личный кабинет</b>\n\n"
        f"👤 <b>ID:</b> <code>{callback.from_user.id}</code>\n"
        f"💰 <b>Баланс:</b> <b>{balance}</b> ₽\n"
        f"👥 <b>Приглашено:</b> <b>{invites}</b> чел.\n\n"
        "<i>Продолжай приглашать друзей, чтобы увеличить заработок!</i>"
    )
    await callback.message.edit_text(text, reply_markup=get_back_button(), parse_mode="HTML")
    await callback.answer()


from config import CHANNEL_ID

from keyboards.inline import get_main_menu, get_back_button, get_earn_menu
from config import CHANNEL_ID  # Если делаешь ссылку на канал


@router.callback_query(F.data == "earn")
async def show_earn_menu(callback: CallbackQuery):
    """Главное меню заработка"""
    text = (
        "💸 <b>СПОСОБЫ ЗАРАБОТКА</b>\n\n"
        "<blockquote>Выбирай любой удобный способ и начинай получать реальные деньги! Чем больше активности — тем выше доход.</blockquote>\n\n"
        "👇 <b>Нажми на нужный раздел:</b>"
    )
    # Показываем меню выбора заработка
    await callback.message.edit_text(text, reply_markup=get_earn_menu(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "earn_bot")
async def earn_bot(callback: CallbackQuery):
    """Заработок на приглашениях в бота"""
    bot_info = await callback.bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={callback.from_user.id}"

    text = (
        "🤖 <b>ЗАРАБОТОК НА БОТЕ</b>\n\n"
        "<blockquote>Получай фиксированную оплату за каждого друга, который перейдет по ссылке и запустит этого бота!</blockquote>\n\n"
        f"🔗 <b>Твоя ссылка для приглашений:</b>\n<code>{ref_link}</code>"
    )
    # Кнопка "Назад" вернет нас в главное меню (или можешь сделать возврат в меню заработка)
    await callback.message.edit_text(text, reply_markup=get_back_button(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "earn_channel")
async def earn_channel(callback: CallbackQuery):
    """Заработок на заявках в канал"""
    try:
        # Создаем уникальную ссылку-заявку для юзера
        link = await callback.bot.create_chat_invite_link(
            chat_id=CHANNEL_ID,
            name=f"Ref_{callback.from_user.id}",
            creates_join_request=True
        )
        link_url = link.invite_link
    except Exception as e:
        link_url = "⚠️ Ошибка: Бот не является админом в канале или неверный ID!"

    text = (
        "📢 <b>ЗАРАБОТОК НА КАНАЛЕ</b>\n\n"
        "<blockquote>Приглашай людей в наш закрытый канал. Оплата начисляется автоматически за каждую поданную заявку!</blockquote>\n\n"
        f"🔗 <b>Твоя персональная ссылка:</b>\n<code>{link_url}</code>"
    )
    await callback.message.edit_text(text, reply_markup=get_back_button(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "earn_tiktok")
async def earn_tiktok(callback: CallbackQuery):
    """Заработок на TikTok (пока заглушка для красоты)"""
    text = (
        "📱 <b>СМОТРИ TIKTOK И ЗАРАБАТЫВАЙ</b>\n\n"
        "<blockquote>Выполняй простые задания: смотри видео, ставь лайки и присылай скриншоты для проверки. Оплата за каждое задание!</blockquote>\n\n"
        "⏳ <i>Раздел формируется. Первые задания появятся совсем скоро...</i>"
    )
    await callback.message.edit_text(text, reply_markup=get_back_button(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery):
    text = (
        "👋 <b>Главное меню</b>\n\n"
        "Выбирай нужный раздел ниже 👇"
    )
    await callback.message.edit_text(text, reply_markup=get_main_menu(), parse_mode="HTML")
    await callback.answer()


# Оставим заглушку для статистики пока что
@router.callback_query(F.data == "stats")
async def show_stats(callback: CallbackQuery):
    text = "📊 <b>Статистика проекта</b>\n\nЗдесь скоро будет крутая статистика..."
    await callback.message.edit_text(text, reply_markup=get_back_button(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "withdraw")
async def withdraw_money(callback: CallbackQuery):
    user_data = await db.get_user(callback.from_user.id)
    invites = user_data["invites_count"] if user_data else 0

    if invites < 10:
        text = (
            "❌ <b>Ошибка вывода</b>\n\n"
            f"Для вывода средств нужно пригласить минимум <b>10</b> человек.\n"
            f"У тебя пока: <b>{invites}</b>"
        )
    else:
        text = (
            "✅ <b>Заявка отправлена!</b>\n\n"
            "Твой запрос на вывод принят в обработку. Админ проверит его в течение 24 часов."
        )
        # Тут в будущем добавим логику отправки сообщения админу

    await callback.message.edit_text(text, reply_markup=get_back_button(), parse_mode="HTML")
    await callback.answer()