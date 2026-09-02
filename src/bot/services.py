import aiohttp
import os
import numpy as np
from datetime import datetime
from database.requests import get_user_history, get_movie_by_id, get_random_movie
from database.models import *
from pathlib import Path
import pandas as pd
from catboost import CatBoostClassifier
from database.engine import AsyncSessionLocal
from sqlalchemy import select

STARTER_IDS = {
    1477565, 348893, 1235877, 1261825, 1368314, 
    255709, 14160, 337404, 537915, 1284016, 
    324786, 931285, 10591, 129, 557
}

if os.path.exists("/app/data"):
    DATA_DIR = Path("/app/data")
else:
    # Фолбэк для локального запуска с ноутбука
    DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"

print(f"[DEBUG] Итоговый путь к папке данных: {DATA_DIR}")

print("[INFO] Загрузка модели CatBoost...")
try:
    model_path = DATA_DIR / "recsys_prod.cbm"
    cb_model = CatBoostClassifier()
    cb_model.load_model(str(model_path))
    MODEL_FEATURES = cb_model.feature_names_
    print("[INFO] Модель CatBoost успешно загружена!")
except Exception as e:
    print(f"[ERROR] Ошибка при загрузке CatBoost: {e}")
    cb_model = None

print("[INFO] Загрузка эмбеддингов в память бота...")
try:
    embeddings_path = DATA_DIR / "movie_embeddings.bin"
    ids_path = DATA_DIR / "movie_ids.bin"

    with open(embeddings_path, 'rb') as f:
        shape = np.fromfile(f, dtype=np.uint32, count=2)
        num_movies, vector_dim = shape[0], shape[1]
        data = np.fromfile(f, dtype=np.float32)
        movie_embeddings = data.reshape(num_movies, vector_dim)

    movie_ids = np.fromfile(ids_path, dtype=np.uint32)
    id_to_index = {int(movie_id): idx for idx, movie_id in enumerate(movie_ids)}
    
    print(f"[INFO] Успешно загружено {len(movie_ids)} векторов размерностью {vector_dim}!")
except Exception as e:
    print(f"[ERROR] Ошибка при загрузке эмбеддингов: {e}")
    movie_embeddings = None
    id_to_index = {}
    vector_dim = 0

async def get_recommendation(user_id: int) -> Movie | None:
    interactions, seen_ids = await get_user_history(user_id)

    seen_starters = seen_ids.intersection(STARTER_IDS)
    if len(seen_starters) < len(STARTER_IDS):
        return await get_random_movie(user_id)

    profile_vector = np.zeros(vector_dim, dtype=np.float32)
    total_weight = 0.0
    now = datetime.utcnow()

    hours_since_last_action = (now - interactions[0].timestamp).total_seconds() / 3600
    session_discount = 0.2 if hours_since_last_action > 3 else 1.0

    for interaction in interactions:
        if interaction.action == 'like':
            base_weight = 1.0
        elif interaction.action == 'watched':
            base_weight = 0.8
        else:
            continue
            
        hours_passed = (now - interaction.timestamp).total_seconds() / 3600
        decay = np.exp(-0.05 * hours_passed)
        
        final_weight = base_weight * decay * session_discount
        
        movie_idx = id_to_index.get(interaction.movie_id)
        if movie_idx is not None:
            profile_vector += movie_embeddings[movie_idx] * final_weight
            total_weight += final_weight

    if total_weight == 0:
        return await get_random_movie(user_id)
        
    profile_vector /= total_weight
    profile_vector = profile_vector / np.linalg.norm(profile_vector)

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://knn_server:8080/recommend", 
                json={"vector": profile_vector.tolist()},
                timeout=5.0
            ) as response:
                if response.status == 200:
                    recommendations = await response.json()

                    candidate_ids = []
                    for rec in recommendations:
                        rec_id = rec["movie_id"]
                        if rec_id not in seen_ids:
                            candidate_ids.append(rec_id)

                    if candidate_ids:
                        return await rank_and_select_movie(user_id, interactions, candidate_ids)
    except Exception as e:
        print(f"Ошибка запроса к C++ серверу: {e}")
        
    return await get_random_movie(user_id)

async def get_similar(user_id: int, movie_id: int):
    _, seen_ids = await get_user_history(user_id)

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"http://knn_server:8080/similar?movie_id={movie_id}", 
                timeout=5.0
            ) as response:
                if response.status == 200:
                    recommendations = await response.json()

                    for rec in recommendations:
                        rec_id = rec["movie_id"]
                        if rec_id not in seen_ids:
                            return await get_movie_by_id(rec_id)
    except Exception as e:
        print(f"[ERROR] Ошибка запроса к C++ серверу (similar): {e}")
    
    return await get_recommendation(user_id)

async def rank_and_select_movie(user_id: int, interactions: list, candidate_ids: list) -> Movie | None:
    if not candidate_ids or cb_model is None:
        return await get_random_movie(user_id)

    interactions_count = len(interactions)
    liked_ids = [i.movie_id for i in interactions if i.action in ('like', 'watched', 'similar')]
    user_like_rate = len(liked_ids) / interactions_count if interactions_count > 0 else np.nan

    user_avg_vote = np.nan
    user_favorite_genres = 'unknown'

    async with AsyncSessionLocal() as session:
        if liked_ids:
            l_result = await session.execute(select(Movie).where(Movie.id.in_(liked_ids)))
            liked_movies = l_result.scalars().all()
            
            if liked_movies:
                votes = [m.vote_average for m in liked_movies if m.vote_average is not None]
                if votes:
                    user_avg_vote = sum(votes) / len(votes)
                    
                genres_list = [m.genres for m in liked_movies if m.genres is not None]
                if genres_list:
                    user_favorite_genres = ' '.join(genres_list)

        c_result = await session.execute(select(Movie).where(Movie.id.in_(candidate_ids)))
        candidate_movies = c_result.scalars().all()

    if not candidate_movies:
        return await get_random_movie(user_id)

    rows = []
    for m in candidate_movies:
        rows.append({
            'movie_id': m.id,
            'title': str(m.title),
            'overview': m.overview,
            'vote_average': m.vote_average,
            'popularity': m.popularity,
            'genres': m.genres,
            'release_year': m.release_year,
            'country': m.country,
            'user_id': user_id,
            'interactions_count': interactions_count,
            'user_like_rate': user_like_rate,
            'user_avg_vote': user_avg_vote,
            'user_favorite_genres': user_favorite_genres
        })
        
    df_scoring = pd.DataFrame(rows)

    df_scoring['overview_length'] = df_scoring['overview'].apply(lambda x: len(str(x)) if pd.notnull(x) else 0)
    df_scoring['is_evening'] = 1 if datetime.utcnow().hour >= 18 else 0

    text_features = ['overview', 'user_favorite_genres', 'genres', 'title']
    cat_features = ['user_id', 'country']
    for col in text_features + cat_features:
        if col in df_scoring.columns:
            df_scoring[col] = df_scoring[col].fillna('unknown').astype(str)

    preds = cb_model.predict_proba(df_scoring[MODEL_FEATURES])[:, 1]
    df_scoring['final_score'] = preds

    best_movie_id = df_scoring.sort_values('final_score', ascending=False).iloc[0]['movie_id']
    
    for m in candidate_movies:
        if m.id == best_movie_id:
            return m
            
    return await get_random_movie(user_id)