import asyncio
import io
import math
import os
import re
import threading
import sympy as sp
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from flask import Flask

# ---------- Настройки ----------
TOKEN = os.environ.get("TOKEN")
if not TOKEN:
    raise ValueError("Токен не задан в переменной окружения TOKEN")

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# ---------- Flask для health-чеков ----------
flask_app = Flask(__name__)

@flask_app.route('/')
def index():
    return "Математический бот работает!"

@flask_app.route('/health')
def health():
    return "OK", 200

def run_flask():
    flask_app.run(host='0.0.0.0', port=8000)

# ---------- Генерация изображения формулы ----------
def generate_formula_image(formula_text: str) -> io.BytesIO:
    img = Image.new('RGB', (600, 120), color='white')
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 24)
    except:
        font = ImageFont.load_default()
    lines = formula_text.split('\n')
    y = 20
    for line in lines:
        draw.text((20, y), line, fill='black', font=font)
        y += 30
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf

# ---------- Построение графика ----------
def plot_expression(expr_str: str, var: str = 'x') -> io.BytesIO:
    x = sp.Symbol(var)
    expr = sp.sympify(expr_str)
    f = sp.lambdify(x, expr, modules='numpy')
    x_vals = np.linspace(-10, 10, 400)
    y_vals = f(x_vals)
    plt.figure(figsize=(8, 6))
    plt.plot(x_vals, y_vals, linewidth=2)
    plt.title(f'График: {expr_str}')
    plt.xlabel(var)
    plt.ylabel(f'f({var})')
    plt.grid(True)
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    buf.seek(0)
    return buf

# ---------- Команды бота ----------
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 Привет! Я <b>математический бот</b>.\n"
        "/help – справка\n"
        "/list – все функции"
    )

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    help_text = (
        "📚 <b>Справка по математическому боту</b>\n\n"
        "🔹 <b>Теорема Пифагора</b>\n"
        "   <code>Пифагор a b</code>\n"
        "   Пример: <code>Пифагор 3 4</code> → гипотенуза = 5\n\n"
        "🔹 <b>Квадратное уравнение</b>\n"
        "   <code>Квадрат a b c</code>\n"
        "   Пример: <code>Квадрат 1 -5 6</code> → корни 2 и 3\n\n"
        "🔹 <b>Системы уравнений</b>\n"
        "   <code>/solve_system уравнение1, уравнение2</code>\n"
        "   Пример: <code>/solve_system x+y=2, x-y=0</code>\n"
        "   → решение: x = 1, y = 1\n\n"
        "   Можно писать просто: <code>реши систему x+y=2, x-y=0</code>\n\n"
        "🔹 <b>Построение графиков</b>\n"
        "   <code>/plot выражение</code>\n"
        "   Пример: <code>/plot x**2 - 3*x + 2</code> → присылает картинку параболы\n\n"
        "   Можно писать: <code>построй график x**2 - 4</code>\n\n"
        "🔹 <b>Поддерживаемые операции в выражениях:</b>\n"
        "   • <code>+</code> сложение, <code>-</code> вычитание\n"
        "   • <code>*</code> умножение, <code>/</code> деление\n"
        "   • <code>**</code> степень (например x**2)\n"
        "   • <code>sqrt(x)</code> корень, <code>sin(x)</code>, <code>cos(x)</code>, <code>log(x)</code>\n\n"
        "🔹 <b>Общие команды:</b>\n"
        "   <code>/start</code> – приветствие\n"
        "   <code>/help</code> – эта справка\n"
        "   <code>/list</code> – краткий список функций\n"
        "   <code>/solve_system</code> – решение систем\n"
        "   <code>/plot</code> – построение графиков\n\n"
        "💡 <b>Совет:</b> Если не знаете, как записать выражение, спросите: <code>как записать степень</code> или <code>примеры</code>\n"
        "📢 <b>Обратная связь:</b> Если нашли ошибку или есть идеи – пишите разработчику."
    )
    await message.answer(help_text)

@dp.message(Command("list"))
async def cmd_list(message: types.Message):
    await message.answer(
        "📋 Список функций:\n"
        "🔹 Теорема Пифагора: <code>Пифагор 3 4</code>\n"
        "🔹 Квадратное уравнение: <code>Квадрат 1 -5 6</code>\n"
        "🔹 Система уравнений: <code>/solve_system x+y=2, x-y=0</code>\n"
        "🔹 График: <code>/plot x**2 - 4</code>"
    )

@dp.message(Command("solve_system"))
async def cmd_solve_system(message: types.Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("❌ Пример: <code>/solve_system x+y=2, x-y=0</code>")
        return
    eq_str = args[1]
    try:
        eq_parts = re.split(r'[,;]', eq_str)
        equations = []
        variables = set()
        for part in eq_parts:
            left, right = part.split('=')
            expr = sp.sympify(left.strip()) - sp.sympify(right.strip())
            equations.append(expr)
            for sym in expr.free_symbols:
                variables.add(sym)
        solution = sp.solve(equations, list(variables))
        if not solution:
            await message.answer("❌ Нет решений")
            return
        if isinstance(solution, dict):
            ans = "\n".join(f"{var} = {solution[var]}" for var in solution)
        else:
            ans = str(solution)
        await message.answer(f"✅ Решение:\n<code>{ans}</code>")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

@dp.message(Command("plot"))
async def cmd_plot(message: types.Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("❌ Пример: <code>/plot x**2 - 4</code>")
        return
    expr = args[1].strip()
    try:
        img_buf = plot_expression(expr)
        await message.answer_photo(
            photo=types.BufferedInputFile(img_buf.getvalue(), filename="plot.png"),
            caption=f"График: {expr}"
        )
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

# ---------- Обработка текстовых сообщений ----------
@dp.message()
async def handle_text(message: types.Message):
    text = message.text.strip().lower()
    try:
        # Пифагор
        if text.startswith("пифагор"):
            parts = text.split()
            if len(parts) != 3:
                await message.answer("❌ Формат: Пифагор a b")
                return
            a, b = float(parts[1]), float(parts[2])
            c = math.hypot(a, b)
            formula = f"c = √({a}² + {b}²) = {c:.2f}"
            img = generate_formula_image(formula)
            await message.answer_photo(
                photo=types.BufferedInputFile(img.getvalue(), filename="formula.png"),
                caption=f"✅ Гипотенуза = {c:.2f}"
            )
            return

        # Квадратное уравнение
        if text.startswith("квадрат"):
            parts = text.split()
            if len(parts) != 4:
                await message.answer("❌ Формат: Квадрат a b c")
                return
            a, b, c = map(float, parts[1:])
            d = b*b - 4*a*c
            if d < 0:
                await message.answer("⚠️ Действительных корней нет")
                return
            sqrt_d = math.sqrt(d)
            x1 = (-b + sqrt_d)/(2*a)
            x2 = (-b - sqrt_d)/(2*a)
            await message.answer(f"x₁ = {x1:.2f}\nx₂ = {x2:.2f}")
            return

        # Реши систему (текстовая команда)
        if text.startswith("реши систему"):
            rest = re.sub(r'^реши систему\s*', '', text)
            if not rest:
                await message.answer("❌ Пример: реши систему x+y=2, x-y=0")
                return
            try:
                eq_parts = re.split(r'[,;]', rest)
                equations = []
                variables = set()
                for part in eq_parts:
                    left, right = part.split('=')
                    expr = sp.sympify(left.strip()) - sp.sympify(right.strip())
                    equations.append(expr)
                    for sym in expr.free_symbols:
                        variables.add(sym)
                solution = sp.solve(equations, list(variables))
                if not solution:
                    await message.answer("❌ Нет решений")
                    return
                if isinstance(solution, dict):
                    ans = "\n".join(f"{var} = {solution[var]}" for var in solution)
                else:
                    ans = str(solution)
                await message.answer(f"✅ Решение:\n<code>{ans}</code>")
            except Exception as e:
                await message.answer(f"❌ Ошибка: {e}")
            return

        # Построй график (текстовая команда)
        if text.startswith("построй график"):
            expr = re.sub(r'^построй график\s*', '', text)
            if not expr:
                await message.answer("❌ Пример: построй график x**2 - 4")
                return
            try:
                img_buf = plot_expression(expr)
                await message.answer_photo(
                    photo=types.BufferedInputFile(img_buf.getvalue(), filename="plot.png"),
                    caption=f"График: {expr}"
                )
            except Exception as e:
                await message.answer(f"❌ Ошибка: {e}")
            return

        # Если ничего не подошло
        await message.answer("🤔 Я не понял запрос.\nИспользуйте /help или /list")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

# ---------- Запуск бота и Flask ----------
async def main():
    # Запускаем Flask в отдельном потоке
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    # Запускаем бота (основной поток)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
