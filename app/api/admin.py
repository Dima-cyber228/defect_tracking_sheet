# app/api/admin.py
from fastapi import APIRouter, HTTPException
# Используем относительный импорт
from ..core.config import ADMIN_PASSWORD

router = APIRouter()

@router.post("/login")
def admin_login(login_data: dict): # Используем dict для совместимости
    # Используем login_data
    if login_data.get('password') == ADMIN_PASSWORD:
        return {"token": "admin_secret_key"}
    else:
        raise HTTPException(status_code=401, detail="Неверный пароль")