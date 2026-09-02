import sys
import os
import pandas as pd
import asyncio
import ast
from sqlalchemy.dialects.postgresql import insert

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
CSV_FILE_PATH = os.path.join(project_root, "data", "tmdb_movies_ru_2.csv")
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
        for _, row in df.iterrows():
            stmt = insert(Movie).values(
                id=int(row['id']),
                title=str(row['title']),
                overview=str(row['overview']) if pd.notna(row['overview']) else None,
                poster_path=str(row['poster_path']) if pd.notna(row['poster_path']) else None,
                vote_average=float(row['vote_average']) if pd.notna(row['vote_average']) else None,
                popularity=float(row['popularity']) if pd.notna(row['popularity']) else None,
                genres=parse_genres_to_string(row['genres']),
                trailer_url=str(row['trailer_url']) if pd.notna(row['trailer_url']) else None,
                release_year=int(row['release_year']) if pd.notna(row['release_year']) else None,
                country=str(row['country']) if pd.notna(row['country']) else None,
                is_starter=(int(row['id']) in STARTER_IDS)
            )

            update_stmt = stmt.on_conflict_do_update(
                index_elements=['id'],
                set_=dict(
                    title=stmt.excluded.title,
                    overview=stmt.excluded.overview,
                    poster_path=stmt.excluded.poster_path,
                    vote_average=stmt.excluded.vote_average,
                    popularity=stmt.excluded.popularity,
                    genres=stmt.excluded.genres,
                    trailer_url=stmt.excluded.trailer_url,
                    release_year=stmt.excluded.release_year,
                    country=stmt.excluded.country,
                    is_starter=stmt.excluded.is_starter
                )
            )
            await session.execute(update_stmt)
            
        await session.commit()

    print("Все фильмы успешно занесены в базу данных")
    
if __name__ == "__main__":
    asyncio.run(load_movies())