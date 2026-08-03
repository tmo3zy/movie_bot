from sqlalchemy import select
from .engine import AsyncSessionLocal
from .models import User, Interaction

async def add_user(tg_id: int, username: str = None):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.telegram_id == tg_id))
        user = result.scalar_one_or_none()

        if not user:
            new_user = User(telegram_id=tg_id, username=username)
            session.add(new_user)
            await session.commit()

async def add_interaction(tg_id: int, movie_id: int, action: str):
    async with AsyncSessionLocal() as session:
        new_action = Interaction(user_id=tg_id, movie_id=movie_id, action=action)
        session.add(new_action)
        await session.commit()

async def get_user_history(tg_id: int):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Interaction.movie_id).where(Interaction.user_id == tg_id)
        )
        return set(result.scalars().all())