from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.database.requests import get_catigories, get_item
from aiogram.types import LabeledPrice, Message


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
    keyboard.row(InlineKeyboardButton(text='Назад', callback_data='main'))
    return keyboard.adjust(2).as_markup()


from app.database.requests import get_items_by_category, get_total_items_count


async def items(category_id, page=0):
    items_per_page = 10
    offset = page * items_per_page
    all_items = await get_items_by_category(category_id, items_per_page, offset)
    total_items = await get_total_items_count(category_id)
    total_pages = (total_items + items_per_page - 1) // items_per_page

    keyboard = InlineKeyboardBuilder()

    # Добавляем товары по 3 в ряд
    for i, item in enumerate(all_items):
        keyboard.add(InlineKeyboardButton(
            text=f"{item.name} ({item.price} RUB)",
            callback_data=f'item_{item.id}'
        ))

    # Добавляем кнопки навигации
    navigation_buttons = []
    if page > 0:
        navigation_buttons.append(
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data=f'items_{category_id}_{page - 1}'
            )
        )

    # Индикатор страницы
    navigation_buttons.append(
        InlineKeyboardButton(
            text=f"{page + 1}/{total_pages}",
            callback_data="ignore"
        )
    )

    if page < total_pages - 1:
        navigation_buttons.append(
            InlineKeyboardButton(
                text="Вперед ➡️",
                callback_data=f'items_{category_id}_{page + 1}'
            )
        )

    if navigation_buttons:
        keyboard.row(*navigation_buttons)

    keyboard.row(InlineKeyboardButton(
        text='Назад к категориям',
        callback_data='buyacc'
    ))

    return keyboard.adjust(2).as_markup()

async def payment_methods(item_id, category_id):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(
        InlineKeyboardButton(text='Telegram Stars 🌟', callback_data=f'pay_stars_{item_id}'),
        InlineKeyboardButton(text='Crypto Bot/USDT', callback_data=f'pay_crypto_{item_id}'),
        InlineKeyboardButton(text='Карта РФ 💳', callback_data=f'pay_card_{item_id}')
    )
    keyboard.row(InlineKeyboardButton(
        text='Назад к товарам',
        callback_data=f'category_{category_id}'
    ))
    return keyboard.adjust(1).as_markup()

def stars_payment_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Оплатить", pay=True)
    builder.button(text="❌ Отмена", callback_data="cancel_stars_payment")
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

