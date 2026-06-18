"""
Tests for profile update feature (Phase C: 自填 + 弹窗)
- POST /api/auth/profile 更新昵称/头像
- GET /api/auth/userinfo 返回新字段
- 默认用户名 (wx_xxxx) 检测工具
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))


# ===== 默认用户名检测 =====
class TestDefaultUsername(unittest.TestCase):
    """'wx_xxxxxxxx' 格式检测 — 用于登录后判断要不要跳 profile-setup"""

    def test_is_default_username_true(self):
        from gerenjizhang.utils.profile import is_default_username
        self.assertTrue(is_default_username('wx_a1b2c3d4'))
        self.assertTrue(is_default_username('wx_12345678'))
        self.assertTrue(is_default_username('wx_ABCDEFGH'))

    def test_is_default_username_false(self):
        from gerenjizhang.utils.profile import is_default_username
        self.assertFalse(is_default_username('张三'))
        self.assertFalse(is_default_username('admin'))
        self.assertFalse(is_default_username('wx_'))  # 太短
        self.assertFalse(is_default_username(''))
        self.assertFalse(is_default_username('wx_12'))  # 不到 8 字符
        self.assertFalse(is_default_username(None))

    def test_is_default_username_partial_match(self):
        """'wx_' 开头但不全是 8 字符的不算默认"""
        from gerenjizhang.utils.profile import is_default_username
        self.assertFalse(is_default_username('wx_12345'))  # 7 字符
        self.assertFalse(is_default_username('wx_123456789'))  # 9 字符
        self.assertFalse(is_default_username('wx_abcdefg!'))  # 含特殊字符


# ===== 昵称/头像验证 =====
class TestProfileValidation(unittest.TestCase):
    """更新前的字段校验"""

    def test_valid_nickname(self):
        from gerenjizhang.utils.profile import validate_profile_update
        ok, err = validate_profile_update({'nickname': '张三', 'avatar_url': 'https://x.com/a.jpg'})
        self.assertTrue(ok)
        self.assertIsNone(err)

    def test_nickname_too_long(self):
        from gerenjizhang.utils.profile import validate_profile_update
        ok, err = validate_profile_update({'nickname': 'a' * 25})
        self.assertFalse(ok)
        self.assertIn('20', err)

    def test_nickname_empty_rejected(self):
        from gerenjizhang.utils.profile import validate_profile_update
        ok, err = validate_profile_update({'nickname': ''})
        self.assertFalse(ok)

    def test_nickname_only_whitespace_rejected(self):
        from gerenjizhang.utils.profile import validate_profile_update
        ok, err = validate_profile_update({'nickname': '   '})
        self.assertFalse(ok)

    def test_avatar_url_must_be_http(self):
        from gerenjizhang.utils.profile import validate_profile_update
        ok, err = validate_profile_update({'nickname': '张三', 'avatar_url': 'file:///etc/passwd'})
        self.assertFalse(ok)
        self.assertIn('http', err)

    def test_avatar_url_too_long(self):
        from gerenjizhang.utils.profile import validate_profile_update
        from gerenjizhang.utils.profile import MAX_AVATAR_URL_LEN
        ok, err = validate_profile_update({
            'nickname': '张三',
            'avatar_url': 'https://x.com/' + 'a' * (MAX_AVATAR_URL_LEN + 1)
        })
        self.assertFalse(ok)

    def test_avatar_url_optional(self):
        """只更新昵称也可以"""
        from gerenjizhang.utils.profile import validate_profile_update
        ok, err = validate_profile_update({'nickname': '张三'})
        self.assertTrue(ok)

    def test_nickname_optional(self):
        """只更新头像也可以"""
        from gerenjizhang.utils.profile import validate_profile_update
        ok, err = validate_profile_update({'avatar_url': 'https://x.com/a.jpg'})
        self.assertTrue(ok)

    def test_extra_fields_stripped(self):
        """未知字段应该被忽略（白名单）"""
        from gerenjizhang.utils.profile import validate_profile_update
        ok, clean = validate_profile_update({
            'nickname': '张三',
            'avatar_url': 'https://x.com/a.jpg',
            'is_admin': True,           # 攻击：试图提权
            'user_id': 999              # 攻击：试图改 user_id
        }, return_cleaned=True)
        self.assertTrue(ok)
        self.assertNotIn('is_admin', clean)
        self.assertNotIn('user_id', clean)
        self.assertEqual(clean['nickname'], '张三')


if __name__ == '__main__':
    unittest.main(verbosity=2)
