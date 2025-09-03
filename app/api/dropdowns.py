# app/api/dropdowns.py
from fastapi import APIRouter, HTTPException, Header
from typing import Optional
# Используем относительные импорты
from ..database import get_dropdown_lists, update_dropdown_lists

router = APIRouter()

# ИЗМЕНЕНО: Путь с "/" на "/dropdown-lists/"
@router.get("/dropdown-lists/") 
def get_dropdown_lists_endpoint():
    return get_dropdown_lists()

# ИЗМЕНЕНО: Путь с "/admin/update-lists" на "/update-lists"
# Потому что префикс "/admin" будет добавлен в main.py
@router.post("/update-lists") 
def update_dropdown_lists_endpoint(lists: dict, authorization: Optional[str] = Header(None)):
    if not authorization or authorization != "Bearer admin_secret_key":
        raise HTTPException(status_code=401, detail="Требуется авторизация")
    
    update_dropdown_lists(lists)
    return {"status": "updated"}