from sqlalchemy import BigInteger, String, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from datetime import datetime
from sqlalchemy import Column, Integer, BigInteger, DateTime

engine = create_async_engine(url='sqlite+aiosqlite:///db.sqlite3')
async_session = async_sessionmaker(engine)

class Base(AsyncAttrs, DeclarativeBase):
    pass

async def create_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

class Order(Base):
    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger)
    item_id = Column(Integer)
    date = Column(DateTime, default=datetime.now)
    status = Column(String(50), default='pending')

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    tg_id = Column(BigInteger, unique=True)
    registered_at = Column(DateTime, default=datetime.now)
    referrals = Column(Integer, default=0)
    balance = Column(Integer, default=0)

class Category(Base):
    __tablename__ = 'categories'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(25))

class Item(Base):
    __tablename__ = 'items'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150))
    description: Mapped[str] = mapped_column(String(500))
    price: Mapped[float] = mapped_column()
    category: Mapped[int] = mapped_column(ForeignKey('categories.id'))

async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
from app.database.models import async_session, User, Category, Item, Order
from sqlalchemy import select, update, delete
from datetime import datetime

async def set_user(tg_id: int):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if not user:
            session.add(User(tg_id=tg_id, registered_at=datetime.now()))
            await session.commit()

async def get_user(tg_id: int):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.tg_id == tg_id))
        return result.scalar()

async def get_user_purchases(tg_id: int):
    async with async_session() as session:
        result = await session.execute(select(Order).where(Order.user_id == tg_id))
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
from aiogram import BaseMiddleware, Bot, types
from aiogram.types import TelegramObject
from typing import Callable, Dict, Awaitable, Any
import logging

CHANNEL_ID = "@aIfanews"

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
            chat_id = event.from_user.id
            await self.bot.send_message(chat_id, text, reply_markup=markup)
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.database.requests import get_catigories, get_item

# Главное меню
main = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Профиль')],
], resize_keyboard=True, input_field_placeholder='Выбери')

# Настройки
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
            [InlineKeyboardButton(text="ℹ️ Информация", callback_data="info"),
             InlineKeyboardButton(text="⭕️ Договор пользователя", callback_data="dogovor")
            ],
        ]
    )

# Меню возврата
menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='в меню', callback_data='main')]
])

# Категории
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

# Товары по категории
async def items(category_id):
    all_items = await get_item(category_id)
    keyboard = InlineKeyboardBuilder()
    for item in all_items:
        keyboard.add(InlineKeyboardButton(
            text=f"{item.name} ({item.price} RUB)",
            callback_data=f'item_{item.id}'
        ))
    keyboard.row(InlineKeyboardButton(
        text='Назад',
        callback_data='buyacc'
    ))
    return keyboard.adjust(2).as_markup()

# Способы оплаты
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

# Оплата через Stars
def stars_payment_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Оплатить", pay=True)
    builder.button(text="❌ Отмена", callback_data="cancel_stars_payment")
    return builder.as_markup()

# Оплата через Crypto Bot
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

# Альтернативная клавиатура проверки Crypto
async def crypto_payment_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Проверить оплату", callback_data="check_crypto_payment")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_payment")]
    ])

# Главное меню возврата
def main_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main")]
    ])
import asyncio
import logging

from aiogram import Bot, Dispatcher
from config import TOKEN
from app.handlers import router
from app.database.models import async_main
from app.middlewares import SubscriptionMiddleware

bot = Bot(token=TOKEN)
dp = Dispatcher(bot=bot)

# Регистрируем middleware
dp.message.middleware.register(SubscriptionMiddleware(bot))
dp.callback_query.middleware.register(SubscriptionMiddleware(bot))
dp.inline_query.middleware.register(SubscriptionMiddleware(bot))

async def main():
    await async_main()  # Создание базы
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Exit")
import asyncio
import contextvars
import inspect
import warnings
from dataclasses import dataclass, field
from functools import partial
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from magic_filter.magic import MagicFilter as OriginalMagicFilter
from aiogram.dispatcher.flags import extract_flags_from_object
from aiogram.filters.base import Filter
from aiogram.handlers import BaseHandler
from aiogram.utils.magic_filter import MagicFilter
from aiogram.utils.warnings import Recommendation

CallbackType = Callable[..., Any]

@dataclass
class CallableObject:
    callback: CallbackType
    awaitable: bool = field(init=False)
    params: Set[str] = field(init=False)
    varkw: bool = field(init=False)

    def __post_init__(self) -> None:
        callback = inspect.unwrap(self.callback)
        self.awaitable = inspect.isawaitable(callback) or inspect.iscoroutinefunction(callback)
        spec = inspect.getfullargspec(callback)
        self.params = {*spec.args, *spec.kwonlyargs}
        self.varkw = spec.varkw is not None

    def _prepare_kwargs(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        if self.varkw:
            return kwargs
        return {k: kwargs[k] for k in self.params if k in kwargs}

    async def call(self, *args: Any, **kwargs: Any) -> Any:
        wrapped = partial(self.callback, *args, **self._prepare_kwargs(kwargs))
        if self.awaitable:
            return await wrapped()
        return await asyncio.to_thread(wrapped)

@dataclass
class FilterObject(CallableObject):
    magic: Optional[MagicFilter] = None

    def __post_init__(self) -> None:
        if isinstance(self.callback, OriginalMagicFilter):
            self.magic = self.callback
            self.callback = self.callback.resolve
            if not isinstance(self.magic, MagicFilter):
                warnings.warn(
                    category=Recommendation,
                    message="You are using F provided by magic_filter package directly, "
                            "but it lacks `.as_()` extension."
                            "\n Please change the import statement: from `from magic_filter import F` "
                            "to `from aiogram import F` to silence this warning.",
                    stacklevel=6,
                )
        super(FilterObject, self).__post_init__()
        if isinstance(self.callback, Filter):
            self.awaitable = True

@dataclass
class HandlerObject(CallableObject):
    filters: Optional[List[FilterObject]] = None
    flags: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        super(HandlerObject, self).__post_init__()
        callback = inspect.unwrap(self.callback)
        if inspect.isclass(callback) and issubclass(callback, BaseHandler):
            self.awaitable = True
        self.flags.update(extract_flags_from_object(callback))

    async def check(self, *args: Any, **kwargs: Any) -> Tuple[bool, Dict[str, Any]]:
        if not self.filters:
            return True, kwargs
        for event_filter in self.filters:
            check = await event_filter.call(*args, **kwargs)
            if not check:
                return False, kwargs
            if isinstance(check, dict):
                kwargs.update(check)
        return True, kwargs
