from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.database.requests import get_catigories, get_item
from aiogram.types import LabeledPrice, Message
def main_menu():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📂 Категории", callback_data="catalog")],
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile")],
        # --- ВОТ ТВОЯ КНОПКА ---
        [InlineKeyboardButton(text="🎁 ПОЛУЧИТЬ АККАУНТ БЕСПЛАТНО", callback_data="gamble_select_item")],
        # -----------------------
        [InlineKeyboardButton(text="ℹ️ Поддержка", callback_data="support")]
    ])
    return keyboard

# Если у тебя Reply-меню (кнопки внизу экрана, где ввод текста):
def reply_main_menu():
    keyboard = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="📂 Категории"), KeyboardButton(text="👤 Профиль")],
        [KeyboardButton(text="🎁 Получить аккаунт бесплатно")] # Обрабатываем по тексту
    ], resize_keyboard=True)
    return keyboard
main = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text = 'Профиль')],
], resize_keyboard=True, input_field_placeholder='Выбери')


# В начало файла добавим новое состояние



# В клавиатуру settings добавим кнопку "Инфо"
def settings():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🛒 Купить аккаунт", callback_data="buyacc")],
            [
                InlineKeyboardButton(text="👤 Профиль", callback_data="profile"),
                InlineKeyboardButton(text="📜 История", callback_data="purchase_history")
            ],
            [InlineKeyboardButton(text="🎁 Рефералы", callback_data="referral")],
            [InlineKeyboardButton(text="🎟 Промокод", callback_data="promo_code")],
            # Добавляем кнопку Инфо
            [InlineKeyboardButton(text="ℹ️ Информация", callback_data="info"),
             InlineKeyboardButton(text="⭕️ Договор пользователя", callback_data="dogovor")
             ],

        ]
    )


# Обработчик кнопки "Инфо"


menu = InlineKeyboardMarkup(inline_keyboard= [
    [InlineKeyboardButton(text = 'в меню', callback_data='main')]
    ])


async def catigories():
    all_categories = await get_catigories()
    keyboard = InlineKeyboardBuilder()
    for category in all_categories:
        keyboard.add(InlineKeyboardButton(
            text=category.name,
            callback_data=f'category_{category.id}'
        ))
    keyboard.row(InlineKeyboardButton(text='↩️ Назад', callback_data='main'))
    return keyboard.adjust(2).as_markup()


from app.database.requests import get_items_by_category, get_total_items_count

import random  # Обязательно добавь этот импорт в начало файла, если его еще нет


async def items(category_id, page=0, sort_mode="asc"):
    items_per_page = 10
    offset = page * items_per_page

    # Теперь передаем 4 аргумента, как и просил Python в прошлой ошибке
    all_items = await get_items_by_category(category_id, items_per_page, offset, sort_mode)
    total_items = await get_total_items_count(category_id)
    total_pages = max((total_items + items_per_page - 1) // items_per_page, 1)

    keyboard = InlineKeyboardBuilder()

    for item in all_items:
        # Генерируем случайное количество от 59 до 219
        qty = random.randint(59, 219)

        keyboard.add(InlineKeyboardButton(
            text=f"{item.name} • {int(item.price)}₽ • {qty} шт.",
            callback_data=f'item_{item.id}'
        ))

    # Изменяем на 1, чтобы товары выводились по одному в строке
    keyboard.adjust(1)

    # Кнопка сортировки
    sort_icon = "⬇️" if sort_mode == "asc" else "⬆️"
    next_sort = "desc" if sort_mode == "asc" else "asc"
    keyboard.row(InlineKeyboardButton(
        text=f"Цена {sort_icon}",
        callback_data=f"items_{category_id}_{page}_{next_sort}"
    ))

    # Навигация
    nav_row = []
    # Если страницы нет, шлем 'ignore_1', чтобы Telegram не ругался на "no modification"
    if page > 0:
        nav_row.append(InlineKeyboardButton(text="‹", callback_data=f'items_{category_id}_{page - 1}_{sort_mode}'))
    else:
        nav_row.append(InlineKeyboardButton(text="·", callback_data="ignore_prev"))

    nav_row.append(InlineKeyboardButton(text=f"{page + 1}/{total_pages}", callback_data="ignore_page"))

    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton(text="›", callback_data=f'items_{category_id}_{page + 1}_{sort_mode}'))
    else:
        nav_row.append(InlineKeyboardButton(text="·", callback_data="ignore_next"))

    keyboard.row(*nav_row)
    keyboard.row(InlineKeyboardButton(text='↩️ Назад', callback_data='buyacc'))

    return keyboard.as_markup()

async def payment_methods(item_id, category_id):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(
        InlineKeyboardButton(text='Telegram Stars 🌟', callback_data=f'pay_stars_{item_id}'),
        InlineKeyboardButton(text='Crypto Bot/USDT', callback_data=f'pay_crypto_{item_id}')
    )
    keyboard.row(InlineKeyboardButton(
        text='Назад к товарам↩️ ',
        callback_data=f'category_{category_id}'
    ))
    return keyboard.adjust(1).as_markup()

# В файле keyboards.py (или где у тебя этот метод)
def stars_payment_keyboard(item_id, category_id):
    builder = InlineKeyboardBuilder()
    # Кнопка для оплаты (обязательна для инвойса)
    builder.row(InlineKeyboardButton(text="Оплатить ⭐️", pay=True))
    # Кнопка возврата
    builder.row(InlineKeyboardButton(
        text="❌ Отменить и назад",
        callback_data=f"cancel_pay_{item_id}_{category_id}"
    ))
    return builder.as_markup()

async def crypto_payment_keyboard(pay_url: str):
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(
        text="💎 Оплатить через Crypto Bot",
        url=pay_url
    ))
    builder.add(InlineKeyboardButton(
        text="✅ Проверить оплату",
        callback_data="check_payment"
    ))
    builder.add(InlineKeyboardButton(
        text="❌ Отмена",
        callback_data="cancel_payment"
    ))
    return builder.adjust(1).as_markup()

async def crypto_payment_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Проверить оплату", callback_data="check_crypto_payment")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_payment")]
    ])

# Добавьте эту клавиатуру в app/keyboards.py

def main_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main")]
    ])

