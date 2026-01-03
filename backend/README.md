# Backend (FastAPI)

## Огляд
Це бекенд PunkSchool, побудований на **FastAPI + SQLAlchemy**. Сервіс відповідає за автентифікацію, курси, уроки, користувачів та фінанси. База за замовчуванням — SQLite (`music_courses.db`) у корені `/backend`.

---

## Вимоги
| Пакет | Версія / Примітка |
|-------|-------------------|
| Python | 3.10+ (рекомендовано 3.11) |
| pip / venv | стандартні модулі Python |
| OS | Windows / macOS / Linux |

---

## Підготовка середовища
1. **Перейдіть у папку бекенду**
   ```powershell
   cd backend
   ```
2. **Створіть та активуйте віртуальне середовище**
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate     # Windows
   source venv/bin/activate    # macOS / Linux
   ```
3. **Встановіть залежності**
   ```powershell
   pip install -r requirements.txt
   ```
> Якщо під час інсталяції `pdfkit` з’являються помилки, встановіть wkhtmltopdf (https://wkhtmltopdf.org/downloads.html) і додайте його в PATH.

---

## Налаштування змінних середовища
Створіть `.env` у папці `backend` (опціонально). Приклад:
```env
DATABASE_URL=sqlite:///./music_courses.db
JWT_SECRET=super-secret-key
JWT_ALGORITHM=HS256
```
Без `.env` використовуються дефолтні значення (SQLite у файлі `music_courses.db`).

---

## Запуск локально
1. Активуйте `venv` (як описано вище).
2. Запустіть сервер:
   ```powershell
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
3. API буде доступне на `http://localhost:8000/api`. Swagger: `http://localhost:8000/docs`.

Стандартний адмін:
```
email: admin@punkschool.com
password: admin
```

---

## Корисні команди
| Дія | Команда |
|-----|---------|
| Запуск (dev) | `uvicorn app.main:app --reload` |
| Перелік залежностей | `pip list` |
| Оновити залежності | `pip install -r requirements.txt --upgrade` |

---

## Структура (скорочено)
```
backend/
├─ app/
│  ├─ routers/      # FastAPI-роутери
│  ├─ services/     # Бізнес-логіка
│  ├─ models/       # SQLAlchemy-моделі
│  ├─ schemas/      # Pydantic-схеми
│  └─ main.py       # Точка входу
├─ requirements.txt
├─ music_courses.db
└─ README.md
```

---

## Типові помилки
1. **`database is locked`** — закрийте інші процеси, що використовують SQLite, перезапустіть сервер.
2. **`401 Unauthorized`** — перевірте токен у `localStorage`, переконайтесь, що бекенд працює, а `JWT_SECRET` не змінено.
3. **CORS** — у `app/main.py` вже додано CORSMiddleware (дозволяє `http://localhost:5173`). Для інших доменів додайте їх у список дозволених.

---

## Деплой коротко
1. Встановіть залежності на сервері (Python 3.10+).
2. Задайте змінні середовища / `.env` з бойовими секретами.
3. Запускайте під `gunicorn` або `hypercorn` (наприклад, `gunicorn -k uvicorn.workers.UvicornWorker app.main:app`).
4. Поставте Nginx / Caddy як реверс-проксі для HTTPS.
