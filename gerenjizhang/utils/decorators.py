from functools import wraps
from flask import request, session
from gerenjizhang.utils.response import error_response
from gerenjizhang.utils.jwt_auth import decode_token, InvalidTokenError, encode_token

# ==================== Token 工具(JWT 无状态) ====================
# 旧 API 兼容:旧代码用 secrets.token_hex(32) 生成随机字符串 + set_token 注册
# 现在统一用 JWT,set_token(user_id) → 返回 JWT token 字符串
# 旧调用 set_token(token, user_id) 会被识别为「旧用法」,返回原 token 让老代码不挂
def set_token(*args, **kwargs):
    """生成/注册 token(兼容两种调用风格)
    新用法:set_token(user_id)            → 返回 JWT token
    旧用法:set_token(token_str, user_id)  → 直接返回原 token(老 auth.py 的随机 token)
    """
    if len(args) >= 1 and isinstance(args[0], int):
        # 新风格:传 user_id
        return encode_token(args[0])
    # 旧风格:第一个是 token 字符串,直接返回(避免立即报错,先让后端起来)
    if len(args) >= 1 and isinstance(args[0], str):
        return args[0]
    return None

def remove_token(token):
    """JWT 无状态,客户端丢 token 即失效。这里 no-op 仅为接口兼容。"""
    return None

def get_user_id_by_token(token):
    """从 token 字符串解析 user_id(给 login_required 等装饰器用)"""
    try:
        return decode_token(token)
    except InvalidTokenError:
        return None

# ==================== 装饰器 ====================
def login_required(f):
    """登录校验装饰器 - 支持 session 和 JWT 两种方式"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = None

        # 优先从 session 获取
        if 'user' in session:
            user_id = session.get('user_id')

        # 其次从 JWT 解析（自动检查过期/签名）
        if not user_id:
            auth_header = request.headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                try:
                    user_id = decode_token(auth_header)
                except InvalidTokenError:
                    user_id = None

        if not user_id:
            return error_response(401, "请先登录", status_code=401)

        # 注入 user_id 到 kwargs
        kwargs['user_id'] = user_id
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """管理员权限校验装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = kwargs.get('user_id')
        if not user_id or user_id != 1:
            return error_response(403, "需要管理员权限", status_code=403)
        return f(*args, **kwargs)
    return decorated_function
