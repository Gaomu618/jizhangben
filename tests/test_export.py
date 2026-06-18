"""
导出接口回归测试

历史教训：之前 export_bill 函数内部用了 `datetime.now()` 但没 import datetime，
返回 500 NameError。因为前端没接这个接口（用 raw fetch 走的另一条路），
bug 一直藏着没被发现。这次用 vitest 风格的端到端测试 + Python 集成测试护栏。
"""
import time
import sys

sys.path.insert(0, '.')

from gerenjizhang.db import Database, add_record
from gerenjizhang.utils.decorators import set_token, remove_token


def test_export_csv():
    """GET /api/bill/export?format=csv → 200 + text/csv"""
    suffix = str(int(time.time() * 1000))[-8:]
    with Database() as db:
        db.c.execute('INSERT INTO users (username, password) VALUES (%s, %s)',
                     (f'expcsv_{suffix}', 'x'))
        uid = db.c.lastrowid
        db.conn.commit()

    add_record('2026-06-01', 100, 'expense', '餐饮', '', uid)
    add_record('2026-06-02', 200, 'expense', '交通', '', uid)

    token = f'expcsv_{suffix}'
    set_token(token, uid)
    from gerenjizhang.app import app
    app.config['TESTING'] = True
    c = app.test_client()
    h = {'Authorization': f'Bearer {token}'}

    r = c.get('/api/bill/export?format=csv&year=2026&month=6', headers=h)
    assert r.status_code == 200, f"期望 200, 实际 {r.status_code}"
    assert 'text/csv' in r.headers.get('Content-Type', ''), \
        f"期望 text/csv, 实际 {r.headers.get('Content-Type')}"
    body = r.data.decode('utf-8')
    assert '餐饮' in body, "CSV 应包含餐饮"
    assert '交通' in body, "CSV 应包含交通"
    assert '100' in body and '200' in body, "CSV 应包含金额"

    # 清理
    with Database() as db:
        db.c.execute('DELETE FROM bill WHERE user_id=%s', (uid,))
        db.c.execute('DELETE FROM users WHERE id=%s', (uid,))
        db.conn.commit()
    remove_token(token)


def test_export_xlsx():
    """GET /api/bill/export?format=xlsx → 200 + spreadsheetml"""
    suffix = str(int(time.time() * 1000))[-8:]
    with Database() as db:
        db.c.execute('INSERT INTO users (username, password) VALUES (%s, %s)',
                     (f'expxlsx_{suffix}', 'x'))
        uid = db.c.lastrowid
        db.conn.commit()

    add_record('2026-06-01', 100, 'expense', '餐饮', '', uid)

    token = f'expxlsx_{suffix}'
    set_token(token, uid)
    from gerenjizhang.app import app
    app.config['TESTING'] = True
    c = app.test_client()
    h = {'Authorization': f'Bearer {token}'}

    r = c.get('/api/bill/export?format=xlsx&year=2026&month=6', headers=h)
    assert r.status_code == 200
    assert 'spreadsheetml' in r.headers.get('Content-Type', ''), \
        f"期望 spreadsheetml, 实际 {r.headers.get('Content-Type')}"
    assert len(r.data) > 1000, f"XLSX 应至少 1KB, 实际 {len(r.data)}B"

    with Database() as db:
        db.c.execute('DELETE FROM bill WHERE user_id=%s', (uid,))
        db.c.execute('DELETE FROM users WHERE id=%s', (uid,))
        db.conn.commit()
    remove_token(token)


def test_export_uses_year_month():
    """导出按 year/month 过滤（不是返回所有数据）"""
    suffix = str(int(time.time() * 1000))[-8:]
    with Database() as db:
        db.c.execute('INSERT INTO users (username, password) VALUES (%s, %s)',
                     (f'expflt_{suffix}', 'x'))
        uid = db.c.lastrowid
        db.conn.commit()

    # 4月 + 5月 各加 1 条
    add_record('2026-04-10', 100, 'expense', '餐饮', '', uid)
    add_record('2026-05-10', 200, 'expense', '交通', '', uid)

    token = f'expflt_{suffix}'
    set_token(token, uid)
    from gerenjizhang.app import app
    app.config['TESTING'] = True
    c = app.test_client()
    h = {'Authorization': f'Bearer {token}'}

    # 只导出 4月
    r = c.get('/api/bill/export?format=csv&year=2026&month=4', headers=h)
    body = r.data.decode('utf-8')
    assert '餐饮' in body, "4月导出应包含餐饮"
    assert '交通' not in body, "4月导出不应包含交通（5月的数据）"

    with Database() as db:
        db.c.execute('DELETE FROM bill WHERE user_id=%s', (uid,))
        db.c.execute('DELETE FROM users WHERE id=%s', (uid,))
        db.conn.commit()
    remove_token(token)
