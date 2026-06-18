"""
Tests for /api/category/* (自定义分类)
"""
import sys
import os
import unittest
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

# 测试环境
os.environ.setdefault('WECHAT_APPID', 'test')
os.environ.setdefault('WECHAT_SECRET', 'test')
os.environ.setdefault('FLASK_ENV', 'testing')

from gerenjizhang.app import app
from gerenjizhang.db import (
    init_db, list_user_categories, create_user_category,
    delete_user_category, add_user_category_keyword,
    list_user_category_keywords, get_user_category_by_id,
)


class TestCategoryAPI(unittest.TestCase):
    """自定义分类 API 端点测试"""

    @classmethod
    def setUpClass(cls):
        init_db()
        app.config['TESTING'] = True
        cls.client = app.test_client()

    def _login(self, username='budget_test', password='test123'):
        r = self.client.post('/api/auth/login', json={'username': username, 'password': password})
        if r.status_code != 200:
            return None
        return r.get_json()['data']['token']

    def test_01_list_categories_authenticated(self):
        """登录后能拿到分类列表（系统 + 自定义）"""
        token = self._login()
        if not token:
            self.skipTest('no token (budget_test 用户不存在)')
        r = self.client.get('/api/category', headers={'Authorization': f'Bearer {token}'})
        self.assertEqual(r.status_code, 200)
        data = r.get_json()['data']
        self.assertIn('categories', data)
        self.assertGreaterEqual(data['system_count'], 10)  # 至少 10 个系统分类
        # 验证 餐饮/交通 等系统分类都存在
        names = [c['name'] for c in data['categories']]
        for sys_cat in ['餐饮', '交通', '购物', '娱乐', '居住', '教育', '医疗', '其他', '工资', '奖金', '理财', '副业', '转账']:
            self.assertIn(sys_cat, names, f'系统分类 {sys_cat} 应该存在')

    def test_02_create_custom_category(self):
        """新增自定义分类"""
        token = self._login()
        if not token:
            self.skipTest('no token')
        r = self.client.post('/api/category',
                             headers={'Authorization': f'Bearer {token}'},
                             json={'name': f'宠物_test_{os.getpid()}', 'icon': '🐶', 'type': 'expense'})
        self.assertEqual(r.status_code, 200)
        cat = r.get_json()['data']
        self.assertEqual(cat['is_system'], 0)
        self.assertEqual(cat['icon'], '🐶')
        self.assertEqual(cat['name'], f'宠物_test_{os.getpid()}')

    def test_03_create_duplicate_name_rejected(self):
        """同名分类被拒"""
        token = self._login()
        if not token:
            self.skipTest('no token')
        name = f'重复测试_{os.getpid()}'
        # 第一次创建
        r1 = self.client.post('/api/category',
                              headers={'Authorization': f'Bearer {token}'},
                              json={'name': name, 'type': 'expense'})
        self.assertEqual(r1.status_code, 200)
        # 第二次同名
        r2 = self.client.post('/api/category',
                              headers={'Authorization': f'Bearer {token}'},
                              json={'name': name, 'type': 'expense'})
        self.assertEqual(r2.status_code, 400)  # 5103 同名错误

    def test_04_empty_name_rejected(self):
        """空名被拒"""
        token = self._login()
        if not token:
            self.skipTest('no token')
        r = self.client.post('/api/category',
                             headers={'Authorization': f'Bearer {token}'},
                             json={'name': '', 'type': 'expense'})
        self.assertEqual(r.status_code, 400)

    def test_05_system_category_cannot_delete(self):
        """系统分类不能删"""
        token = self._login()
        if not token:
            self.skipTest('no token')
        # 拿一个系统分类
        r = self.client.get('/api/category', headers={'Authorization': f'Bearer {token}'})
        sys_cat = next(c for c in r.get_json()['data']['categories'] if c['is_system'] and c['name'] == '餐饮')
        # 尝试删除
        r2 = self.client.delete(f'/api/category/{sys_cat["id"]}',
                                headers={'Authorization': f'Bearer {token}'})
        self.assertEqual(r2.status_code, 400)  # 5110 系统不可删

    def test_06_custom_category_can_delete(self):
        """自定义分类可以删"""
        token = self._login()
        if not token:
            self.skipTest('no token')
        # 创建
        name = f'待删_{os.getpid()}'
        r = self.client.post('/api/category',
                             headers={'Authorization': f'Bearer {token}'},
                             json={'name': name, 'type': 'expense'})
        cat_id = r.get_json()['data']['id']
        # 删除
        r2 = self.client.delete(f'/api/category/{cat_id}',
                                headers={'Authorization': f'Bearer {token}'})
        self.assertEqual(r2.status_code, 200)
        # 再查应该没了
        r3 = self.client.get('/api/category', headers={'Authorization': f'Bearer {token}'})
        names = [c['name'] for c in r3.get_json()['data']['categories']]
        self.assertNotIn(name, names)

    def test_07_add_keyword_to_category(self):
        """给分类加关键词"""
        token = self._login()
        if not token:
            self.skipTest('no token')
        name = f'关键词测试_{os.getpid()}'
        r = self.client.post('/api/category',
                             headers={'Authorization': f'Bearer {token}'},
                             json={'name': name, 'type': 'expense'})
        cat_id = r.get_json()['data']['id']
        # 加 2 个关键词
        self.client.post(f'/api/category/{cat_id}/keywords',
                         headers={'Authorization': f'Bearer {token}'},
                         json={'keyword': '猫粮'})
        self.client.post(f'/api/category/{cat_id}/keywords',
                         headers={'Authorization': f'Bearer {token}'},
                         json={'keyword': '狗粮'})
        # 列出来
        r2 = self.client.get(f'/api/category/{cat_id}/keywords',
                             headers={'Authorization': f'Bearer {token}'})
        kws = [k['keyword'] for k in r2.get_json()['data']['keywords']]
        self.assertIn('猫粮', kws)
        self.assertIn('狗粮', kws)
        # 清理
        self.client.delete(f'/api/category/{cat_id}',
                           headers={'Authorization': f'Bearer {token}'})

    def test_08_duplicate_keyword_rejected(self):
        """重复关键词被拒"""
        token = self._login()
        if not token:
            self.skipTest('no token')
        name = f'去重测试_{os.getpid()}'
        r = self.client.post('/api/category',
                             headers={'Authorization': f'Bearer {token}'},
                             json={'name': name, 'type': 'expense'})
        cat_id = r.get_json()['data']['id']
        self.client.post(f'/api/category/{cat_id}/keywords',
                         headers={'Authorization': f'Bearer {token}'},
                         json={'keyword': '狗粮'})
        r2 = self.client.post(f'/api/category/{cat_id}/keywords',
                              headers={'Authorization': f'Bearer {token}'},
                              json={'keyword': '狗粮'})
        self.assertEqual(r2.status_code, 400)  # 5131 重复
        self.client.delete(f'/api/category/{cat_id}',
                           headers={'Authorization': f'Bearer {token}'})

    def test_09_50_categories_limit(self):
        """50 个分类上限 — 直接调函数验证逻辑（不真填 50 条）"""
        # budget_test 是 uid 5160，登录拿 token
        r = self.client.post('/api/auth/login', json={'username': 'budget_test', 'password': 'test123'})
        if r.status_code != 200:
            self.skipTest('budget_test not available')
        token = r.get_json()['data']['token']
        # 用一个真实存在的用户（budget_test = uid 5160）
        # 这里只验证函数可调用 + 上限校验逻辑，不真填 50 条
        # 通过查看预算用户当前分类数 + 加 1 个测试
        cats = list_user_categories(5160)
        initial = len(cats)
        # 应该能正常加一个（不到上限）
        result, err = create_user_category(5160, f'_limit_test_{os.getpid()}', type_='expense')
        if initial < 50:
            self.assertIsNotNone(result, f'加第 {initial+1} 个应该成功: {err}')
            # 清理
            if result:
                delete_user_category(5160, result['id'])
        else:
            self.assertIsNone(result)  # 满了就拒绝

    def test_10_403_unauthenticated(self):
        """未认证 401"""
        r = self.client.get('/api/category')
        self.assertEqual(r.status_code, 401)


if __name__ == '__main__':
    unittest.main(verbosity=2)
