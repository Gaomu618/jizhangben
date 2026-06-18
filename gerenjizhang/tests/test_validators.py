"""
Tests for utils/validators.py
- 密码强度策略
- 用户名策略
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from gerenjizhang.utils.validators import validate_password, validate_username


class TestPasswordStrength(unittest.TestCase):
    """validate_password 强度策略"""

    def test_empty_rejected(self):
        ok, msg = validate_password('')
        self.assertFalse(ok)

    def test_none_rejected(self):
        ok, msg = validate_password(None)
        self.assertFalse(ok)

    def test_too_short_rejected(self):
        ok, msg = validate_password('a1b')  # 3 位
        self.assertFalse(ok)
        self.assertIn('8', msg)

    def test_no_letter_rejected(self):
        ok, msg = validate_password('12345678')  # 只有数字
        self.assertFalse(ok)

    def test_no_digit_rejected(self):
        ok, msg = validate_password('abcdefgh')  # 只有字母
        self.assertFalse(ok)

    def test_valid_password_accepted(self):
        ok, msg = validate_password('hello123')
        self.assertTrue(ok)
        self.assertIsNone(msg)

    def test_too_long_rejected(self):
        ok, msg = validate_password('a' * 200)
        self.assertFalse(ok)

    def test_exactly_8_chars_accepted(self):
        ok, msg = validate_password('abcd1234')
        self.assertTrue(ok)


class TestUsernameStrength(unittest.TestCase):
    """validate_username 策略"""

    def test_empty_rejected(self):
        ok, msg = validate_username('')
        self.assertFalse(ok)

    def test_too_short_rejected(self):
        ok, msg = validate_username('ab')
        self.assertFalse(ok)

    def test_too_long_rejected(self):
        ok, msg = validate_username('a' * 25)
        self.assertFalse(ok)

    def test_invalid_chars_rejected(self):
        ok, msg = validate_username('user@name')
        self.assertFalse(ok)

    def test_valid_english_accepted(self):
        ok, msg = validate_username('john_doe')
        self.assertTrue(ok)

    def test_valid_chinese_accepted(self):
        ok, msg = validate_username('小明同学')
        self.assertTrue(ok)

    def test_valid_alphanumeric_accepted(self):
        ok, msg = validate_username('user123')
        self.assertTrue(ok)


if __name__ == '__main__':
    unittest.main(verbosity=2)
