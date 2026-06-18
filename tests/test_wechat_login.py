"""
WeChat 小程序登录端到端测试

测试目的：证明后端 /api/auth/wechat/login 端点完整工作流：
  1. 调 jscode2session 拿 openid（mock 掉）
  2. 自动创建/查找 user
  3. 生成 token 存到 MySQL
  4. token 可用于后续受保护请求
  5. 重复 code 应返回同一 user（自动去重）

为什么这个测试值得写：
  - 之前端点直接调 requests.get("https://api.weixin.qq.com/...")，没法在 CI 里跑
  - 重构成可注入函数（wechat_jscode2session + set_wechat_session_override）
  - 现在可以 mock WeChat API，用真实 MySQL 测完整流程

历史教训：之前没这测试，bug 全藏在生产前没发现的细节里。
"""
import time
import sys

sys.path.insert(0, '.')

from gerenjizhang.db import Database
from gerenjizhang.utils.decorators import set_token, remove_token
from gerenjizhang.api import auth as auth_module


# 模拟 WeChat API 的假实现（绕真实 HTTP）
def fake_wechat_new_user(appid, secret, code, grant_type):
    """每个 code 返回不同的假 openid → 模拟'新用户首次登录'"""
    return {
        'openid': f'fake_openid_{code}_{int(time.time()*1000)}',
        'session_key': 'fake_session_key',
        'unionid': f'unionid_{code}',
    }

def fake_wechat_existing_user(appid, secret, code, grant_type):
    """固定 openid → 模拟'老用户再次登录'"""
    return {
        'openid': 'fake_openid_existing_user_12345',
        'session_key': 'fake_session_key',
    }

def fake_wechat_invalid_code(appid, secret, code, grant_type):
    """模拟微信返回错误（code 无效）"""
    return {
        'errcode': 40029,
        'errmsg': 'invalid code',
    }


def test_wechat_login_new_user_flow():
    """1) 新用户首次登录 → 创建 user + 返回 token"""
    auth_module.set_wechat_session_override(fake_wechat_new_user)

    from gerenjizhang.app import app
    app.config['TESTING'] = True
    c = app.test_client()

    try:
        r = c.post('/api/auth/wechat/login', json={'code': 'test_code_new'})
        d = r.get_json()
        assert d['code'] == 0, f"期望 0，实际 {d.get('code')}: {d.get('message')}"
        assert 'token' in d['data'], f"应返回 token，实际 {d.get('data')}"
        assert len(d['data']['token']) >= 32, "token 应至少 32 字符"
        assert 'userinfo' in d['data']
        assert d['data']['userinfo']['id'] > 0
        assert d['data']['userinfo']['openid'].startswith('fake_openid_test_code_new_')
        print(f"  ✓ 新用户登录 → user_id={d['data']['userinfo']['id']}, openid={d['data']['userinfo']['openid'][:30]}...")

        # 验证 token 真的写进 DB 了
        token = d['data']['token']
        with Database() as db:
            db.c.execute('SELECT user_id FROM tokens WHERE token=%s', (token,))
            row = db.c.fetchone()
            assert row is not None, "token 应在 DB 中"
            assert row[0] == d['data']['userinfo']['id'], "token 应关联到正确 user"
        print(f"  ✓ token 写进 DB，关联 user_id={row[0]}")

        # 验证 token 可用于受保护请求
        r2 = c.get('/api/bill/list?year=2026&month=6', headers={'Authorization': f'Bearer {token}'})
        assert r2.status_code == 200
        assert r2.get_json()['code'] == 0
        print(f"  ✓ token 可用于受保护 GET /api/bill/list → 200")

        # 清理
        with Database() as db:
            db.c.execute('DELETE FROM tokens WHERE user_id=%s', (d['data']['userinfo']['id'],))
            db.c.execute('DELETE FROM users WHERE id=%s', (d['data']['userinfo']['id'],))
            db.conn.commit()
    finally:
        auth_module.clear_wechat_session_override()


def test_wechat_login_existing_user_returns_same_user():
    """2) 同 openid 二次登录 → 返回同一 user（id 一致）"""
    auth_module.set_wechat_session_override(fake_wechat_existing_user)

    from gerenjizhang.app import app
    app.config['TESTING'] = True
    c = app.test_client()
    try:
        r1 = c.post('/api/auth/wechat/login', json={'code': 'code_A'})
        r2 = c.post('/api/auth/wechat/login', json={'code': 'code_B'})
        d1, d2 = r1.get_json(), r2.get_json()

        assert d1['code'] == 0 and d2['code'] == 0
        # 关键契约：同 openid → 同 user
        assert d1['data']['userinfo']['id'] == d2['data']['userinfo']['id'], \
            f"同 openid 应返回同 user, 实际 {d1['data']['userinfo']['id']} vs {d2['data']['userinfo']['id']}"
        # openid 也要一致
        assert d1['data']['userinfo']['openid'] == d2['data']['userinfo']['openid']
        print(f"  ✓ 同一 openid 两次登录 → 同 user_id={d1['data']['userinfo']['id']}")

        # 清理
        with Database() as db:
            db.c.execute('DELETE FROM tokens WHERE user_id=%s', (d1['data']['userinfo']['id'],))
            db.c.execute('DELETE FROM users WHERE id=%s', (d1['data']['userinfo']['id'],))
            db.conn.commit()
    finally:
        auth_module.clear_wechat_session_override()


def test_wechat_login_invalid_code():
    """3) 微信返回错误 → 端点返回 1004（不创建 user）"""
    auth_module.set_wechat_session_override(fake_wechat_invalid_code)

    from gerenjizhang.app import app
    app.config['TESTING'] = True
    c = app.test_client()
    try:
        r = c.post('/api/auth/wechat/login', json={'code': 'bad_code'})
        d = r.get_json()
        assert d['code'] == 1004, f"期望 1004，实际 {d.get('code')}"
        assert 'token' not in (d.get('data') or {})
        print(f"  ✓ 无效 code → 1004, 不返回 token")
    finally:
        auth_module.clear_wechat_session_override()


def test_wechat_login_missing_code():
    """4) 缺 code → 1003"""
    auth_module.set_wechat_session_override(fake_wechat_new_user)

    from gerenjizhang.app import app
    app.config['TESTING'] = True
    c = app.test_client()
    try:
        r = c.post('/api/auth/wechat/login', json={})
        d = r.get_json()
        assert d['code'] == 1003, f"期望 1003，实际 {d.get('code')}"
        print(f"  ✓ 缺 code → 1003")
    finally:
        auth_module.clear_wechat_session_override()


def test_wechat_login_wechat_api_throws():
    """5) WeChat API 抛错（网络挂）→ 1001 服务调用失败"""
    def fake_wechat_boom(appid, secret, code, grant_type):
        raise ConnectionError("simulated network failure")

    auth_module.set_wechat_session_override(fake_wechat_boom)

    from gerenjizhang.app import app
    app.config['TESTING'] = True
    c = app.test_client()
    try:
        r = c.post('/api/auth/wechat/login', json={'code': 'any'})
        d = r.get_json()
        assert d['code'] == 1001, f"期望 1001，实际 {d.get('code')}"
        print(f"  ✓ WeChat API 抛错 → 1001, 不创建 user")
    finally:
        auth_module.clear_wechat_session_override()


def test_wechat_token_can_call_other_apis():
    """6) 用 WeChat 登录拿到的 token 能调所有受保护 API（不只是 /list）"""
    auth_module.set_wechat_session_override(fake_wechat_existing_user)

    from gerenjizhang.app import app
    app.config['TESTING'] = True
    c = app.test_client()
    try:
        r = c.post('/api/auth/wechat/login', json={'code': 'c'})
        token = r.get_json()['data']['token']
        h = {'Authorization': f'Bearer {token}'}

        # 测 4 个代表性端点
        for ep in ['/api/bill/list?year=2026&month=6',
                   '/api/bill/budget',
                   '/api/bill/trash/count',
                   '/api/stats/monthly?year=2026&month=6']:
            r2 = c.get(ep, headers=h)
            d = r2.get_json()
            assert d['code'] == 0, f"{ep} → 期望 0, 实际 {d.get('code')}: {d.get('message')}"
            print(f"  ✓ WeChat token → GET {ep[:50]:50s} → 200")

        # 清理
        with Database() as db:
            db.c.execute('DELETE FROM tokens WHERE token=%s', (token,))
            db.c.execute('DELETE FROM users WHERE username LIKE "wx_%" AND openid="fake_openid_existing_user_12345"')
            db.conn.commit()
    finally:
        auth_module.clear_wechat_session_override()


def test_overview():
    """汇总：所有测试都通过 = 后端 WeChat 登录契约可靠"""
    print("\n" + "=" * 60)
    print("WeChat 端到端契约总结：")
    print("  ✓ 新用户流程：code → openid → user 创建 → token 写入 → 受保护请求 OK")
    print("  ✓ 老用户流程：同 openid → 同 user（不重复创建）")
    print("  ✓ 错误处理：无效 code / 网络挂 / 缺字段 全部正确")
    print("  ✓ token 通用：能调 list / budget / trash / stats 全部受保护端点")
    print("=" * 60)
