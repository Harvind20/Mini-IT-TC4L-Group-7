import sqlite3

# Connect to SQLite database (creates the file if it doesn't exist)
conn = sqlite3.connect('budgetbadger.db')

# Create a cursor object to execute SQL commands
cursor = conn.cursor()

# Create the users table
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

# Create the friends table
cursor.execute('''
CREATE TABLE IF NOT EXISTS friends (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_username TEXT NOT NULL,
    friend_username TEXT NOT NULL,
    FOREIGN KEY (user_username) REFERENCES users(username),
    FOREIGN KEY (friend_username) REFERENCES users(username),
    UNIQUE(user_username, friend_username)
)
''')

# Create the expense_income_log table
cursor.execute('''
CREATE TABLE IF NOT EXISTS expense_income_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_username TEXT NOT NULL,
    type TEXT CHECK(type IN ('expense', 'income')) NOT NULL,
    date TEXT NOT NULL,
    amount REAL CHECK(amount >= 0.01) NOT NULL,
    category TEXT CHECK(category IN ('food', 'transport', 'bills', 'entertainment', 'salary', 'business', 'investments', 'gifts', 'other incomes')) NOT NULL,
    description TEXT,
    FOREIGN KEY (user_username) REFERENCES users(username)
)
''')

# Commit changes and close the connection
conn.commit()
conn.close()
