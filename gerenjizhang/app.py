"""
应用入口
使用模块化架构：config / models / services / schemas / middleware
"""
import os
import sys
import fnmatch
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

# 启动时加载 .env（如果存在）— 把 WECHAT_APPID / SECRET_KEY / DB 等环境变量
# 从 .env 文件读到 os.environ。已存在的环境变量优先（命令行/env 覆盖 .env）
try:
    from dotenv import load_dotenv
    _env_path = Path(__file__).parent.parent / '.env'
    if _env_path.exists():
        load_dotenv(_env_path, override=False)  # override=False：系统 env 优先
        print(f'[env] loaded from {_env_path}')
    else:
        print(f'[env] no .env found at {_env_path}, using system env only')
except ImportError:
    print('[env] python-dotenv not installed, using system env only')

from flask import Flask, request, session, Response, jsonify, send_from_directory
from datetime import datetime
import time
import logging

#加载配置
from gerenjizhang.config import get_config
from gerenjizhang.middleware import register_error_handlers, init_limiter
from gerenjizhang.middleware.request_logger import register_request_logger
from gerenjizhang.utils.response import success_response, error_response
from gerenjizhang.db import init_db, get_records

# 获取配置
config = get_config()

# 创建 Flask 应用
app = Flask(__name__)
app.secret_key = config.SECRET_KEY
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
)

# 配置日志 - 控制台 + 文件
from logging.handlers import RotatingFileHandler
import os

os.makedirs(config.LOG_DIR, exist_ok=True)
file_handler = RotatingFileHandler(
    config.LOG_FILE,
    maxBytes=config.LOG_MAX_BYTES,
    backupCount=config.LOG_BACKUP_COUNT,
    encoding='utf-8'
)
file_handler.setLevel(getattr(logging, config.LOG_LEVEL))
formatter = logging.Formatter(config.LOG_FORMAT)
file_handler.setFormatter(formatter)

root_logger = logging.getLogger()
root_logger.setLevel(getattr(logging, config.LOG_LEVEL))
root_logger.addHandler(file_handler)

console_handler = logging.StreamHandler()
console_handler.setLevel(getattr(logging, config.LOG_LEVEL))
console_handler.setFormatter(formatter)
root_logger.addHandler(console_handler)

# CORS — 白名单模式（生产前必须设 CORS_ALLOWED_ORIGINS env var）
# 支持通配符：*.weixin.qq.com 匹配 mp.weixin.qq.com / servicewechat.com 等子域
# dev 模式：白名单空 → 自动允许 localhost:*（开发体验）
@app.after_request
def add_cors_headers(response):
    origin = request.headers.get('Origin')
    cfg = get_config()
    allowed = cfg.CORS_ALLOWED_ORIGINS

    # 决定是否回显 Access-Control-Allow-Origin
    if origin:
        is_allowed = (
            # 精确匹配 OR 通配符匹配（fnmatch 支持 *.weixin.qq.com）
            any(fnmatch.fnmatch(origin, o) for o in allowed) or
            # dev 体验：白名单空时允许 localhost:*
            (not allowed and (origin.startswith('http://localhost:') or origin.startswith('http://127.0.0.1:')))
        )
        if is_allowed:
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        # 不在白名单：不设 Allow-Origin → 浏览器拦截
    # 无 Origin 头（curl/Postman/服务端）：不设 CORS 头，不影响功能
    return response

# 注册中间件
register_error_handlers(app)
register_request_logger(app)
init_limiter(app)

# 注册 API 蓝图
from gerenjizhang.api.auth import auth_bp
from gerenjizhang.api.bill import bill_bp
from gerenjizhang.api.stats import stats_bp
from gerenjizhang.api.notification import notification_bp
from gerenjizhang.api.category import category_bp

app.register_blueprint(auth_bp)
app.register_blueprint(bill_bp)
app.register_blueprint(stats_bp)
app.register_blueprint(notification_bp)
app.register_blueprint(category_bp)

# 初始化数据库
init_db()

# 启动定时任务（每天 22:00 跑预算检查 + 凌晨 4:00 清理过期通知）
from gerenjizhang.scheduler import init_scheduler
_scheduler = init_scheduler(app)

# 登录失败计数（内存中，生产环境用 Redis）
_login_attempts = {}
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_SECONDS = 300


@app.route('/')
def index():
    """首页"""
    return error_response(401, "请先登录", status_code=401)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """登录接口（兼容旧版）"""
    msg = ""

    # 检查是否被锁定
    ip = request.remote_addr
    if ip in _login_attempts:
        count, first_attempt = _login_attempts[ip]
        if count >= MAX_LOGIN_ATTEMPTS:
            if time.time() - first_attempt < LOCKOUT_SECONDS:
                return error_response(429, "登录失败次数过多，请稍后再试")
            else:
                del _login_attempts[ip]

    if request.method == 'POST':
        from gerenjizhang.db import get_user_by_username
        from werkzeug.security import check_password_hash

        username = request.form.get('username') or (request.json or {}).get('username')
        password = request.form.get('password') or (request.json or {}).get('password')

        user = get_user_by_username(username)
        if user:
            if check_password_hash(user[2], password):
                session['user'] = username
                session['user_id'] = user[0]
                _login_attempts.pop(ip, None)

                return success_response({
                    "token": None,
                    "userinfo": {
                        "id": user[0],
                        "username": username
                    }
                }, message="登录成功")
            else:
                _login_attempts[ip] = (_login_attempts.get(ip, [0, 0])[0] + 1, time.time())
                msg = "账号或密码错误"
        else:
            _login_attempts[ip] = (_login_attempts.get(ip, [0, 0])[0] + 1, time.time())
            msg = "账号或密码错误"

    return error_response(401, msg or "请提供用户名和密码")


@app.route('/logout')
def logout():
    """登出"""
    session.clear()
    return success_response(message="登出成功")


@app.route('/export')
def export():
    """导出账单 CSV"""
    from flask import _get_user_id_from_request
    user_id = session.get('user_id')
    if not user_id:
        return error_response(401, "请先登录", status_code=401)

    year = request.args.get('year', type=int) or datetime.now().year
    month = request.args.get('month', type=int) or datetime.now().month

    start = f"{year}-{month:02d}-01"
    end = f"{year}-{month+1:02d}-01" if month < 12 else f"{year+1}-01-01"

    records = get_records(user_id, start_date=start, end_date=end)

    import csv
    from io import StringIO

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['日期', '类型', '分类', '金额', '备注'])

    for r in records:
        type_text = '收入' if r[3] == 'income' else '支出'
        amount = float(r[2]) if r[2] else 0
        writer.writerow([r[1], type_text, r[4], amount, r[5] or ''])

    csv_content = output.getvalue()
    output.close()

    filename = f"bill_{year}_{month}.csv"
    response = Response(csv_content, mimetype='text/csv')
    response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@app.route('/api/debug/reset-test-data', methods=['POST'])
def reset_test_data():
    """清理测试数据（仅开发环境）"""
    if app.debug:
        from gerenjizhang.db import Database
        try:
            with Database() as db:
                db.c.execute('DELETE FROM bill WHERE amount > 10000')
            return success_response(message="测试数据已清理")
        except Exception as e:
            return error_response(500, f"清理失败: {str(e)}")
    return error_response(403, "仅开发环境可用")


@app.route('/api/health')
def health():
    """健康检查"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    })


# ============ 静态文件（头像上传）============
import os as _os
UPLOAD_ROOT = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), 'uploads')

@app.route('/uploads/<path:filename>')
def serve_upload(filename):
    """服务 uploads 目录的静态文件（头像等）"""
    return send_from_directory(UPLOAD_ROOT, filename)


if __name__ == '__main__':
    # 根据 FLASK_ENV 选择启动方式：
    # - development: Flask 自带 dev server（自动 reload，改代码不用手动重启）
    # - testing / production: waitress（更稳，不挂）
    # 用法：
    #   FLASK_ENV=development python gerenjizhang/app.py   # 开发，自动 reload
    #   FLASK_ENV=production  python gerenjizhang/app.py   # 生产，waitress
    # 默认 development（未设置时）
    env = os.environ.get('FLASK_ENV', 'development')
    host = '0.0.0.0'
    port = 5002

    if env == 'development':
        print(f'[dev] Flask dev server on {host}:{port} (FLASK_ENV=development, auto-reload on)')
        # use_reloader=True → 改代码自动重启（含新增路由/蓝图，debug 模式才有效）
        app.run(host=host, port=port, debug=True, use_reloader=True)
    else:
        from waitress import serve
        print(f'[{env}] waitress on {host}:{port}')
        serve(app, host=host, port=port, threads=4)