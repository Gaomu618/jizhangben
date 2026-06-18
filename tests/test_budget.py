"""
预算 API 测试：包括按月过滤 + spent/percent 计算

历史教训：之前前端 loadBudget() 不传 year/month，导致后端默认返回
"当前月"，用户切 Ledger 的 selectedMonth 时看到的是错位的预算。
"""
import time
import sys

sys.path.insert(0, '.')

from gerenjizhang.db import Database, add_record
from gerenjizhang.utils.decorators import set_token, remove_token


def test_budget_filters_by_year_month():
    """预算按月隔离：5 月设的预算在 6 月查不到"""
    suffix = str(int(time.time() * 1000))[-8:]
    with Database() as db:
        db.c.execute('INSERT INTO users (username, password) VALUES (%s, %s)',
                     (f'budget_{suffix}', 'x'))
        uid = db.c.lastrowid
        db.conn.commit()

    # 加几条不同月的记录
    add_record('2026-04-10', 200, 'expense', '餐饮', '4月', uid)
    add_record('2026-05-15', 500, 'expense', '餐饮', '5月', uid)
    add_record('2026-06-10', 800, 'expense', '餐饮', '6月', uid)

    token = f'budget_tok_{suffix}'
    set_token(token, uid)
    from gerenjizhang.app import app
    app.config['TESTING'] = True
    c = app.test_client()
    h = {'Authorization': f'Bearer {token}'}

    # 4 月设 1000 预算
    r = c.post('/api/bill/budget', json={
        'category': '餐饮', 'amount': 1000, 'type': 'expense', 'month': '2026-04'
    }, headers=h)
    assert r.get_json()['code'] == 0

    # 5 月设 2000 预算
    r = c.post('/api/bill/budget', json={
        'category': '餐饮', 'amount': 2000, 'type': 'expense', 'month': '2026-05'
    }, headers=h)
    assert r.get_json()['code'] == 0

    # 4 月查预算
    r = c.get('/api/bill/budget?year=2026&month=4', headers=h)
    data = r.get_json()['data'][0]
    assert data['budget'] == 1000, f"4月预算应=1000, 实际 {data['budget']}"
    assert data['spent'] == 200, f"4月 spent 应=200, 实际 {data['spent']}"

    # 5 月查预算
    r = c.get('/api/bill/budget?year=2026&month=5', headers=h)
    data = r.get_json()['data'][0]
    assert data['budget'] == 2000, f"5月预算应=2000, 实际 {data['budget']}"
    assert data['spent'] == 500, f"5月 spent 应=500, 实际 {data['spent']}"

    # 6 月没设预算 → 应返回空
    r = c.get('/api/bill/budget?year=2026&month=6', headers=h)
    assert r.get_json()['data'] == [], f"6月没设预算应返回空，实际 {r.get_json()['data']}"

    # 清理
    with Database() as db:
        db.c.execute('DELETE FROM bill WHERE user_id=%s', (uid,))
        db.c.execute('DELETE FROM budgets WHERE user_id=%s', (uid,))
        db.c.execute('DELETE FROM users WHERE id=%s', (uid,))
        db.conn.commit()
    remove_token(token)


def test_budget_spent_only_counts_that_month():
    """spent 只算当月的消费（不算其他月）"""
    suffix = str(int(time.time() * 1000))[-8:]
    with Database() as db:
        db.c.execute('INSERT INTO users (username, password) VALUES (%s, %s)',
                     (f'bspend_{suffix}', 'x'))
        uid = db.c.lastrowid
        db.conn.commit()

    # 5 月花 300
    add_record('2026-05-10', 300, 'expense', '餐饮', '', uid)
    # 6 月花 700
    add_record('2026-06-10', 700, 'expense', '餐饮', '', uid)

    # 设 5 月预算 1000
    token = f'bs_tok_{suffix}'
    set_token(token, uid)
    from gerenjizhang.app import app
    app.config['TESTING'] = True
    c = app.test_client()
    h = {'Authorization': f'Bearer {token}'}

    c.post('/api/bill/budget', json={
        'category': '餐饮', 'amount': 1000, 'type': 'expense', 'month': '2026-05'
    }, headers=h)

    # 5 月查：spent 应只算 5 月的 300（不算 6 月的 700）
    r = c.get('/api/bill/budget?year=2026&month=5', headers=h)
    data = r.get_json()['data'][0]
    assert data['spent'] == 300, f"5月 spent 应=300, 实际 {data['spent']}"
    assert data['percent'] == 30.0, f"5月 percent 应=30, 实际 {data['percent']}"

    # 清理
    with Database() as db:
        db.c.execute('DELETE FROM bill WHERE user_id=%s', (uid,))
        db.c.execute('DELETE FROM budgets WHERE user_id=%s', (uid,))
        db.c.execute('DELETE FROM users WHERE id=%s', (uid,))
        db.conn.commit()
    remove_token(token)
