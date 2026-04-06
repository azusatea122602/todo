import sqlite3
import datetime
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "todo.db")

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    # 建立清單表 (List)
    c.execute('''
        CREATE TABLE IF NOT EXISTS lists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            is_smart BOOLEAN DEFAULT 0,
            created_at TEXT NOT NULL
        )
    ''')
    
    # 建立任務表 (Task)
    c.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            list_id INTEGER,
            title TEXT NOT NULL,
            is_completed BOOLEAN DEFAULT 0,
            is_important BOOLEAN DEFAULT 0,
            due_date TEXT,
            reminder_time TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (list_id) REFERENCES lists(id) ON DELETE CASCADE
        )
    ''')
    
    # 建立子任務/步驟表 (Subtask)
    c.execute('''
        CREATE TABLE IF NOT EXISTS subtasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER,
            title TEXT NOT NULL,
            is_completed BOOLEAN DEFAULT 0,
            created_at TEXT NOT NULL,
            FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
        )
    ''')
    
    # 預設加入智慧清單 (如果尚未建立)
    c.execute("SELECT COUNT(*) FROM lists WHERE is_smart = 1")
    count = c.fetchone()[0]
    if count == 0:
        now = datetime.datetime.now().isoformat()
        c.execute("INSERT INTO lists (name, is_smart, created_at) VALUES (?, ?, ?)", ("Tasks", 1, now))
    
    conn.commit()
    conn.close()

# ---- Lists CRUD ----
def get_all_lists():
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM lists ORDER BY id")
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def add_list(name):
    conn = get_connection()
    c = conn.cursor()
    now = datetime.datetime.now().isoformat()
    c.execute("INSERT INTO lists (name, is_smart, created_at) VALUES (?, ?, ?)", (name, 0, now))
    conn.commit()
    conn.close()

def delete_list(list_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM lists WHERE id = ? AND is_smart = 0", (list_id,))
    conn.commit()
    conn.close()

# ---- Tasks CRUD ----
def get_tasks_by_list(list_id):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM tasks WHERE list_id = ? ORDER BY is_completed, created_at DESC", (list_id,))
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_important_tasks():
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM tasks WHERE is_important = 1 ORDER BY is_completed, created_at DESC")
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def add_task(list_id, title):
    conn = get_connection()
    c = conn.cursor()
    now = datetime.datetime.now().isoformat()
    c.execute("INSERT INTO tasks (list_id, title, created_at) VALUES (?, ?, ?)", (list_id, title, now))
    conn.commit()
    conn.close()

def update_task_status(task_id, is_completed):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE tasks SET is_completed = ? WHERE id = ?", (is_completed, task_id))
    conn.commit()
    conn.close()

def update_task_importance(task_id, is_important):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE tasks SET is_important = ? WHERE id = ?", (is_important, task_id))
    conn.commit()
    conn.close()

def update_task_details(task_id, due_date, reminder_time):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE tasks SET due_date = ?, reminder_time = ? WHERE id = ?", (due_date, reminder_time, task_id))
    conn.commit()
    conn.close()
    
def delete_task(task_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()

# ---- Subtasks CRUD ----
def get_subtasks_by_task(task_id):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM subtasks WHERE task_id = ? ORDER BY created_at", (task_id,))
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def add_subtask(task_id, title):
    conn = get_connection()
    c = conn.cursor()
    now = datetime.datetime.now().isoformat()
    c.execute("INSERT INTO subtasks (task_id, title, created_at) VALUES (?, ?, ?)", (task_id, title, now))
    conn.commit()
    conn.close()

def update_subtask_status(subtask_id, is_completed):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE subtasks SET is_completed = ? WHERE id = ?", (is_completed, subtask_id))
    conn.commit()
    conn.close()

def delete_subtask(subtask_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM subtasks WHERE id = ?", (subtask_id,))
    conn.commit()
    conn.close()

# 初始化 SQLite 外鍵支援
def enable_foreign_keys():
    conn = get_connection()
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.close()

init_db()
enable_foreign_keys()
