import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from .models import Base
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DB_URL")

engine = create_async_engine(DATABASE_URL, echo=True)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def init_db():
    """
    Проверяет структуру базы данных и создает таблицы, если их нет.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    print("[INFO] База данных успешно инициализирована!")