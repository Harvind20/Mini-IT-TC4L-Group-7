from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
import sqlite3
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import os
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'Amongus'

def get_db_connection():
    conn = sqlite3.connect('budgetbadger.db', timeout=30)
    conn.row_factory = sqlite3.Row
    return conn

def fetch_incomes_from_db(username):
    conn = get_db_connection()
    incomes = conn.execute('SELECT * FROM income WHERE username = ?', (username,)).fetchall()
    conn.close()
    return incomes

def fetch_expenses_from_db(username):
    conn = get_db_connection()
    expenses = conn.execute('SELECT * FROM expenses WHERE username = ?', (username,)).fetchall()
    conn.close()
    return expenses

def fetch_entries(username):
    conn = get_db_connection()
    query = '''
        SELECT date FROM income WHERE username = ?
        UNION ALL
        SELECT date FROM expenses WHERE username = ?
    '''
    entries = conn.execute(query, (username, username)).fetchall()
    conn.close()
    return [entry['date'] for entry in entries]

def fetch_monthly_entries(username):
    conn = get_db_connection()
    
    income_entries_query = '''
        SELECT strftime('%Y-%m', date) AS month, COUNT(*) AS count
        FROM income
        WHERE username = ?
        GROUP BY month
    '''
    income_entries = conn.execute(income_entries_query, (username,)).fetchall()
    
    expense_entries_query = '''
        SELECT strftime('%Y-%m', date) AS month, COUNT(*) AS count
        FROM expenses
        WHERE username = ?
        GROUP BY month
    '''
    expense_entries = conn.execute(expense_entries_query, (username,)).fetchall()
    
    conn.close()

    monthly_income_entries = {entry['month']: entry['count'] for entry in income_entries}
    monthly_expense_entries = {entry['month']: entry['count'] for entry in expense_entries}

    return {
        'income': sum(monthly_income_entries.values()),
        'expense': sum(monthly_expense_entries.values())
    }

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
    
    if total_expense == 0:
        return balance_bonus

    income_expense_ratio = total_income / total_expense
    if income_expense_ratio > 1:
        percentage_extra_income = (income_expense_ratio - 1) * 100
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

def update_all_users_points():
    conn = get_db_connection()
    cursor = conn.cursor()
    users = cursor.execute('SELECT username FROM users').fetchall()
    conn.close()
    
    for user in users:
        username = user['username']
        update_totals(username)

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
    plt.plot(merged_df['month'], merged_df['amount'], marker='o', linestyle='-', color='#39FF14')
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

def determine_ap_badge_id(ap):
    if ap is None or ap <= 0: return 1
    if ap >= 20000: return 7
    if ap >= 10000: return 6
    if ap >= 5000: return 5
    if ap >= 2000: return 4
    if ap >= 1000: return 3
    return 2

def determine_income_badge_id(income):
    if income is None or income <= 0: return 1
    if income >= 20000: return 7
    if income >= 10000: return 6
    if income >= 5000: return 5
    if income >= 2000: return 4
    if income >= 1000: return 3
    return 2

def determine_expense_badge_id(expense):
    if expense is None or expense <= 0: return 1
    if expense >= 20000: return 7
    if expense >= 10000: return 6
    if expense >= 5000: return 5
    if expense >= 2000: return 4
    if expense >= 1000: return 3
    return 2

def assign_badges(username):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT achievement_points, total_income, total_expense FROM leaderboard WHERE username = ?', (username,))
    totals = cursor.fetchone()

    if totals is None:
        return

    total_ap, total_income, total_expense = totals

    ap_badge_id = determine_ap_badge_id(total_ap)
    income_badge_id = determine_income_badge_id(total_income)
    expense_badge_id = determine_expense_badge_id(total_expense)

    cursor.execute('''
    INSERT INTO user_badges (username, apbadgeid, incomebadgeid, expensebadgeid) 
    VALUES (?, ?, ?, ?)
    ON CONFLICT(username) 
    DO UPDATE SET 
        apbadgeid = excluded.apbadgeid,
        incomebadgeid = excluded.incomebadgeid,
        expensebadgeid = excluded.expensebadgeid
    ''', (username, ap_badge_id, income_badge_id, expense_badge_id))

    conn.commit()
    conn.close()

def update_follower_following_counts(username):
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('SELECT COUNT(*) FROM follow_relationships WHERE following = ?', (username,))
    follower_count = cur.fetchone()[0]
    cur.execute('UPDATE users SET follower_count = ? WHERE username = ?', (follower_count, username))

    cur.execute('SELECT COUNT(*) FROM follow_relationships WHERE follower = ?', (username,))
    following_count = cur.fetchone()[0]
    cur.execute('UPDATE users SET following_count = ? WHERE username = ?', (following_count, username))

    conn.commit()
    conn.close()

def follow_user(follower, following):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute('INSERT INTO follow_relationships (follower, following) VALUES (?, ?)', (follower, following))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    finally:
        conn.close()

    update_follower_following_counts(follower)
    update_follower_following_counts(following)

def unfollow_user(follower, following):
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('DELETE FROM follow_relationships WHERE follower = ? AND following = ?', (follower, following))
    conn.commit()
    conn.close()

    update_follower_following_counts(follower)
    update_follower_following_counts(following)

def fetch_global_leaderboard():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT username, achievement_points 
        FROM leaderboard 
        ORDER BY achievement_points DESC 
        LIMIT 10
    ''')
    top_users = cursor.fetchall()
    conn.close()
    return top_users


def fetch_followed_leaderboard(current_user):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT l.username, l.achievement_points
        FROM leaderboard l
        JOIN follow_relationships f ON l.username = f.following
        WHERE f.follower = ?
        ORDER BY l.achievement_points DESC
        LIMIT 10
    ''', (current_user,))
    followed_users = cursor.fetchall()
    conn.close()
    return followed_users

def update_leaderboard():
    conn = get_db_connection()
    cursor = conn.cursor()

    users = conn.execute('SELECT username FROM users').fetchall()

    for user in users:
        username = user['username']

        total_ap = calculate_income_points(username) + \
                   calculate_expense_points(username) + \
                   calculate_balanced_activity_bonus(username) + \
                   calculate_daily_streak(username)

        total_income = conn.execute('SELECT SUM(amount) FROM income WHERE username = ?', (username,)).fetchone()[0] or 0
        total_expense = conn.execute('SELECT SUM(amount) FROM expenses WHERE username = ?', (username,)).fetchone()[0] or 0

        cursor.execute('''
        INSERT INTO leaderboard (username, achievement_points, total_income, total_expense)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(username)
        DO UPDATE SET
            achievement_points = excluded.achievement_points,
            total_income = excluded.total_income,
            total_expense = excluded.total_expense
        ''', (username, total_ap, total_income, total_expense))

    conn.commit()
    conn.close()

def update_leaderboard_for_user(username):
    conn = get_db_connection()
    cursor = conn.cursor()

    total_ap = (
        calculate_income_points(username) +
        calculate_expense_points(username) +
        calculate_balanced_activity_bonus(username) +
        calculate_daily_streak(username)
    )

    total_income = conn.execute('SELECT SUM(amount) FROM income WHERE username = ?', (username,)).fetchone()[0] or 0
    total_expense = conn.execute('SELECT SUM(amount) FROM expenses WHERE username = ?', (username,)).fetchone()[0] or 0

    cursor.execute('''
    INSERT INTO leaderboard (username, achievement_points, total_income, total_expense)
    VALUES (?, ?, ?, ?)
    ON CONFLICT(username)
    DO UPDATE SET
        achievement_points = excluded.achievement_points,
        total_income = excluded.total_income,
        total_expense = excluded.total_expense
    ''', (username, total_ap, total_income, total_expense))

    conn.commit()
    conn.close()

@app.route('/global_leaderboard')
def global_leaderboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    update_leaderboard()
    
    global_leaderboard_data = fetch_global_leaderboard()
    
    return render_template('GlobalLeaderboard.html', leaderboard=global_leaderboard_data)

@app.route('/followed_leaderboard')
def followed_leaderboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    current_user = session['username']
        
    update_leaderboard()
    
    followed_leaderboard_data = fetch_followed_leaderboard(current_user)
    
    return render_template('FollowedLeaderboard.html', leaderboard=followed_leaderboard_data)

@app.route('/search', methods=['GET'])
def search_user():
    query = request.args.get('search_query')
    if not query:
        return redirect(url_for('global_leaderboard'))
    
    username = query.strip()

    if 'username' in session and session['username'] == username:
        return redirect(url_for('user_profile', username=username))

    return redirect(url_for('user_profile', username=username))

@app.route('/user/', defaults={'username': None})
@app.route('/user/<username>')
def user_profile(username):
    if 'username' not in session:
        return redirect(url_for('login'))

    if username is None:
        username = session['username']

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = cur.fetchone()

    if user is None:
        conn.close()
        return "User not found", 404

    update_leaderboard_for_user(username)
    assign_badges(username)

    cur.execute('SELECT COUNT(*) FROM follow_relationships WHERE following = ?', (username,))
    follower_count = cur.fetchone()[0]

    cur.execute('SELECT COUNT(*) FROM follow_relationships WHERE follower = ?', (username,))
    following_count = cur.fetchone()[0]

    logged_in_user = session['username']
    cur.execute('SELECT COUNT(*) FROM follow_relationships WHERE follower = ? AND following = ?', (logged_in_user, username))
    is_following = cur.fetchone()[0] > 0

    cur.execute('''SELECT apbadgeid, incomebadgeid, expensebadgeid 
                   FROM user_badges 
                   WHERE username = ?''', (username,))
    badge_ids = cur.fetchone() or (1, 1, 1)

    badge_ids = [str(badge_id) for badge_id in badge_ids]

    conn.close()

    return render_template('user_profile.html', user=user, follower_count=follower_count, following_count=following_count,
                           is_following=is_following, badge_ids=badge_ids)

@app.route('/follow', methods=['POST'])
def follow():
    if 'username' not in session:
        return redirect(url_for('login'))

    logged_in_user = session['username']
    user_to_follow = request.form['user_id']

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute('SELECT COUNT(*) FROM follow_relationships WHERE follower = ? AND following = ?', (logged_in_user, user_to_follow))
    followed = cur.fetchone()[0] > 0

    if followed:
        cur.execute('DELETE FROM follow_relationships WHERE follower = ? AND following = ?', (logged_in_user, user_to_follow))
    else:
        cur.execute('INSERT INTO follow_relationships (follower, following) VALUES (?, ?)', (logged_in_user, user_to_follow))

    conn.commit()
    conn.close()
    
    return redirect(url_for('user_profile', username=user_to_follow))

@app.route('/my_profile')
def my_profile():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = cur.fetchone()

    if user is None:
        conn.close()
        return "User not found", 404

    update_leaderboard_for_user(username)
    assign_badges(username)

    cur.execute('SELECT COUNT(*) FROM follow_relationships WHERE following = ?', (username,))
    follower_count = cur.fetchone()[0]

    cur.execute('SELECT COUNT(*) FROM follow_relationships WHERE follower = ?', (username,))
    following_count = cur.fetchone()[0]

    logged_in_user = session['username']
    cur.execute('SELECT COUNT(*) FROM follow_relationships WHERE follower = ? AND following = ?', (logged_in_user, username))
    is_following = cur.fetchone()[0] > 0

    cur.execute('''SELECT apbadgeid, incomebadgeid, expensebadgeid 
                   FROM user_badges 
                   WHERE username = ?''', (username,))
    badge_ids = cur.fetchone() or (1, 1, 1)

    badge_ids = [str(badge_id) for badge_id in badge_ids]

    conn.close()

    return render_template('my_profile.html', user=user, follower_count=follower_count, 
                           following_count=following_count, is_following=is_following, 
                           badge_ids=badge_ids)

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

        hashed_password = generate_password_hash(password)

        conn = get_db_connection()
        conn.execute('''
            INSERT INTO users (username, email, password)
            VALUES (?, ?, ?)
        ''', (username, email, hashed_password))
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

        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()

        if user:
            if check_password_hash(user['password'], password):
                session['username'] = user['username']
                return redirect(url_for('home'))
            else:
                flash('Invalid username or password. Please try again.')
        else:
            flash('Invalid username or password. Please try again.')
            
        return redirect(url_for('login'))

    return render_template('Login.html')

@app.route('/home')
def home():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('Home.html')
  
@app.route('/expense_form', methods=['GET', 'POST'])
def expense_form():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        username = session['username']
        date = request.form['date']
        try:
            amount = float(request.form['amount'])
        except ValueError:
            return "Invalid amount", 400

        category = request.form['category']
        description = request.form['description']

        if amount < 0.01:
            return "Amount must be at least 0.01", 400
        
        conn = get_db_connection()
        conn.execute('''INSERT INTO expenses (username, date, amount, category, description)
                         VALUES (?, ?, ?, ?, ?)''', 
                     (username, date, amount, category, description))
        conn.commit()
        conn.close()

        update_leaderboard()
        assign_badges(username)

        return redirect(url_for('transaction'))

    return render_template('expenseform.html')

@app.route('/income_form', methods=['GET', 'POST'])
def income_form():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        username = session['username']
        date = request.form['date']
        amount = float(request.form['amount'])
        category = request.form['category']
        description = request.form['description']

        if amount < 0.01:
            return "Amount must be at least 0.01", 400
        
        valid_categories = [
            'Salary', 'Business', 'Investments', 'Gifts', 
            'Extra Income', 'Loan', 'Insurance Payout', 'Other Incomes'
        ]
        if category not in valid_categories:
            return "Invalid category", 400

        conn = get_db_connection()
        try:
            conn.execute('''
                INSERT INTO income (username, date, amount, category, description)
                VALUES (?, ?, ?, ?, ?)
            ''', (username, date, amount, category, description))
            conn.commit()
        except sqlite3.IntegrityError as e:
            return f"IntegrityError: {e}", 400
        finally:
            conn.close()

        update_leaderboard()
        assign_badges(username)

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

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
