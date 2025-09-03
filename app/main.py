# app/main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os
# Импортируем lifespan из telegram_notifier
from .telegram_notifier import lifespan

# Импортируем роутеры
from .api.defects import router as defects_router
from .api.dropdowns import router as dropdowns_router
from .api.admin import router as admin_router
from .api.users import router as users_router

# Импортируем инициализацию БД
from .core import init_db

# Создаем приложение FastAPI с lifespan
app = FastAPI(lifespan=lifespan)

# Создаем папку для загрузок, если её нет
if not os.path.exists("uploads"):
    os.makedirs("uploads")

# Подключаем статические файлы
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

# Подключаем роутеры
app.include_router(defects_router, prefix="/defects")
app.include_router(dropdowns_router, prefix="/dropdown-lists")
app.include_router(admin_router, prefix="/admin")
app.include_router(users_router, prefix="/users")

# Инициализируем базу данных при запуске
init_db.init_db()
print("База данных инициализирована")

# Основной маршрут для index.html
@app.get("/")
def read_root():
    """Главная страница."""
    with open("frontend/index.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    return html_content

# Маршрут для admin.html
@app.get("/admin")
def read_admin():
    """Страница администрирования."""
    with open("frontend/admin.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    return html_content

# Маршрут для subscribe.html
@app.get("/subscribe")
def read_subscribe():
    """Страница подписки на уведомления."""
    with open("frontend/subscribe.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    return html_content