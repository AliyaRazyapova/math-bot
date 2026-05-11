import asyncio
import io
import math
import os
import re
from PIL import Image, ImageDraw, ImageFont
from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command

# ---------- Настройки ----------
TOKEN = os.environ.get("TOKEN")
if not TOKEN:
    raise ValueError("Токен не задан в переменной окружения TOKEN")

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# ---------- Вспомогательные функции ----------
def generate_formula_image(formula_text: str) -> io.BytesIO:
    """Создаёт PNG-изображение с формулой и возвращает BytesIO."""
    img = Image.new('RGB', (500, 120), color='white')
    draw = ImageDraw.Draw(img)
    try:
        # Попробуем загрузить шрифт (если есть), иначе default
        font = ImageFont.truetype("arial.ttf", 24)
    except:
        font = ImageFont.load_default()
    # Разбиваем длинный текст на строки
    lines = formula_text.split('\n')
    y = 20
    for line in lines:
        draw.text((20, y), line, fill='black', font=font)
        y += 30
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf

# ---------- Обработчики команд ----------
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 Привет! Я <b>математический бот</b>.\n"
        "Доступные команды:\n"
        "/help – справка\n"
        "/list – список формул и задач\n\n"
        "Примеры:\n"
        "<code>Пифагор 3 4</code> – гипотенуза\n"
        "<code>Квадрат 1 -5 6</code> – корни уравнения"
    )

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        "📚 <b>Помощь</b>\n\n"
        "<b>Теорема Пифагора:</b>\n"
        "Напишите: <code>Пифагор a b</code>, где a и b – катеты.\n"
        "Пример: <code>Пифагор 3 4</code> → гипотенуза = 5\n\n"
        "<b>Квадратное уравнение:</b>\n"
        "Напишите: <code>Квадрат a b c</code>\n"
        "Пример: <code>Квадрат 1 -5 6</code> → корни 2.0 и 3.0\n\n"
        "<b>Другие команды:</b>\n"
        "/list – полный список функций\n"
        "/start – приветствие"
    )

@dp.message(Command("list"))
async def cmd_list(message: types.Message):
    text = (
        "📋 <b>Доступные математические функции:</b>\n\n"
        "1️⃣ <b>Теорема Пифагора</b>\n"
        "   → <code>Пифагор 3 4</code>\n\n"
        "2️⃣ <b>Квадратное уравнение</b>\n"
        "   → <code>Квадрат 1 -5 6</code>\n\n"
        "Больше функций будет добавлено в следующих версиях!"
    )
    await message.answer(text)

# ---------- Обработка текстовых сообщений ----------
@dp.message()
async def handle_math(message: types.Message):
    text = message.text.strip().lower()
    try:
        # ----- Теорема Пифагора -----
        if text.startswith("пифагор"):
            parts = text.split()
            if len(parts) != 3:
                await message.answer("❌ Ошибка: введите <code>Пифагор a b</code>, где a и b – катеты.")
                return
            a = float(parts[1])
            b = float(parts[2])
            c = math.sqrt(a*a + b*b)
            # Исправленная строка формулы
            formula_str = f"c = √({a}² + {b}²) = {c:.2f}"
            img_buf = generate_formula_image(formula_str)
            await message.answer_photo(
                photo=types.BufferedInputFile(img_buf.getvalue(), filename="formula.png"),
                caption=f"✅ Гипотенуза = <b>{c:.2f}</b>"
            )
            return

        # ----- Квадратное уравнение -----
        if text.startswith("квадрат"):
            parts = text.split()
            if len(parts) != 4:
                await message.answer("❌ Ошибка: введите <code>Квадрат a b c</code>")
                return
            a, b, c = float(parts[1]), float(parts[2]), float(parts[3])
            d = b*b - 4*a*c
            if d < 0:
                await message.answer("⚠️ Дискриминант отрицательный. Действительных корней нет.")
                return
            sqrt_d = math.sqrt(d)
            x1 = (-b + sqrt_d) / (2*a)
            x2 = (-b - sqrt_d) / (2*a)
            formula_str = f"x₁ = {x1:.2f}\nx₂ = {x2:.2f}"
            # Можно отправить текстом
            await message.answer(f"🔢 Корни уравнения:\n<code>{formula_str}</code>")
            return

        # ----- Если ничего не подошло -----
        await message.answer(
            "🤔 Я не понял запрос.\n"
            "Используйте /help или /list для списка команд.\n"
            "Пример: <code>Пифагор 3 4</code>"
        )
    except ValueError:
        await message.answer("❌ Ошибка: введите числа. Например: <code>Пифагор 3 4</code>")
    except Exception as e:
        await message.answer(f"❌ Произошла ошибка:\n<code>{str(e)}</code>")
        print(f"Ошибка: {e}")

# ---------- Запуск ----------
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
