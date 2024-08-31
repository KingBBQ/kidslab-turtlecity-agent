import sqlite3
import os
from datetime import datetime, timedelta

# Ensure the db directory exists
os.makedirs('db', exist_ok=True)

DATABASE_FILE = 'db/players.db'

def initialize_database():
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS players (
            username TEXT PRIMARY KEY,
            last_login TEXT,
            last_logout TEXT,
            total_time INTEGER DEFAULT 0,
            login_count INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

def update_last_login(username):
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    last_login = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('''
        INSERT INTO players (username, last_login, login_count)
        VALUES (?, ?, 1)
        ON CONFLICT(username) DO UPDATE SET 
            last_login=excluded.last_login,
            login_count=login_count + 1
    ''', (username, last_login))
    conn.commit()
    conn.close()

def update_last_logout(username):
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    last_logout = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('''
        UPDATE players
        SET last_logout = ?
        WHERE username = ?
    ''', (last_logout, username))
    conn.commit()
    conn.close()

def update_total_time(username):
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT last_login, last_logout, total_time FROM players WHERE username = ?
    ''', (username,))
    row = cursor.fetchone()
    if row and row[0] and row[1]:
        last_login = datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S')
        last_logout = datetime.strptime(row[1], '%Y-%m-%d %H:%M:%S')
        session_time = int((last_logout - last_login).total_seconds() / 60)
        total_time = row[2] + session_time
        cursor.execute('''
            UPDATE players
            SET total_time = ?
            WHERE username = ?
        ''', (total_time, username))
    conn.commit()
    conn.close()

def get_recent_players(days=180):
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('''
        SELECT username, last_login, login_count, total_time
        FROM players
        WHERE last_login >= ?
        ORDER BY total_time DESC
    ''', (cutoff_date,))
    players = cursor.fetchall()
    conn.close()
    return players