import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
import os

TOKEN = os.environ.get("TOKEN")  # Токен будет передан через переменную окружения
if not TOKEN:
    raise ValueError("Не задан токен")

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("Привет! Я <b>математический бот</b>. Отправь мне пример, и я решу.")

@dp.message(Command("help"))
async def help(message: types.Message):
    await message.answer("Доступны команды: /start, /help\nА также решение примеров, например: 2+2")

@dp.message()
async def echo(message: types.Message):
    # Здесь потом добавишь свою логику
    await message.answer(f"Вы написали: <code>{message.text}</code>")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())