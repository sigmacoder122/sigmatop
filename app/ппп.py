print('кого будем сегодня')
a = input()
print('старт')
print('✅ Dependencies processed: 34 packages\n⚠️ Warnings: 3 build issues detected\n❌ Critical: pydantic_core compilation failed (Rust incompatibility)\n📦 Total size: ~45MB downloaded')
print('сделанно!')
print(
    '├ Телефон: 79256409904\n'
    '├ Оператор: Мегафон\n'
    '├ Регион: г.Москва и Московская область\n'
    '└ Страна: Россия\n'
    '👤 Основные данные\n'
    '├ ФИО: Горбатько Милана\n'
    '├ Дата рождения: 26.06.2010\n'
    '└ Возраст: 15\n' 'тг: @gorbatko_gorbatko')
from sqlalchemy import String, Integer, DateTime, select
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmakerfrom sqlalchemy import String, Integer, DateTime, select
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker