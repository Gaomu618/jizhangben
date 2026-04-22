from functools import wraps
from flask import request
from gerenjizhang.utils.response import error_response

_token_store = {}

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        token = auth_header.replace('Bearer ', '') if auth_header else ''

        if not token:
            return error_response(1001, "请先登录", status_code=401)

        user_id = _token_store.get(token)
        if not user_id:
            return error_response(1002, "token无效或已过期", status_code=401)

        kwargs['user_id'] = user_id
        return f(*args, **kwargs)
    return decorated_function

def set_token(token, user_id):
    _token_store[token] = user_id

def remove_token(token):
    _token_store.pop(token, None)

def get_user_id_by_token(token):
    return _token_store.get(token)