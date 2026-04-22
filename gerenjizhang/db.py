# db.py - 统一数据库模块
import mysql.connector
from mysql.connector import Error
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "jizhangapp",
    "charset": "utf8mb4"
}


class Database:
    def __init__(self):
        self.conn = None
        self.c = None

    def __enter__(self):
        self.conn = mysql.connector.connect(pool_name="jizhang_pool", pool_size=5, **DB_CONFIG)
        self.c = self.conn.cursor()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.c:
            self.c.close()
        if self.conn:
            if exc_type is None:
                self.conn.commit()
            else:
                self.conn.rollback()
            self.conn.close()
        return False


def init_db():
    try:
        with Database() as db:
            db.c.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    username VARCHAR(50) UNIQUE,
                    password VARCHAR(255),
                    openid VARCHAR(64) UNIQUE
                )
            ''')
            db.c.execute('''
                CREATE TABLE IF NOT EXISTS bill (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    date VARCHAR(20) NOT NULL,
                    amount DECIMAL(10,2) NOT NULL,
                    type VARCHAR(10) NOT NULL,
                    category VARCHAR(20) NOT NULL,
                    note TEXT,
                    user_id INT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
    except Error as e:
        logger.error(f"初始化数据库错误: {e}")


def add_record(date, amount, type_, category, note, user_id):
    try:
        with Database() as db:
            db.c.execute('''
                INSERT INTO bill (date, amount, type, category, note, user_id)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (date, amount, type_, category, note, user_id))
    except Error as e:
        logger.error(f"添加记录错误: {e}")


def edit_record(record_id, date, amount, type_, category, note, user_id):
    try:
        with Database() as db:
            db.c.execute('''
                UPDATE bill SET date=%s, amount=%s, type=%s, category=%s, note=%s
                WHERE id=%s AND user_id=%s
            ''', (date, amount, type_, category, note, record_id, user_id))
    except Error as e:
        logger.error(f"修改记录错误: {e}")


def delete_record(record_id, user_id):
    try:
        with Database() as db:
            db.c.execute('DELETE FROM bill WHERE id=%s AND user_id=%s', (record_id, user_id))
    except Error as e:
        logger.error(f"删除记录错误: {e}")


def get_record_by_id(record_id, user_id):
    try:
        with Database() as db:
            db.c.execute('SELECT * FROM bill WHERE id=%s AND user_id=%s', (record_id, user_id))
            return db.c.fetchone()
    except Error as e:
        logger.error(f"查询单条记录错误: {e}")
        return None


def get_records(user_id, start_date=None, end_date=None, type_filter=None, category_filter=None, limit=None, offset=None):
    try:
        with Database() as db:
            query = "SELECT * FROM bill WHERE user_id=%s"
            params = [user_id]

            if start_date:
                query += " AND date >= %s"
                params.append(start_date)
            if end_date:
                query += " AND date <= %s"
                params.append(end_date)
            if type_filter:
                query += " AND type = %s"
                params.append(type_filter)
            if category_filter:
                query += " AND category = %s"
                params.append(category_filter)

            query += " ORDER BY date DESC"
            if limit is not None:
                query += f" LIMIT {int(limit)}"
                if offset is not None:
                    query += f" OFFSET {int(offset)}"

            db.c.execute(query, params)
            return db.c.fetchall()
    except Error as e:
        logger.error(f"查询记录错误: {e}")
        return []


def get_monthly_summary(user_id, year, month):
    start = f"{year}-{month:02d}-01"
    end = f"{year}-{month+1:02d}-01" if month < 12 else f"{year+1}-01-01"

    try:
        with Database() as db:
            db.c.execute(
                'SELECT IFNULL(SUM(amount),0) FROM bill WHERE user_id=%s AND date>=%s AND date<%s AND type="income"',
                (user_id, start, end))
            income = db.c.fetchone()[0] or 0

            db.c.execute(
                'SELECT IFNULL(SUM(amount),0) FROM bill WHERE user_id=%s AND date>=%s AND date<%s AND type="expense"',
                (user_id, start, end))
            expense = db.c.fetchone()[0] or 0

            return income, expense
    except Error as e:
        logger.error(f"月度统计错误: {e}")
        return 0, 0


def get_category_summary(user_id, year, month):
    start = f"{year}-{month:02d}-01"
    end = f"{year}-{month+1:02d}-01" if month < 12 else f"{year+1}-01-01"

    try:
        with Database() as db:
            db.c.execute('''
                SELECT category, SUM(amount) FROM bill
                WHERE user_id=%s AND date>=%s AND date<%s AND type="expense"
                GROUP BY category
            ''', (user_id, start, end))
            return db.c.fetchall()
    except Error as e:
        logger.error(f"分类统计错误: {e}")
        return []


def get_user_by_username(username):
    try:
        with Database() as db:
            db.c.execute("SELECT id, username, password FROM users WHERE username=%s", (username,))
            return db.c.fetchone()
    except Error as e:
        logger.error(f"查询用户错误: {e}")
        return None


def create_user(username, password):
    try:
        with Database() as db:
            db.c.execute(
                "INSERT INTO users (username, password) VALUES (%s, %s)",
                (username, password))
            return True
    except Error as e:
        logger.error(f"创建用户错误: {e}")
        return False


def get_user_by_openid(openid):
    try:
        with Database() as db:
            db.c.execute("SELECT id, username, openid FROM users WHERE openid=%s", (openid,))
            row = db.c.fetchone()
            if row:
                return {"id": row[0], "username": row[1], "openid": row[2]}
            return None
    except Error as e:
        logger.error(f"查询用户错误: {e}")
        return None


def create_user_with_openid(openid, username=None):
    try:
        with Database() as db:
            db.c.execute(
                "INSERT INTO users (username, password, openid) VALUES (%s, %s, %s)",
                (username or f"wx_{openid[:8]}", "", openid))
            return {"id": db.c.lastrowid, "username": username or f"wx_{openid[:8]}", "openid": openid}
    except Error as e:
        logger.error(f"创建微信用户错误: {e}")
        return None


def bind_openid(user_id, openid):
    try:
        with Database() as db:
            db.c.execute("UPDATE users SET openid=%s WHERE id=%s", (openid, user_id))
            return True
    except Error as e:
        logger.error(f"绑定openid错误: {e}")
        return False


def get_user_by_id(user_id):
    try:
        with Database() as db:
            db.c.execute("SELECT id, username, openid FROM users WHERE id=%s", (user_id,))
            return db.c.fetchone()
    except Error as e:
        logger.error(f"查询用户错误: {e}")
        return None
