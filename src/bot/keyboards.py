from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder

class MovieAction(CallbackData, prefix="mov"):
    action: str
    movie_id: int
    is_similar: bool = False


def get_movie_keyboard(movie_id: int, trailer_url: str | None = None, is_similar: bool = False) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    builder.button(
        text="👎 Скип", 
        callback_data=MovieAction(action="skip", movie_id=movie_id)
    )
    builder.button(
        text="🍿 Буду смотреть", 
        callback_data=MovieAction(action="like", movie_id=movie_id)
    )
    builder.button(
        text="❤️ Смотрел(а), топ", 
        callback_data=MovieAction(action="watched", movie_id=movie_id)
    )

    if is_similar:
        builder.button(
            text="🔙 В ленту", 
            callback_data=MovieAction(action="back_to_feed", movie_id=movie_id)
        )
    else:
        builder.button(
            text="🔎 Похожие", 
            callback_data=MovieAction(action="similar", movie_id=movie_id)
        )
    
    if trailer_url:
        builder.button(text="🎬 Трейлер", url=trailer_url)
        
    builder.adjust(3, 2)
    
    return builder.as_markup()

# Меню для Ленты (только кнопка перехода в понравившиеся)
def get_feed_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🍿 Понравившиеся фильмы")]],
        resize_keyboard=True
    )

# Меню для Понравившихся (Лента по центру, стрелки по бокам если нужны)
def get_likes_menu(has_prev: bool, has_next: bool) -> ReplyKeyboardMarkup:
    row = []
    if has_prev:
        row.append(KeyboardButton(text="⬅️ Назад"))
    
    row.append(KeyboardButton(text="🎲 Лента"))
    
    if has_next:
        row.append(KeyboardButton(text="Вперед ➡️"))
        
    return ReplyKeyboardMarkup(
        keyboard=[row],
        resize_keyboard=True
    )