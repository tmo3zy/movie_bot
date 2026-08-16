import sys
import os
import pandas as pd
import asyncio
import ast

def parse_genres_to_string(raw_genres) -> str | None:
    if pd.isna(raw_genres) or not raw_genres:
        return None
    try:
        genres_list = ast.literal_eval(str(raw_genres))
        if isinstance(genres_list, list) and genres_list:
            return ", ".join(g.capitalize() for g in genres_list if g)
    except Exception:
        pass
    return str(raw_genres)

current_dir = os.path.dirname(os.path.abspath(__file__))
bot_dir = os.path.dirname(current_dir) 
sys.path.append(bot_dir)

from database.engine import AsyncSessionLocal, init_db
from database.models import Movie

project_root = os.path.dirname(os.path.dirname(bot_dir))
CSV_FILE_PATH = os.path.join(project_root, "data", "tmdb_movies_ru.csv")
STARTER_IDS = {
    1477565, 348893, 1235877, 1261825, 1368314, 
    255709, 14160, 337404, 537915, 1284016, 
    324786, 931285, 10591, 129, 557
}

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
                overview=str(row['overview']) if pd.notna(row['overview']) else None,
                poster_path=str(row['poster_path']) if pd.notna(row['poster_path']) else None,
                vote_average=float(row['vote_average']) if pd.notna(row['vote_average']) else None,
                popularity=float(row['popularity']) if pd.notna(row['popularity']) else None,
                genres=parse_genres_to_string(row['genres']),
                trailer_url=str(row['trailer_url']) if pd.notna(row['trailer_url']) else None,
                is_starter=(int(row['id']) in STARTER_IDS)
            )
            movies_to_add.append(movie)

        session.add_all(movies_to_add)
        await session.commit()

    print("Все фильмы успешно занесены в базу данных")
    
if __name__ == "__main__":
    asyncio.run(load_movies())