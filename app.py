from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
import sqlite3
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import os
from datetime import datetime
import database

# Initialize the database
database.init_db()

# Create a Flask application
app = Flask(__name__)
app.secret_key = '200220051805200528102005'  # Set the secret key for session management

def get_db_connection():
    # Establish a connection to the SQLite database
    conn = sqlite3.connect('budgetbadger.db', timeout=30)
    conn.row_factory = sqlite3.Row  # Set row factory to return rows as dictionaries
    return conn

def fetch_incomes_from_db(username):
    # Fetch all income records for a specific user
    conn = get_db_connection()
    incomes = conn.execute('SELECT * FROM income WHERE username = ?', (username,)).fetchall()
    conn.close()  # Close the database connection
    return incomes

def fetch_expenses_from_db(username):
    # Fetch all expense records for a specific user
    conn = get_db_connection()
    expenses = conn.execute('SELECT * FROM expenses WHERE username = ?', (username,)).fetchall()
    conn.close()  # Close the database connection
    return expenses

def fetch_recent_incomes_from_db(username, limit=4):
    conn = get_db_connection()
    query = 'SELECT * FROM income WHERE username = ? ORDER BY date DESC LIMIT ?'
    incomes = conn.execute(query, (username, limit)).fetchall()
    conn.close()
    return incomes

def fetch_recent_expenses_from_db(username, limit=4):
    conn = get_db_connection()
    query = 'SELECT * FROM expenses WHERE username = ? ORDER BY date DESC LIMIT ?'
    expenses = conn.execute(query, (username, limit)).fetchall()
    conn.close()
    return expenses

def fetch_current_month_expenses(username):
    # Get the current year and month
    current_year = datetime.now().year
    current_month = datetime.now().month

    # SQL query to fetch only expenses for the current month and year
    query = """
        SELECT * FROM expenses 
        WHERE username = ? AND strftime('%Y', date) = ? AND strftime('%m', date) = ?
    """
    year_str = str(current_year)
    month_str = f'{current_month:02d}'  # Ensure it's two digits (e.g., '09' for September)

    # Execute the query and return the result
    conn = get_db_connection()  # Use get_db_connection() to get the database connection
    expenses = conn.execute(query, (username, year_str, month_str)).fetchall()
    conn.close()  # Remember to close the connection
    return expenses

def fetch_current_month_incomes(username):
    # Get the current year and month
    current_year = datetime.now().year
    current_month = datetime.now().month

    # SQL query to fetch only incomes for the current month and year
    query = """
        SELECT * FROM income 
        WHERE username = ? AND strftime('%Y', date) = ? AND strftime('%m', date) = ?
    """
    year_str = str(current_year)
    month_str = f'{current_month:02d}'  # Ensure it's two digits (e.g., '09' for September)

    # Execute the query and return the result
    conn = get_db_connection()  # Use get_db_connection() to get the database connection
    incomes = conn.execute(query, (username, year_str, month_str)).fetchall()
    conn.close()  # Remember to close the connection
    return incomes

def fetch_current_year_expenses(username):
    # Get the current year
    current_year = datetime.now().year

    # SQL query to fetch only expenses for the current year
    query = """
        SELECT * FROM expenses 
        WHERE username = ? AND strftime('%Y', date) = ?
    """
    year_str = str(current_year)

    # Execute the query and return the result
    conn = get_db_connection()
    expenses = conn.execute(query, (username, year_str)).fetchall()
    conn.close()
    return expenses

def fetch_current_year_incomes(username):
    # Get the current year
    current_year = datetime.now().year

    # SQL query to fetch only incomes for the current year
    query = """
        SELECT * FROM income
        WHERE username = ? AND strftime('%Y', date) = ?
    """
    year_str = str(current_year)

    # Execute the query and return the result
    conn = get_db_connection()
    incomes = conn.execute(query, (username, year_str)).fetchall()
    conn.close()
    return incomes

def fetch_entries(username):
    # Establish a database connection
    conn = get_db_connection()
    
    # SQL query to fetch all dates from income and expenses for the user
    query = '''
        SELECT date FROM income WHERE username = ?
        UNION ALL
        SELECT date FROM expenses WHERE username = ?
    '''
    # Execute the query and fetch all results
    entries = conn.execute(query, (username, username)).fetchall()
    
    conn.close()  # Close the database connection
    # Return a list of dates from the entries
    return [entry['date'] for entry in entries]

def fetch_monthly_entries(username):
    # Establish a database connection
    conn = get_db_connection()
    
    # SQL query to count income entries grouped by month
    income_entries_query = '''
        SELECT strftime('%Y-%m', date) AS month, COUNT(*) AS count
        FROM income
        WHERE username = ?
        GROUP BY month
    '''
    income_entries = conn.execute(income_entries_query, (username,)).fetchall()
    
    # SQL query to count expense entries grouped by month
    expense_entries_query = '''
        SELECT strftime('%Y-%m', date) AS month, COUNT(*) AS count
        FROM expenses
        WHERE username = ?
        GROUP BY month
    '''
    expense_entries = conn.execute(expense_entries_query, (username,)).fetchall()
    
    conn.close()  # Close the database connection

    # Create dictionaries for monthly income and expense counts
    monthly_income_entries = {entry['month']: entry['count'] for entry in income_entries}
    monthly_expense_entries = {entry['month']: entry['count'] for entry in expense_entries}

    # Return the total counts of income and expenses
    return {
        'income': sum(monthly_income_entries.values()),
        'expense': sum(monthly_expense_entries.values())
    }

def calculate_income_points(username):
    # Fetch incomes for the specified user
    incomes = fetch_incomes_from_db(username)
    income_points = 0
    
    # Calculate points based on income categories
    for income in incomes:
        amount = income['amount']
        category = income['category']

        # Assign points based on the category of income
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

    return income_points  # Return the total income points

def calculate_expense_points(username):
    # Fetch expenses for the specified user
    expenses = fetch_expenses_from_db(username)
    essential_expenses_categories = {'Groceries', 'Healthcare', 'Education', 'Food & Drinks', 'Transport'}
    expense_points = 0
    non_essential_points = 0
    total_non_essential_spending = 0

    # Calculate points based on expense categories
    for expense in expenses:
        amount = expense['amount']
        category = expense['category']

        if category in essential_expenses_categories:
            expense_points += (amount // 100) * 5  # Points for essential expenses
        else:
            non_essential_points += (amount // 100) * 2  # Points for non-essential expenses
            total_non_essential_spending += amount

    # Apply penalty for excessive non-essential spending over $1000
    if total_non_essential_spending > 1000:
        excess_amount = total_non_essential_spending - 1000
        penalty_points = (excess_amount // 100) * 5
        non_essential_points -= penalty_points

    return expense_points + non_essential_points  # Return total expense points

def calculate_balanced_activity_bonus(username):
    # Fetch incomes and expenses for the specified user
    incomes = fetch_incomes_from_db(username)
    expenses = fetch_expenses_from_db(username)

    # Calculate total income and expenses
    total_income = sum(income['amount'] for income in incomes)
    total_expense = sum(expense['amount'] for expense in expenses)

    balance_bonus = 0
    
    # Return 0 if there are no expenses
    if total_expense == 0:
        return balance_bonus

    # Calculate income-to-expense ratio and determine balance bonus
    income_expense_ratio = total_income / total_expense
    if income_expense_ratio > 1:
        percentage_extra_income = (income_expense_ratio - 1) * 100
        balance_bonus = (percentage_extra_income // 10) * 20

    # Fetch monthly entries for consistency bonus
    monthly_entries = fetch_monthly_entries(username)
    income_entries = monthly_entries['income']
    expense_entries = monthly_entries['expense']

    # Consistency bonus based on the number of entries
    consistency_bonus = 30 if income_entries >= 5 and expense_entries >= 5 else 0

    return balance_bonus + consistency_bonus  # Return total bonus points

def has_seven_day_streak(dates):
    date_format = "%Y-%m-%d"
    dates = [datetime.strptime(date, date_format) for date in dates]  # Convert date strings to datetime objects
    dates = sorted(set(dates))  # Remove duplicates and sort the dates
    
    # Check if there are at least 7 unique dates
    if len(dates) < 7:
        return False

    # Check for a 7-day streak
    for i in range(len(dates) - 6):
        streak_dates = dates[i:i+7]
        if streak_dates[-1] - streak_dates[0] == timedelta(days=6):
            return True  # Return True if a streak is found
    
    return False  # Return False if no streak is found

def calculate_daily_streak(username):
    # Fetch entries for the specified user
    entries = fetch_entries(username)
    daily_streak_points = 0

    # Check for a 7-day streak and award points if found
    if has_seven_day_streak(entries):
        daily_streak_points += 10

    return daily_streak_points  # Return daily streak points

def update_all_users_points():
    # Establish a database connection
    conn = get_db_connection()
    cursor = conn.cursor()
    # Fetch all usernames from the users table
    users = cursor.execute('SELECT username FROM users').fetchall()
    conn.close()
    
    # Update points for each user
    for user in users:
        username = user['username']
        update_totals(username)  # Call the function to update totals for each user

def generate_pie_chart(data, title, labels, filename, username):
    # Create a directory for the user if it doesn't exist
    user_folder = f'static/images/{username}/'
    os.makedirs(user_folder, exist_ok=True)

    # Prepare data for pie chart
    amounts = [item['amount'] for item in data]
    categories = [item['category'] for item in data]

    # Create a pie chart
    plt.figure(figsize=(8, 6))
    label_font = {'fontsize': 17, 'fontfamily': 'serif', 'fontweight': 'bold', 'color': '#c0e2df'}
    autopct_font = {'fontsize': 15, 'fontfamily': 'serif', 'fontweight': 'normal', 'color': '#c0e2df'}
    plt.pie(amounts, labels=categories, autopct=lambda p: f'{p:.1f}%', startangle=140,
            textprops=label_font)
    plt.title(title, fontsize=25, fontfamily='serif', fontweight='bold', color='#c0e2df')

    # Save the pie chart as an image
    file_path = f'{user_folder}/{filename}.png'
    plt.savefig(file_path, dpi=300, transparent=True)
    plt.close()

    return file_path

def generate_frequency_polygon(data, title, filename, username):
    # Create a directory for the user if it doesn't exist
    user_folder = f'static/images/{username}/'
    os.makedirs(user_folder, exist_ok=True)

    # Convert data into a DataFrame for processing
    df = pd.DataFrame(data, columns=['date', 'amount'])

    # Validate DataFrame structure
    if 'date' not in df.columns or 'amount' not in df.columns:
        raise ValueError("Data must contain 'date' and 'amount' columns")

    # Convert date strings to datetime objects
    df['date'] = pd.to_datetime(df['date'])
    
    # Set date as index and resample to monthly totals
    df.set_index('date', inplace=True)
    monthly_totals = df.resample('M').sum().reset_index()

    # Prepare a complete range of months for the year
    all_months = pd.date_range(start='2024-01-01', end='2024-12-31', freq='M')
    all_months_df = pd.DataFrame({'date': all_months})
    all_months_df['month'] = all_months_df['date'].dt.strftime('%b')
    all_months_df['amount'] = 0

    # Merge monthly totals with all months for plotting
    monthly_totals['month'] = monthly_totals['date'].dt.strftime('%b')
    merged_df = pd.merge(all_months_df, monthly_totals, on='month', suffixes=('_all', '_actual'), how='left')
    merged_df['amount'] = merged_df['amount_actual'].fillna(0)

    # Create a frequency polygon
    plt.figure(figsize=(21, 14))
    plt.plot(merged_df['month'], merged_df['amount'], marker='o', linestyle='-', color='#39FF14')
    plt.title(title, fontsize=50, fontfamily='serif', fontweight='bold', color='#c0e2df')
    plt.xlabel('Month', fontsize=40, fontfamily='serif', fontweight='bold', color='#c0e2df') 
    plt.ylabel('Amount', fontsize=40, fontfamily='serif', fontweight='bold', color='#c0e2df')
    
    plt.xticks(ticks=range(12), labels=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'], rotation=45)
    
    # Customize ticks and spine colors
    plt.tick_params(axis='x', labelsize=30, colors='#c0e2df')
    plt.tick_params(axis='y', labelsize=30, colors='#c0e2df')
    
    ax = plt.gca()
    ax.spines['bottom'].set_color('#c0e2df')
    ax.spines['top'].set_color('#c0e2df')
    ax.spines['right'].set_color('#c0e2df')
    ax.spines['left'].set_color('#c0e2df')

    # Add grid and adjust layout
    plt.grid(color='gray', linestyle='--', linewidth=0.7)
    plt.tight_layout()  # Adjust layout to prevent clipping of tick-labels

    # Save the plot
    file_path = os.path.join(user_folder, f'{filename}_{username}.png')
    plt.savefig(file_path, dpi=300, transparent=True)
    plt.close()

    return file_path

def determine_ap_badge_id(ap):
    # Determine badge ID based on achievement points
    if ap is None or ap <= 0: 
        return 1
    if ap >= 50000: 
        return 7
    if ap >= 25000: 
        return 6
    if ap >= 10000: 
        return 5
    if ap >= 5000: 
        return 4
    if ap >= 2500: 
        return 3
    return 2

def determine_income_badge_id(income):
    # Determine badge ID based on total income
    if income is None or income <= 0: 
        return 1
    if income >= 20000: 
        return 7
    if income >= 10000: 
        return 6
    if income >= 5000: 
        return 5
    if income >= 2000: 
        return 4
    if income >= 100: 
        return 3
    return 2

def determine_expense_badge_id(expense):
    # Determine badge ID based on total expenses
    if expense is None or expense <= 0: 
        return 1
    if expense >= 20000: 
        return 7
    if expense >= 10000: 
        return 6
    if expense >= 5000: 
        return 5
    if expense >= 2000: 
        return 4
    if expense >= 1000: 
        return 3
    return 2

def assign_badges(username):
    # Connect to the database and retrieve user data for badge assignment
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT achievement_points, total_income, total_expense FROM leaderboard WHERE username = ?', (username,))
    totals = cursor.fetchone()

    if totals is None:
        return  # No totals found for user

    total_ap, total_income, total_expense = totals

    # Determine badge IDs based on user totals
    ap_badge_id = determine_ap_badge_id(total_ap)
    income_badge_id = determine_income_badge_id(total_income)
    expense_badge_id = determine_expense_badge_id(total_expense)

    # Insert or update user badge information in the database
    cursor.execute('''INSERT INTO user_badges (username, apbadgeid, incomebadgeid, expensebadgeid) 
                      VALUES (?, ?, ?, ?)
                      ON CONFLICT(username) 
                      DO UPDATE SET 
                          apbadgeid = excluded.apbadgeid,
                          incomebadgeid = excluded.incomebadgeid,
                          expensebadgeid = excluded.expensebadgeid
                   ''', (username, ap_badge_id, income_badge_id, expense_badge_id))

    # Commit the changes and close the connection
    conn.commit()
    conn.close()

def update_follower_following_counts(username):
    # Establishes a database connection and updates the follower and following counts for the given username.
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Counts the number of users following the specified username and updates the follower count in the users table.
    cur.execute('SELECT COUNT(*) FROM follow_relationships WHERE following = ?', (username,))
    follower_count = cur.fetchone()[0]
    cur.execute('UPDATE users SET follower_count = ? WHERE username = ?', (follower_count, username))

    # Counts how many users the specified username is following and updates the following count in the users table.
    cur.execute('SELECT COUNT(*) FROM follow_relationships WHERE follower = ?', (username,))
    following_count = cur.fetchone()[0]
    cur.execute('UPDATE users SET following_count = ? WHERE username = ?', (following_count, username))

    conn.commit()
    conn.close()

def fetch_global_leaderboard():
    # Retrieves the top 10 users based on achievement points from the leaderboard.
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''SELECT username, achievement_points FROM leaderboard ORDER BY achievement_points DESC LIMIT 10''')
    top_users = cursor.fetchall()
    conn.close()
    return top_users

def fetch_followed_leaderboard(current_user):
    # Fetches the leaderboard for users that the current_user is following, limited to the top 10 by achievement points.
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''SELECT l.username, l.achievement_points
                      FROM leaderboard l
                      JOIN follow_relationships f ON l.username = f.following
                      WHERE f.follower = ?
                      ORDER BY l.achievement_points DESC
                      LIMIT 10''', (current_user,))
    followed_users = cursor.fetchall()
    conn.close()
    return followed_users

def update_leaderboard():
    # Updates the leaderboard for all users by calculating and storing their total achievement points, income, and expenses.
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetches all usernames from the users table.
    users = conn.execute('SELECT username FROM users').fetchall()

    for user in users:
        username = user['username']

        # Calculates total achievement points based on different criteria.
        total_ap = calculate_income_points(username) + \
                   calculate_expense_points(username) + \
                   calculate_balanced_activity_bonus(username) + \
                   calculate_daily_streak(username)

        # Sums up total income and total expenses for the user.
        total_income = conn.execute('SELECT SUM(amount) FROM income WHERE username = ?', (username,)).fetchone()[0] or 0
        total_expense = conn.execute('SELECT SUM(amount) FROM expenses WHERE username = ?', (username,)).fetchone()[0] or 0

        # Updates or inserts the user's achievement points, total income, and total expenses in the leaderboard.
        cursor.execute('''INSERT INTO leaderboard (username, achievement_points, total_income, total_expense)
                          VALUES (?, ?, ?, ?)
                          ON CONFLICT(username)
                          DO UPDATE SET
                              achievement_points = excluded.achievement_points,
                              total_income = excluded.total_income,
                              total_expense = excluded.total_expense''', (username, total_ap, total_income, total_expense))

    conn.commit()
    conn.close()

def update_leaderboard_for_user(username):
    # Updates the leaderboard for a specific user by recalculating their total achievement points, income, and expenses.
    conn = get_db_connection()
    cursor = conn.cursor()

    # Calculates total achievement points for the specific user.
    total_ap = (
        calculate_income_points(username) +
        calculate_expense_points(username) +
        calculate_balanced_activity_bonus(username) +
        calculate_daily_streak(username)
    )

    # Sums up total income and total expenses for the user.
    total_income = conn.execute('SELECT SUM(amount) FROM income WHERE username = ?', (username,)).fetchone()[0] or 0
    total_expense = conn.execute('SELECT SUM(amount) FROM expenses WHERE username = ?', (username,)).fetchone()[0] or 0

    # Updates or inserts the user's achievement points, total income, and total expenses in the leaderboard.
    cursor.execute('''INSERT INTO leaderboard (username, achievement_points, total_income, total_expense)
                      VALUES (?, ?, ?, ?)
                      ON CONFLICT(username)
                      DO UPDATE SET
                          achievement_points = excluded.achievement_points,
                          total_income = excluded.total_income,
                          total_expense = excluded.total_expense''', (username, total_ap, total_income, total_expense))

    conn.commit()
    conn.close()

@app.route('/global_leaderboard')
def global_leaderboard():
    # Check if the user is logged in
    if 'username' not in session:
        return redirect(url_for('login'))  # Redirect to login if not authenticated
    
    update_leaderboard()  # Update the leaderboard data
    
    # Fetch the data for the global leaderboard
    global_leaderboard_data = fetch_global_leaderboard()
    
    # Render the global leaderboard template with the fetched data
    return render_template('GlobalLeaderboard.html', leaderboard=global_leaderboard_data)

@app.route('/followed_leaderboard')
def followed_leaderboard():
    # Check if the user is logged in
    if 'username' not in session:
        return redirect(url_for('login'))  # Redirect to login if not authenticated
    
    current_user = session['username']  # Get the current logged-in user
    
    update_leaderboard()  # Update the leaderboard data
    
    # Fetch the data for the followed leaderboard based on the current user
    followed_leaderboard_data = fetch_followed_leaderboard(current_user)
    
    # Render the followed leaderboard template with the fetched data
    return render_template('FollowedLeaderboard.html', leaderboard=followed_leaderboard_data)


@app.route('/search', methods=['GET'])
def search_user():
    # Gets the search query from the request arguments.
    query = request.args.get('search_query')
    
    # If no query is provided, redirects to the global leaderboard.
    if not query:
        return redirect(url_for('global_leaderboard'))
    
    # Strips whitespace from the search query.
    username = query.strip()

    # Checks if the logged-in user is searching for their own profile and redirects accordingly.
    if 'username' in session and session['username'] == username:
        return redirect(url_for('user_profile', username=username))

    # Redirects to the user profile page for the searched username.
    return redirect(url_for('user_profile', username=username))


@app.route('/user/', defaults={'username': None})
@app.route('/user/<username>')
def user_profile(username):
    # Check if the user is logged in. If not, redirect to the login page
    if 'username' not in session:
        return redirect(url_for('login'))

    # If no username is provided, use the logged-in user's username
    if username is None:
        username = session['username']

    # Connect to the database
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Retrieve user details from the database
    cur.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = cur.fetchone()

    # If the user is not found, return a 404 error
    if user is None:
        conn.close()
        return "User not found", 404

    # Update the leaderboard and assign badges for the user
    update_leaderboard_for_user(username)
    assign_badges(username)

    # Get the count of followers for the user
    cur.execute('SELECT COUNT(*) FROM follow_relationships WHERE following = ?', (username,))
    follower_count = cur.fetchone()[0]

    # Get the count of users the user is following
    cur.execute('SELECT COUNT(*) FROM follow_relationships WHERE follower = ?', (username,))
    following_count = cur.fetchone()[0]

    # Check if the logged-in user is following this user
    logged_in_user = session['username']
    cur.execute('SELECT COUNT(*) FROM follow_relationships WHERE follower = ? AND following = ?', (logged_in_user, username))
    is_following = cur.fetchone()[0] > 0

    # Retrieve the badge IDs for the user
    cur.execute('''SELECT apbadgeid, incomebadgeid, expensebadgeid 
                   FROM user_badges 
                   WHERE username = ?''', (username,))
    badge_ids = cur.fetchone() or (1, 1, 1)  # Default badge IDs if none found

    badge_ids = [str(badge_id) for badge_id in badge_ids]  # Convert badge IDs to strings

    conn.close()  # Close the database connection

    # Render the user profile template with the retrieved data
    return render_template('user_profile.html', user=user, follower_count=follower_count, following_count=following_count,
                           is_following=is_following, badge_ids=badge_ids)

@app.route('/follow', methods=['POST'])
def follow():
    # Check if the user is logged in; if not, redirect to the login page.
    if 'username' not in session:
        return redirect(url_for('login'))

    logged_in_user = session['username']
    user_to_follow = request.form['user_id']  # Get the user ID of the user to follow/unfollow.

    conn = get_db_connection()
    cur = conn.cursor()

    # Check if the user is already following the specified user.
    cur.execute('SELECT COUNT(*) FROM follow_relationships WHERE follower = ? AND following = ?', (logged_in_user, user_to_follow))
    followed = cur.fetchone()[0] > 0

    # If already followed, unfollow; otherwise, follow the user.
    if followed:
        cur.execute('DELETE FROM follow_relationships WHERE follower = ? AND following = ?', (logged_in_user, user_to_follow))
    else:
        cur.execute('INSERT INTO follow_relationships (follower, following) VALUES (?, ?)', (logged_in_user, user_to_follow))

    conn.commit()
    conn.close()
    
    # Redirect back to the profile of the user being followed/unfollowed.
    return redirect(url_for('user_profile', username=user_to_follow))

# Route for the profile page of the user logged-in.
@app.route('/my_profile')
def my_profile():
    # Check if the user is logged in; if not, redirect to the login page.
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']

    conn = get_db_connection()
    cur = conn.cursor()

    # Fetch the user's profile details.
    cur.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = cur.fetchone()

    if user is None:
        conn.close()
        return "User not found", 404  # Return 404 if the user is not found.

    update_leaderboard_for_user(username)  # Update leaderboard for the current user.
    assign_badges(username)  # Assign badges based on user's activity.

    # Get follower and following counts.
    cur.execute('SELECT COUNT(*) FROM follow_relationships WHERE following = ?', (username,))
    follower_count = cur.fetchone()[0]

    cur.execute('SELECT COUNT(*) FROM follow_relationships WHERE follower = ?', (username,))
    following_count = cur.fetchone()[0]

    logged_in_user = session['username']
    # Check if the logged-in user is following the profile being viewed.
    cur.execute('SELECT COUNT(*) FROM follow_relationships WHERE follower = ? AND following = ?', (logged_in_user, username))
    is_following = cur.fetchone()[0] > 0

    # Fetch the badge IDs for the user.
    cur.execute('''SELECT apbadgeid, incomebadgeid, expensebadgeid 
                   FROM user_badges 
                   WHERE username = ?''', (username,))
    badge_ids = cur.fetchone() or (1, 1, 1)  # Default badge IDs if none found.

    badge_ids = [str(badge_id) for badge_id in badge_ids]  # Convert badge IDs to strings for rendering.

    conn.close()

    # Render the profile page with user details and follow stats.
    return render_template('my_profile.html', user=user, follower_count=follower_count, 
                           following_count=following_count, is_following=is_following, 
                           badge_ids=badge_ids)

# Route for the summary page.
@app.route('/summary')
def summary():
    # Check if the user is logged in; if not, redirect to the login page.
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    
    # Fetch monthly expenses and incomes for the pie charts
    monthly_expenses = fetch_current_month_expenses(username)
    monthly_incomes = fetch_current_month_incomes(username)

    # Fetch yearly expenses and incomes for the frequency polygons
    yearly_expenses = fetch_current_year_expenses(username)
    yearly_incomes = fetch_current_year_incomes(username)

    # Format monthly expenses and incomes for chart generation
    formatted_monthly_expenses = [{'date': exp['date'], 'amount': exp['amount']} for exp in monthly_expenses]
    formatted_monthly_incomes = [{'date': inc['date'], 'amount': inc['amount']} for inc in monthly_incomes]

    # Format yearly expenses and incomes for frequency polygon generation
    formatted_yearly_expenses = [{'date': exp['date'], 'amount': exp['amount']} for exp in yearly_expenses]
    formatted_yearly_incomes = [{'date': inc['date'], 'amount': inc['amount']} for inc in yearly_incomes]

    # Generate pie charts for the current month
    expense_pie_chart_filename = f'expense_pie_chart'
    income_pie_chart_filename = f'income_pie_chart'
    
    expense_pie_chart = generate_pie_chart(
        monthly_expenses,
        'Monthly Expenses by Category',
        [exp['category'] for exp in monthly_expenses],
        expense_pie_chart_filename,
        username
    )
    
    income_pie_chart = generate_pie_chart(
        monthly_incomes,
        'Monthly Incomes by Category',
        [inc['category'] for inc in monthly_incomes],
        income_pie_chart_filename,
        username
    )

    # Generate frequency polygons for the entire year
    expense_frequency_polygon_filename = f'expense_frequency_polygon'
    income_frequency_polygon_filename = f'income_frequency_polygon'
    
    expense_frequency_polygon = generate_frequency_polygon(
        formatted_yearly_expenses,
        'Yearly Expense Frequency',
        expense_frequency_polygon_filename,
        username
    )
    
    income_frequency_polygon = generate_frequency_polygon(
        formatted_yearly_incomes,
        'Yearly Income Frequency',
        income_frequency_polygon_filename,
        username
    )

    # Render the summary page with the generated charts.
    return render_template(
        'summary.html', 
        expense_pie_chart=expense_pie_chart,
        income_pie_chart=income_pie_chart,
        expense_frequency_polygon=expense_frequency_polygon,
        income_frequency_polygon=income_frequency_polygon,
        username=username
    )

# Route for the sign up page.
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        hashed_password = generate_password_hash(password)  # Hash the password for security.

        conn = get_db_connection()
        conn.execute('''INSERT INTO users (username, email, password) VALUES (?, ?, ?)''', 
                     (username, email, hashed_password))
        conn.commit()
        conn.close()

        # Redirect to the login page after successful signup.
        return redirect(url_for('login'))

    # Render the signup page.
    return render_template('SignUp.html')

# Route for the login page.
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()

        # Fetch the user based on the provided username.
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()

        if user:
            # Check if the provided password matches the hashed password in the database.
            if check_password_hash(user['password'], password):
                session['username'] = user['username']  # Store the username in session.
                return redirect(url_for('home'))
            else:
                flash('Invalid username or password. Please try again.')
        else:
            flash('Invalid username or password. Please try again.')
            
        return redirect(url_for('login'))

    # Render the login page.
    return render_template('Login.html')

@app.route('/home')
def home():
    # Check if the user is logged in
    if 'username' not in session:
        return redirect(url_for('login'))  # Redirect to login if not authenticated
    
    username = session['username']  # Get the current logged-in username

    piechart_expenses = fetch_current_month_expenses(username)
    piechart_incomes = fetch_current_month_incomes(username)

    # Fetch recent income and expense records, limiting to the latest 4 each
    recent_incomes = fetch_recent_incomes_from_db(username, limit=4)
    recent_expenses = fetch_recent_expenses_from_db(username, limit=4)

    # Define filenames for the pie chart images
    income_pie_chart_filename = f'income_pie_chart'
    expense_pie_chart_filename = f'expense_pie_chart'

    # Generate pie charts for the recent incomes and expenses
    income_pie_chart = generate_pie_chart(
        piechart_incomes, 
        'Monthly Incomes by Category', 
        [inc['category'] for inc in recent_incomes], 
        income_pie_chart_filename, 
        username
    )
    
    expense_pie_chart = generate_pie_chart(
        piechart_expenses, 
        'Monthly Expenses by Category', 
        [exp['category'] for exp in recent_expenses], 
        expense_pie_chart_filename, 
        username
    )

    # Render the home template with recent incomes, expenses, and username
    return render_template(
        'Home.html', 
        incomes=recent_incomes, 
        expenses=recent_expenses, 
        username=username
    )

#  Route for the expense form.
@app.route('/expense_form', methods=['GET', 'POST'])
def expense_form():
    # Check if the user is logged in by verifying the session
    if 'username' not in session:
        return redirect(url_for('login'))

    # Handle form submission
    if request.method == 'POST':
        username = session['username']
        date = request.form['date']  # Get the date from the form
        try:
            amount = float(request.form['amount'])  # Convert amount to float
        except ValueError:
            return "Invalid amount", 400  # Return error for invalid amount

        category = request.form['category']  # Get category from the form
        description = request.form['description']  # Get description from the form

        # Validate that the amount is at least 0.01
        if amount < 0.01:
            return "Amount must be at least 0.01", 400
        
        # Connect to the database and insert the expense record
        conn = get_db_connection()
        conn.execute('''INSERT INTO expenses (username, date, amount, category, description)
                         VALUES (?, ?, ?, ?, ?)''', 
                     (username, date, amount, category, description))
        conn.commit()  # Commit the transaction
        conn.close()  # Close the database connection

        # Update leaderboard and assign badges to the user
        update_leaderboard()
        assign_badges(username)

        return redirect(url_for('transaction'))  # Redirect to transaction page

    return render_template('expenseform.html')  # Render expense form

#  Route for the income form.
@app.route('/income_form', methods=['GET', 'POST'])
def income_form():
    # Check if the user is logged in by verifying the session
    if 'username' not in session:
        return redirect(url_for('login'))

    # Handle form submission
    if request.method == 'POST':
        username = session['username']
        date = request.form['date']  # Get the date from the form
        amount = float(request.form['amount'])  # Convert amount to float
        category = request.form['category']  # Get category from the form
        description = request.form['description']  # Get description from the form

        # Validate that the amount is at least 0.01
        if amount < 0.01:
            return "Amount must be at least 0.01", 400
        
        # Define valid income categories
        valid_categories = [
            'Salary', 'Business', 'Investments', 'Gifts', 
            'Extra Income', 'Loan', 'Insurance Payout', 'Other Incomes'
        ]
        # Check if the selected category is valid
        if category not in valid_categories:
            return "Invalid category", 400

        # Connect to the database and insert the income record
        conn = get_db_connection()
        try:
            conn.execute('''INSERT INTO income (username, date, amount, category, description)
                             VALUES (?, ?, ?, ?, ?)''', 
                         (username, date, amount, category, description))
            conn.commit()  # Commit the transaction
        except sqlite3.IntegrityError as e:
            return f"IntegrityError: {e}", 400  # Return error for integrity issues
        finally:
            conn.close()  # Close the database connection

        # Update leaderboard and assign badges to the user
        update_leaderboard()
        assign_badges(username)

        return redirect(url_for('transaction'))  # Redirect to transaction page

    return render_template('incomeform.html')  # Render income form

# Route for the transaction page.
@app.route('/transaction', methods=['GET'])
def transaction():
    # Check if the user is logged in by verifying the session
    if 'username' not in session:
        return redirect(url_for('login'))
    
    filter_option = request.args.get('filter', 'all')  # Get filter option from query parameters
    username = session['username']

    # Fetch incomes and expenses from the database
    incomes = fetch_incomes_from_db(username)
    expenses = fetch_expenses_from_db(username)

    # Filter incomes or expenses based on the selected option
    if filter_option == 'incomes':
        expenses = []  # Clear expenses if filtering by incomes
    elif filter_option == 'expenses':
        incomes = []  # Clear incomes if filtering by expenses

    return render_template('transaction.html', incomes=incomes, expenses=expenses, filter=filter_option)

# Route to logout
@app.route('/logout')
def logout():
    session.pop('username', None)  # Remove username from session
    return redirect(url_for('login'))  # Redirect to login page

if __name__ == '__main__':
    app.run(debug=True)  # Run the application in debug mode