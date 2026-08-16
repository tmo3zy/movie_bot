import asyncio
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InputMediaPhoto
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database.engine import init_db
from database.requests import add_user, add_interaction, get_liked_movies_page 
from database.models import Movie
from keyboards import get_movie_keyboard, MovieAction, get_feed_menu, get_likes_menu, get_start_keyboard
from services import get_recommendation, get_similar

load_dotenv()

bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500"

class UserState(StatesGroup):
    viewing_likes = State()

@dp.startup()
async def on_startup(dispatcher: Dispatcher):
    await init_db()

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear() 
    await add_user(tg_id=message.from_user.id, username=message.from_user.username)
    
    # Отправляем сообщение с правилами и инлайн-кнопкой
    await message.answer(
        "<b>Привет! Я КиноКомпас. </b> 🍿\n\n"
        "Я помогу тебе найти фильм на вечер. Вот, как со мной работать:\n"
        "👎 <b>Скип</b> - не хочу смотреть\n"
        "🍿 <b>Буду смотреть</b> - отложить фильм\n"
        "❤️ <b>Смотрел(а), топ</b> - уже смотрел(а), понравилось\n"
        "🔎 <b>Похожие</b> - переключиться в ленту похожих фильмов\n\n"
        "Внимательно изучи кнопки и нажимай старт!",
        parse_mode="HTML",
        reply_markup=get_start_keyboard()
    )

@dp.callback_query(F.data == "start_search")
async def process_start_search(callback: types.CallbackQuery):
    await callback.message.answer("Запускаем ленту... 🧭", reply_markup=get_feed_menu())
    
    first_movie = await get_recommendation(callback.from_user.id)
    if first_movie:
        await send_movie_card(callback.message, first_movie)
        
    await callback.answer()

@dp.message(F.text == "🎲 Лента")
async def cmd_feed(message: types.Message, state: FSMContext):
    await state.clear() 
    await message.answer("Возвращаемся в ленту 🍿", reply_markup=get_feed_menu())
    
    next_movie = await get_recommendation(message.from_user.id)
    if next_movie:
        await send_movie_card(message, next_movie)

async def send_movie_card(message_or_callback, movie: Movie):
    overview = movie.overview if movie.overview else "Описание отсутствует."
    genres_text = movie.genres if movie.genres else "Не указаны"
    if len(overview) > 850:
        overview = f"{overview[:850]}..."
    
    caption = (
        f"🎬 <b>{movie.title}</b>\n\n"
        f"⭐ Рейтинг: {movie.vote_average or 'Нет'}\n\n"
        f"🎭 Жанры: {genres_text}\n\n"
        f"<i>{overview}</i>"
    )
    
    keyboard = get_movie_keyboard(movie.id, movie.trailer_url)
    
    if movie.poster_path and str(movie.poster_path).lower() != "none":
        poster_url = f"{TMDB_IMAGE_BASE}{movie.poster_path}"
    else:
        poster_url = "https://placehold.co/500x750/222222/FFFFFF/png?text=No+Poster"

    if isinstance(message_or_callback, types.Message):
        await message_or_callback.answer_photo(
            photo=poster_url,
            caption=caption,
            reply_markup=keyboard,
            parse_mode="HTML"
        )


async def edit_movie_card(message: types.Message, movie: Movie, is_similar: bool = False):
    overview = movie.overview if movie.overview else "Описание отсутствует."
    genres_text = movie.genres if movie.genres else "Не указаны"
    if len(overview) > 850:
        overview = f"{overview[:850]}..."

    caption = (
        f"🎬 <b>{movie.title}</b>\n\n"
        f"⭐ Рейтинг: {movie.vote_average or 'Нет'}\n\n"
        f"🎭 Жанры: {genres_text}\n\n"
        f"<i>{overview}</i>"
    )
    
    keyboard = get_movie_keyboard(movie.id, movie.trailer_url, is_similar)
    
    if movie.poster_path and str(movie.poster_path).lower() != "none":
        poster_url = f"{TMDB_IMAGE_BASE}{movie.poster_path}"
    else:
        poster_url = "https://placehold.co/500x750/222222/FFFFFF/png?text=No+Poster"

    try:
        await message.edit_media(
            media=InputMediaPhoto(media=poster_url, caption=caption, parse_mode="HTML"),
            reply_markup=keyboard
        )
    except Exception as e:
        print(f"[ERROR] Не удалось обновить медиа: {e}")

@dp.callback_query(MovieAction.filter())
async def handle_movie_action(callback: types.CallbackQuery, callback_data: MovieAction):
    user_id = callback.from_user.id
    action = callback_data.action
    movie_id = callback_data.movie_id
    is_similar = callback_data.is_similar

    await add_interaction(tg_id=user_id, movie_id=movie_id, action=action)
    
    try:
        messages = {
            "skip": "Пропущено ⏩",
            "like": "Добавлено в закладки 🍿",
            "watched": "Отмечено как просмотренное 🔥",
            "similar": "Ищем похожие фильмы... 🔎",
            "back_to_feed": "Возвращаемся в ленту... 🔙"
        }
        await callback.answer(messages.get(action, "Принято!"))
    except Exception as e:
        print(f"[WARNING] Не удалось ответить на callback (возможно, устарел): {e}")

    if action == "similar" or (action in ("skip", "like", "watched") and is_similar):
        next_movie = await get_similar(user_id, movie_id)
        
        if next_movie:
            await edit_movie_card(callback.message, next_movie, is_similar=True)
        else:
            next_movie = await get_recommendation(user_id)
            if next_movie:
                await edit_movie_card(callback.message, next_movie, is_similar=False)

    elif action in ("skip", "like", "watched", "back_to_feed"):
        next_movie = await get_recommendation(user_id)
        if next_movie:
            await edit_movie_card(callback.message, next_movie, is_similar=False)

@dp.message(F.text == "🍿 Понравившиеся фильмы")
async def show_likes_first_page(message: types.Message, state: FSMContext):
    await state.set_state(UserState.viewing_likes)
    await state.update_data(page=0)
    await send_likes_page(message, message.from_user.id, 0)

@dp.message(UserState.viewing_likes, F.text.in_(["⬅️ Назад", "Вперед ➡️"]))
async def handle_pagination(message: types.Message, state: FSMContext):
    data = await state.get_data()
    page = data.get("page", 0)
    
    if message.text == "Вперед ➡️":
        page += 1
    else:
        page -= 1
        
    await state.update_data(page=page)
    await send_likes_page(message, message.from_user.id, page)

async def send_likes_page(message: types.Message, user_id: int, page: int):
    limit = 5
    movies, total = await get_liked_movies_page(user_id, page, limit)
    
    if total == 0:
        await message.answer("У вас пока нет отложенных фильмов 🍿", reply_markup=get_feed_menu())
        return
        
    for movie in movies:
        await send_movie_card(message, movie)
        
    total_pages = (total + limit - 1) // limit
    has_prev = page > 0
    has_next = page < total_pages - 1
    
    await message.answer(
        f"Страница {page + 1} из {total_pages}", 
        reply_markup=get_likes_menu(has_prev, has_next)
    )

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())