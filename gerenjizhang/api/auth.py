import secrets
import re
import os
import uuid
import time
import logging
import requests
from flask import Blueprint, request, current_app, send_from_directory

logger = logging.getLogger(__name__)
from werkzeug.utils import secure_filename
from gerenjizhang.config import get_config
from gerenjizhang.db import get_user_by_username, create_user, get_user_by_openid, create_user_with_openid, bind_openid, get_user_by_id, get_user_by_email
from werkzeug.security import generate_password_hash, check_password_hash
from gerenjizhang.utils.response import success_response, error_response
from gerenjizhang.utils.decorators import login_required
from gerenjizhang.utils.jwt_auth import encode_token
from gerenjizhang.utils.profile import validate_profile_update, is_default_username
from gerenjizhang.db import update_user_profile, get_user_by_id
from gerenjizhang.middleware.limiter import limiter

# 头像上传配置
AVATAR_UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads', 'avatars')
ALLOWED_AVATAR_EXT = {'.png', '.jpg', '.jpeg', '.gif', '.webp'}
MAX_AVATAR_SIZE = 2 * 1024 * 1024  # 2MB

EMAIL_REGEX = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')

# 密码强度策略（详见 utils/validators.py）
from gerenjizhang.utils.validators import validate_password, validate_username

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


def _wx_creds():
    """从 config 拿 AppID/Secret。config.validate() 启动时已保证非空。"""
    cfg = get_config()
    return cfg.WECHAT_APPID, cfg.WECHAT_SECRET


# WeChat jscode2session API 调用 — 抽成可注入函数（默认真实，测试可 mock）
_wechat_session_override = None  # 测试时设置

def wechat_jscode2session(appid, secret, code, grant_type='authorization_code'):
    """调微信 jscode2session 拿 openid。测试时可通过 set_wechat_override() mock。"""
    if _wechat_session_override is not None:
        return _wechat_session_override(appid, secret, code, grant_type)
    url = "https://api.weixin.qq.com/sns/jscode2session"
    params = {
        "appid": appid, "secret": secret,
        "js_code": code, "grant_type": grant_type,
    }
    resp = requests.get(url, params=params, timeout=10)
    return resp.json()

def set_wechat_session_override(fn):
    """测试用：注入自定义实现，绕过真实 HTTP 调用。返回 None 取消 override。"""
    global _wechat_session_override
    _wechat_session_override = fn

def clear_wechat_session_override():
    set_wechat_session_override(None)


@auth_bp.route('/wechat/login', methods=['POST'])
@limiter.limit("10 per minute")
def wechat_login():
    data = request.get_json() or {}
    code = data.get('code')

    if not code:
        return error_response(1003, "code不能为空")

    try:
        appid, secret = _wx_creds()
        wx_result = wechat_jscode2session(appid, secret, code)
    except Exception as e:
        # 详细异常写日志，不外泄
        logger = logging.getLogger(__name__)
        logger.exception(f"wechat jscode2session error: {e}")
        return error_response(1001, "微信服务调用失败")

    if 'openid' not in wx_result:
        # 微信返回的 errcode/errmsg 写日志，不回客户端（防泄漏内部信息）
        logger = logging.getLogger(__name__)
        errcode = wx_result.get('errcode', 'unknown')
        errmsg = wx_result.get('errmsg', 'unknown')
        logger.warning(f"wechat login failed: errcode={errcode}, errmsg={errmsg}")
        return error_response(1004, "微信登录失败")

    openid = wx_result['openid']

    # 查询用户是否已存在
    user = get_user_by_openid(openid)

    if not user:
        # 不存在则创建新用户
        user = create_user_with_openid(openid)
        if not user:
            return error_response(1005, "创建用户失败")

    # JWT 签名生成 token（无状态，Flask 重启不丢登录态）
    token = encode_token(user['id'])

    # 拉完整 profile（含 nickname / avatar_url）+ 算 is_default_username
    # 让前端能判断是否需要把新用户带到 /pages/profile-setup
    full = get_user_by_id(user['id']) or user
    username = full.get('username', '')

    return success_response({
        "token": token,
        "userinfo": {
            "id": full['id'],
            "username": username,
            "openid": openid,
            "nickname": full.get('nickname', ''),
            "avatar_url": full.get('avatar_url', ''),
            "is_default_username": is_default_username(username)
        }
    })


@auth_bp.route('/login', methods=['POST'])
@limiter.limit("10 per minute")
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

    # JWT 签名生成 token
    token = encode_token(user[0])

    return success_response({
        "token": token,
        "userinfo": {
            "id": user[0],
            "username": user[1],
            "openid": user[3] if len(user) > 3 else None
        }
    })


@auth_bp.route('/register', methods=['POST'])
@limiter.limit("5 per minute")
def register():
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '')
    email = (data.get('email') or '').strip() or None

    if not username or not password:
        return error_response(1008, "用户名和密码不能为空")

    # 用户名策略（详细规则见 validators.validate_username）
    ok, msg = validate_username(username)
    if not ok:
        return error_response(1009, msg)

    # 密码强度策略（详细规则见 validators.validate_password）
    # 至少 8 位 + 字母 + 数字 — 够用且不打击注册
    ok, msg = validate_password(password)
    if not ok:
        return error_response(1019, msg)

    # 邮箱可选，但传了就要校验
    if email and not EMAIL_REGEX.match(email):
        return error_response(1016, "邮箱格式不正确")

    # 邮箱被占用
    if email and get_user_by_email(email):
        return error_response(1017, "该邮箱已被注册")

    hashed = generate_password_hash(password)
    if not create_user(username, hashed, email=email):
        return error_response(1010, "用户名已存在")

    return success_response(message="注册成功")


@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout(user_id):
    # JWT 是无状态的：服务端无需存储/撤销 token。
    # 前端 logout 只需把 storage 里的 token 清掉，下次请求 401 就被踢回登录页。
    return success_response(message="退出成功")


@auth_bp.route('/userinfo', methods=['GET'])
@login_required
def get_userinfo(user_id):
    user = get_user_by_id(user_id)
    if not user:
        return error_response(1011, "用户不存在")

    return success_response({
        "id": user['id'],
        "username": user.get('username', ''),
        "openid": user.get('openid', ''),
        "nickname": user.get('nickname', ''),
        "avatar_url": user.get('avatar_url', ''),
        "is_default_username": is_default_username(user.get('username', ''))
    })


@auth_bp.route('/profile', methods=['PUT', 'POST'])
@login_required
def update_profile(user_id):
    """更新用户昵称 / 头像"""
    data = request.get_json() or {}
    ok, result = validate_profile_update(data, return_cleaned=True)
    if not ok:
        return error_response(1020, result)

    if not update_user_profile(user_id, **result):
        return error_response(1021, "更新失败")

    # 返回最新的 userinfo
    user = get_user_by_id(user_id)
    return success_response({
        "nickname": user.get('nickname', ''),
        "avatar_url": user.get('avatar_url', ''),
        "is_default_username": is_default_username(user.get('username', ''))
    })


@auth_bp.route('/avatar', methods=['POST'])
@login_required
@limiter.limit("20 per minute")
def upload_avatar(user_id):
    """
    上传头像文件
    - multipart/form-data, field name = 'file'
    - 限制: 2MB, 图片格式 (png/jpg/jpeg/gif/webp)
    - 存储: gerenjizhang/uploads/avatars/<uuid>.ext
    - 返回: { avatar_url: '/uploads/avatars/xxx.png' } (相对路径,前端拼 baseUrl)

    安全加固：
    - 用 Pillow Image.verify 校验文件内容确实是合法图片（防 .php.jpg / 损坏文件）
    - 同时保留扩展名校验作为快速失败（白名单在前）
    """
    from gerenjizhang.utils.validators import validate_image_content

    if 'file' not in request.files:
        return error_response(1030, "请选择文件")
    f = request.files['file']
    if not f or not f.filename:
        return error_response(1031, "文件无效")

    # 第一道关：扩展名白名单（快速失败，节省 IO）
    ext = os.path.splitext(f.filename)[1].lower()
    if ext not in ALLOWED_AVATAR_EXT:
        return error_response(1032, f"仅支持 {', '.join(sorted(ALLOWED_AVATAR_EXT))}")

    # 第二道关：内容真实校验（Pillow 解析文件头 + 结构）
    ok, err, fmt, size = validate_image_content(f, max_size_mb=2)
    if not ok:
        return error_response(1035, err or "图片校验失败")

    # 用 Pillow 识别的 fmt 重写扩展名（防 ext 与内容不一致的攻击）
    ext_map = {'png': '.png', 'jpeg': '.jpg', 'jpg': '.jpg', 'gif': '.gif', 'webp': '.webp'}
    real_ext = ext_map.get(fmt, ext)

    # 确保目录存在
    os.makedirs(AVATAR_UPLOAD_DIR, exist_ok=True)

    # 唯一文件名（防覆盖 + 防路径注入）
    safe_name = f"{user_id}_{int(time.time())}_{uuid.uuid4().hex[:8]}{real_ext}"
    filepath = os.path.join(AVATAR_UPLOAD_DIR, safe_name)

    # 指针已经在 validate_image_content 里 reset 过了
    f.save(filepath)

    # 返回相对 URL（前端拼 baseUrl）
    rel_url = f"/uploads/avatars/{safe_name}"
    update_user_profile(user_id, avatar_url=rel_url)

    return success_response({
        "avatar_url": rel_url,
        "size": size
    })


@auth_bp.route('/bind', methods=['POST'])
@login_required
@limiter.limit("10 per minute")
def bind_wechat(user_id):
    data = request.get_json() or {}
    code = data.get('code')

    if not code:
        return error_response(1012, "code不能为空")

    try:
        appid, secret = _wx_creds()
        wx_result = wechat_jscode2session(appid, secret, code)
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.exception(f"wechat jscode2session error (bind): {e}")
        return error_response(1013, "微信服务调用失败")

    if 'openid' not in wx_result:
        logger = logging.getLogger(__name__)
        errcode = wx_result.get('errcode', 'unknown')
        errmsg = wx_result.get('errmsg', 'unknown')
        logger.warning(f"wechat bind failed: errcode={errcode}, errmsg={errmsg}")
        return error_response(1014, "绑定失败")

    if bind_openid(user_id, wx_result['openid']):
        return success_response(message="绑定成功")
    return error_response(1015, "绑定失败")