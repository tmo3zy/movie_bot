from sqlalchemy import select, func
from .engine import AsyncSessionLocal
from .models import User, Interaction, Movie

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

async def get_random_movie(user_id: int) -> Movie | None:
    async with AsyncSessionLocal() as session:
        seen_movies_subq = select(Interaction.movie_id).where(Interaction.user_id == user_id)
        
        result = await session.execute(
            select(Movie)
            .where(Movie.id.notin_(seen_movies_subq))
            .order_by(func.random())
            .limit(1)
        )
        return result.scalar_one_or_none()

async def get_movie_by_id(movie_id: int) -> Movie | None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Movie).where(Movie.id == movie_id)
        )
        return result.scalar_one_or_none()

async def get_liked_movies_page(user_id: int, page: int = 0, limit: int = 5):
    offset = page * limit
    async with AsyncSessionLocal() as session:
        count_query = select(func.count()).select_from(Interaction).where(
            Interaction.user_id == user_id,
            Interaction.action.in_(['like'])
        )
        total_likes = (await session.execute(count_query)).scalar()

        if total_likes == 0:
            return [], 0

        movies_query = select(Movie).join(Interaction, Movie.id == Interaction.movie_id).where(
            Interaction.user_id == user_id,
            Interaction.action.in_(['like'])
        ).order_by(Interaction.timestamp.desc()).offset(offset).limit(limit)
        
        result = await session.execute(movies_query)
        movies = result.scalars().all()
        
        return movies, total_likes