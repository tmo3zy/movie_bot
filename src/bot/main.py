import asyncio
from aiogram import Bot, Dispatcher
from database.engine import init_db
import os
from dotenv import load_dotenv
from aiogram.filters import Command
from aiogram import types
from database.requests import add_user

load_dotenv()

bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await add_user(
        tg_id=message.from_user.id,
        username=message.from_user.username
    )

    await message.answer(
        "Привет! Я КиноКомпас. 🍿\n"
        "Я помогу тебе найти фильм на вечер"
    )

@dp.startup()
async def on_startup(dispatcher: Dispatcher):
    await init_db()
    print("Бот готов к работе!")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())