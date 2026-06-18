"""
Tests for /api/auth/avatar (头像上传)
- multipart 文件上传
- 格式/大小校验
- 静态文件服务
"""
import sys
import os
import io
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

# 必须先有 env vars 让 config 启动
os.environ.setdefault('WECHAT_APPID', 'test')
os.environ.setdefault('WECHAT_SECRET', 'test')
os.environ.setdefault('FLASK_ENV', 'testing')


# ===== 静态服务路由 =====
class TestStaticServing(unittest.TestCase):
    """/uploads/<filename> 路由能 serve 文件"""

    def setUp(self):
        from gerenjizhang.app import app, UPLOAD_ROOT
        self.app = app
        self.client = app.test_client()
        self.upload_root = UPLOAD_ROOT

    def test_uploads_dir_exists(self):
        """/uploads 目录应被自动创建"""
        self.assertTrue(os.path.isdir(self.upload_root))

    def test_serve_existing_file(self):
        """在 uploads 写个文件，访问应能拿到"""
        test_file = os.path.join(self.upload_root, 'test_unit.png')
        with open(test_file, 'wb') as f:
            f.write(b'\x89PNG\r\n\x1a\n')  # PNG 头
        try:
            r = self.client.get('/uploads/test_unit.png')
            self.assertEqual(r.status_code, 200)
        finally:
            # 用 try/except 防 Windows 文件锁导致 OSError
            try:
                os.remove(test_file)
            except OSError:
                pass

    def test_serve_missing_file_404(self):
        """不存在的文件应返 404"""
        r = self.client.get('/uploads/does_not_exist.png')
        self.assertEqual(r.status_code, 404)


# ===== 头像上传端点 =====
class TestAvatarUploadEndpoint(unittest.TestCase):
    """POST /api/auth/avatar 接收 multipart file"""

    def setUp(self):
        from gerenjizhang.app import app
        self.app = app
        self.client = app.test_client()
        # 登录拿 token（用 budget_test 真账号）
        r = self.client.post('/api/auth/login',
                              json={'username': 'budget_test', 'password': 'test123'})
        if r.status_code == 200:
            self.token = r.get_json()['data']['token']
            self.headers = {'Authorization': f'Bearer {self.token}'}
        else:
            self.token = None
            self.headers = {}

    def _make_png(self, size_kb=1):
        """生成一个有效的 PNG 文件用于上传测试"""
        # 用 Pillow 真正生成合法 PNG（1x1 像素）
        from PIL import Image
        img = Image.new('RGB', (1, 1), color=(255, 0, 0))
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        png_data = buf.getvalue()
        # 填充到目标 size（粗略）
        if size_kb > 1:
            png_data += b'\x00' * (size_kb * 1024 - len(png_data))
        return io.BytesIO(png_data)

    def test_no_file_400(self):
        if not self.token:
            self.skipTest('no token')
        r = self.client.post('/api/auth/avatar', headers=self.headers)
        self.assertEqual(r.status_code, 400)

    def test_no_token_401(self):
        r = self.client.post('/api/auth/avatar',
                              data={'file': (self._make_png(), 'test.png')},
                              content_type='multipart/form-data')
        self.assertEqual(r.status_code, 401)

    def test_png_upload_succeeds(self):
        if not self.token:
            self.skipTest('no token')
        r = self.client.post('/api/auth/avatar',
                              headers=self.headers,
                              data={'file': (self._make_png(), 'avatar.png')},
                              content_type='multipart/form-data')
        self.assertEqual(r.status_code, 200)
        data = r.get_json()['data']
        self.assertTrue(data['avatar_url'].startswith('/uploads/avatars/'))
        self.assertTrue(data['avatar_url'].endswith('.png'))

    def test_jpg_upload_succeeds(self):
        if not self.token:
            self.skipTest('no token')
        r = self.client.post('/api/auth/avatar',
                              headers=self.headers,
                              data={'file': (self._make_png(), 'pic.jpg')},
                              content_type='multipart/form-data')
        self.assertEqual(r.status_code, 200)

    def test_invalid_ext_rejected(self):
        if not self.token:
            self.skipTest('no token')
        # .txt 不在白名单
        txt = io.BytesIO(b'not an image' * 100)
        r = self.client.post('/api/auth/avatar',
                              headers=self.headers,
                              data={'file': (txt, 'avatar.txt')},
                              content_type='multipart/form-data')
        self.assertEqual(r.status_code, 400)

    def test_oversized_rejected(self):
        if not self.token:
            self.skipTest('no token')
        # 3MB > 2MB limit
        big = self._make_png(size_kb=3000)
        r = self.client.post('/api/auth/avatar',
                              headers=self.headers,
                              data={'file': (big, 'big.png')},
                              content_type='multipart/form-data')
        self.assertEqual(r.status_code, 400)


if __name__ == '__main__':
    unittest.main(verbosity=2)
