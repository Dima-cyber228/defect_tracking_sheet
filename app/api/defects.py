# app/api/defects.py
from fastapi import APIRouter, Form, File, UploadFile, HTTPException
from typing import Optional
import os
import uuid
from datetime import datetime
# Используем относительные импорты
from ..database import create_defect, get_all_defects, update_defect, get_defect_by_id
from ..telegram_notifier import send_telegram_notification_async

router = APIRouter()

@router.post("/")
async def create_defect_endpoint(
    equipment: str = Form(...),
    description: str = Form(...),
    section: str = Form(...),
    danger_level: str = Form(...),
    responsible: str = Form(""),
    photo: Optional[UploadFile] = File(None)
):
    """Создание нового дефекта."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    photo_url = None
    if photo and photo.filename:
        file_extension = os.path.splitext(photo.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join("uploads", unique_filename)
        # Читаем содержимое файла
        photo_content = await photo.read()
        # Проверяем тип для корректной записи
        if isinstance(photo_content, bytes):
            with open(file_path, "wb") as buffer:
                buffer.write(photo_content)
            photo_url = f"/uploads/{unique_filename}"
        else:
            print(f"[WARNING] UploadFile.read() вернул не bytes: {type(photo_content)}")

    # Подготавливаем значение responsible для БД
    responsible_value = responsible if responsible.strip() else None
    defect_data = {
        "equipment": equipment,
        "description": description,
        "section": section,
        "time_found": now,
        "danger_level": danger_level,
        "responsible": responsible_value,
        "photo_url": photo_url
    }
    defect_id = create_defect(defect_data)
    
    # Отправка уведомлений при создании
    defect_info = {
        "id": defect_id,
        "equipment": equipment,
        "section": section,
        "description": description,
        "danger_level": danger_level,
        "responsible": responsible_value,
        "photo_url": photo_url
    }
    # Отправляем уведомление ответственному
    if responsible_value:
        send_telegram_notification_async(defect_info, responsible_person=responsible_value, executor_person=None)
    
    return {"status": "created", "id": defect_id}

@router.get("/")
def get_defects_endpoint(
    section: Optional[str] = None,
    status: Optional[str] = None,
    danger_level: Optional[str] = None,
    assigned_to: Optional[str] = None
):
    """Получение списка дефектов с фильтрацией."""
    return get_all_defects(section, status, danger_level, assigned_to)

@router.put("/{defect_id}")
def update_defect_endpoint(defect_id: int, update_data: dict):
    """Обновление дефекта."""
    # Получаем текущие данные дефекта до обновления
    defect_row = get_defect_by_id(defect_id)
    if not defect_row:
        raise HTTPException(status_code=404, detail="Дефект не найден")
        
    current_responsible = defect_row.get('responsible')
    current_assigned_to = defect_row.get('assigned_to')
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Обновляем временные метки в зависимости от статуса
    if update_data.get('status') == "в работе":
        update_data['time_started'] = now
    elif update_data.get('status') == "завершён":
        update_data['time_completed'] = now

    # Выполняем обновление в базе данных
    success = update_defect(defect_id, update_data)
    if not success:
        raise HTTPException(status_code=404, detail="Дефект не найден или не обновлён")

    # Отправка уведомлений после успешного обновления
    updated_defect_row = get_defect_by_id(defect_id)
    if updated_defect_row:
        # Подготавливаем данные для уведомления
        defect_info_after_update = {
            "id": updated_defect_row['id'],
            "equipment": updated_defect_row['equipment'],
            "section": updated_defect_row['section'],
            "description": updated_defect_row['description'],
            "danger_level": updated_defect_row['danger_level'],
            "responsible": updated_defect_row.get('responsible'),
            "assigned_to": updated_defect_row.get('assigned_to'),
            "photo_url": updated_defect_row.get('photo_url')
        }

        # Определяем, какие поля изменились
        new_assigned_to = updated_defect_row.get('assigned_to')
        new_responsible = updated_defect_row.get('responsible')

        # Отправляем уведомление новому исполнителю, если он изменился
        if new_assigned_to and new_assigned_to != current_assigned_to:
            send_telegram_notification_async(
                defect_info_after_update, 
                responsible_person=None, 
                executor_person=new_assigned_to
            )

        # Отправляем уведомление новому ответственному, если он изменился
        # и если это не тот же человек, что и новый исполнитель
        if new_responsible and new_responsible != current_responsible and new_responsible != new_assigned_to:
            send_telegram_notification_async(
                defect_info_after_update, 
                responsible_person=new_responsible, 
                executor_person=None
            )
        
    return {"status": "updated"}