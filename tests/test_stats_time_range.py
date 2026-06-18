"""
统计时间范围区分测试：不同时间段查出来的账单应该不一样。

历史 bug：前端 Stats.vue 的 selectRange() 漏调 computeRange()，
导致用户点 "本月 / 上月 / 近7天" 等不同 chip 时，API 实际用
的是同一个日期范围，结果数据完全一样。

这个测试在 API 层验证不同时间范围返回不同数据。
"""
import time
import sys

sys.path.insert(0, '.')

from gerenjizhang.db import Database, add_record
from gerenjizhang.utils.decorators import set_token, remove_token


def test_time_range_differentiation():
    """不同时段 → 不同的 expense 数字"""
    suffix = str(int(time.time() * 1000))[-8:]
    with Database() as db:
        db.c.execute('INSERT INTO users (username, password) VALUES (%s, %s)',
                     (f'timerange_{suffix}', 'x'))
        uid = db.c.lastrowid
        db.conn.commit()

    # 加 3 条不同时段的记录
    add_record('2026-04-15', 100, 'expense', '餐饮', '4月', uid)
    add_record('2026-05-20', 500, 'expense', '购物', '5月', uid)
    add_record('2026-06-10', 1000, 'expense', '交通', '6月', uid)

    token = f'tr_tok_{suffix}'
    set_token(token, uid)
    from gerenjizhang.app import app
    app.config['TESTING'] = True
    c = app.test_client()
    h = {'Authorization': f'Bearer {token}'}

    # 4 月
    r4 = c.get('/api/stats/summary?start=2026-04-01&end=2026-05-01', headers=h).get_json()['data']
    # 5 月
    r5 = c.get('/api/stats/summary?start=2026-05-01&end=2026-06-01', headers=h).get_json()['data']
    # 6 月
    r6 = c.get('/api/stats/summary?start=2026-06-01&end=2026-07-01', headers=h).get_json()['data']
    # 4-6 月
    rAll = c.get('/api/stats/summary?start=2026-04-01&end=2026-07-01', headers=h).get_json()['data']

    # 验证
    assert r4['expense'] == 100, f"4月 expense 应=100, 实际 {r4['expense']}"
    assert r5['expense'] == 500, f"5月 expense 应=500, 实际 {r5['expense']}"
    assert r6['expense'] == 1000, f"6月 expense 应=1000, 实际 {r6['expense']}"
    assert rAll['expense'] == 1600, f"4-6月 expense 应=1600, 实际 {rAll['expense']}"

    # 核心断言：4 个时段必须各不相同
    assert len({r4['expense'], r5['expense'], r6['expense'], rAll['expense']}) == 4, \
        "4 个时间段的 expense 必须各不相同（核心契约）"

    # 清理
    with Database() as db:
        db.c.execute('DELETE FROM bill WHERE user_id=%s', (uid,))
        db.c.execute('DELETE FROM users WHERE id=%s', (uid,))
        db.conn.commit()
    remove_token(token)


def test_category_breakdown_differs_by_range():
    """分类汇总也按时间范围过滤"""
    suffix = str(int(time.time() * 1000))[-8:]
    with Database() as db:
        db.c.execute('INSERT INTO users (username, password) VALUES (%s, %s)',
                     (f'catrange_{suffix}', 'x'))
        uid = db.c.lastrowid
        db.conn.commit()

    add_record('2026-04-15', 100, 'expense', '餐饮', '', uid)
    add_record('2026-05-15', 200, 'expense', '购物', '', uid)
    add_record('2026-06-15', 300, 'expense', '交通', '', uid)

    token = f'cr_tok_{suffix}'
    set_token(token, uid)
    from gerenjizhang.app import app
    app.config['TESTING'] = True
    c = app.test_client()
    h = {'Authorization': f'Bearer {token}'}

    # 4 月
    r4 = c.get('/api/stats/category?start=2026-04-01&end=2026-05-01', headers=h).get_json()['data']
    cats4 = {x['category']: x['amount'] for x in r4}
    assert cats4 == {'餐饮': 100}, f"4月分类应只有餐饮=100, 实际 {cats4}"

    # 5 月
    r5 = c.get('/api/stats/category?start=2026-05-01&end=2026-06-01', headers=h).get_json()['data']
    cats5 = {x['category']: x['amount'] for x in r5}
    assert cats5 == {'购物': 200}, f"5月分类应只有购物=200, 实际 {cats5}"

    # 6 月
    r6 = c.get('/api/stats/category?start=2026-06-01&end=2026-07-01', headers=h).get_json()['data']
    cats6 = {x['category']: x['amount'] for x in r6}
    assert cats6 == {'交通': 300}, f"6月分类应只有交通=300, 实际 {cats6}"

    # 清理
    with Database() as db:
        db.c.execute('DELETE FROM bill WHERE user_id=%s', (uid,))
        db.c.execute('DELETE FROM users WHERE id=%s', (uid,))
        db.conn.commit()
    remove_token(token)
