import sqlite3
import os

DB_PATH = os.environ.get("DATABASE_URL", "sqlite:///data/memory.db").replace("sqlite:///", "")

def get_db():
    # Ensure directory exists
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        topic TEXT NOT NULL,
        variant_id TEXT NOT NULL,
        reward REAL NOT NULL,
        passed BOOLEAN NOT NULL,
        retry_count INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS rejections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id INTEGER REFERENCES runs(id),
        checkpoint TEXT NOT NULL,
        reasoning TEXT NOT NULL,
        suggestion TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()
    conn.close()

def log_run(topic: str, variant_id: str, reward: float, passed: bool, retry_count: int = 0) -> int:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO runs (topic, variant_id, reward, passed, retry_count) VALUES (?, ?, ?, ?, ?)",
        (topic, variant_id, reward, passed, retry_count)
    )
    run_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return run_id

def log_rejection(run_id: int, checkpoint: str, reasoning: str, suggestion: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO rejections (run_id, checkpoint, reasoning, suggestion) VALUES (?, ?, ?, ?)",
        (run_id, checkpoint, reasoning, suggestion)
    )
    conn.commit()
    conn.close()
