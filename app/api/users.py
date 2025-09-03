# app/api/users.py
from fastapi import APIRouter, HTTPException
# Используем относительный импорт
from ..database import subscribe_user

router = APIRouter()

@router.post("/subscribe")
def subscribe_user_endpoint(subscribe_data: dict): # Используем dict для совместимости
    success = subscribe_user(subscribe_data['name'], subscribe_data['telegram_id'])
    
    if not success:
        raise HTTPException(status_code=400, detail="Пользователь с таким Telegram ID уже существует")
    
    return {"status": "subscribed"}