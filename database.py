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
    category TEXT CHECK(category IN (
        'Food & Drinks', 'Shopping', 'Transport', 'Home', 
        'Bills & Fees', 'Entertainment', 'Car', 'Travel', 
        'Family & Personal', 'Healthcare', 'Education', 
        'Groceries', 'Gifts', 'Sports & Hobbies', 'Beauty', 
        'Work', 'Other Expenses'
    )) NOT NULL,
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
    category TEXT CHECK(category IN (
        'Salary', 'Business', 'Gifts', 'Extra Income', 
        'Loan', 'Insurance Payout', 'Other Incomes'
    )) NOT NULL,
    description TEXT,
    FOREIGN KEY (user_username) REFERENCES users(username)
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS follow_relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    follower TEXT NOT NULL,
    following TEXT NOT NULL,
    FOREIGN KEY (follower) REFERENCES users(username),
    FOREIGN KEY (following) REFERENCES users(username),
    UNIQUE(follower, following)
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
