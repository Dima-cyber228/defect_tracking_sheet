# app/models.py
from pydantic import BaseModel
from typing import Optional, List

class DefectCreate(BaseModel):
    equipment: str
    description: str
    section: str
    danger_level: str
    responsible: Optional[str] = None

class DefectUpdate(BaseModel):
    status: str
    assigned_to: Optional[str] = None
    responsible: Optional[str] = None

class DropdownUpdate(BaseModel):
    executors: str
    responsibles: str
    sections: str
    equipment: str

class AdminLogin(BaseModel):
    password: str

class SubscribeRequest(BaseModel):
    name: str
    telegram_id: str