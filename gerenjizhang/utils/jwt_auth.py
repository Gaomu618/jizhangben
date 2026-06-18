"""
JWT 认证工具 — 无状态 token
- encode_token(user_id, expires_in) → JWT string
- decode_token(token) → user_id（自动剥 'Bearer ' 前缀）
- 过期/无效 token 抛 jwt.InvalidTokenError

优点：
- 无状态：Flask 重启不丢登录（不依赖内存/DB）
- 自包含过期：exp 字段嵌在 payload 里
- 跨实例：多进程/多机可共享同一密钥验证

P2 加固：
- payload 包含 aud (audience) / iss (issuer)，避免 token 在跨服务时被滥用
- 旧的 token（没有 aud/iss）也能解析（向后兼容）
"""
import time
import jwt as pyjwt
from gerenjizhang.config import get_config

# 重新导出，方便调用方抓一个统一异常
InvalidTokenError = pyjwt.InvalidTokenError


def encode_token(user_id, expires_in=None):
    """
    生成 JWT token
    @param {int} user_id
    @param {int} expires_in - 过期秒数（None = 用 config 默认 7 天）
    @returns {string} JWT token
    """
    cfg = get_config()
    if expires_in is None:
        expires_in = cfg.JWT_EXPIRES_SECONDS

    now = int(time.time())
    payload = {
        'user_id': user_id,
        'iat': now,
        'exp': now + expires_in,
        'aud': cfg.JWT_AUDIENCE,  # 受众 — 防止 token 跨服务滥用
        'iss': cfg.JWT_ISSUER,    # 签发者
    }
    return pyjwt.encode(payload, cfg.JWT_SECRET, algorithm=cfg.JWT_ALGORITHM)


def decode_token(token):
    """
    解析 JWT token
    @param {string} token - 原始 token 或 'Bearer xxx'
    @returns {int} user_id
    @raises {jwt.InvalidTokenError} 过期/无效/签名错误
    """
    if not token:
        raise InvalidTokenError('Empty token')

    # 剥 'Bearer ' 前缀
    if token.startswith('Bearer '):
        token = token[7:]

    cfg = get_config()
    # 验证 aud / iss；options 里不指定就跳过（向后兼容老 token）
    # 新 token 一定带 aud/iss，验证失败就 InvalidTokenError
    try:
        payload = pyjwt.decode(
            token,
            cfg.JWT_SECRET,
            algorithms=[cfg.JWT_ALGORITHM],
            audience=cfg.JWT_AUDIENCE,
            issuer=cfg.JWT_ISSUER,
        )
    except pyjwt.MissingRequiredClaimError:
        # 兼容老 token（没 aud/iss）：用宽松模式再解一次
        payload = pyjwt.decode(
            token,
            cfg.JWT_SECRET,
            algorithms=[cfg.JWT_ALGORITHM],
            options={'verify_aud': False, 'verify_iss': False},
        )

    user_id = payload.get('user_id')
    if user_id is None:
        raise InvalidTokenError('Missing user_id in payload')
    return int(user_id)


# ============ 内部工具（测试用） ============

def _decode_with_options(token, verify_exp=True):
    """测试用：解 payload 本身（不验证签名）"""
    if token.startswith('Bearer '):
        token = token[7:]
    cfg = get_config()
    return pyjwt.decode(token, options={'verify_signature': False, 'verify_exp': verify_exp})
