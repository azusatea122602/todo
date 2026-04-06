import sqlite3
import datetime
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "todo.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db():
    conn = get_connection()
    c = conn.cursor()

    # 建立清單表 (List)
    c.execute('''
        CREATE TABLE IF NOT EXISTS lists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            icon TEXT DEFAULT '📁',
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
            my_day BOOLEAN DEFAULT 0,
            due_date TEXT,
            reminder_time TEXT,
            notes TEXT DEFAULT '',
            created_at TEXT NOT NULL,
            completed_at TEXT,
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

    # --- Schema 遷移：為舊資料表補上新欄位 ---
    existing_cols = [row[1] for row in c.execute("PRAGMA table_info(tasks)").fetchall()]
    migrations = {
        "my_day": "ALTER TABLE tasks ADD COLUMN my_day BOOLEAN DEFAULT 0",
        "notes": "ALTER TABLE tasks ADD COLUMN notes TEXT DEFAULT ''",
        "completed_at": "ALTER TABLE tasks ADD COLUMN completed_at TEXT",
    }
    for col, sql in migrations.items():
        if col not in existing_cols:
            c.execute(sql)

    existing_list_cols = [row[1] for row in c.execute("PRAGMA table_info(lists)").fetchall()]
    if "icon" not in existing_list_cols:
        c.execute("ALTER TABLE lists ADD COLUMN icon TEXT DEFAULT '📁'")

    # 預設加入智慧清單 (如果尚未建立)
    c.execute("SELECT COUNT(*) FROM lists WHERE is_smart = 1")
    count = c.fetchone()[0]
    if count == 0:
        now = datetime.datetime.now().isoformat()
        c.execute(
            "INSERT INTO lists (name, icon, is_smart, created_at) VALUES (?, ?, ?, ?)",
            ("Tasks", "🏠", 1, now),
        )

    conn.commit()
    conn.close()


# ===================== Lists CRUD =====================

def get_all_lists():
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM lists ORDER BY is_smart DESC, id").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_list(name, icon="📁"):
    conn = get_connection()
    now = datetime.datetime.now().isoformat()
    conn.execute(
        "INSERT INTO lists (name, icon, is_smart, created_at) VALUES (?, ?, 0, ?)",
        (name, icon, now),
    )
    conn.commit()
    conn.close()


def rename_list(list_id, new_name):
    conn = get_connection()
    conn.execute("UPDATE lists SET name = ? WHERE id = ?", (new_name, list_id))
    conn.commit()
    conn.close()


def delete_list(list_id):
    conn = get_connection()
    # 先刪除清單內所有任務的子任務
    conn.execute(
        "DELETE FROM subtasks WHERE task_id IN (SELECT id FROM tasks WHERE list_id = ?)",
        (list_id,),
    )
    # 再刪除清單內所有任務
    conn.execute("DELETE FROM tasks WHERE list_id = ?", (list_id,))
    # 最後刪除清單本身
    conn.execute("DELETE FROM lists WHERE id = ? AND is_smart = 0", (list_id,))
    conn.commit()
    conn.close()


# ===================== Tasks CRUD =====================

def _task_rows(conn, sql, params=()):
    conn.row_factory = sqlite3.Row
    rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def get_tasks_by_list(list_id):
    conn = get_connection()
    result = _task_rows(
        conn,
        "SELECT * FROM tasks WHERE list_id = ? ORDER BY is_completed, created_at DESC",
        (list_id,),
    )
    conn.close()
    return result


def get_important_tasks():
    conn = get_connection()
    result = _task_rows(
        conn,
        "SELECT * FROM tasks WHERE is_important = 1 ORDER BY is_completed, created_at DESC",
    )
    conn.close()
    return result


def get_my_day_tasks():
    today = datetime.date.today().isoformat()
    conn = get_connection()
    result = _task_rows(
        conn,
        "SELECT * FROM tasks WHERE my_day = 1 OR due_date = ? ORDER BY is_completed, created_at DESC",
        (today,),
    )
    conn.close()
    return result


def get_today_due_tasks():
    today = datetime.date.today().isoformat()
    conn = get_connection()
    result = _task_rows(
        conn,
        "SELECT * FROM tasks WHERE due_date = ? ORDER BY is_completed, created_at DESC",
        (today,),
    )
    conn.close()
    return result


def get_all_tasks():
    conn = get_connection()
    result = _task_rows(
        conn,
        "SELECT * FROM tasks ORDER BY is_completed, created_at DESC",
    )
    conn.close()
    return result


def search_tasks(keyword):
    conn = get_connection()
    result = _task_rows(
        conn,
        "SELECT * FROM tasks WHERE title LIKE ? OR notes LIKE ? ORDER BY is_completed, created_at DESC",
        (f"%{keyword}%", f"%{keyword}%"),
    )
    conn.close()
    return result


def add_task(list_id, title, due_date=None):
    conn = get_connection()
    now = datetime.datetime.now().isoformat()
    cur = conn.execute(
        "INSERT INTO tasks (list_id, title, due_date, created_at) VALUES (?, ?, ?, ?)",
        (list_id, title, due_date, now),
    )
    new_id = cur.lastrowid
    conn.commit()
    conn.close()
    return new_id


def update_task_status(task_id, is_completed):
    conn = get_connection()
    completed_at = datetime.datetime.now().isoformat() if is_completed else None
    conn.execute(
        "UPDATE tasks SET is_completed = ?, completed_at = ? WHERE id = ?",
        (is_completed, completed_at, task_id),
    )
    conn.commit()
    conn.close()


def update_task_importance(task_id, is_important):
    conn = get_connection()
    conn.execute("UPDATE tasks SET is_important = ? WHERE id = ?", (is_important, task_id))
    conn.commit()
    conn.close()


def update_task_my_day(task_id, my_day):
    conn = get_connection()
    conn.execute("UPDATE tasks SET my_day = ? WHERE id = ?", (my_day, task_id))
    conn.commit()
    conn.close()


def update_task_due_date(task_id, due_date):
    conn = get_connection()
    conn.execute("UPDATE tasks SET due_date = ? WHERE id = ?", (due_date, task_id))
    conn.commit()
    conn.close()


def update_task_notes(task_id, notes):
    conn = get_connection()
    conn.execute("UPDATE tasks SET notes = ? WHERE id = ?", (notes, task_id))
    conn.commit()
    conn.close()


def update_task_title(task_id, title):
    conn = get_connection()
    conn.execute("UPDATE tasks SET title = ? WHERE id = ?", (title, task_id))
    conn.commit()
    conn.close()


def update_task_list(task_id, new_list_id):
    conn = get_connection()
    conn.execute("UPDATE tasks SET list_id = ? WHERE id = ?", (new_list_id, task_id))
    conn.commit()
    conn.close()


def delete_task(task_id):
    conn = get_connection()
    conn.execute("DELETE FROM subtasks WHERE task_id = ?", (task_id,))
    conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()


# ===================== Subtasks CRUD =====================

def get_subtasks_by_task(task_id):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM subtasks WHERE task_id = ? ORDER BY created_at", (task_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_subtask(task_id, title):
    conn = get_connection()
    now = datetime.datetime.now().isoformat()
    conn.execute(
        "INSERT INTO subtasks (task_id, title, created_at) VALUES (?, ?, ?)",
        (task_id, title, now),
    )
    conn.commit()
    conn.close()


def update_subtask_status(subtask_id, is_completed):
    conn = get_connection()
    conn.execute("UPDATE subtasks SET is_completed = ? WHERE id = ?", (is_completed, subtask_id))
    conn.commit()
    conn.close()


def delete_subtask(subtask_id):
    conn = get_connection()
    conn.execute("DELETE FROM subtasks WHERE id = ?", (subtask_id,))
    conn.commit()
    conn.close()


# ===================== 統計 =====================

def get_task_count_by_list(list_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT COUNT(*) FROM tasks WHERE list_id = ? AND is_completed = 0", (list_id,)
    ).fetchone()
    conn.close()
    return row[0] if row else 0


def get_important_count():
    conn = get_connection()
    row = conn.execute(
        "SELECT COUNT(*) FROM tasks WHERE is_important = 1 AND is_completed = 0"
    ).fetchone()
    conn.close()
    return row[0] if row else 0


def get_my_day_count():
    today = datetime.date.today().isoformat()
    conn = get_connection()
    row = conn.execute(
        "SELECT COUNT(*) FROM tasks WHERE (my_day = 1 OR due_date = ?) AND is_completed = 0",
        (today,),
    ).fetchone()
    conn.close()
    return row[0] if row else 0


def get_today_due_count():
    today = datetime.date.today().isoformat()
    conn = get_connection()
    row = conn.execute(
        "SELECT COUNT(*) FROM tasks WHERE due_date = ? AND is_completed = 0", (today,)
    ).fetchone()
    conn.close()
    return row[0] if row else 0


def get_all_task_count():
    conn = get_connection()
    row = conn.execute(
        "SELECT COUNT(*) FROM tasks WHERE is_completed = 0"
    ).fetchone()
    conn.close()
    return row[0] if row else 0


def get_list_name(list_id):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT name FROM lists WHERE id = ?", (list_id,)).fetchone()
    conn.close()
    return row["name"] if row else "Unknown"


# ===================== 初始化 =====================
init_db()
