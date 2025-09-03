# app/database.py
import sqlite3
from typing import List, Dict, Any, Optional
from .core.config import DATABASE_PATH

def get_db_connection():
    """Создание соединения с базой данных."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # Позволяет обращаться к столбцам по имени
    return conn

def get_all_defects(
    section: Optional[str] = None,
    status: Optional[str] = None,
    danger_level: Optional[str] = None,
    assigned_to: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Получение списка всех дефектов с фильтрацией."""
    conn = get_db_connection()
    c = conn.cursor()
    
    query = "SELECT * FROM defects WHERE 1=1"
    params: List[str] = []
    
    if section:
        query += " AND section = ?"
        params.append(section)
    if status:
        query += " AND status = ?"
        params.append(status)
    if danger_level:
        query += " AND danger_level = ?"
        params.append(danger_level)
    if assigned_to:
        query += " AND assigned_to = ?"
        params.append(assigned_to)
    
    c.execute(query, params)
    rows = c.fetchall()
    conn.close()
    
    defects = []
    for row in rows:
        resolution_time = ""
        if row['time_started'] and row['time_completed']:
            try:
                from datetime import datetime
                start_time = datetime.strptime(row['time_started'], "%Y-%m-%d %H:%M:%S")
                end_time = datetime.strptime(row['time_completed'], "%Y-%m-%d %H:%M:%S")
                diff = end_time - start_time
                hours = diff.total_seconds() / 3600
                resolution_time = f"{hours:.1f} ч"
            except Exception as e:
                print(f"Ошибка вычисления времени: {e}")
                resolution_time = "Ошибка"
        elif row['time_started']:
            try:
                from datetime import datetime
                start_time = datetime.strptime(row['time_started'], "%Y-%m-%d %H:%M:%S")
                now = datetime.now()
                diff = now - start_time
                hours = diff.total_seconds() / 3600
                resolution_time = f"{hours:.1f} ч (в работе)"
            except Exception as e:
                print(f"Ошибка вычисления времени: {e}")
                resolution_time = "Ошибка"
        
        defects.append({
            "id": row['id'],
            "equipment": row['equipment'],
            "description": row['description'],
            "section": row['section'],
            "time_found": row['time_found'],
            "danger_level": row['danger_level'],
            "status": row['status'],
            "assigned_to": row['assigned_to'],
            "responsible": row['responsible'],
            "time_started": row['time_started'],
            "time_completed": row['time_completed'],
            "resolution_time": resolution_time,
            "photo_url": row['photo_url'] if 'photo_url' in row.keys() else None
        })
    
    return defects

def create_defect(defect_data: Dict[str, Any]) -> int:
    """Создание нового дефекта."""
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute('''
        INSERT INTO defects (equipment, description, section, time_found, danger_level, responsible, photo_url)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        defect_data['equipment'],
        defect_data['description'],
        defect_data['section'],
        defect_data['time_found'],
        defect_data['danger_level'],
        defect_data['responsible'],
        defect_data['photo_url']
    ))
    
    defect_id = c.lastrowid
    conn.commit()
    conn.close()
    
    # Явная проверка и приведение типа для удовлетворения Pyright
    if defect_id is None:
        raise RuntimeError("Failed to get the ID of the newly created defect.")
    return int(defect_id)

def update_defect(defect_id: int, update_data: Dict[str, Any]) -> bool:
    """Обновление дефекта."""
    conn = get_db_connection()
    c = conn.cursor()
    
    # Формируем запрос на обновление
    query_parts = []
    params = []
    
    for key, value in update_data.items():
        if key in ['status', 'assigned_to', 'responsible', 'time_started', 'time_completed']:
            query_parts.append(f"{key} = ?")
            params.append(value)
    
    if query_parts:
        query = f"UPDATE defects SET {', '.join(query_parts)} WHERE id = ?"
        params.append(defect_id)
        c.execute(query, params)
        conn.commit()
        updated_rows = c.rowcount
        conn.close()
        return updated_rows > 0
    
    conn.close()
    return False

def get_dropdown_lists() -> Dict[str, List[str]]:
    """Получение всех списков выбора."""
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute("SELECT list_name, items FROM dropdown_lists")
    rows = c.fetchall()
    conn.close()
    
    result = {}
    for row in rows:
        items = []
        if row['items']:
            items_list = [item.strip() for item in row['items'].split('\n') if item.strip()]
            items = items_list
        result[row['list_name']] = items
    
    return result

def update_dropdown_lists(lists: Dict[str, str]) -> None:
    """Обновление списков выбора."""
    conn = get_db_connection()
    c = conn.cursor()
    
    for list_name, items in lists.items():
        c.execute('''
            INSERT OR REPLACE INTO dropdown_lists (list_name, items)
            VALUES (?, ?)
        ''', (list_name, items))
    
    conn.commit()
    conn.close()

def subscribe_user(name: str, telegram_id: str) -> bool:
    """Подписка пользователя на уведомления."""
    conn = get_db_connection()
    c = conn.cursor()
    
    try:
        c.execute('''
            INSERT INTO users (name, telegram_id)
            VALUES (?, ?)
        ''', (name, telegram_id))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.rollback()
        conn.close()
        return False
    except Exception as e:
        conn.rollback()
        conn.close()
        raise e

def get_user_by_name(name: str) -> Optional[Dict[str, str]]:
    """Получение пользователя по имени."""
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute("SELECT * FROM users WHERE name = ?", (name,))
    row = c.fetchone()
    conn.close()
    
    if row:
        return {
            "id": row['id'],
            "name": row['name'],
            "telegram_id": row['telegram_id']
        }
    
    return None

def get_defect_by_id(defect_id: int) -> Optional[Dict[str, Any]]:
    """Получение дефекта по ID."""
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute("SELECT * FROM defects WHERE id = ?", (defect_id,))
    row = c.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    
    return None