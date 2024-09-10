from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
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

def generate_pie_chart(data, title, labels, filename):
    amounts = [item['amount'] for item in data]
    categories = [item['category'] for item in data]
    
    plt.figure(figsize=(6, 6))
    plt.pie(amounts, labels=categories, autopct='%1.1f%%', startangle=140)
    plt.title(title)
    
    file_path = f'static/images/{filename}.png'
    plt.savefig(file_path)
    plt.close()
    
    return file_path

def generate_frequency_polygon(data, title, filename):
    df = pd.DataFrame(data, columns=['date', 'amount'])
    df['date'] = pd.to_datetime(df['date'])
    
    daily_totals = df.groupby('date').sum().reset_index()
    
    plt.figure(figsize=(10, 6))
    plt.plot(daily_totals['date'], daily_totals['amount'], marker='o', linestyle='-', color='b')
    plt.title(title)
    plt.xlabel('Date')
    plt.ylabel('Amount')
    
    file_path = f'static/images/{filename}.png'
    plt.savefig(file_path)
    plt.close()
    
    return file_path

@app.route('/summary')
def summary():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    
    expenses = fetch_expenses_from_db(username)
    incomes = fetch_incomes_from_db(username)
    
    expense_pie_chart = generate_pie_chart(expenses, 'Monthly Expenses by Category', [exp['category'] for exp in expenses], 'expense_pie_chart')
    expense_frequency_polygon = generate_frequency_polygon(expenses, 'Daily Expense Frequency', 'expense_frequency_polygon')
    
    income_pie_chart = generate_pie_chart(incomes, 'Monthly Incomes by Category', [inc['category'] for inc in incomes], 'income_pie_chart')
    income_frequency_polygon = generate_frequency_polygon(incomes, 'Daily Income Frequency', 'income_frequency_polygon')
    
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

@app.route('/expense-form', methods=['GET', 'POST'])
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

@app.route('/income-form', methods=['GET', 'POST'])
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

if __name__ == '__main__':
    app.run(debug=True)
