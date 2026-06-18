"""
Tests for utils/jwt_auth.py
运行: python -m unittest gerenjizhang.tests.test_jwt_auth
"""
import sys
import os
import time
import unittest
from pathlib import Path

# 把项目根目录加进 path，让 gerenjizhang.* 能被 import
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

# 让 unittest 能找到 gerenjizhang 包
from gerenjizhang.utils.jwt_auth import (
    encode_token, decode_token, InvalidTokenError
)


class TestJwtBasic(unittest.TestCase):
    """基础 encode/decode"""

    def test_encode_decode_roundtrip(self):
        """encode 后 decode 应该拿回相同 payload"""
        token = encode_token(42)
        user_id = decode_token(token)
        self.assertEqual(user_id, 42)

    def test_encode_returns_string(self):
        token = encode_token(1)
        self.assertIsInstance(token, str)
        self.assertGreater(len(token), 20)  # JWT 至少几十字符

    def test_decode_accepts_prefix_bearer(self):
        """decode 应自动去掉 'Bearer ' 前缀"""
        token = encode_token(99)
        user_id = decode_token(f'Bearer {token}')
        self.assertEqual(user_id, 99)


class TestJwtInvalidToken(unittest.TestCase):
    """无效/过期 token"""

    def test_decode_empty_string(self):
        with self.assertRaises(InvalidTokenError):
            decode_token('')

    def test_decode_garbage(self):
        with self.assertRaises(InvalidTokenError):
            decode_token('this-is-not-a-jwt')

    def test_decode_tampered_signature(self):
        """篡改签名的 token 应该被拒"""
        token = encode_token(1)
        # 篡改最后 5 个字符（signature 部分）
        tampered = token[:-5] + ('AAAAA' if token[-5:] != 'AAAAA' else 'BBBBB')
        with self.assertRaises(InvalidTokenError):
            decode_token(tampered)

    def test_decode_expired_token(self):
        """过期的 token 应该抛 InvalidTokenError"""
        # 创建一个 1 秒后过期的 token
        token = encode_token(1, expires_in=1)
        # 等 2 秒让它过期
        time.sleep(2)
        with self.assertRaises(InvalidTokenError):
            decode_token(token)


class TestJwtExpiration(unittest.TestCase):
    """过期时间配置"""

    def test_default_expiration_is_seven_days(self):
        """默认过期时间是 7 天（604800 秒）"""
        import jwt as pyjwt
        from gerenjizhang.utils.jwt_auth import _decode_with_options
        token = encode_token(1)
        # 解码看 exp
        payload = _decode_with_options(token, verify_exp=True)
        iat = payload['iat']
        exp = payload['exp']
        # 7 天 = 7 * 24 * 3600 = 604800 秒，允许 ±10 秒误差
        self.assertAlmostEqual(exp - iat, 7 * 24 * 3600, delta=10)

    def test_custom_expiration(self):
        """自定义 expires_in 应生效"""
        token = encode_token(1, expires_in=3600)
        from gerenjizhang.utils.jwt_auth import _decode_with_options
        payload = _decode_with_options(token, verify_exp=True)
        iat = payload['iat']
        exp = payload['exp']
        self.assertAlmostEqual(exp - iat, 3600, delta=10)


class TestJwtStatelessness(unittest.TestCase):
    """无状态：decode 不依赖任何外部存储"""

    def test_decode_works_without_db(self):
        """decode 不应该查 DB/缓存"""
        # encode 一次
        token = encode_token(12345)
        # decode 在没有任何 DB 状态的情况下应该也能工作
        # （只要 JWT 签名密钥没变）
        user_id = decode_token(token)
        self.assertEqual(user_id, 12345)

    def test_token_is_url_safe(self):
        """token 应该 URL 安全（不包含 . + 之外的特殊字符）"""
        token = encode_token(1)
        # JWT 标准字符集: A-Z a-z 0-9 - _ .
        import re
        self.assertRegex(token, r'^[A-Za-z0-9_\-\.]+$')


if __name__ == '__main__':
    unittest.main(verbosity=2)
