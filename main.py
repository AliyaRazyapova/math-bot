import asyncio
import io
import math
import os
import re
import sympy as sp
import matplotlib.pyplot as plt
import numpy as np
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

def plot_expression(expr_str: str, var: str = 'x') -> io.BytesIO:
    """Строит график функции и возвращает BytesIO с PNG."""
    try:
        # Определяем символ и функцию
        x = sp.Symbol(var)
        expr = sp.sympify(expr_str)
        f = sp.lambdify(x, expr, modules='numpy')
        # Генерируем точки
        x_vals = np.linspace(-10, 10, 400)
        y_vals = f(x_vals)
        # Строим график
        plt.figure(figsize=(8, 6))
        plt.plot(x_vals, y_vals, linewidth=2)
        plt.title(f'График функции: {expr_str}')
        plt.xlabel(var)
        plt.ylabel(f'f({var})')
        plt.grid(True)
        # Сохраняем в буфер
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        plt.close()
        buf.seek(0)
        return buf
    except Exception as e:
        raise ValueError(f"Ошибка построения графика: {e}")

# ---------- Обработчики команд ----------
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 Привет! Я <b>математический бот</b>.\n"
        "Доступные команды:\n"
        "/help – справка\n"
        "/list – список всех функций\n\n"
        "Примеры:\n"
        "<code>Пифагор 3 4</code> – гипотенуза\n"
        "<code>Квадрат 1 -5 6</code> – корни уравнения\n"
        "<code>/solve_system x+y=2, x-y=0</code> – система уравнений\n"
        "<code>/plot x**2 - 3*x + 2</code> – построить график"
    )

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        "📚 <b>Помощь</b>\n\n"
        "<b>1. Теорема Пифагора:</b>\n"
        "<code>Пифагор a b</code> → пример: Пифагор 3 4\n\n"
        "<b>2. Квадратные уравнения:</b>\n"
        "<code>Квадрат a b c</code> → пример: Квадрат 1 -5 6\n\n"
        "<b>3. Системы уравнений:</b>\n"
        "<code>/solve_system уравнение1, уравнение2</code>\n"
        "Пример: <code>/solve_system x+y=2, x-y=0</code>\n\n"
        "<b>4. Построение графиков:</b>\n"
        "<code>/plot выражение</code> (переменная x)\n"
        "Пример: <code>/plot x**2 - 4</code>\n\n"
        "<b>Общие команды:</b>\n"
        "/list – полный список\n"
        "/start – приветствие"
    )

@dp.message(Command("list"))
async def cmd_list(message: types.Message):
    text = (
        "📋 <b>Все возможности бота</b>\n\n"
        "🔹 <b>Теорема Пифагора</b>\n"
        "   <code>Пифагор 3 4</code>\n\n"
        "🔹 <b>Квадратное уравнение</b>\n"
        "   <code>Квадрат 1 -5 6</code>\n\n"
        "🔹 <b>Системы линейных уравнений</b>\n"
        "   <code>/solve_system x+y=2, x-y=0</code>\n\n"
        "🔹 <b>Построение графиков</b>\n"
        "   <code>/plot x**2 - 3*x + 2</code>\n\n"
        "🔹 <b>Справка</b>\n"
        "   <code>/help</code>\n"
    )
    await message.answer(text)

@dp.message(Command("solve_system"))
async def cmd_solve_system(message: types.Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("❌ Введите уравнения после команды. Пример:\n<code>/solve_system x+y=2, x-y=0</code>")
        return
    eq_str = args[1]
    try:
        # Разделяем уравнения по запятой или точке с запятой
        eq_parts = re.split(r'[,;]', eq_str)
        equations = []
        variables = set()
        for part in eq_parts:
            left, right = part.split('=')
            expr = sp.sympify(left.strip()) - sp.sympify(right.strip())
            equations.append(expr)
            # Находим все символы (переменные)
            for sym in expr.free_symbols:
                variables.add(sym)
        if not variables:
            await message.answer("❌ Не удалось определить переменные.")
            return
        # Решаем систему
        solution = sp.solve(equations, list(variables))
        if not solution:
            await message.answer("❌ Система не имеет решений.")
            return
        # Формируем ответ
        if isinstance(solution, list) and len(solution) == 1:
            solution = solution[0]  # один кортеж решений
        # Если решение – словарь
        if isinstance(solution, dict):
            ans_lines = [f"{var} = {solution[var]}" for var in solution]
        elif isinstance(solution, (tuple, list)):
            ans_lines = [f"{var} = {solution[i]}" for i, var in enumerate(variables)]
        else:
            ans_lines = [str(solution)]
        answer_text = "✅ Решение системы:\n" + "\n".join(ans_lines)
        await message.answer(answer_text)
    except Exception as e:
        await message.answer(f"❌ Ошибка при решении: {e}\nПример: <code>/solve_system x+y=2, x-y=0</code>")

@dp.message(Command("plot"))
async def cmd_plot(message: types.Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("❌ Укажите выражение. Пример:\n<code>/plot x**2 - 4</code>")
        return
    expr = args[1].strip()
    try:
        img_buf = plot_expression(expr)
        await message.answer_photo(
            photo=types.BufferedInputFile(img_buf.getvalue(), filename="plot.png"),
            caption=f"📈 График функции: <code>{expr}</code>"
        )
    except Exception as e:
        await message.answer(f"❌ Не удалось построить график: {e}\nПример: <code>/plot x**2 - 4</code>")

# ---------- Обработка текстовых сообщений (без команд) ----------
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
            answer_text = f"x₁ = {x1:.2f}\nx₂ = {x2:.2f}"
            await message.answer(f"🔢 Корни квадратного уравнения:\n<code>{answer_text}</code>")
            return

        # ----- Альтернативный формат для систем уравнений (без команды) -----
        if text.startswith("реши систему") or text.startswith("система"):
            # Извлекаем уравнения после ключевых слов
            rest = re.sub(r'^(реши систему|система)', '', text).strip()
            if not rest:
                await message.answer("❌ Пример: <code>реши систему x+y=2, x-y=0</code>")
                return
            # Переиспользуем логику solve_system
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
                if not variables:
                    await message.answer("❌ Не удалось определить переменные.")
                    return
                solution = sp.solve(equations, list(variables))
                if not solution:
                    await message.answer("❌ Система не имеет решений.")
                    return
                if isinstance(solution, list) and len(solution) == 1:
                    solution = solution[0]
                if isinstance(solution, dict):
                    ans_lines = [f"{var} = {solution[var]}" for var in solution]
                elif isinstance(solution, (tuple, list)):
                    ans_lines = [f"{var} = {solution[i]}" for i, var in enumerate(variables)]
                else:
                    ans_lines = [str(solution)]
                answer_text = "✅ Решение системы:\n" + "\n".join(ans_lines)
                await message.answer(answer_text)
            except Exception as e:
                await message.answer(f"❌ Ошибка: {e}\nПример: <code>реши систему x+y=2, x-y=0</code>")
            return

        # ----- Альтернативный формат для графика (без команды) -----
        if text.startswith("построй график") or text.startswith("график"):
            expr = re.sub(r'^(построй график|график)', '', text).strip()
            if not expr:
                await message.answer("❌ Пример: <code>построй график x**2 - 4</code>")
                return
            try:
                img_buf = plot_expression(expr)
                await message.answer_photo(
                    photo=types.BufferedInputFile(img_buf.getvalue(), filename="plot.png"),
                    caption=f"📈 График: <code>{expr}</code>"
                )
            except Exception as e:
                await message.answer(f"❌ Ошибка: {e}")
            return

        # ----- Если ничего не подошло -----
        await message.answer(
            "🤔 Я не понял запрос.\n"
            "Используйте /help или /list для списка команд.\n"
            "Примеры:\n"
            "<code>Пифагор 3 4</code>\n"
            "<code>/plot x**2 - 4</code>\n"
            "<code>/solve_system x+y=2, x-y=0</code>"
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