import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from flask import Flask, render_template, request, redirect, session
from flask_cors import CORS
from gerenjizhang.db import (
    get_user_by_username, create_user, init_db,
    get_records, get_monthly_summary, add_record, delete_record
)
from gerenjizhang.api.auth import auth_bp
from gerenjizhang.api.bill import bill_bp
from gerenjizhang.api.stats import stats_bp
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import time

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'fallback-dev-key-change-in-prod')
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
)

CORS(app, resources={r"/api/*": {"origins": "*"}})

# 注册 API 蓝图
app.register_blueprint(auth_bp)
app.register_blueprint(bill_bp)
app.register_blueprint(stats_bp)

init_db()

# 登录失败计数（内存中，生产环境用 Redis）
_login_attempts = {}

MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_SECONDS = 300


@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not username or not password:
            msg = "用户名和密码不能为空"
            return render_template("register.html", msg=msg)
        if len(username) < 3 or len(password) < 6:
            msg = "用户名至少3位，密码至少6位"
            return render_template("register.html", msg=msg)

        hashed = generate_password_hash(password)
        if create_user(username, hashed):
            return redirect('/login')
        else:
            msg = "用户名已存在"
    return render_template("register.html", msg=msg)


@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ""

    # 检查是否被锁定
    ip = request.remote_addr
    if ip in _login_attempts:
        count, first_attempt = _login_attempts[ip]
        if count >= MAX_LOGIN_ATTEMPTS:
            if time.time() - first_attempt < LOCKOUT_SECONDS:
                msg = "登录失败次数过多，请稍后再试"
                return render_template("login.html", msg=msg)
            else:
                del _login_attempts[ip]

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = get_user_by_username(username)
        if user:
            if check_password_hash(user[2], password):
                session['user'] = username
                session['user_id'] = user[0]
                _login_attempts.pop(ip, None)
                return redirect('/')
            else:
                _login_attempts[ip] = (_login_attempts.get(ip, [0, 0])[0] + 1, time.time())
                msg = "账号或密码错误"
        else:
            _login_attempts[ip] = (_login_attempts.get(ip, [0, 0])[0] + 1, time.time())
            msg = "账号或密码错误"

    return render_template("login.html", msg=msg)


@app.route('/')
def index():
    if 'user' not in session:
        return redirect('/login')

    user_id = session.get('user_id')
    now = datetime.now()
    year, month = now.year, now.month

    # 分页
    page = request.args.get('page', 1, type=int)
    per_page = 20
    offset = (page - 1) * per_page

    start = f"{year}-{month:02d}-01"
    end = f"{year}-{month+1:02d}-01" if month < 12 else f"{year+1}-01-01"

    records = get_records(user_id, start_date=start, end_date=end, limit=per_page, offset=offset)
    income, expense = get_monthly_summary(user_id, year, month)
    balance = income - expense

    total_records = get_records(user_id, start_date=start, end_date=end)
    total_pages = (len(total_records) + per_page - 1) // per_page

    return render_template("index.html",
                           records=records,
                           income=income,
                           expense=expense,
                           balance=balance,
                           page=page,
                           total_pages=total_pages,
                           month=month,
                           year=year)


@app.route('/add', methods=['POST'])
def add():
    if 'user' not in session:
        return redirect('/login')

    user_id = session.get('user_id')
    date = request.form['date']
    try:
        amount = float(request.form['amount'])
    except (ValueError, TypeError):
        return redirect('/')

    type_ = request.form['type']
    category = request.form['category']
    note = request.form.get('note', '')

    add_record(date, amount, type_, category, note, user_id)
    return redirect('/')


@app.route('/edit/<int:rid>', methods=['GET', 'POST'])
def edit(rid):
    if 'user' not in session:
        return redirect('/login')

    user_id = session.get('user_id')

    if request.method == 'POST':
        date = request.form['date']
        try:
            amount = float(request.form['amount'])
        except (ValueError, TypeError):
            return redirect('/')

        type_ = request.form['type']
        category = request.form['category']
        note = request.form.get('note', '')

        from gerenjizhang.db import edit_record
        edit_record(rid, date, amount, type_, category, note, user_id)
        return redirect('/')

    # GET: 查询单条记录
    from gerenjizhang.db import get_record_by_id
    record = get_record_by_id(rid, user_id)
    if not record:
        return redirect('/')
    return render_template("edit.html", record=record)


@app.route('/delete/<int:rid>')
def delete(rid):
    if 'user' not in session:
        return redirect('/login')

    user_id = session.get('user_id')
    delete_record(rid, user_id)
    return redirect('/')


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
