import sys
import os
import pandas as pd
import asyncio

current_dir = os.path.dirname(os.path.abspath(__file__))
bot_dir = os.path.dirname(current_dir) 
sys.path.append(bot_dir)

from database.engine import AsyncSessionLocal, init_db
from database.models import Movie

project_root = os.path.dirname(os.path.dirname(bot_dir))
CSV_FILE_PATH = os.path.join(project_root, "data", "tmdb_movies_ru.csv")

async def load_movies():
    await init_db()

    df = pd.read_csv(CSV_FILE_PATH)
    df = df.where(pd.notnull(df), None)

    async with AsyncSessionLocal() as session:
        movies_to_add = []
        for _, row in df.iterrows():
            movie = Movie(
                id=int(row['id']),
                title=str(row['title']),
                overview=str(row['overview']) if row['overview'] else None,
                poster_path=str(row['poster_path']) if row['poster_path'] else None,
                vote_average=float(row['vote_average']) if row['vote_average'] is not None else None,
                popularity=float(row['popularity']) if row['popularity'] is not None else None,
                trailer_url=str(row['trailer_url']) if row['trailer_url'] else None
            )
            movies_to_add.append(movie)

        session.add_all(movies_to_add)
        await session.commit()

    print("Все фильмы успешно занесены в базу данных")
    
if __name__ == "__main__":
    asyncio.run(load_movies())