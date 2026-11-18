# 🍏 NutriHub — Django трекер питания c планировщиком и соц.ленточкой

[![CI](https://img.shields.io/github/actions/workflow/status/USER/REPO/ci.yml?label=CI&logo=github)](../../actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11–3.13-blue)]()
[![Django](https://img.shields.io/badge/Django-5.2.x-0C4B33)]()
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![ruff](https://img.shields.io/badge/linter-ruff-%23232F3E)](https://github.com/astral-sh/ruff)

Современный, адаптивный и визуально чистый трекер калорий/БЖУ с дневником, базой продуктов, рецептами, **планировщиком приёмов**, экспортом (CSV/PDF/Markdown) и светлой/тёмной темами.

## ✨ Возможности
- 👤 Регистрация/логин, профиль, цели
- 📔 Дневник: продукты/рецепты, быстрый поиск, итоги за день/месяц, **экспорт**
- 🍳 Рецепты: ингредиенты из базы, пересчёт нутриентов на порции/100 г
- 🗓 Планировщик: план на день, перенос в дневник в один клик, стрелки/быстрый выбор дат
- 📈 Графики прогресса и нормы (TDEE/BMR), калькулятор
- 🌓 Светлая/тёмная тема, адаптивный UI

## 🚀 Быстрый старт (локально)
```bash
git clone https://github.com/USER/REPO.git
cd REPO
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py loaddata fixtures/products.sample.json || true
python manage.py runserver
```

## 🐳 Docker
```bash
docker compose up --build -d
```

## 🔧 Команды
```bash
make fmt   # black + isort + ruff --fix
make lint  # проверки
make run   # dev-сервер
make fixtures
```
