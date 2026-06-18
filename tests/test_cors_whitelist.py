"""
CORS 白名单测试

历史教训：当前 CORS 是 `Access-Control-Allow-Origin: <echoed Origin>`，等于
"任何 origin 都能调"。生产环境微信小程序需要白名单（只允许配置过的域名），
否则恶意网站也能调 API。

重构：CORS 改为白名单模式，从配置 CORS_ALLOWED_ORIGINS 读（环境变量驱动）。
"""
import os
import sys
import importlib

sys.path.insert(0, '.')


def _reload_app_with_cors(origins_csv):
    """用指定的白名单重置 Flask app"""
    os.environ['CORS_ALLOWED_ORIGINS'] = origins_csv
    # 重新加载 app 模块（让它读新的 env var）
    import gerenjizhang.app as app_mod
    importlib.reload(app_mod)
    import gerenjizhang.config as config_mod
    importlib.reload(config_mod)
    return app_mod


def test_allowed_origin_gets_echoed(monkeypatch):
    """白名单内的 origin → Access-Control-Allow-Origin 回显该 origin"""
    _reload_app_with_cors('https://example.com,https://weixin.qq.com')

    from gerenjizhang.app import app
    c = app.test_client()
    r = c.get('/api/health', headers={'Origin': 'https://example.com'})

    assert r.headers.get('Access-Control-Allow-Origin') == 'https://example.com', \
        f"白名单 origin 应被回显，实际 {r.headers.get('Access-Control-Allow-Origin')}"
    assert r.headers.get('Access-Control-Allow-Credentials') == 'true'
    print(f"  ✓ 白名单 origin → Access-Control-Allow-Origin: https://example.com")


def test_blocked_origin_no_cors_header(monkeypatch):
    """非白名单 origin → 不返回 Access-Control-Allow-Origin（浏览器会 block）"""
    _reload_app_with_cors('https://example.com')

    from gerenjizhang.app import app
    c = app.test_client()
    r = c.get('/api/health', headers={'Origin': 'https://evil.com'})

    # 关键契约：不被白名单的 origin 不能拿到 CORS 头
    cors = r.headers.get('Access-Control-Allow-Origin', None)
    assert cors is None, \
        f"非白名单 origin 应**没有** CORS 头，实际 {cors}"
    # 状态码仍然是 200（服务器响应正常，但浏览器会因 CORS 拦截）
    assert r.status_code == 200
    print(f"  ✓ 非白名单 origin → 无 CORS 头（浏览器拦截）")


def test_no_origin_header(monkeypatch):
    """没有 Origin 头（如服务端调用、Postman）→ 不返回 CORS 头（不影响功能）"""
    _reload_app_with_cors('https://example.com')

    from gerenjizhang.app import app
    c = app.test_client()
    r = c.get('/api/health')
    assert r.status_code == 200
    assert r.headers.get('Access-Control-Allow-Origin') is None
    print(f"  ✓ 无 Origin 头 → 200, 无 CORS 头（不影响 curl/Postman）")


def test_options_preflight_includes_methods_and_headers(monkeypatch):
    """OPTIONS 预检请求 → 必须返回允许的方法 + 头"""
    _reload_app_with_cors('https://example.com')

    from gerenjizhang.app import app
    c = app.test_client()
    r = c.options('/api/bill/add', headers={
        'Origin': 'https://example.com',
        'Access-Control-Request-Method': 'POST',
        'Access-Control-Request-Headers': 'Content-Type, Authorization',
    })

    allow_methods = r.headers.get('Access-Control-Allow-Methods', '')
    allow_headers = r.headers.get('Access-Control-Allow-Headers', '')

    assert 'POST' in allow_methods, f"POST 应在 allow methods，实际 {allow_methods}"
    assert 'Authorization' in allow_headers, \
        f"Authorization 应在 allow headers，实际 {allow_headers}"
    assert 'Content-Type' in allow_headers
    print(f"  ✓ OPTIONS 预检 → methods={allow_methods}, headers={allow_headers}")


def test_localhost_always_allowed_in_dev(monkeypatch):
    """开发模式（白名单空）→ 自动允许 localhost 各种端口（开发体验）"""
    _reload_app_with_cors('')  # 空白名单

    from gerenjizhang.app import app
    c = app.test_client()
    for port in ['3000', '5173', '8080']:
        r = c.get('/api/health', headers={'Origin': f'http://localhost:{port}'})
        cors = r.headers.get('Access-Control-Allow-Origin')
        assert cors == f'http://localhost:{port}', \
            f"dev 模式应允许 localhost:{port}，实际 {cors}"
    print(f"  ✓ dev 模式（空白名单）→ 自动允许 localhost:3000/5173/8080")


def test_wildcard_subdomain_match(monkeypatch):
    """通配符 *.weixin.qq.com 应匹配 mp/api/long.open 等子域"""
    _reload_app_with_cors('*.weixin.qq.com')

    from gerenjizhang.app import app
    c = app.test_client()
    for sub in ['https://mp.weixin.qq.com', 'https://api.weixin.qq.com', 'https://long.open.weixin.qq.com']:
        r = c.get('/api/health', headers={'Origin': sub})
        cors = r.headers.get('Access-Control-Allow-Origin')
        assert cors == sub, f"通配符应匹配 {sub}，实际 {cors}"
    print(f"  ✓ *.weixin.qq.com → 匹配 mp/api/long.open 等子域")


def test_wildcard_does_not_match_unrelated(monkeypatch):
    """通配符 *.weixin.qq.com 不应匹配无关域"""
    _reload_app_with_cors('*.weixin.qq.com')

    from gerenjizhang.app import app
    c = app.test_client()
    r = c.get('/api/health', headers={'Origin': 'https://evil.com'})
    assert r.headers.get('Access-Control-Allow-Origin') is None, \
        "无关域不应被通配符匹配"
    # 同样的 origin 字符串里包含 weixin.qq.com 也不行（fnmatch 严格匹配模式）
    r2 = c.get('/api/health', headers={'Origin': 'https://attacker.com/?redirect=weixin.qq.com'})
    assert r2.headers.get('Access-Control-Allow-Origin') is None, \
        "应防止 URL 字符串包含域名的攻击"
    print(f"  ✓ *.weixin.qq.com 不匹配 evil.com / 字符串钓鱼")


def test_mixed_exact_and_wildcard(monkeypatch):
    """白名单可以混搭：精确 origin + 通配符"""
    _reload_app_with_cors('https://my-app.com,*.weixin.qq.com,https://staging.com')

    from gerenjizhang.app import app
    c = app.test_client()
    # 三种都应允许
    for origin in ['https://my-app.com', 'https://mp.weixin.qq.com', 'https://staging.com']:
        r = c.get('/api/health', headers={'Origin': origin})
        assert r.headers.get('Access-Control-Allow-Origin') == origin, \
            f"应允许 {origin}，实际 {r.headers.get('Access-Control-Allow-Origin')}"
    # 不在白名单的应被拒
    r = c.get('/api/health', headers={'Origin': 'https://blocked.com'})
    assert r.headers.get('Access-Control-Allow-Origin') is None
    print(f"  ✓ 混搭白名单（精确 + 通配符）正确生效")


def test_overview():
    print("\n" + "=" * 60)
    print("CORS 白名单契约总结：")
    print("  ✓ 白名单 origin → 回显（小程序合法域名能调）")
    print("  ✓ 非白名单 origin → 无 CORS 头（浏览器拦截）")
    print("  ✓ 无 Origin 头 → 200 不影响 curl/Postman")
    print("  ✓ OPTIONS 预检 → 正确返回 methods/headers")
    print("  ✓ dev 模式 → localhost:* 自动允许")
    print("  ✓ 通配符 *.weixin.qq.com → 匹配子域")
    print("  ✓ 通配符不匹配无关域（防钓鱼）")
    print("  ✓ 精确 + 通配符混搭白名单")
    print("=" * 60)
