import secrets
import requests
from flask import Blueprint, request
from gerenjizhang.db import get_user_by_username, create_user, get_user_by_openid, create_user_with_openid, bind_openid, get_user_by_id
from werkzeug.security import generate_password_hash, check_password_hash
from gerenjizhang.utils.response import success_response, error_response
from gerenjizhang.utils.decorators import login_required, set_token, remove_token

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

WECHAT_APPID = "wx5f6c28819df23a00"
WECHAT_SECRET = "aa75e6b15b08547efae322554083574d"


@auth_bp.route('/wechat/login', methods=['POST'])
def wechat_login():
    data = request.get_json() or {}
    code = data.get('code')

    if not code:
        return error_response(1003, "code不能为空")

    # 调用微信接口获取 openid
    url = "https://api.weixin.qq.com/sns/jscode2session"
    params = {
        "appid": WECHAT_APPID,
        "secret": WECHAT_SECRET,
        "js_code": code,
        "grant_type": "authorization_code"
    }

    try:
        resp = requests.get(url, params=params, timeout=10)
        wx_result = resp.json()
    except Exception as e:
        return error_response(1001, "微信服务调用失败")

    if 'openid' not in wx_result:
        return error_response(1004, "微信登录失败", wx_result)

    openid = wx_result['openid']

    # 查询用户是否已存在
    user = get_user_by_openid(openid)

    if not user:
        # 不存在则创建新用户
        user = create_user_with_openid(openid)
        if not user:
            return error_response(1005, "创建用户失败")

    # 生成 token
    token = secrets.token_hex(32)
    set_token(token, user['id'])

    return success_response({
        "token": token,
        "userinfo": {
            "id": user['id'],
            "username": user.get('username', ''),
            "openid": openid
        }
    })


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        return error_response(1006, "用户名和密码不能为空")

    user = get_user_by_username(username)
    if not user:
        return error_response(1007, "账号或密码错误")

    if not check_password_hash(user[2], password):
        return error_response(1007, "账号或密码错误")

    token = secrets.token_hex(32)
    set_token(token, user[0])

    return success_response({
        "token": token,
        "userinfo": {
            "id": user[0],
            "username": user[1],
            "openid": user[3] if len(user) > 3 else None
        }
    })


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        return error_response(1008, "用户名和密码不能为空")

    if len(username) < 3 or len(password) < 6:
        return error_response(1009, "用户名至少3位，密码至少6位")

    hashed = generate_password_hash(password)
    if not create_user(username, hashed):
        return error_response(1010, "用户名已存在")

    return success_response(message="注册成功")


@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout(user_id):
    auth_header = request.headers.get('Authorization', '')
    token = auth_header.replace('Bearer ', '')
    remove_token(token)
    return success_response(message="退出成功")


@auth_bp.route('/userinfo', methods=['GET'])
@login_required
def get_userinfo(user_id):
    user = get_user_by_id(user_id)
    if not user:
        return error_response(1011, "用户不存在")

    return success_response({
        "id": user[0],
        "username": user[1] or '',
        "openid": user[2] or ''
    })


@auth_bp.route('/bind', methods=['POST'])
@login_required
def bind_wechat(user_id):
    data = request.get_json() or {}
    code = data.get('code')

    if not code:
        return error_response(1012, "code不能为空")

    url = "https://api.weixin.qq.com/sns/jscode2session"
    params = {
        "appid": WECHAT_APPID,
        "secret": WECHAT_SECRET,
        "js_code": code,
        "grant_type": "authorization_code"
    }

    try:
        resp = requests.get(url, params=params, timeout=10)
        wx_result = resp.json()
    except Exception as e:
        return error_response(1013, "微信服务调用失败")

    if 'openid' not in wx_result:
        return error_response(1014, "绑定失败")

    if bind_openid(user_id, wx_result['openid']):
        return success_response(message="绑定成功")
    return error_response(1015, "绑定失败")