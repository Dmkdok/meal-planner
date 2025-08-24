# Раскладка (Meal Planner)

Веб‑приложение на Flask для планирования питания в походах: создавайте раскладки по дням и приёмам пищи, добавляйте продукты, считайте общий вес и формируйте отчёт в Excel.

### Основные возможности
- Управление раскладками: создание, переименование, удаление
- Дни и приёмы пищи в раскладке; продукты с весом на человека
- Серверный расчёт итогов на заданные дни и людей
- Экспорт расчёта в Excel
- Импорт/экспорт данных пользователя в JSON
- Регистрация/вход, смена пароля
- Health‑endpoint для оркестраторов

## Стек
- **Backend**: Flask 3, Flask‑SQLAlchemy, Flask‑Login, Flask‑Bcrypt
- **DB**: SQLite (локально) / PostgreSQL (в Docker Compose)
- **Migrations**: Alembic (авто‑upgrade по флагу `INIT_DB` в `wsgi`)
- **Serve**: Gunicorn (Docker), встроенный Flask сервер локально

## Структура проекта
```
raskladka/
├─ raskladka/
│  ├─ __init__.py       # конфиг Flask, БД, хэндлеры ошибок, /health
│  ├─ models.py         # модели SQLAlchemy
│  ├─ services.py       # бизнес‑логика (расчёты, CRUD)
│  ├─ utils.py          # валидации и утилиты
│  ├─ views.py          # маршруты и API
│  ├─ wsgi.py           # точка входа в Docker, Alembic upgrade по INIT_DB
│  ├─ templates/        # HTML шаблоны
│  └─ static/           # статические файлы
├─ migrations/          # Alembic (env.py, versions/)
├─ docker-compose.yml   # Postgres + веб‑сервис
├─ Dockerfile           # prod‑образ (gunicorn)
├─ requirements.txt     # зависимости Python
├─ run.py               # локальный запуск (debug)
└─ env.example          # пример переменных окружения
```

## Быстрый старт
### Вариант A: Локально (SQLite)
1) Создайте и активируйте виртуальное окружение, установите зависимости:
```bash
pip install -r requirements.txt
```
2) Запустите приложение (создание таблиц произойдёт при старте):
```bash
python run.py
```
3) Откройте `http://localhost:5000`

По умолчанию используется `DATABASE_URI=sqlite:///meals.db` (см. `raskladka/__init__.py`). Чтобы указать иной путь для SQLite, выставьте `DATABASE_URI` в окружении, например:
```bash
set DATABASE_URI=sqlite:///E:/Dev/raskladka/instance/meals.db   # Windows (cmd)
export DATABASE_URI=sqlite:////path/to/meals.db                 # bash
```

### Вариант B: Docker Compose (PostgreSQL)
Требуется Docker и Docker Compose.

1) Настройте переменные окружения, при необходимости скопировав `env.example` в `.env` и изменив значения:
```bash
cp env.example .env
# отредактируйте .env по необходимости
```
2) Соберите и поднимите сервисы:
```bash
docker compose pull   # подтянуть образ веб‑сервиса (или пересобрать локально)
docker compose up -d
```
3) Откройте `http://localhost:5123`

По умолчанию:
- веб: `5123 -> 5000`
- база: `postgresql+psycopg://rask_user:${POSTGRES_PASSWORD}@db:5432/raskladka`

#### Инициализация/миграции в Docker
Автоматический `alembic upgrade head` выполняется на старте, если `INIT_DB=true` в окружении веб‑контейнера (см. `raskladka/wsgi.py`). В `docker-compose.yml` флаг можно задать через `.env`:
```bash
INIT_DB=true docker compose up -d
```

### Сборка собственного Docker‑образа
```bash
docker build -t raskladka:latest .
docker run -d \
  -p 5000:5000 \
  -e SECRET_KEY=change-me \
  -e DATABASE_URI=sqlite:////app/instance/meals.db \
  -e INIT_DB=false \
  -v ${PWD}/instance:/app/instance \
  --name raskladka_web \
  raskladka:latest
```

## Переменные окружения
- `SECRET_KEY` — секретный ключ Flask (по умолчанию `change-me`)
- `DATABASE_URI` — строка подключения SQLAlchemy
  - SQLite пример: `sqlite:///meals.db` или `sqlite:////abs/path/meals.db`
  - Postgres пример: `postgresql+psycopg://user:pass@host:5432/dbname`
- `INIT_DB` — если `true/1/yes`, при старте выполнится `alembic upgrade head` (только в `wsgi`/Docker)
- `FLASK_ENV` — режим Flask (`production`/`development`), в Docker по умолчанию `production`
- Дополнительно для контейнера: том `instance` монтируется для хранения БД/файлов пользователя

## Работа с миграциями (Alembic)
Локально (если используете PostgreSQL/другую СУБД и не полагаетесь на `create_all()`):
```bash
alembic revision -m "your message"
alembic upgrade head
```
В Docker используйте флаг `INIT_DB=true` для авто‑upgrade на старте контейнера, либо выполняйте Alembic вручную внутри контейнера при необходимости.

## Использование
- Перейдите на страницу регистрации/входа
- Создайте раскладку, добавляйте дни и приёмы пищи
- Добавляйте продукты с весом на человека
- Выполните расчёт через кнопку/форму, укажите дни похода и количество людей
- При необходимости экспортируйте расчёт в Excel
- В профиле доступен импорт/экспорт всех раскладок в JSON

### API (минимум)
- `POST /calculate` — расчёт по раскладке
- `GET /export_excel` — экспорт расчёта в Excel
- `GET /health` — проверка работоспособности

Пример запроса `POST /calculate`:
```json
{
  "plan_id": 1,
  "trip_days": 7,
  "people_count": 3
}
```

## Безопасность и рекомендации
- Меняйте `SECRET_KEY` в продакшене
- Для PostgreSQL используйте отдельного пользователя и сложный пароль
- Размещайте приложение за обратным прокси (напр., nginx) и включайте HTTPS
- В Docker‑сборке уже включён `ProxyFix`, корректно обрабатывающий заголовки прокси

## Лицензия
MIT
