
import sqlite3
import hashlib
from typing import Optional, List, Dict, Any

DB_PATH = 'ratings.db'

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL
    );''')
    cur.execute('''
    CREATE TABLE IF NOT EXISTS ratings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        movie_id INTEGER NOT NULL,
        rating REAL NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, movie_id)
    );''')
    conn.commit()
    conn.close()

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def create_user(username: str, password: str) -> Dict[str, Any]:
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', (username, hash_password(password)))
        conn.commit()
        user_id = cur.lastrowid
        return {'id': user_id, 'username': username}
    except sqlite3.IntegrityError:
        return {'error': 'username_taken'}
    finally:
        conn.close()

def authenticate(username: str, password: str) -> Optional[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('SELECT id, username, password_hash FROM users WHERE username = ?', (username,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    if row['password_hash'] == hash_password(password):
        return {'id': row['id'], 'username': row['username']}
    return None

def add_rating(user_id: int, movie_id: int, rating: float) -> None:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('INSERT OR REPLACE INTO ratings (user_id, movie_id, rating) VALUES (?, ?, ?)', (user_id, movie_id, rating))
    conn.commit()
    conn.close()

def get_user_ratings(user_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('SELECT movie_id, rating FROM ratings WHERE user_id = ?', (user_id,))
    rows = cur.fetchall()
    conn.close()
    return {row['movie_id']: row['rating'] for row in rows}

def get_all_ratings():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('SELECT user_id, movie_id, rating FROM ratings')
    rows = cur.fetchall()
    conn.close()
    return [{'user_id': r['user_id'], 'movie_id': r['movie_id'], 'rating': r['rating']} for r in rows]
