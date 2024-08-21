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
    user_id INTEGER NOT NULL,
    friend_id INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (friend_id) REFERENCES users(id),
    UNIQUE(user_id, friend_id)
)
''')

# Commit changes and close the connection
conn.commit()
conn.close()
