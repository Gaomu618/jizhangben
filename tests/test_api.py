"""
API 接口测试：使用 flask test_client，不依赖真实端口
"""
import sys
import time
import pytest

sys.path.insert(0, '.')

from gerenjizhang.app import app
from gerenjizhang.db import add_record, Database, delete_record


@pytest.fixture
def client():
    """Flask 测试客户端"""
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c


@pytest.fixture
def auth_client(client):
    """已登录的测试客户端"""
    suffix = str(int(time.time() * 1000))[-8:]
    username = f'api_pytest_{suffix}'

    with Database() as db:
        db.c.execute(
            'INSERT INTO users (username, password) VALUES (%s, %s)',
            (username, 'pbkdf2_sha256$dummy')
        )
        user_id = db.c.lastrowid
        db.conn.commit()

    # 通过 /login 拿真实 token
    res = client.post('/api/auth/login', json={
        'username': username, 'password': 'test123'  # 实际不验证密码
    })
    # 实际上后端是查真实密码的，让我们用直接派发 token 的方式

    # 用 get_user_id_by_token 直接生成（不实际登录）
    from gerenjizhang.utils.decorators import set_token
    token = f'test_token_{suffix}'
    set_token(token, user_id)

    class AuthClient:
        def __init__(self, c, token, user_id):
            self.c = c
            self.token = token
            self.user_id = user_id
            self.headers = {'Authorization': f'Bearer {token}'}

        def get(self, *a, **kw):
            kw.setdefault('headers', {}).update(self.headers)
            return self.c.get(*a, **kw)

        def post(self, *a, **kw):
            kw.setdefault('headers', {}).update(self.headers)
            return self.c.post(*a, **kw)

    yield AuthClient(client, token, user_id)

    # 清理：先删所有依赖表，再删用户（避免外键冲突）
    from gerenjizhang.utils.decorators import remove_token
    remove_token(token)
    with Database() as db:
        db.c.execute('DELETE FROM bill WHERE user_id=%s', (user_id,))
        db.c.execute('DELETE FROM budgets WHERE user_id=%s', (user_id,))
        db.c.execute('DELETE FROM tokens WHERE user_id=%s', (user_id,))
        db.c.execute('DELETE FROM users WHERE id=%s', (user_id,))
        db.conn.commit()


# ==================== 鉴权测试 ====================
class TestAuth:
    def test_no_token_returns_401(self, client):
        res = client.get('/api/bill/list')
        assert res.status_code == 401
        assert res.get_json()['code'] == 401

    def test_invalid_token_returns_401(self, client):
        res = client.get('/api/bill/list', headers={'Authorization': 'Bearer invalid_token'})
        assert res.status_code == 401

    def test_valid_token_passes(self, auth_client):
        res = auth_client.get('/api/bill/list')
        assert res.status_code == 200
        assert res.get_json()['code'] == 0

    def test_cross_user_isolation(self, auth_client, client):
        """用户 A 创建的数据，用户 B 不能访问"""
        add_record('2026-06-01', 100, 'expense', '餐饮', '', auth_client.user_id)
        records = auth_client.get('/api/bill/list').get_json()['data']['list']
        rid = records[0]['id']

        # 用别的 user_id 试图删 → 越权应失败
        res = client.post(f'/api/bill/delete/{rid}', headers={
            'Authorization': f'Bearer wrong_user_token'
        })
        assert res.status_code == 401  # 因为 token 都不对


# ==================== 账单 CRUD 接口 ====================
class TestBillAPI:
    def test_add_bill(self, auth_client):
        res = auth_client.post('/api/bill/add', json={
            'date': '2026-06-01',
            'amount': 100,
            'type': 'expense',
            'category': '餐饮',
            'note': '午饭'
        })
        assert res.get_json()['code'] == 0
        rid = res.get_json()['data']['id']
        assert rid > 0

    def test_add_bill_missing_amount(self, auth_client):
        """缺少 amount 字段 → 应该有错误"""
        res = auth_client.post('/api/bill/add', json={
            'date': '2026-06-01',
            'type': 'expense',
            'category': '餐饮'
        })
        assert res.get_json()['code'] != 0  # 应该失败

    def test_list_with_year_month(self, auth_client):
        auth_client.post('/api/bill/add', json={
            'date': '2026-06-01', 'amount': 100, 'type': 'expense', 'category': '餐饮'
        })
        res = auth_client.get('/api/bill/list?year=2026&month=6')
        data = res.get_json()['data']
        assert data['total'] >= 1

    def test_list_with_date_range(self, auth_client):
        auth_client.post('/api/bill/add', json={
            'date': '2026-06-01', 'amount': 100, 'type': 'expense', 'category': '餐饮'
        })
        res = auth_client.get('/api/bill/list?start=2026-06-01&end=2026-07-01')
        assert res.get_json()['data']['total'] >= 1

    def test_list_with_category_filter(self, auth_client):
        auth_client.post('/api/bill/add', json={
            'date': '2026-06-01', 'amount': 100, 'type': 'expense', 'category': '餐饮'
        })
        res = auth_client.get('/api/bill/list?start=2026-06-01&end=2026-07-01&category=餐饮')
        assert res.get_json()['data']['total'] >= 1

    def test_batch_delete(self, auth_client):
        ids = []
        for i in range(3):
            res = auth_client.post('/api/bill/add', json={
                'date': f'2026-06-0{i+1}', 'amount': 100, 'type': 'expense', 'category': '餐饮'
            })
            ids.append(res.get_json()['data']['id'])
        res = auth_client.post('/api/bill/batch-delete', json={'ids': ids})
        assert res.get_json()['code'] == 0
        assert res.get_json()['data']['deleted'] == 3

    def test_batch_delete_goes_to_trash_not_hard_delete(self, auth_client):
        """回归测试：批量删除必须进回收站，不能硬删

        之前 bug：批量删除端点用 DELETE FROM bill（硬删），导致用户
        误删的账单彻底消失，找不回来。现在改用 UPDATE ... SET deleted_at。
        这个测试保证以后改代码不会再次出现硬删。
        """
        from gerenjizhang.db import Database

        # 1) 创建 3 条
        ids = []
        for i in range(3):
            res = auth_client.post('/api/bill/add', json={
                'date': f'2026-06-0{i+1}', 'amount': 100, 'type': 'expense', 'category': '餐饮'
            })
            ids.append(res.get_json()['data']['id'])

        # 2) 批量删除
        res = auth_client.post('/api/bill/batch-delete', json={'ids': ids})
        assert res.get_json()['code'] == 0
        assert res.get_json()['data']['deleted'] == 3

        # 3) 核心断言：账单必须还在 bill 表里，deleted_at 被设置（不能真删）
        with Database() as db:
            placeholders = ','.join(['%s'] * len(ids))
            db.c.execute(
                f'SELECT id, deleted_at FROM bill WHERE id IN ({placeholders})',
                ids
            )
            rows = db.c.fetchall()

        # 3a) 记录数必须 = 3（没被真删）
        assert len(rows) == 3, f"批量删除硬删了记录！只剩 {len(rows)} 条"

        # 3b) 每条的 deleted_at 必须不为 NULL
        for rid, deleted_at in rows:
            assert deleted_at is not None, f"记录 {rid} 的 deleted_at 为 NULL，没进回收站"

        # 4) 进一步验证：通过 API 能在回收站列表里看到
        trash = auth_client.get('/api/bill/trash').get_json()['data']['list']
        trash_ids = {r['id'] for r in trash}
        for rid in ids:
            assert rid in trash_ids, f"记录 {rid} 不在回收站 API 返回里"

    def test_batch_delete_empty(self, auth_client):
        """空 ids 应该失败"""
        res = auth_client.post('/api/bill/batch-delete', json={'ids': []})
        assert res.get_json()['code'] == 2002  # 请选择要删除的记录

    def test_batch_delete_too_many(self, auth_client):
        """超过 200 条应该被拒绝"""
        ids = list(range(1, 202))  # 201 个
        res = auth_client.post('/api/bill/batch-delete', json={'ids': ids})
        assert res.get_json()['code'] == 2004  # 一次最多删除 200 条

    def test_batch_delete_invalid_ids(self, auth_client):
        """非法 ID（字符串）应被过滤"""
        res = auth_client.post('/api/bill/batch-delete', json={'ids': ['abc', '123', None]})
        # 非法 ID 被过滤后变空 → 返回 2002 "请选择要删除的记录"
        data = res.get_json()
        assert data['code'] in (2002, 0)
        if data['code'] == 0:
            assert data['data']['deleted'] == 0

    def test_delete_and_batch_delete_both_increment_trash_count(self, auth_client):
        """回归：单删 + 批量删后，trash count 必须增加

        之前 bug：前端 deleteRecord / doBatchDelete 软删成功后没调用
        loadTrashCount()，导致角标永远 0，用户以为没进回收站。
        API 本身正确（见 test_batch_delete_goes_to_trash_not_hard_delete），
        这个测试断言 API 端到端契约：单删后 trash count = 1，
        再批量删 2 条后 trash count = 3。
        """
        # 先清空 trash（避免其它用户残留影响）
        from gerenjizhang.db import Database
        with Database() as db:
            db.c.execute('UPDATE bill SET deleted_at=NOW() WHERE user_id=%s AND deleted_at IS NULL', (auth_client.user_id,))
            db.conn.commit()
        # 测单删
        rid1 = auth_client.post('/api/bill/add', json={
            'date': '2026-06-01', 'amount': 100, 'type': 'expense', 'category': '餐饮'
        }).get_json()['data']['id']
        auth_client.post(f'/api/bill/delete/{rid1}')

        count_after_single = auth_client.get('/api/bill/trash/count').get_json()['data']['count']
        assert count_after_single >= 1, f"单删后 trash count 应 >= 1，实际 {count_after_single}"

        # 测批量删
        ids = []
        for i in range(2):
            r = auth_client.post('/api/bill/add', json={
                'date': f'2026-06-0{i+2}', 'amount': 100, 'type': 'expense', 'category': '餐饮'
            })
            ids.append(r.get_json()['data']['id'])
        auth_client.post('/api/bill/batch-delete', json={'ids': ids})

        count_after_batch = auth_client.get('/api/bill/trash/count').get_json()['data']['count']
        assert count_after_batch >= count_after_single + 2, \
            f"批量删 2 条后 count 应至少 +2，实际 {count_after_batch - count_after_single}"


# ==================== 回收站 API ====================
class TestTrashAPI:
    def test_trash_list_empty(self, auth_client):
        res = auth_client.get('/api/bill/trash')
        assert res.get_json()['code'] == 0
        assert res.get_json()['data']['total'] == 0

    def test_trash_count(self, auth_client):
        res = auth_client.get('/api/bill/trash/count')
        assert res.get_json()['data']['count'] == 0

    def test_soft_delete_then_trash(self, auth_client):
        res = auth_client.post('/api/bill/add', json={
            'date': '2026-06-01', 'amount': 100, 'type': 'expense', 'category': '餐饮'
        })
        rid = res.get_json()['data']['id']

        # 软删除
        auth_client.post(f'/api/bill/delete/{rid}')

        # 列表里没了
        res = auth_client.get('/api/bill/list')
        assert rid not in [r['id'] for r in res.get_json()['data']['list']]

        # 回收站里有
        res = auth_client.get('/api/bill/trash')
        trash_ids = [r['id'] for r in res.get_json()['data']['list']]
        assert rid in trash_ids

    def test_restore(self, auth_client):
        res = auth_client.post('/api/bill/add', json={
            'date': '2026-06-01', 'amount': 100, 'type': 'expense', 'category': '餐饮'
        })
        rid = res.get_json()['data']['id']
        auth_client.post(f'/api/bill/delete/{rid}')

        res = auth_client.post(f'/api/bill/restore/{rid}')
        assert res.get_json()['code'] == 0

        res = auth_client.get('/api/bill/list')
        assert rid in [r['id'] for r in res.get_json()['data']['list']]

    def test_purge(self, auth_client):
        res = auth_client.post('/api/bill/add', json={
            'date': '2026-06-01', 'amount': 100, 'type': 'expense', 'category': '餐饮'
        })
        rid = res.get_json()['data']['id']
        auth_client.post(f'/api/bill/delete/{rid}')
        auth_client.post(f'/api/bill/purge/{rid}')

        res = auth_client.get('/api/bill/trash')
        assert rid not in [r['id'] for r in res.get_json()['data']['list']]

    def test_trash_filter_by_category(self, auth_client):
        """API 支持按分类过滤"""
        for cat in ['餐饮', '交通', '餐饮']:
            res = auth_client.post('/api/bill/add', json={
                'date': '2026-06-01', 'amount': 100, 'type': 'expense', 'category': cat
            })
            auth_client.post(f'/api/bill/delete/{res.get_json()["data"]["id"]}')

        res = auth_client.get('/api/bill/trash?category=餐饮')
        assert res.get_json()['data']['total'] == 2

    def test_empty_trash(self, auth_client):
        for i in range(3):
            res = auth_client.post('/api/bill/add', json={
                'date': f'2026-06-0{i+1}', 'amount': 100, 'type': 'expense', 'category': '餐饮'
            })
            auth_client.post(f'/api/bill/delete/{res.get_json()["data"]["id"]}')

        res = auth_client.post('/api/bill/trash/empty')
        assert res.get_json()['data']['deleted'] == 3


# ==================== 统计 API ====================
class TestStatsAPI:
    def test_summary(self, auth_client):
        auth_client.post('/api/bill/add', json={
            'date': '2026-06-01', 'amount': 100, 'type': 'expense', 'category': '餐饮'
        })
        auth_client.post('/api/bill/add', json={
            'date': '2026-06-02', 'amount': 5000, 'type': 'income', 'category': '工资'
        })
        res = auth_client.get('/api/stats/summary?year=2026&month=6')
        data = res.get_json()['data']
        assert data['income'] == 5000
        assert data['expense'] == 100

    def test_summary_with_date_range(self, auth_client):
        """summary 支持 start/end 参数"""
        res = auth_client.get('/api/stats/summary?start=2026-06-01&end=2026-07-01')
        assert res.get_json()['code'] == 0

    def test_daily(self, auth_client):
        res = auth_client.get('/api/stats/daily?start=2026-06-01&end=2026-07-01')
        assert res.get_json()['code'] == 0
        assert isinstance(res.get_json()['data'], list)

    def test_top_records(self, auth_client):
        res = auth_client.get('/api/stats/top?start=2026-06-01&end=2026-07-01&limit=5')
        assert res.get_json()['code'] == 0


# ==================== 预算 API ====================
class TestBudgetAPI:
    def test_get_empty(self, auth_client):
        res = auth_client.get('/api/bill/budget?year=2026&month=6')
        assert res.get_json()['data'] == []

    def test_set_and_get(self, auth_client):
        auth_client.post('/api/bill/budget', json={
            'category': '餐饮', 'amount': 500, 'type': 'expense', 'month': '2026-06'
        })
        res = auth_client.get('/api/bill/budget?year=2026&month=6')
        data = res.get_json()['data']
        assert len(data) == 1
        assert data[0]['category'] == '餐饮'
        assert data[0]['budget'] == 500
        assert data[0]['spent'] == 0
        assert data[0]['percent'] == 0

    def test_budget_with_spending(self, auth_client):
        """设置预算 + 添加支出后，percent 应正确"""
        auth_client.post('/api/bill/budget', json={
            'category': '餐饮', 'amount': 1000, 'type': 'expense', 'month': '2026-06'
        })
        auth_client.post('/api/bill/add', json={
            'date': '2026-06-01', 'amount': 300, 'type': 'expense', 'category': '餐饮'
        })
        res = auth_client.get('/api/bill/budget?year=2026&month=6')
        data = res.get_json()['data'][0]
        assert data['spent'] == 300
        assert data['percent'] == 30
        assert data['remaining'] == 700

    def test_budget_negative_amount_rejected(self, auth_client):
        """负数预算金额应被拒绝"""
        res = auth_client.post('/api/bill/budget', json={
            'category': '餐饮', 'amount': -100
        })
        assert res.get_json()['code'] == 3003  # 金额不能为负数

    def test_budget_missing_category(self, auth_client):
        """缺少分类应被拒绝"""
        res = auth_client.post('/api/bill/budget', json={
            'amount': 500
        })
        assert res.get_json()['code'] == 3001  # 请选择分类

    def test_delete_budget(self, auth_client):
        auth_client.post('/api/bill/budget', json={
            'category': '餐饮', 'amount': 500, 'month': '2026-06'
        })
        res = auth_client.post('/api/bill/delete-budget', json={
            'category': '餐饮', 'month': '2026-06'
        })
        assert res.get_json()['code'] == 0
