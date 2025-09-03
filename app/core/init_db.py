# app/core/init_db.py
import sqlite3
import os
from .config import DATABASE_PATH

def init_db():
    """Инициализация базы данных."""
    # Создаем папку для загрузок если её нет
    os.makedirs("uploads", exist_ok=True)
    
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    
    # Проверим, существует ли таблица defects
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='defects'")
    table_exists = c.fetchone()
    if not table_exists:
        # Если таблицы нет, создаем её с актуальной структурой
        print("Создание новой таблицы defects...")
        c.execute('''
            CREATE TABLE defects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                equipment TEXT,
                description TEXT,
                section TEXT,
                time_found TEXT,
                danger_level TEXT,
                status TEXT DEFAULT 'новый',
                assigned_to TEXT,
                responsible TEXT,
                time_started TEXT,
                time_completed TEXT,
                photo_url TEXT
            )
        ''')
        print("Таблица defects создана.")
    else:
        # Если таблица есть, проверим наличие столбцов
        c.execute("PRAGMA table_info(defects)")
        columns = [info[1] for info in c.fetchall()]
        if 'equipment' not in columns:
            print("Добавление столбца equipment в таблицу defects...")
            if 'location' in columns:
                c.execute('''
                    CREATE TABLE defects_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        equipment TEXT,
                        description TEXT,
                        section TEXT,
                        time_found TEXT,
                        danger_level TEXT,
                        status TEXT DEFAULT 'новый',
                        assigned_to TEXT,
                        responsible TEXT,
                        time_started TEXT,
                        time_completed TEXT,
                        photo_url TEXT
                    )
                ''')
                c.execute('''
                    INSERT INTO defects_new (id, equipment, description, section, time_found, danger_level, status, assigned_to, responsible, time_started, time_completed, photo_url)
                    SELECT id, location, description, section, time_found, danger_level, status, assigned_to, responsible, time_started, time_completed, NULL
                    FROM defects
                ''')
                c.execute("DROP TABLE defects")
                c.execute("ALTER TABLE defects_new RENAME TO defects")
                print("Столбец equipment добавлен, location удален.")
            else:
                c.execute("ALTER TABLE defects ADD COLUMN equipment TEXT")
                print("Столбец equipment добавлен.")
        else:
            print("Таблица defects уже имеет столбец equipment.")
        if 'photo_url' not in columns:
            print("Добавление столбца photo_url в таблицу defects...")
            c.execute("ALTER TABLE defects ADD COLUMN photo_url TEXT")
            print("Столбец photo_url добавлен.")
    
    # Таблица для списков выбора
    c.execute('''
        CREATE TABLE IF NOT EXISTS dropdown_lists (
            id INTEGER PRIMARY KEY,
            list_name TEXT UNIQUE,
            items TEXT
        )
    ''')
    
    # Добавляем стандартные списки, если их нет
    default_lists = {
        'executors': 'Шуев\nМалоев\nКозырев\nОвчинников',
        'responsibles': 'Овчинников\nСулейманов',
        'sections': 'Фасовка\nКомпозиция\nБашня\nСульфирование\nБаковое хозяйство',
        'equipment': 'Линия 1\nЛиния 2\nАвтоклав ГВ-3,2\nНасос ц/б АХ100-65-31Б'
    }
    for list_name, items in default_lists.items():
        c.execute('''
            INSERT OR IGNORE INTO dropdown_lists (list_name, items)
            VALUES (?, ?)
        ''', (list_name, items))
    
    # Таблица для пользователей
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            telegram_id TEXT NOT NULL UNIQUE
        )
    ''')
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("База данных готова.")