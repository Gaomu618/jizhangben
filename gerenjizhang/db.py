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
        self.conn = mysql.connector.connect(**DB_CONFIG)
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
                    openid VARCHAR(64) UNIQUE,
                    email VARCHAR(120) DEFAULT NULL,
                    nickname VARCHAR(20) DEFAULT NULL,
                    avatar_url VARCHAR(500) DEFAULT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            # 在线迁移：老库可能没有 email 列
            try:
                db.c.execute('''
                    SELECT COUNT(*) FROM information_schema.columns
                    WHERE table_schema=DATABASE() AND table_name='users' AND column_name='email'
                ''')
                if db.c.fetchone()[0] == 0:
                    db.c.execute('ALTER TABLE users ADD COLUMN email VARCHAR(120) DEFAULT NULL')
                    logger.info("迁移：已为 users 表添加 email 列")
            except Error as e:
                logger.warning(f"检查 email 列失败（可能已存在）: {e}")
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
            db.c.execute('''
                CREATE TABLE IF NOT EXISTS budgets (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    user_id INT NOT NULL,
                    type VARCHAR(10) NOT NULL DEFAULT 'expense',
                    category VARCHAR(20) NOT NULL,
                    amount DECIMAL(10,2) NOT NULL,
                    month VARCHAR(7) NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    UNIQUE KEY unique_budget (user_id, type, category, month)
                )
            ''')
            db.c.execute('''
                CREATE TABLE IF NOT EXISTS import_history (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    user_id INT NOT NULL,
                    source VARCHAR(20) NOT NULL,
                    total_count INT NOT NULL,
                    imported_count INT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
            # 负样本：用户改分类时，记下"这段文本**不**应该归到 X 类"
            # 用于降低智能分类的误判（"美团退款 28.5" 不应该归到"餐饮"）
            db.c.execute('''
                CREATE TABLE IF NOT EXISTS user_memory_negatives (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    user_id INT NOT NULL,
                    keyword VARCHAR(255) NOT NULL,
                    wrong_category VARCHAR(20) NOT NULL,
                    use_count INT NOT NULL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    UNIQUE KEY unique_neg (user_id, keyword, wrong_category),
                    INDEX idx_user (user_id)
                )
            ''')
            # 通知日志：记录"已推过"的提醒，用于每日频率控制
            db.c.execute('''
                CREATE TABLE IF NOT EXISTS notification_log (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    user_id INT NOT NULL,
                    rule_type VARCHAR(32) NOT NULL,
                    triggered_at DATETIME NOT NULL,
                    INDEX idx_user_time (user_id, triggered_at),
                    INDEX idx_time (triggered_at)
                )
            ''')
            # 用户正向分类记忆（之前 save_user_memory 引用但没建表，补上）
            db.c.execute('''
                CREATE TABLE IF NOT EXISTS user_memory (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    user_id INT NOT NULL,
                    keyword VARCHAR(255) NOT NULL,
                    category VARCHAR(20) NOT NULL,
                    type VARCHAR(10) NOT NULL DEFAULT 'expense',
                    use_count INT NOT NULL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    UNIQUE KEY unique_mem (user_id, keyword, category, type),
                    INDEX idx_user (user_id)
                )
            ''')
            # ===== 自定义分类 =====
            db.c.execute('''
                CREATE TABLE IF NOT EXISTS user_category (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    user_id INT NOT NULL,
                    name VARCHAR(20) NOT NULL,
                    is_system TINYINT(1) NOT NULL DEFAULT 0,
                    icon VARCHAR(20) DEFAULT NULL,
                    type VARCHAR(10) NOT NULL DEFAULT 'expense',
                    sort_order INT NOT NULL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    UNIQUE KEY uniq_user_cat (user_id, name)
                )
            ''')
            # ===== 用户分类关键词（用户给自定义分类配的关键词）=====
            db.c.execute('''
                CREATE TABLE IF NOT EXISTS user_category_keyword (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    user_id INT NOT NULL,
                    category_id INT NOT NULL,
                    keyword VARCHAR(50) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (category_id) REFERENCES user_category(id) ON DELETE CASCADE,
                    UNIQUE KEY uniq_cat_kw (category_id, keyword)
                )
            ''')
            # ===== 给老用户 seed 12 个系统分类 =====
            SYSTEM_CATEGORIES = [
                ('餐饮', '🍔', 'expense', 1),
                ('交通', '🚗', 'expense', 2),
                ('购物', '🛒', 'expense', 3),
                ('娱乐', '🎮', 'expense', 4),
                ('居住', '🏠', 'expense', 5),
                ('教育', '📚', 'expense', 6),
                ('医疗', '💊', 'expense', 7),
                ('其他', '📦', 'expense', 8),
                ('工资', '💰', 'income', 9),
                ('奖金', '🎁', 'income', 10),
                ('理财', '📈', 'income', 11),
                ('副业', '💼', 'income', 12),
                ('转账', '🔄', 'expense', 13),
            ]
            db.c.execute('SELECT id FROM users')
            user_ids = [r[0] for r in db.c.fetchall()]
            for uid in user_ids:
                for name, icon, type_, order in SYSTEM_CATEGORIES:
                    db.c.execute('''
                        INSERT IGNORE INTO user_category
                            (user_id, name, is_system, icon, type, sort_order)
                        VALUES (%s, %s, 1, %s, %s, %s)
                    ''', (uid, name, icon, type_, order))
            # ===== 迁移：给已存在的 users 表加 nickname/avatar_url/created_at 列 =====
            # MySQL 8.0+ 支持 IF NOT EXISTS；5.7 不支持。所以先查再决定 ALTER
            try:
                db.c.execute('''
                    SELECT COLUMN_NAME FROM information_schema.COLUMNS
                    WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'users'
                ''')
                existing_cols = {row[0] for row in db.c.fetchall()}
                for col, ddl in [
                    ('nickname', 'ALTER TABLE users ADD COLUMN nickname VARCHAR(20) DEFAULT NULL'),
                    ('avatar_url', 'ALTER TABLE users ADD COLUMN avatar_url VARCHAR(500) DEFAULT NULL'),
                    ('created_at', 'ALTER TABLE users ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
                ]:
                    if col not in existing_cols:
                        db.c.execute(ddl)
                        logger.info(f"迁移：给 users 表添加列 {col}")
            except Error as e:
                logger.error(f"迁移 users 表失败: {e}")
    except Error as e:
        logger.error(f"初始化数据库错误: {e}")


def update_user_profile(user_id, nickname=None, avatar_url=None):
    """
    更新用户资料。只更新传入的非 None 字段。
    @returns True/False
    """
    fields = []
    params = []
    if nickname is not None:
        fields.append('nickname=%s')
        params.append(nickname)
    if avatar_url is not None:
        fields.append('avatar_url=%s')
        params.append(avatar_url)
    if not fields:
        return False
    params.append(user_id)
    try:
        with Database() as db:
            db.c.execute(f'UPDATE users SET {", ".join(fields)} WHERE id=%s', tuple(params))
            db.conn.commit()
            return db.c.rowcount > 0 or True
    except Error as e:
        logger.error(f"更新用户资料失败: {e}")
        return False


def add_record(date, amount, type_, category, note, user_id):
    # 基础输入校验
    if amount is None or float(amount) <= 0:
        raise ValueError(f"金额必须大于 0（当前: {amount}）")
    if type_ not in ('income', 'expense'):
        raise ValueError(f"type 必须是 income 或 expense（当前: {type_!r}）")
    if not category or not category.strip():
        raise ValueError("分类不能为空")

    try:
        with Database() as db:
            db.c.execute('''
                INSERT INTO bill (date, amount, type, category, note, user_id)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (date, amount, type_, category, note, user_id))
            return db.c.lastrowid  # 返回新 ID，方便调用方
    except Error as e:
        logger.error(f"添加记录错误: {e}")
        raise  # 让上层 API 知道失败


def add_record_batch(records, user_id):
    """批量添加记录 records: [(date, amount, type, category, note), ...]"""
    if not records:
        return 0
    try:
        with Database() as db:
            db.c.executemany('''
                INSERT INTO bill (date, amount, type, category, note, user_id)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', [(r[0], r[1], r[2], r[3], r[4], user_id) for r in records])
            return db.c.rowcount
    except Error as e:
        logger.error(f"批量添加记录错误: {e}")
        return 0


def check_record_exists(user_id, date, amount, type_, category, note):
    """检查记录是否已存在（用于导入去重）"""
    try:
        with Database() as db:
            db.c.execute('''
                SELECT id FROM bill
                WHERE user_id=%s AND date=%s AND amount=%s AND type=%s AND category=%s AND (note=%s OR (note IS NULL AND %s IS NULL))
            ''', (user_id, date, amount, type_, category, note, note))
            return db.c.fetchone() is not None
    except Error as e:
        logger.error(f"检查记录是否存在错误: {e}")
        return False


def get_existing_record_hashes(user_id):
    """获取用户所有记录的hash集合，用于快速去重"""
    try:
        with Database() as db:
            db.c.execute('SELECT date, amount, type, category, COALESCE(note, "") FROM bill WHERE user_id=%s', (user_id,))
            rows = db.c.fetchall()
            # 统一金额格式：去掉小数点后的尾随 0，避免 str(100.0) != str(Decimal('100.00'))
            def _amt(s):
                return f"{float(s):g}"
            return set(hash((r[0], _amt(r[1]), r[2], r[3], r[4])) for r in rows)
    except Error as e:
        logger.error(f"获取记录hash错误: {e}")
        return set()


def save_import_history(user_id, source, count, imported_count):
    """保存导入历史"""
    try:
        with Database() as db:
            db.c.execute('''
                INSERT INTO import_history (user_id, source, total_count, imported_count)
                VALUES (%s, %s, %s, %s)
            ''', (user_id, source, count, imported_count))
    except Error as e:
        logger.error(f"保存导入历史错误: {e}")


# ==================== 负样本学习 ====================
# 用户改分类时，记住"这段文本**不**应该归到 X 类"
# 比如用户把"美团退款 28.5"从"餐饮"改到"其他"，我们就记：
#   keyword="美团 退款"（清理后）, wrong_category="餐饮"
# 下次再分类时，如果分类器想归到"餐饮"，看到这条负样本，会降权
def save_negative_memory(user_id, keyword, wrong_category):
    """保存一条负样本（upsert：已存在则 use_count+1）"""
    if not user_id or not keyword or not wrong_category:
        return False
    try:
        with Database() as db:
            db.c.execute('''
                INSERT INTO user_memory_negatives (user_id, keyword, wrong_category, use_count)
                VALUES (%s, %s, %s, 1)
                ON DUPLICATE KEY UPDATE use_count = use_count + 1
            ''', (user_id, keyword, wrong_category))
            db.conn.commit()
            return True
    except Error as e:
        logger.error(f"保存负样本失败: {e}")
        return False


def get_user_negatives(user_id):
    """获取用户所有负样本 {keyword: {wrong_category: use_count}}"""
    if not user_id:
        return {}
    try:
        with Database() as db:
            db.c.execute(
                'SELECT keyword, wrong_category, use_count FROM user_memory_negatives WHERE user_id=%s',
                (user_id,)
            )
            rows = db.fetchall() if hasattr(db, 'fetchall') else db.c.fetchall()
            # 结构：{ keyword: { wrong_category: use_count } }
            result = {}
            for kw, cat, cnt in rows:
                result.setdefault(kw, {})[cat] = cnt
            return result
    except Error as e:
        logger.error(f"查询负样本失败: {e}")
        return {}


def clear_user_negatives(user_id):
    """清空某用户的所有负样本，返回删除条数"""
    if not user_id:
        return 0
    try:
        with Database() as db:
            db.c.execute('DELETE FROM user_memory_negatives WHERE user_id=%s', (user_id,))
            return db.c.rowcount
    except Error as e:
        logger.error(f"清空负样本失败: {e}")
        return 0


def increment_negative_use(user_id, keyword, wrong_category):
    """命中负样本时引用计数 +1（异步、低优先级）"""
    try:
        with Database() as db:
            db.c.execute('''
                UPDATE user_memory_negatives SET use_count = use_count + 1
                WHERE user_id=%s AND keyword=%s AND wrong_category=%s
            ''', (user_id, keyword, wrong_category))
    except Error as e:
        logger.debug(f"更新负样本计数失败（可忽略）: {e}")


# ==================== 通知日志 ====================
# 用来做"同规则每天最多推 1 次"的频率控制
def has_notification_today(user_id, rule_type):
    """检查今天是否已经推送过某规则（用于频率控制）"""
    if not user_id or not rule_type:
        return False
    try:
        with Database() as db:
            db.c.execute('''
                SELECT COUNT(*) FROM notification_log
                WHERE user_id=%s AND rule_type=%s AND DATE(triggered_at) = CURDATE()
            ''', (user_id, rule_type))
            row = db.c.fetchone()
            return bool(row and row[0] > 0)
    except Error as e:
        logger.error(f"检查通知日志失败: {e}")
        return False


def save_notification_log(user_id, rule_type):
    """记录一次通知推送（user_id, rule_type, NOW）"""
    if not user_id or not rule_type:
        return False
    try:
        with Database() as db:
            db.c.execute('''
                INSERT INTO notification_log (user_id, rule_type, triggered_at)
                VALUES (%s, %s, NOW())
            ''', (user_id, rule_type))
            db.conn.commit()
            return True
    except Error as e:
        logger.error(f"保存通知日志失败: {e}")
        return False


def cleanup_old_notifications(days=30):
    """清理 N 天前的通知日志（防止表无限增长）"""
    try:
        with Database() as db:
            db.c.execute(
                'DELETE FROM notification_log WHERE triggered_at < DATE_SUB(NOW(), INTERVAL %s DAY)',
                (days,)
            )
            deleted = db.c.rowcount
            if deleted > 0:
                logger.info(f"清理了 {deleted} 条过期通知日志")
            return deleted
    except Error as e:
        logger.error(f"清理通知日志失败: {e}")
        return 0


def edit_record(record_id, date, amount, type_, category, note, user_id):
    """返回受影响行数：0=记录不存在/已删/无权编辑,1=成功,-1=出错"""
    try:
        with Database() as db:
            db.c.execute('''
                UPDATE bill SET date=%s, amount=%s, type=%s, category=%s, note=%s
                WHERE id=%s AND user_id=%s AND deleted_at IS NULL
            ''', (date, amount, type_, category, note, record_id, user_id))
            return db.c.rowcount
    except Error as e:
        logger.error(f"修改记录错误: {e}")
        return -1


def delete_record(record_id, user_id):
    """软删除：标记 deleted_at，不真正删除数据
    返回受影响行数：0=记录不存在/已删/无权删,1=成功,-1=出错
    """
    try:
        with Database() as db:
            db.c.execute(
                'UPDATE bill SET deleted_at=NOW() WHERE id=%s AND user_id=%s AND deleted_at IS NULL',
                (record_id, user_id)
            )
            return db.c.rowcount
    except Error as e:
        logger.error(f"软删除记录错误: {e}")
        return -1


def restore_record(record_id, user_id):
    """从回收站还原"""
    try:
        with Database() as db:
            db.c.execute(
                'UPDATE bill SET deleted_at=NULL WHERE id=%s AND user_id=%s AND deleted_at IS NOT NULL',
                (record_id, user_id)
            )
            return db.c.rowcount > 0
    except Error as e:
        logger.error(f"还原记录错误: {e}")
        return False


def purge_record(record_id, user_id):
    """永久删除：真正从数据库删除（回收站用）"""
    try:
        with Database() as db:
            db.c.execute(
                'DELETE FROM bill WHERE id=%s AND user_id=%s AND deleted_at IS NOT NULL',
                (record_id, user_id)
            )
            return db.c.rowcount > 0
    except Error as e:
        logger.error(f"永久删除错误: {e}")
        return False


def get_trash_records(user_id, limit=None, offset=None):
    """获取回收站记录（deleted_at 不为空）"""
    try:
        with Database() as db:
            query = 'SELECT * FROM bill WHERE user_id=%s AND deleted_at IS NOT NULL ORDER BY deleted_at DESC'
            params = [user_id]
            if limit is not None:
                query += f' LIMIT {int(limit)}'
                if offset is not None:
                    query += f' OFFSET {int(offset)}'
            db.c.execute(query, params)
            return db.c.fetchall()
    except Error as e:
        logger.error(f"查询回收站错误: {e}")
        return []


def count_trash(user_id):
    """回收站记录数"""
    try:
        with Database() as db:
            db.c.execute('SELECT COUNT(*) FROM bill WHERE user_id=%s AND deleted_at IS NOT NULL', (user_id,))
            return db.c.fetchone()[0] or 0
    except Error as e:
        logger.error(f"统计回收站错误: {e}")
        return 0


def empty_trash(user_id):
    """清空回收站：永久删除所有软删除的记录"""
    try:
        with Database() as db:
            db.c.execute('DELETE FROM bill WHERE user_id=%s AND deleted_at IS NOT NULL', (user_id,))
            return db.c.rowcount
    except Error as e:
        logger.error(f"清空回收站错误: {e}")
        return 0


def cleanup_old_trash(days=30):
    """清理超过 N 天的回收站记录（全局任务，无需 user_id）"""
    try:
        with Database() as db:
            db.c.execute(
                'DELETE FROM bill WHERE deleted_at IS NOT NULL AND deleted_at < (NOW() - INTERVAL %s DAY)',
                (days,)
            )
            deleted = db.c.rowcount
            db.conn.commit()
            if deleted:
                logger.info(f"自动清理了 {deleted} 条超过 {days} 天的回收站记录")
            return deleted
    except Error as e:
        logger.error(f"自动清理回收站错误: {e}")
        return 0


def get_budgets(user_id, month):
    try:
        with Database() as db:
            db.c.execute('SELECT category, amount FROM budgets WHERE user_id=%s AND month=%s', (user_id, month))
            return db.c.fetchall()
    except Error as e:
        logger.error(f"查询预算错误: {e}")
        return []


def save_budget(user_id, type_, category, amount, month):
    try:
        with Database() as db:
            db.c.execute('''
                INSERT INTO budgets (user_id, type, category, amount, month)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE amount=%s
            ''', (user_id, type_, category, amount, month, amount))
    except Error as e:
        logger.error(f"保存预算错误: {e}")


def delete_budget(user_id, category, month):
    """返回受影响行数：0=预算不存在/无权删,1=成功,-1=出错"""
    try:
        with Database() as db:
            db.c.execute('''
                DELETE FROM budgets WHERE user_id=%s AND category=%s AND month=%s
            ''', (user_id, category, month))
            return db.c.rowcount
    except Error as e:
        logger.error(f"删除预算错误: {e}")
        return -1


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
            query = "SELECT * FROM bill WHERE user_id=%s AND deleted_at IS NULL"
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

            query += " ORDER BY date DESC, id DESC"
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
            # 注意：必须排除 deleted_at，否则软删的记录还会被算进总额
            db.c.execute(
                'SELECT IFNULL(SUM(amount),0) FROM bill WHERE user_id=%s AND date>=%s AND date<%s AND type="income" AND deleted_at IS NULL',
                (user_id, start, end))
            income = db.c.fetchone()[0] or 0

            db.c.execute(
                'SELECT IFNULL(SUM(amount),0) FROM bill WHERE user_id=%s AND date>=%s AND date<%s AND type="expense" AND deleted_at IS NULL',
                (user_id, start, end))
            expense = db.c.fetchone()[0] or 0

            return income, expense
    except Error as e:
        logger.error(f"月度统计错误: {e}")
        return 0, 0


def get_category_summary(user_id, year=None, month=None, bill_type=None, start_date=None, end_date=None):
    """按分类汇总账单金额。
    两种调用方式：
      1) year + month: 当月汇总
      2) start_date + end_date: 自定义区间
    bill_type: 'income' | 'expense' | None（不区分）
    返回: [(category, amount, type), ...]
    """
    if start_date is None or end_date is None:
        if year is None or month is None:
            now = datetime.now()
            year = year or now.year
            month = month or now.month
        start = f"{year}-{month:02d}-01"
        end = f"{year}-{month+1:02d}-01" if month < 12 else f"{year+1}-01-01"
    else:
        start, end = start_date, end_date

    try:
        with Database() as db:
            if bill_type:
                db.c.execute('''
                    SELECT category, SUM(amount), type FROM bill
                    WHERE user_id=%s AND date>=%s AND date<%s AND type=%s AND deleted_at IS NULL
                    GROUP BY category
                    ORDER BY SUM(amount) DESC
                ''', (user_id, start, end, bill_type))
            else:
                db.c.execute('''
                    SELECT category, SUM(amount), type FROM bill
                    WHERE user_id=%s AND date>=%s AND date<%s AND deleted_at IS NULL
                    GROUP BY type, category
                    ORDER BY type, SUM(amount) DESC
                ''', (user_id, start, end))
            return db.c.fetchall()
    except Error as e:
        logger.error(f"分类统计错误: {e}")
        return []


def get_summary(user_id, start_date, end_date):
    """统计区间内汇总：日均、最大单笔、最高频分类、笔数（不含已删除）"""
    try:
        with Database() as db:
            # 总收入/总支出（必须排除 deleted_at）
            db.c.execute('''
                SELECT type, IFNULL(SUM(amount),0), COUNT(*) FROM bill
                WHERE user_id=%s AND date>=%s AND date<%s AND deleted_at IS NULL
                GROUP BY type
            ''', (user_id, start_date, end_date))
            type_stats = {row[0]: {'total': float(row[1]), 'count': row[2]} for row in db.c.fetchall()}

            # 最大单笔支出（也排除已删除）
            db.c.execute('''
                SELECT date, amount, category, note FROM bill
                WHERE user_id=%s AND date>=%s AND date<%s AND type='expense' AND deleted_at IS NULL
                ORDER BY amount DESC LIMIT 1
            ''', (user_id, start_date, end_date))
            max_expense = db.c.fetchone()

            # 最高频分类（按笔数）
            db.c.execute('''
                SELECT category, COUNT(*) as cnt, SUM(amount) as total FROM bill
                WHERE user_id=%s AND date>=%s AND date<%s AND type='expense' AND deleted_at IS NULL
                GROUP BY category ORDER BY cnt DESC LIMIT 1
            ''', (user_id, start_date, end_date))
            top_category = db.c.fetchone()

            # 计算天数
            from datetime import datetime
            d1 = datetime.strptime(start_date, '%Y-%m-%d')
            d2 = datetime.strptime(end_date, '%Y-%m-%d')
            days = max((d2 - d1).days, 1)

            income = type_stats.get('income', {'total': 0, 'count': 0})
            expense = type_stats.get('expense', {'total': 0, 'count': 0})

            return {
                'income': income['total'],
                'expense': expense['total'],
                'balance': income['total'] - expense['total'],
                'income_count': income['count'],
                'expense_count': expense['count'],
                'avg_daily_expense': round(expense['total'] / days, 2),
                'days': days,
                'max_expense': {
                    'date': max_expense[0] if max_expense else None,
                    'amount': float(max_expense[1]) if max_expense else 0,
                    'category': max_expense[2] if max_expense else None,
                    'note': max_expense[3] if max_expense else None,
                } if max_expense else None,
                'top_category': {
                    'name': top_category[0],
                    'count': top_category[1],
                    'total': float(top_category[2]),
                } if top_category else None,
            }
    except Error as e:
        logger.error(f"汇总统计错误: {e}")
        return None


def get_daily_expense(user_id, start_date, end_date):
    """区间内每日支出和笔数（用于热力图，不含已删除）"""
    try:
        with Database() as db:
            db.c.execute('''
                SELECT date, SUM(amount), COUNT(*) FROM bill
                WHERE user_id=%s AND date>=%s AND date<%s AND type='expense' AND deleted_at IS NULL
                GROUP BY date
            ''', (user_id, start_date, end_date))
            return [
                {'date': row[0], 'amount': float(row[1]), 'count': row[2]}
                for row in db.c.fetchall()
            ]
    except Error as e:
        logger.error(f"每日统计错误: {e}")
        return []


def get_top_records(user_id, start_date, end_date, bill_type='expense', limit=5):
    """区间内金额最大的 N 条记录（不含已删除）"""
    try:
        with Database() as db:
            db.c.execute('''
                SELECT id, date, amount, category, note FROM bill
                WHERE user_id=%s AND date>=%s AND date<%s AND type=%s AND deleted_at IS NULL
                ORDER BY amount DESC LIMIT %s
            ''', (user_id, start_date, end_date, bill_type, limit))
            return [
                {'id': r[0], 'date': r[1], 'amount': float(r[2]), 'category': r[3], 'note': r[4] or ''}
                for r in db.c.fetchall()
            ]
    except Error as e:
        logger.error(f"排行查询错误: {e}")
        return []


def get_user_by_username(username):
    try:
        with Database() as db:
            db.c.execute("SELECT id, username, password FROM users WHERE username=%s", (username,))
            return db.c.fetchone()
    except Error as e:
        logger.error(f"查询用户错误: {e}")
        return None


def create_user(username, password, email=None):
    """注册用户。email 可选,但传了就要存(用户期望注册的字段都被保留)"""
    try:
        with Database() as db:
            db.c.execute(
                "INSERT INTO users (username, password, email) VALUES (%s, %s, %s)",
                (username, password, email or None))
            return True
    except Error as e:
        logger.error(f"创建用户错误: {e}")
        return False


def get_user_by_email(email):
    """通过邮箱查用户(用于注册时查重)"""
    try:
        with Database() as db:
            db.c.execute("SELECT id, username, email FROM users WHERE email=%s", (email,))
            return db.c.fetchone()
    except Error as e:
        logger.error(f"按邮箱查用户错误: {e}")
        return None


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
    """查用户完整资料（含 nickname / avatar_url）。返回 dict 或 None。"""
    try:
        with Database() as db:
            db.c.execute(
                "SELECT id, username, openid, email, nickname, avatar_url FROM users WHERE id=%s",
                (user_id,)
            )
            row = db.c.fetchone()
            if not row:
                return None
            return {
                'id': row[0],
                'username': row[1] or '',
                'openid': row[2] or '',
                'email': row[3] or '',
                'nickname': row[4] or '',
                'avatar_url': row[5] or ''
            }
    except Error as e:
        logger.error(f"查询用户错误: {e}")
        return None


# ==================== 用户分类记忆（持久化） ====================
def save_user_memory(user_id, keyword, category, bill_type='expense'):
    """保存或更新用户的一条分类记忆（upsert）"""
    if not keyword or not category or not user_id:
        return False
    try:
        with Database() as db:
            # 先查是否已存在 → 累加 use_count
            db.c.execute(
                'SELECT id, use_count FROM user_classify_memory WHERE user_id=%s AND keyword=%s',
                (user_id, keyword)
            )
            row = db.c.fetchone()
            if row:
                db.c.execute(
                    'UPDATE user_classify_memory SET category=%s, type=%s, use_count=use_count+1 WHERE id=%s',
                    (category, bill_type, row[0])
                )
            else:
                db.c.execute(
                    'INSERT INTO user_classify_memory (user_id, keyword, category, type, use_count) VALUES (%s, %s, %s, %s, 1)',
                    (user_id, keyword, category, bill_type)
                )
            db.conn.commit()
            return True
    except Error as e:
        logger.error(f"保存用户记忆错误: {e}")
        return False


def get_user_memory(user_id, limit=500):
    """获取用户的所有分类记忆（按 use_count 倒序）"""
    try:
        with Database() as db:
            db.c.execute('''
                SELECT id, keyword, category, type, use_count, created_at, updated_at
                FROM user_classify_memory
                WHERE user_id=%s
                ORDER BY use_count DESC, updated_at DESC
                LIMIT %s
            ''', (user_id, int(limit)))
            return [
                {
                    'id': r[0],
                    'keyword': r[1],
                    'category': r[2],
                    'type': r[3],
                    'use_count': r[4],
                    'created_at': r[5].isoformat() if r[5] else None,
                    'updated_at': r[6].isoformat() if r[6] else None,
                }
                for r in db.c.fetchall()
            ]
    except Error as e:
        logger.error(f"查询用户记忆错误: {e}")
        return []


def get_user_memory_dict(user_id):
    """获取用户记忆的字典形式 {keyword: (category, type)}（给分类用）"""
    memories = get_user_memory(user_id, limit=1000)
    return {m['keyword']: (m['category'], m['type']) for m in memories}


def delete_user_memory(user_id, memory_id):
    """删除某条记忆"""
    try:
        with Database() as db:
            db.c.execute(
                'DELETE FROM user_classify_memory WHERE user_id=%s AND id=%s',
                (user_id, memory_id)
            )
            db.conn.commit()
            return db.c.rowcount > 0
    except Error as e:
        logger.error(f"删除用户记忆错误: {e}")
        return False


def clear_user_memory(user_id):
    """清空某用户的所有记忆"""
    try:
        with Database() as db:
            db.c.execute('DELETE FROM user_classify_memory WHERE user_id=%s', (user_id,))
            db.conn.commit()
            return db.c.rowcount
    except Error as e:
        logger.error(f"清空用户记忆错误: {e}")
        return 0


def increment_memory_use(user_id, keyword):
    """分类时引用了某条记忆 → use_count+1（异步/可选）"""
    try:
        with Database() as db:
            db.c.execute(
                'UPDATE user_classify_memory SET use_count=use_count+1 WHERE user_id=%s AND keyword=%s',
                (user_id, keyword)
            )
            db.conn.commit()
    except Error:
        pass  # 静默失败


# ================ 自定义分类 CRUD ================

def list_user_categories(user_id):
    """列出用户所有分类（系统 + 自定义，按 sort_order 排序）"""
    try:
        with Database() as db:
            db.c.execute('''
                SELECT id, name, is_system, icon, type, sort_order, created_at
                FROM user_category
                WHERE user_id = %s
                ORDER BY is_system DESC, sort_order ASC, id ASC
            ''', (user_id,))
            cols = ['id', 'name', 'is_system', 'icon', 'type', 'sort_order', 'created_at']
            return [dict(zip(cols, row)) for row in db.c.fetchall()]
    except Error as e:
        logger.error(f"列出用户分类错误: {e}")
        return []


def get_user_category(user_id, name):
    """按 name 查单个分类（用于分类器集成）"""
    try:
        with Database() as db:
            db.c.execute('''
                SELECT id, name, is_system, icon, type FROM user_category
                WHERE user_id = %s AND name = %s
            ''', (user_id, name))
            row = db.c.fetchone()
            if not row:
                return None
            return {'id': row[0], 'name': row[1], 'is_system': row[2], 'icon': row[3], 'type': row[4]}
    except Error as e:
        logger.error(f"查分类错误: {e}")
        return None


def get_user_category_by_id(cat_id, user_id):
    """按 id 查（权限校验用）"""
    try:
        with Database() as db:
            db.c.execute('''
                SELECT id, name, is_system, icon, type FROM user_category
                WHERE id = %s AND user_id = %s
            ''', (cat_id, user_id))
            row = db.c.fetchone()
            if not row:
                return None
            return {'id': row[0], 'name': row[1], 'is_system': row[2], 'icon': row[3], 'type': row[4]}
    except Error as e:
        logger.error(f"查分类错误: {e}")
        return None


def create_user_category(user_id, name, icon=None, type_='expense'):
    """新增自定义分类（最多 50 个 / 用户）"""
    if not name or not name.strip():
        return None, '分类名不能为空'
    name = name.strip()[:20]  # 限制 20 字符
    if not name:
        return None, '分类名不能为空'
    try:
        with Database() as db:
            # 上限校验
            db.c.execute('SELECT COUNT(*) FROM user_category WHERE user_id = %s', (user_id,))
            if db.c.fetchone()[0] >= 50:
                return None, '自定义分类已达上限（50 个）'
            # 重名校验
            db.c.execute(
                'SELECT id FROM user_category WHERE user_id = %s AND name = %s',
                (user_id, name)
            )
            if db.c.fetchone():
                return None, '已存在同名分类'
            # 新增
            db.c.execute('''
                INSERT INTO user_category (user_id, name, is_system, icon, type)
                VALUES (%s, %s, 0, %s, %s)
            ''', (user_id, name, icon, type_))
            cat_id = db.c.lastrowid
            db.conn.commit()
            return {'id': cat_id, 'name': name, 'is_system': 0, 'icon': icon, 'type': type_}, None
    except Error as e:
        logger.error(f"新增分类错误: {e}")
        return None, str(e)


def delete_user_category(user_id, cat_id):
    """删除分类（仅自定义可删，账单保留 category 字符串）"""
    try:
        with Database() as db:
            # 权限 + 系统分类校验
            db.c.execute(
                'SELECT is_system, name FROM user_category WHERE id = %s AND user_id = %s',
                (cat_id, user_id)
            )
            row = db.c.fetchone()
            if not row:
                return False, '分类不存在'
            if row[0] == 1:
                return False, '系统分类不可删除'
            # 删除（外键级联会带走 category_keyword）
            db.c.execute('DELETE FROM user_category WHERE id = %s AND user_id = %s', (cat_id, user_id))
            db.conn.commit()
            return True, None
    except Error as e:
        logger.error(f"删除分类错误: {e}")
        return False, str(e)


def list_user_category_keywords(user_id, cat_id):
    """列出某分类的所有关键词"""
    try:
        with Database() as db:
            db.c.execute('''
                SELECT id, keyword, created_at FROM user_category_keyword
                WHERE user_id = %s AND category_id = %s
                ORDER BY id
            ''', (user_id, cat_id))
            cols = ['id', 'keyword', 'created_at']
            return [dict(zip(cols, row)) for row in db.c.fetchall()]
    except Error as e:
        logger.error(f"列分类关键词错误: {e}")
        return []


def add_user_category_keyword(user_id, cat_id, keyword):
    """给某分类加关键词（最多 200 词 / 分类）"""
    keyword = (keyword or '').strip()[:50]
    if not keyword:
        return None, '关键词不能为空'
    try:
        with Database() as db:
            # 上限校验
            db.c.execute(
                'SELECT COUNT(*) FROM user_category_keyword WHERE category_id = %s',
                (cat_id,)
            )
            if db.c.fetchone()[0] >= 200:
                return None, '关键词已达上限（200 个）'
            # 重复校验
            db.c.execute(
                'SELECT id FROM user_category_keyword WHERE category_id = %s AND keyword = %s',
                (cat_id, keyword)
            )
            if db.c.fetchone():
                return None, '已存在相同关键词'
            # 插入
            db.c.execute('''
                INSERT INTO user_category_keyword (user_id, category_id, keyword)
                VALUES (%s, %s, %s)
            ''', (user_id, cat_id, keyword))
            kw_id = db.c.lastrowid
            db.conn.commit()
            return {'id': kw_id, 'keyword': keyword}, None
    except Error as e:
        logger.error(f"加关键词错误: {e}")
        return None, str(e)


def delete_user_category_keyword(user_id, kw_id):
    """删一个关键词"""
    try:
        with Database() as db:
            db.c.execute(
                'DELETE FROM user_category_keyword WHERE id = %s AND user_id = %s',
                (kw_id, user_id)
            )
            db.conn.commit()
            return db.c.rowcount > 0
    except Error as e:
        logger.error(f"删关键词错误: {e}")
        return False


def get_user_keywords_for_classifier(user_id):
    """分类器用：拉用户所有自定义分类 + 关键词，返回 {keyword: {category, type}}"""
    try:
        with Database() as db:
            db.c.execute('''
                SELECT k.keyword, c.name, c.type
                FROM user_category_keyword k
                JOIN user_category c ON k.category_id = c.id
                WHERE k.user_id = %s
            ''', (user_id,))
            result = {}
            for kw, cat, type_ in db.c.fetchall():
                if kw not in result:  # 第一个匹配的分类胜出
                    result[kw] = {'category': cat, 'type': type_}
            return result
    except Error as e:
        logger.error(f"拉分类关键词错误: {e}")
        return {}
