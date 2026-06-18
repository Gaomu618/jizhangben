"""
用户服务层
处理用户相关的业务逻辑
"""
from gerenjizhang.models import User
from gerenjizhang.db import (
    get_user_by_username, create_user, get_user_by_openid,
    create_user_with_openid, bind_openid, get_user_by_id
)


class AuthService:
    """用户认证服务"""

    @staticmethod
    def register(username, password):
        """用户注册"""
        # 参数校验
        if not username or not password:
            raise ValueError("用户名和密码不能为空")
        if len(username) < 3:
            raise ValueError("用户名至少3位")
        if len(password) < 6:
            raise ValueError("密码至少6位")

        import re
        if not re.search(r'[A-Za-z]', password) or not re.search(r'[0-9]', password):
            raise ValueError("密码必须包含字母和数字")

        # 检查用户名是否已存在
        existing = get_user_by_username(username)
        if existing:
            raise ValueError("用户名已存在")

        # 创建用户
        user = User(username=username)
        user.set_password(password)

        if create_user(username, user.password_hash):
            return user
        raise ValueError("注册失败")

    @staticmethod
    def login(username, password):
        """用户登录"""
        if not username or not password:
            raise ValueError("用户名和密码不能为空")

        user_data = get_user_by_username(username)
        if not user_data:
            raise ValueError("账号或密码错误")

        user = User(
            id=user_data[0],
            username=user_data[1],
            password_hash=user_data[2],
            openid=user_data[3] if len(user_data) > 3 else ''
        )

        if not user.check_password(password):
            raise ValueError("账号或密码错误")

        return user

    @staticmethod
    def login_by_openid(openid):
        """微信登录"""
        user_data = get_user_by_openid(openid)
        if user_data:
            return User(
                id=user_data['id'],
                username=user_data['username'],
                openid=user_data['openid']
            )
        return None

    @staticmethod
    def register_by_openid(openid, username=None):
        """微信注册"""
        user_data = create_user_with_openid(openid, username)
        if user_data:
            return User(
                id=user_data['id'],
                username=user_data['username'],
                openid=user_data['openid']
            )
        return None

    @staticmethod
    def get_user_by_id(user_id):
        """根据ID获取用户"""
        user_data = get_user_by_id(user_id)
        if user_data:
            return User(
                id=user_data[0],
                username=user_data[1],
                openid=user_data[2] if len(user_data) > 2 else ''
            )
        return None