import sqlite3

def init_db():
    conn = sqlite3.connect('budgetbadger.db')
    cursor = conn.cursor()

# Create the 'users' table if it doesn't exist already.
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

# Create the 'expenses' table if it doesn't exist already.
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
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
        FOREIGN KEY (username) REFERENCES users(username)
    )
    ''')

# Create the 'income' table if it doesn't exist already.
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS income (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        date TEXT NOT NULL,
        amount REAL CHECK(amount >= 0.01) NOT NULL,
        category TEXT CHECK(category IN (
            'Salary', 'Business', 'Gifts', 'Extra Income', 
            'Loan', 'Investments', 'Insurance Payout', 'Other Incomes'
        )) NOT NULL,
        description TEXT,
        FOREIGN KEY (username) REFERENCES users(username)
    )
    ''')

# Create the 'follow_relationships' table to manage user followings.
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

# Create the 'user_badges' table to store badges associated with each user.
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_badges (
        username TEXT PRIMARY KEY,
        apbadgeid INTEGER DEFAULT 1,
        incomebadgeid INTEGER DEFAULT 1,
        expensebadgeid INTEGER DEFAULT 1,
        FOREIGN KEY (username) REFERENCES users(username)
    )
    ''')

# Create leaderboard table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS leaderboard (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        achievement_points INTEGER NOT NULL,
        total_income REAL DEFAULT 0,
        total_expense REAL DEFAULT 0,
        FOREIGN KEY (username) REFERENCES users(username),
        UNIQUE(username)
    )
    ''')

    conn.commit()
    conn.close()
