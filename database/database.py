from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from config import config
from .models import Base

# Создание движка БД
engine = create_async_engine(config.DATABASE_URL, echo=False)

# Создание фабрики сессий
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def init_db():
    """Инициализация базы данных"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def drop_db():
    """Удаляет все таблицы в базе"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def get_session():
    """Получение сессии БД"""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()