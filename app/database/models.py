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
    registered_at = Column(DateTime, default=datetime.now)  # Добавлено значение по умолчанию
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