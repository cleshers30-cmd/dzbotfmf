"""
Работа с базой данных SQLite для хранения домашних заданий.
"""

import sqlite3
from config import DB_NAME

def init_db():
    """Создаёт таблицу для хранения ДЗ при первом запуске."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS hw (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject INTEGER NOT NULL,
            date TEXT NOT NULL,
            text TEXT NOT NULL,
            file_id TEXT DEFAULT NULL,
            file_type TEXT DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Добавляем колонки file_id и file_type, если таблица уже существует без них
    try:
        c.execute("ALTER TABLE hw ADD COLUMN file_id TEXT DEFAULT NULL")
    except sqlite3.OperationalError:
        pass  # Колонка уже существует
    try:
        c.execute("ALTER TABLE hw ADD COLUMN file_type TEXT DEFAULT NULL")
    except sqlite3.OperationalError:
        pass  # Колонка уже существует

    conn.commit()
    conn.close()

def add_hw_to_db(subject: int, date: str, text: str, file_id: str = None, file_type: str = None):
    """Добавляет запись о ДЗ в базу."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        "INSERT INTO hw (subject, date, text, file_id, file_type) VALUES (?, ?, ?, ?, ?)",
        (subject, date, text, file_id, file_type)
    )
    conn.commit()
    conn.close()

def get_hw_by_subject(subject: int):
    """Возвращает все ДЗ по предмету, отсортированные по убыванию ID (новые сверху)."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        "SELECT id, date, text, file_id, file_type FROM hw WHERE subject = ? ORDER BY id DESC",
        (subject,)
    )
    rows = c.fetchall()
    conn.close()
    return rows

def get_hw_by_id(hw_id: int):
    """Возвращает одно ДЗ по его ID."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        "SELECT id, subject, date, text, file_id, file_type FROM hw WHERE id = ?",
        (hw_id,)
    )
    row = c.fetchone()
    conn.close()
    return row

def delete_hw_from_db(hw_id: int):
    """Удаляет ДЗ по ID."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM hw WHERE id = ?", (hw_id,))
    conn.commit()
    affected = c.rowcount
    conn.close()
    return affected > 0