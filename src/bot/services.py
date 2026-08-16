import aiohttp
import numpy as np
from datetime import datetime
from database.requests import get_user_history, get_movie_by_id, get_random_movie
from database.models import *
from pathlib import Path

STARTER_IDS = {
    1477565, 348893, 1235877, 1261825, 1368314, 
    255709, 14160, 337404, 537915, 1284016, 
    324786, 931285, 10591, 129, 557
}

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"

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
                    
                    for rec in recommendations:
                        rec_id = rec["movie_id"]
                        if rec_id not in seen_ids:
                            return await get_movie_by_id(rec_id)
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