from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = 'Amongus'

def get_db_connection():
    conn = sqlite3.connect('budgetbadger.db')
    conn.row_factory = sqlite3.Row
    return conn

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

        return redirect(url_for('expense_form'))

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

        return redirect(url_for('income_form'))

    return render_template('incomeform.html')

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
            return redirect(url_for('expense_form'))
        else:
            return 'Login failed. Check your email and password.'

    return render_template('Login.html')

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

    return render_template('Signup.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
