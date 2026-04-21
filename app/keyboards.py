from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.database.requests import get_catigories, get_item, get_items_by_category, get_total_items_count
from aiogram.types import LabeledPrice, Message
import random

# --- ГЛАВНЫЕ МЕНЮ ---

def main_menu():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="▤ Категории", callback_data="catalog")],
        [InlineKeyboardButton(text="☺︎ Профиль", callback_data="profile")],
        [InlineKeyboardButton(text="⚠ Поддержка", callback_data="support")]
    ])
    return keyboard

def reply_main_menu():
    keyboard = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="▤ Категории"), KeyboardButton(text="☺︎ Профиль")],
    ], resize_keyboard=True)
    return keyboard

main = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Профиль')],
], resize_keyboard=True, input_field_placeholder='Выбери')

menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='↺ В меню', callback_data='main')]
])

def main_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⌂ Главное меню", callback_data="main")]
    ])

# --- НАСТРОЙКИ И ОТЛЕГА ---

def settings():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            # Используем самолетик, как на твоем скриншоте
            [InlineKeyboardButton(text="✈ Купить аккаунт", callback_data="buyacc")],
            [InlineKeyboardButton(text="▤ Другие товары", callback_data="other_items")],
            [
                InlineKeyboardButton(text="☺︎ Профиль", callback_data="profile"),
                InlineKeyboardButton(text="☷ История", callback_data="purchase_history")
            ],
            [InlineKeyboardButton(text="♺ Рефералы", callback_data="referral")],
            [InlineKeyboardButton(text="✄ Промокод", callback_data="promo_code")],
            [
                InlineKeyboardButton(text="ⓘ Информация", callback_data="info"),
                InlineKeyboardButton(text="✍ Договор", callback_data="dogovor")
            ],
        ]
    )


# --- ТОВАРЫ И КАТЕГОРИИ ---

async def catigories():
    all_categories = await get_catigories()
    keyboard = InlineKeyboardBuilder()
    for category in all_categories:
        keyboard.add(InlineKeyboardButton(
            text=category.name,
            callback_data=f'category_{category.id}'
        ))
    keyboard.row(InlineKeyboardButton(text='↶ Назад', callback_data='main'))
    return keyboard.adjust(2).as_markup()

async def items(category_id, page=0, sort_mode="asc"):
    items_per_page = 10
    offset = page * items_per_page

    all_items = await get_items_by_category(category_id, items_per_page, offset, sort_mode)
    total_items = await get_total_items_count(category_id)
    total_pages = max((total_items + items_per_page - 1) // items_per_page, 1)

    keyboard = InlineKeyboardBuilder()

    for item in all_items:
        qty = random.randint(59, 219)
        keyboard.add(InlineKeyboardButton(
            text=f"{item.name} • {int(item.price)}₽ • {qty} шт.",
            callback_data=f'item_{item.id}'
        ))

    keyboard.adjust(1)

    sort_icon = "▾" if sort_mode == "asc" else "▴"
    next_sort = "desc" if sort_mode == "asc" else "asc"
    keyboard.row(InlineKeyboardButton(
        text=f"Цена {sort_icon}",
        callback_data=f"items_{category_id}_{page}_{next_sort}"
    ))

    nav_row = []
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
    keyboard.row(InlineKeyboardButton(text='↶ Назад', callback_data='buyacc'))

    return keyboard.as_markup()
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
def cancel_fsm_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="↶ Отменить покупку", callback_data="cancel_stars_fsm")]
    ])
# Главное меню "Другие товары"
def other_items_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="◷ Аккаунты с отлегой", callback_data="aging_menu")],
            # НОВАЯ КНОПКА СО ЗВЕЗДАМИ:
            [InlineKeyboardButton(text="☆ Telegram Stars (1.32₽)", callback_data="buy_tg_stars")],
            [InlineKeyboardButton(text="✎ Текст для разморозки • 50₽", callback_data="buy_special_unfreeze")],
            [InlineKeyboardButton(text="ⓘ Мануал «Антибан» • 50₽", callback_data="buy_special_manual")],
            [InlineKeyboardButton(text="↶ Назад", callback_data="main")]
        ]
    )

def cancel_fsm_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="↶ Отменить покупку", callback_data="cancel_stars_fsm")]
    ])

# Обновленная клавиатура для категорий отлеги (меняем кнопку "назад")
def aging_categories_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⌚ Отлега 30 дней", callback_data="aging_group_30")],
            [InlineKeyboardButton(text="⌚ Отлега 90+ дней", callback_data="aging_group_90")],
            [InlineKeyboardButton(text="⌚ Отлега 180+ дней", callback_data="aging_group_180")],
            [InlineKeyboardButton(text="⌚ Отлега год+", callback_data="aging_group_360")],
            [InlineKeyboardButton(text="⌚ Отлега 2 года+", callback_data="aging_group_720")],
            [InlineKeyboardButton(text="⌚ Отлега 3 года+", callback_data="aging_group_1080")],
            # Теперь назад ведет в "Другие товары"
            [InlineKeyboardButton(text="↶ Назад", callback_data="other_items")]
        ]
    )
# --- МЕТОДЫ ОПЛАТЫ ---

async def payment_methods(item_id, category_id):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(
        InlineKeyboardButton(text='Telegram Stars ☆', callback_data=f'pay_stars_{item_id}'),
        InlineKeyboardButton(text='Crypto Bot / USDT ◈', callback_data=f'pay_crypto_{item_id}')
    )
    keyboard.row(
        InlineKeyboardButton(text='Банковская карта / СБП ⎚ (от 100р)', callback_data=f'pay_card_{item_id}')
    )
    keyboard.row(
        InlineKeyboardButton(text='СБП 2 ⎚ (от 50р)', callback_data=f'pay_platega_{item_id}')
    )
    keyboard.row(InlineKeyboardButton(
        text='↶ Назад к товарам',
        callback_data=f'category_{category_id}'
    ))
    return keyboard.adjust(1).as_markup()


from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def admin_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить товар", callback_data="adm_add_item")],
        [InlineKeyboardButton(text="🔄 Изменить цену", callback_data="adm_edit_price")],
        [InlineKeyboardButton(text="❌ Закрыть", callback_data="adm_close")]
    ])


def cancel_admin_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Отменить действие", callback_data="adm_cancel")]
    ])
def stars_payment_keyboard(item_id, category_id):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Оплатить ☆", pay=True))
    builder.row(InlineKeyboardButton(
        text="✕ Отменить и назад",
        callback_data=f"cancel_pay_{item_id}_{category_id}"
    ))
    return builder.as_markup()

async def crypto_payment_keyboard(pay_url: str = None):
    builder = InlineKeyboardBuilder()
    if pay_url:
        builder.add(InlineKeyboardButton(
            text="◈ Оплатить через Crypto Bot",
            url=pay_url
        ))
    builder.add(InlineKeyboardButton(
        text="✓ Проверить оплату",
        callback_data="check_payment"
    ))
    builder.add(InlineKeyboardButton(
        text="✕ Отмена",
        callback_data="cancel_payment"
    ))
    return builder.adjust(1).as_markup()