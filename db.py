import sqlite3
import os

DB_NAME = os.path.join(os.path.expanduser("~"), "stickers.db")

def init_db():
    conn = sqlite3.connect(DB_NAME, timeout=20)
    c = conn.cursor()
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (name TEXT PRIMARY KEY)''')
    # Needs table
    c.execute('''CREATE TABLE IF NOT EXISTS needs
                 (user_name TEXT, sticker_number INTEGER, 
                 FOREIGN KEY(user_name) REFERENCES users(name),
                 PRIMARY KEY (user_name, sticker_number))''')
    # Duplicates table
    c.execute('''CREATE TABLE IF NOT EXISTS duplicates
                 (user_name TEXT, sticker_number INTEGER, 
                 FOREIGN KEY(user_name) REFERENCES users(name),
                 PRIMARY KEY (user_name, sticker_number))''')
    conn.commit()
    conn.close()

def add_user(name):
    conn = sqlite3.connect(DB_NAME, timeout=20)
    c = conn.cursor()
    try:
        c.execute("INSERT OR IGNORE INTO users (name) VALUES (?)", (name,))
        conn.commit()
    finally:
        conn.close()

def update_collection(user_name, needs_list, duplicates_list):
    conn = sqlite3.connect(DB_NAME, timeout=20)
    c = conn.cursor()
    
    # Ensure user exists
    add_user(user_name)

    # Clear old data for user
    c.execute("DELETE FROM needs WHERE user_name = ?", (user_name,))
    c.execute("DELETE FROM duplicates WHERE user_name = ?", (user_name,))

    # Insert new data
    if needs_list:
        c.executemany("INSERT OR IGNORE INTO needs (user_name, sticker_number) VALUES (?, ?)", 
                      [(user_name, int(n)) for n in needs_list])
    
    if duplicates_list:
        c.executemany("INSERT OR IGNORE INTO duplicates (user_name, sticker_number) VALUES (?, ?)", 
                      [(user_name, int(n)) for n in duplicates_list])
    
    conn.commit()
    conn.close()

def get_user_collection(user_name):
    conn = sqlite3.connect(DB_NAME, timeout=20)
    c = conn.cursor()
    
    c.execute("SELECT sticker_number FROM needs WHERE user_name = ?", (user_name,))
    needs = [row[0] for row in c.fetchall()]
    
    c.execute("SELECT sticker_number FROM duplicates WHERE user_name = ?", (user_name,))
    duplicates = [row[0] for row in c.fetchall()]
    
    conn.close()
    return needs, duplicates

def get_all_data():
    conn = sqlite3.connect(DB_NAME, timeout=20)
    c = conn.cursor()
    
    # Get all users
    c.execute("SELECT name FROM users")
    users = [row[0] for row in c.fetchall()]
    
    all_needs = {}
    all_duplicates = {}
    
    for u in users:
        n, d = get_user_collection(u)
        all_needs[u] = set(n)
        all_duplicates[u] = set(d)
        
    conn.close()
    return all_needs, all_duplicates
