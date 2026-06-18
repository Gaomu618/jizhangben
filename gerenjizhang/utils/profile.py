"""
Profile 工具：默认用户名检测 + 资料更新校验
- is_default_username(username) → bool: 是否是 'wx_xxxxxxxx' 格式（系统自动生成）
- validate_profile_update(data, return_cleaned=False) → (ok, err_or_cleaned)
  - 校验昵称长度/头像 URL 合法性
  - 白名单字段（拒绝 user_id/is_admin 等敏感字段）
"""

import re

# 限制
MAX_NICKNAME_LEN = 20
MAX_AVATAR_URL_LEN = 500

# 默认用户名格式：wx_ + 8 字符
# 在 db.py:547 create_user_with_openid 里生成: f"wx_{openid[:8]}"
DEFAULT_USERNAME_PATTERN = re.compile(r'^wx_[a-zA-Z0-9]{8}$')

# 头像允许的前缀：
# - http(s)://         外链头像（保留兼容，未来可能允许第三方 URL）
# - /uploads/avatars/  后端 POST /api/auth/avatar 上传后返回的相对路径（自家产物，前端拼 baseUrl 渲染）
# 不允许任意 '/' 开头的路径，防 path injection（比如 /etc/passwd）
ALLOWED_AVATAR_PREFIXES = ('http://', 'https://', '/uploads/avatars/')

# 允许的字段（白名单）
ALLOWED_FIELDS = {'nickname', 'avatar_url'}


def is_default_username(username):
    """
    检查 username 是否是系统自动生成的默认名（'wx_' + 8 字符）
    用于登录后判断要不要跳"完善资料"页
    """
    if not username or not isinstance(username, str):
        return False
    return bool(DEFAULT_USERNAME_PATTERN.match(username))


def validate_profile_update(data, return_cleaned=False):
    """
    校验 profile 更新数据
    @param {dict} data - 前端发来的 { nickname?, avatar_url? }
    @param {bool} return_cleaned - True 返回清理后的数据；False 返回错误信息
    @returns (ok, result) - ok=True 时 result 是 cleaned data 或 None；ok=False 时 result 是 error message

    安全要点：
    - 白名单字段（只允许 nickname/avatar_url）
    - 昵称长度限制
    - 头像 URL 必须是 http(s)
    """
    if not isinstance(data, dict):
        return (False, '请求数据格式错误')

    cleaned = {}

    # 昵称
    if 'nickname' in data:
        nick = data['nickname']
        if nick is None:
            pass  # 允许显式置空
        elif not isinstance(nick, str):
            return (False, '昵称必须是字符串')
        else:
            nick = nick.strip()
            if nick == '':
                # 允许空字符串（视为"不改昵称"）
                pass
            elif len(nick) > MAX_NICKNAME_LEN:
                return (False, f'昵称最多 {MAX_NICKNAME_LEN} 个字符')
            else:
                cleaned['nickname'] = nick

    # 头像 URL
    if 'avatar_url' in data:
        url = data['avatar_url']
        if url is None:
            pass
        elif not isinstance(url, str):
            return (False, '头像 URL 必须是字符串')
        elif not url.startswith(ALLOWED_AVATAR_PREFIXES):
            return (False, '头像 URL 必须以 http://、https:// 或 /uploads/avatars/ 开头')
        elif len(url) > MAX_AVATAR_URL_LEN:
            return (False, f'头像 URL 过长（>{MAX_AVATAR_URL_LEN}）')
        else:
            cleaned['avatar_url'] = url

    # 如果什么都没改
    if not cleaned:
        return (False, '没有可更新的字段')

    # 统一返 (ok, result)：
    #   - return_cleaned=True  → result = cleaned dict
    #   - return_cleaned=False → result = None（调用方只关心 ok/err）
    return (True, cleaned if return_cleaned else None)
