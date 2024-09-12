import sqlite3

conn = sqlite3.connect('budgetbadger.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    reset_token TEXT,
    reset_token_expiry DATETIME
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_username TEXT NOT NULL,
    date TEXT NOT NULL,
    amount REAL CHECK(amount >= 0.01) NOT NULL,
    category TEXT CHECK(category IN ('food', 'transport', 'bills', 'entertainment', 'other expenses')) NOT NULL,
    description TEXT,
    FOREIGN KEY (user_username) REFERENCES users(username)
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_username TEXT NOT NULL,
    date TEXT NOT NULL,
    amount REAL CHECK(amount >= 0.01) NOT NULL,
    category TEXT CHECK(category IN ('food', 'transport', 'bills', 'entertainment', 'other expenses')) NOT NULL,
    description TEXT,
    FOREIGN KEY (user_username) REFERENCES users(username)
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS income (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_username TEXT NOT NULL,
    date TEXT NOT NULL,
    amount REAL CHECK(amount >= 0.01) NOT NULL,
    category TEXT CHECK(category IN ('salary', 'business', 'investments', 'gifts', 'other incomes')) NOT NULL,
    description TEXT,
    FOREIGN KEY (user_username) REFERENCES users(username)
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS user_badges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_username TEXT NOT NULL,
    badge_type TEXT NOT NULL,
    badge_level INTEGER NOT NULL,
    image_filename TEXT NOT NULL,
    FOREIGN KEY (user_username) REFERENCES users(username)
)
''')

conn.commit()
conn.close()
