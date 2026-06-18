"""
数据模型
"""
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


class User:
    """用户模型"""

    def __init__(self, id=None, username='', password_hash='', openid=''):
        self.id = id
        self.username = username
        self.password_hash = password_hash
        self.openid = openid
        self.created_at = datetime.now()

    def set_password(self, password):
        """设置密码（自动哈希）"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'openid': self.openid,
        }


class Bill:
    """账单模型"""

    def __init__(self, id=None, date='', amount=0.0, type_='', category='', note='', user_id=None):
        self.id = id
        self.date = date
        self.amount = amount
        self.type = type_  # income / expense
        self.category = category
        self.note = note
        self.user_id = user_id
        self.created_at = datetime.now()

    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date,
            'amount': float(self.amount),
            'type': self.type,
            'category': self.category,
            'note': self.note or ''
        }


class Budget:
    """预算模型"""

    def __init__(self, id=None, user_id=None, type_='expense', category='', amount=0.0, month=''):
        self.id = id
        self.user_id = user_id
        self.type = type_
        self.category = category
        self.amount = amount
        self.month = month  # YYYY-MM 格式

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'type': self.type,
            'category': self.category,
            'amount': float(self.amount),
            'month': self.month
        }