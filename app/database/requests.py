from app.database.models import async_session, User, Category, Item
from sqlalchemy import select, update, delete
from datetime import datetime
from aiogram.types import Message  # Добавьте это в начале файла
from app.database.models import async_session, User, Category, Item, Order  # Добавьте Order
from sqlalchemy import func

async def get_categories_paginated(limit=12, offset=0):
    async with async_session() as session:
        result = await session.scalars(
            select(Category)
            .limit(limit)
            .offset(offset)
            .order_by(Category.id)
        )
        return result.all()
async def set_user(tg_id: int):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if not user:
            # Создаем пользователя с текущей датой регистрации
            session.add(User(tg_id=tg_id, registered_at=datetime.now()))
            await session.commit()
async def get_total_items_count(category_id):
    async with async_session() as session:
        result = await session.scalar(
            select(func.count(Item.id))
            .where(Item.category == category_id)
        )
        return result or 0
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

async def get_items_by_category(category_id, limit=12, offset=0):
    async with async_session() as session:
        result = await session.scalars(
            select(Item)
            .where(Item.category == category_id)
            .limit(limit)
            .offset(offset)
        )
        return result.all()
async def get_all_users():
    async with async_session() as session:
        result = await session.execute(select(User))
        return result.scalars().all()
# requests.py

async def get_total_categories_count():
    async with async_session() as session:
        result = await session.scalar(select(func.count(Category.id)))
        return result or 0

async def get_items_by_category_paginated(category_id, limit=12, offset=0):
    async with async_session() as session:
        result = await session.scalars(
            select(Item)
            .where(Item.category == category_id)
            .limit(limit)
            .offset(offset)
            .order_by(Item.id)
        )
        return result.all()

