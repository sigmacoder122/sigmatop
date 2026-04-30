from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_main_menu():
    """Главное меню бота"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💼 Личный кабинет", callback_data="profile")],
        [InlineKeyboardButton(text="💸 Заработать", callback_data="earn"),
         InlineKeyboardButton(text="📊 Статистика", callback_data="stats")]
    ])
    return keyboard

def get_back_button():
    """Кнопка возврата в главное меню"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
    ])
    return keyboard

def get_profile_kb():
    """Кнопки в личном кабинете"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Вывести средства", callback_data="withdraw")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
    ])
    return keyboard
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# ... твои старые функции get_main_menu и get_back_button оставляем ...

def get_earn_menu():
    """Меню выбора способора заработка"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤖 Приглашать в бота", callback_data="earn_bot")],
        [InlineKeyboardButton(text="📢 Приглашать в канал", callback_data="earn_channel")],
        [InlineKeyboardButton(text="📱 Смотреть TikTok", callback_data="earn_tiktok")],
        [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_main")]
    ])
    return keyboard
def get_admin_kb():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➖ 1 ₽", callback_data="rew_-1"),
            InlineKeyboardButton(text="➕ 1 ₽", callback_data="rew_+1")
        ],
        [InlineKeyboardButton(text="📢 Рассылка", callback_data="broadcast")],
        [InlineKeyboardButton(text="🔙 Выйти", callback_data="back_to_main")]
    ])
    return keyboard