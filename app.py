from flask import Flask, render_template, request, redirect, session, flash
import sqlite3, os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'supersecretkey'
DB = 'database.db'

def init_db():
    if not os.path.exists(DB):
        conn = sqlite3.connect(DB)
        conn.executescript('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT,
                role TEXT
            );
            CREATE TABLE IF NOT EXISTS cars (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                car_number TEXT,
                car_type TEXT,
                status TEXT DEFAULT 'available'
            );
            CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                car_id INTEGER,
                date_start TEXT,
                date_end TEXT,
                reason TEXT,
                status TEXT DEFAULT 'pending'
            );
            INSERT OR IGNORE INTO users (username, password, role) VALUES
            ('admin', '1234', 'admin'),
            ('driver1', '1234', 'driver'),
            ('user1', '1234', 'user');
        ''')
        conn.commit()
        conn.close()

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    u, p = request.form['user'], request.form['pass']
    conn = sqlite3.connect(DB)
    cur = conn.execute('SELECT role FROM users WHERE username=? AND password=?', (u, p))
    row = cur.fetchone()
    conn.close()
    if row:
        session['user'], session['role'] = u, row[0]
        return redirect('/dashboard')
    flash('ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง')
    return redirect('/')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session: return redirect('/')
    return render_template('dashboard.html', user=session['user'], role=session['role'])

@app.route('/cars')
def cars():
    conn = sqlite3.connect(DB)
    cars = conn.execute('SELECT * FROM cars').fetchall()
    conn.close()
    return render_template('cars.html', cars=cars)

@app.route('/add_car', methods=['POST'])
def add_car():
    num, typ = request.form['num'], request.form['type']
    conn = sqlite3.connect(DB)
    conn.execute('INSERT INTO cars (car_number, car_type) VALUES (?,?)', (num, typ))
    conn.commit()
    conn.close()
    return redirect('/cars')

@app.route('/request_car', methods=['GET', 'POST'])
def request_car():
    if request.method == 'POST':
        user_id = 1  # simplified
        car_id = request.form['car_id']
        ds, de = request.form['ds'], request.form['de']
        reason = request.form['reason']
        conn = sqlite3.connect(DB)
        conn.execute('INSERT INTO requests (user_id, car_id, date_start, date_end, reason) VALUES (?,?,?,?,?)',
                     (user_id, car_id, ds, de, reason))
        conn.commit()
        conn.close()
        return redirect('/requests')
    conn = sqlite3.connect(DB)
    cars = conn.execute('SELECT * FROM cars WHERE status="available"').fetchall()
    conn.close()
    return render_template('request_car.html', cars=cars)

@app.route('/requests')
def requests():
    conn = sqlite3.connect(DB)
    rows = conn.execute('''
        SELECT r.id, c.car_number, r.date_start, r.date_end, r.reason, r.status
        FROM requests r
        JOIN cars c ON r.car_id = c.id
    ''').fetchall()
    conn.close()
    return render_template('requests.html', rows=rows)

@app.route('/approve/<int:rid>')
def approve(rid):
    conn = sqlite3.connect(DB)
    conn.execute('UPDATE requests SET status="approved" WHERE id=?', (rid,))
    conn.commit()
    conn.close()
    return redirect('/requests')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    init_db()
    app.run(debug=True)