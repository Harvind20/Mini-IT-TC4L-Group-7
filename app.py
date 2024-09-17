from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
import sqlite3
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use the non-GUI backend
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import os

app = Flask(__name__)
app.secret_key = 'Amongus'

def get_db_connection():
    conn = sqlite3.connect('budgetbadger.db', timeout=10)
    conn.row_factory = sqlite3.Row
    return conn

def fetch_incomes_from_db(username):
    conn = get_db_connection()
    incomes = conn.execute('SELECT * FROM income WHERE user_username = ?', (username,)).fetchall()
    conn.close()
    return incomes

def fetch_expenses_from_db(username):
    conn = get_db_connection()
    expenses = conn.execute('SELECT * FROM expenses WHERE user_username = ?', (username,)).fetchall()
    conn.close()
    return expenses

def fetch_entries(username):
    conn = get_db_connection()
    query = '''
        SELECT date FROM income WHERE user_username = ?
        UNION ALL
        SELECT date FROM expenses WHERE user_username = ?
    '''
    entries = conn.execute(query, (username, username)).fetchall()
    conn.close()
    return [entry['date'] for entry in entries]

def calculate_income_points(username):
    incomes = fetch_incomes_from_db(username)
    income_points = 0
    for income in incomes:
        amount = income['amount']
        category = income['category']

        if category == 'Salary':
            income_points += (amount // 100) * 10
        elif category == 'Business':
            income_points += (amount // 100) * 15
        elif category == 'Gifts':
            income_points += (amount // 100) * 5
        elif category == 'Extra Income':
            income_points += (amount // 100) * 7
        elif category == 'Loan':
            income_points += (amount // 100) * 3
        elif category == 'Insurance Payout':
            income_points += (amount // 100) * 8
        elif category == 'Other Incomes':
            income_points += (amount // 100) * 6

    return income_points

def calculate_expense_points(username):
    expenses = fetch_expenses_from_db(username)
    essential_expenses_categories = {'Groceries', 'Healthcare', 'Education', 'Food & Drinks', 'Transport'}
    expense_points = 0
    non_essential_points = 0
    total_non_essential_spending = 0

    for expense in expenses:
        amount = expense['amount']
        category = expense['category']

        if category in essential_expenses_categories:
            expense_points += (amount // 100) * 5
        else:
            non_essential_points += (amount // 100) * 2
            total_non_essential_spending += amount

    if total_non_essential_spending > 1000:
        excess_amount = total_non_essential_spending - 1000
        penalty_points = (excess_amount // 100) * 5
        non_essential_points -= penalty_points

    return expense_points + non_essential_points

def calculate_balanced_activity_bonus(username):
    incomes = fetch_incomes_from_db(username)
    expenses = fetch_expenses_from_db(username)

    total_income = sum(income['amount'] for income in incomes)
    total_expense = sum(expense['amount'] for expense in expenses)

    balance_bonus = 0
    if total_income > 0:
        income_expense_ratio = total_income / total_expense
        if income_expense_ratio > 1:
            percentage_extra_income = (total_income / total_expense - 1) * 100
            balance_bonus = (percentage_extra_income // 10) * 50

    monthly_entries = fetch_monthly_entries(username)
    income_entries = monthly_entries['income']
    expense_entries = monthly_entries['expense']

    consistency_bonus = 30 if income_entries >= 5 and expense_entries >= 5 else 0

    return balance_bonus + consistency_bonus

def has_seven_day_streak(dates):
    date_format = "%Y-%m-%d"
    dates = [datetime.strptime(date, date_format) for date in dates]
    dates = sorted(set(dates))
    
    if len(dates) < 7:
        return False

    for i in range(len(dates) - 6):
        streak_dates = dates[i:i+7]
        if streak_dates[-1] - streak_dates[0] == timedelta(days=6):
            return True
    
    return False

def calculate_daily_streak(username):
    entries = fetch_entries(username)
    daily_streak_points = 0

    if has_seven_day_streak(entries):
        daily_streak_points += 10

    return daily_streak_points

def update_user_points(username):
    income_points = calculate_income_points(username)
    expense_points = calculate_expense_points(username)
    balanced_activity_bonus = calculate_balanced_activity_bonus(username)
    daily_streak_points = calculate_daily_streak(username)

    total_points = income_points + expense_points + balanced_activity_bonus + daily_streak_points

    conn = get_db_connection()
    conn.execute('UPDATE users SET total_points = ? WHERE username = ?', (total_points, username))
    conn.commit()
    conn.close()

def update_all_users_points():
    conn = get_db_connection()
    users = conn.execute('SELECT username FROM users').fetchall()
    conn.close()
    
    for user in users:
        username = user['username']
        update_user_points(username)

def generate_pie_chart(data, title, labels, filename):
    amounts = [item['amount'] for item in data]
    categories = [item['category'] for item in data]

    plt.figure(figsize=(8, 6))
    label_font = {'fontsize': 20, 'fontfamily': 'serif', 'fontweight': 'bold', 'color': '#c0e2df'}
    autopct_font = {'fontsize': 15, 'fontfamily': 'serif', 'fontweight': 'normal', 'color': '#c0e2df'}
    plt.pie(amounts, labels=categories, autopct=lambda p: f'{p:.1f}%', startangle=140,
            textprops=label_font)
    plt.title(title, fontsize=25, fontfamily='serif', fontweight='bold', color='#c0e2df')

    file_path = f'static/images/{filename}.png'
    
    plt.savefig(file_path, dpi=300, transparent=True)
    plt.close()

    return file_path

def generate_frequency_polygon(data, title, filename):
    df = pd.DataFrame(data, columns=['date', 'amount'])
    
    if 'date' not in df.columns or 'amount' not in df.columns:
        raise ValueError("Data must contain 'date' and 'amount' columns")

    df['date'] = pd.to_datetime(df['date'])
    
    df.set_index('date', inplace=True)
    monthly_totals = df.resample('M').sum().reset_index()

    all_months = pd.date_range(start='2024-01-01', end='2024-12-31', freq='M')
    all_months_df = pd.DataFrame({'date': all_months})
    all_months_df['month'] = all_months_df['date'].dt.strftime('%b')
    all_months_df['amount'] = 0

    monthly_totals['month'] = monthly_totals['date'].dt.strftime('%b')
    merged_df = pd.merge(all_months_df, monthly_totals, on='month', suffixes=('_all', '_actual'), how='left')
    merged_df['amount'] = merged_df['amount_actual'].fillna(0)

    plt.figure(figsize=(21, 14))
    plt.plot(merged_df['month'], merged_df['amount'], marker='o', linestyle='-', color='b')
    plt.title(title, fontsize=50, fontfamily='serif', fontweight='bold', color='#c0e2df')
    plt.xlabel('Month', fontsize=40, fontfamily='serif', fontweight='bold', color='#c0e2df') 
    plt.ylabel('Amount', fontsize=40, fontfamily='serif', fontweight='bold', color='#c0e2df')
    
    plt.xticks(ticks=range(12), labels=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'], rotation=45)

    plt.tick_params(axis='x', labelsize=30, colors='#c0e2df')
    plt.tick_params(axis='y', labelsize=30, colors='#c0e2df')

    ax = plt.gca()
    ax.spines['bottom'].set_color('#c0e2df')
    ax.spines['top'].set_color('#c0e2df')
    ax.spines['right'].set_color('#c0e2df')
    ax.spines['left'].set_color('#c0e2df')

    file_path = f'static/images/{filename}.png'
    
    plt.savefig(file_path, dpi=300, transparent=True)
    plt.close()
    
    return file_path

@app.route('/summary')
def summary():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    
    expenses = fetch_expenses_from_db(username)
    incomes = fetch_incomes_from_db(username)

    formatted_expenses = [{'date': exp['date'], 'amount': exp['amount']} for exp in expenses]
    formatted_incomes = [{'date': inc['date'], 'amount': inc['amount']} for inc in incomes]

    expense_pie_chart = generate_pie_chart(expenses, 'Monthly Expenses by Category', [exp['category'] for exp in expenses], 'expense_pie_chart')
    expense_frequency_polygon = generate_frequency_polygon(formatted_expenses, 'Yearly Expense Frequency', 'expense_frequency_polygon')
    
    income_pie_chart = generate_pie_chart(incomes, 'Monthly Incomes by Category', [inc['category'] for inc in incomes], 'income_pie_chart')
    income_frequency_polygon = generate_frequency_polygon(formatted_incomes, 'Yearly Income Frequency', 'income_frequency_polygon')

    return render_template('summary.html', 
                           expense_pie_chart=expense_pie_chart,
                           expense_frequency_polygon=expense_frequency_polygon,
                           income_pie_chart=income_pie_chart,
                           income_frequency_polygon=income_frequency_polygon)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        conn.execute('''
            INSERT INTO users (username, email, password)
            VALUES (?, ?, ?)
        ''', (username, email, password))
        conn.commit()
        conn.close()

        return redirect(url_for('login'))

    return render_template('SignUp.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password)).fetchone()
        conn.close()

        if user:
            session['username'] = user['username']
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password. Please try again.')
            return redirect(url_for('login'))

    return render_template('Login.html')

@app.route('/home')
def home():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('Home.html')

# Global Leaderboard page route
@app.route('/global_leaderboard')
def global_leaderboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('GlobalLeaderboard.html')

# Followed Leaderboard page route
@app.route('/followed_leaderboard')
def followed_leaderboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('FollowedLeaderboard.html')
  
@app.route('/expense_form', methods=['GET', 'POST'])
def expense_form():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        user_username = session['username']
        date = request.form['date']
        amount = request.form['amount']
        category = request.form['category']
        description = request.form['description']

        conn = get_db_connection()
        conn.execute('''
            INSERT INTO expenses (user_username, date, amount, category, description)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_username, date, amount, category, description))
        conn.commit()
        conn.close()

        return redirect(url_for('transaction'))

    return render_template('expenseform.html')

@app.route('/income_form', methods=['GET', 'POST'])
def income_form():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        user_username = session['username']
        date = request.form['date']
        amount = request.form['amount']
        category = request.form['category']
        description = request.form['description']

        conn = get_db_connection()
        conn.execute('''
            INSERT INTO income (user_username, date, amount, category, description)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_username, date, amount, category, description))
        conn.commit()
        conn.close()

        return redirect(url_for('transaction'))

    return render_template('incomeform.html')

@app.route('/transaction', methods=['GET'])
def transaction():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    filter_option = request.args.get('filter', 'all')
    username = session['username']

    incomes = fetch_incomes_from_db(username)
    expenses = fetch_expenses_from_db(username)

    if filter_option == 'incomes':
        expenses = []
    elif filter_option == 'expenses':
        incomes = []

    return render_template('transaction.html', incomes=incomes, expenses=expenses, filter=filter_option)

@app.route('/userprofile')
def user_profile():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']

    conn = get_db_connection()
    
    follower_count = conn.execute('SELECT COUNT(*) FROM followers WHERE following = ?', (username,)).fetchone()[0]
    following_count = conn.execute('SELECT COUNT(*) FROM followers WHERE follower = ?', (username,)).fetchone()[0]
    badges = conn.execute('SELECT badge_name FROM user_badges WHERE user_username = ?', (username,)).fetchall()
    
    conn.close()

    return render_template('userprofilee.html', username=username, follower_count=follower_count, 
                           following_count=following_count, badges=badges)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/follow', methods=['POST'])
def follow():
    if 'username' not in session:
        return redirect(url_for('login'))

    follower = session['username']
    following = request.form['following']

    conn = get_db_connection()
    try:
        conn.execute('''
            INSERT INTO follow_relationships (follower, following)
            VALUES (?, ?)
        ''', (follower, following))
        conn.commit()
    except sqlite3.IntegrityError:
        flash('You are already following this user.')
    finally:
        conn.close()

    return redirect(url_for('profile', username=following))

def count_followers(username):
    conn = get_db_connection()
    followers_count = conn.execute('''
        SELECT COUNT(*) FROM follow_relationships WHERE following = ?
    ''', (username,)).fetchone()[0]
    conn.close()
    return followers_count

def count_following(username):
    conn = get_db_connection()
    following_count = conn.execute('''
        SELECT COUNT(*) FROM follow_relationships WHERE follower = ?
    ''', (username,)).fetchone()[0]
    conn.close()
    return following_count

def get_user_badges(username):
    conn = get_db_connection()
    badges = conn.execute('''
        SELECT badge_type, badge_level, image_filename 
        FROM user_badges 
        WHERE user_username = ?
    ''', (username,)).fetchall()
    conn.close()
    return badges

@app.route('/profile/<username>')
def profile(username):
    # Check if the user is logged in
    if 'username' not in session:
        return redirect(url_for('login'))

    # Get the follower and following counts
    followers_count = count_followers(username)
    following_count = count_following(username)

    # Get the user's badges
    badges = get_user_badges(username)

    # Render the profile page with the username, follower/following counts, and badges
    return render_template('userprofilee.html', username=username, 
                           followers_count=followers_count, following_count=following_count, badges=badges)

if __name__ == '__main__':
    app.run(debug=True)
