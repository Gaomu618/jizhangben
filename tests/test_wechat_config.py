"""
WeChat 配置可注入性测试（重构后）

历史教训：WECHAT_APPID / WECHAT_SECRET 之前硬编码在源码里，CI 测不到，
推到 Git 公开后会被刷库。重构后：
  1. 全部从环境变量读
  2. 没有硬编码 fallback（避免静默用错的值）
  3. 启动时 validate() 校验：缺 env 立即 raise
  4. TESTING 模式跳过校验（让 CI 跑通）

契约：
  - 未设 env + 非 TESTING → get_config() raise RuntimeError
  - 未设 env + TESTING → get_config() 返回，WECHAT_APPID/SECRET 为 None
  - 设了 env → config 拿到 env 值
  - wechat_login 端点实际把 env 值传给 jscode2session（不只是改了常量）
"""
import os
import sys
import importlib

sys.path.insert(0, '.')


def _reload_config(flask_env='development'):
    """重置 env vars 重新加载 config 模块"""
    os.environ['FLASK_ENV'] = flask_env
    import gerenjizhang.config as config_mod
    importlib.reload(config_mod)
    return config_mod


def test_missing_env_raises_in_production(monkeypatch):
    """生产/开发模式缺 WECHAT_APPID → 启动失败（fail fast）"""
    monkeypatch.delenv('WECHAT_APPID', raising=False)
    monkeypatch.delenv('WECHAT_SECRET', raising=False)

    config_mod = _reload_config('development')

    try:
        config_mod.get_config()
        assert False, "缺 env 应 raise RuntimeError"
    except RuntimeError as e:
        assert 'WECHAT_APPID' in str(e), f"错误应提到 WECHAT_APPID，实际: {e}"
        assert 'WECHAT_SECRET' in str(e)
        print(f"  ✓ 缺 env → RuntimeError fail-fast")
    finally:
        # 恢复
        monkeypatch.undo()


def test_missing_env_ok_in_testing(monkeypatch):
    """测试模式缺 env → 跳过校验（CI 可跑）"""
    monkeypatch.delenv('WECHAT_APPID', raising=False)
    monkeypatch.delenv('WECHAT_SECRET', raising=False)

    config_mod = _reload_config('testing')
    cfg = config_mod.get_config()

    assert cfg.WECHAT_APPID is None, "testing 模式不要求 env"
    assert cfg.WECHAT_SECRET is None
    print(f"  ✓ testing 模式缺 env → get_config() 正常返回")


def test_env_var_injected(monkeypatch):
    """设了 WECHAT_APPID/SECRET → config 拿到 env 值"""
    monkeypatch.setenv('WECHAT_APPID', 'wx_test_appid_123')
    monkeypatch.setenv('WECHAT_SECRET', 'test_secret_456')
    monkeypatch.setenv('FLASK_ENV', 'development')

    config_mod = _reload_config('development')
    cfg = config_mod.get_config()

    assert cfg.WECHAT_APPID == 'wx_test_appid_123'
    assert cfg.WECHAT_SECRET == 'test_secret_456'
    print(f"  ✓ env var → config.WECHAT_APPID/SECRET 正确读取")


def test_env_creds_passed_to_jscode2session(monkeypatch):
    """env 注入的 appid/secret 应该真传到 WeChat API（不是只改了常量）"""
    monkeypatch.setenv('WECHAT_APPID', 'wx_env_override_999')
    monkeypatch.setenv('WECHAT_SECRET', 'env_secret_999')
    monkeypatch.setenv('FLASK_ENV', 'testing')  # 跳过启动校验

    config_mod = _reload_config('testing')
    config_mod.get_config()  # 触发 validate（testing 模式跳过）

    import gerenjizhang.api.auth as auth_mod
    importlib.reload(auth_mod)

    # 用 wechat_jscode2session 的 override 抓取参数
    captured = {}
    def fake_capture(appid, secret, code, grant_type):
        captured['appid'] = appid
        captured['secret'] = secret
        captured['code'] = code
        return {'openid': f'oid_{code}'}
    auth_mod.set_wechat_session_override(fake_capture)

    try:
        from gerenjizhang.app import app
        c = app.test_client()
        c.post('/api/auth/wechat/login', json={'code': 'test_code_abc'})

        assert captured['appid'] == 'wx_env_override_999', \
            f"appid 应来自 env，实际 {captured['appid']}"
        assert captured['secret'] == 'env_secret_999', \
            f"secret 应来自 env，实际 {captured['secret']}"
        assert captured['code'] == 'test_code_abc'
        print(f"  ✓ env 注入的 appid/secret 真传到 WeChat API")
    finally:
        auth_mod.clear_wechat_session_override()


def test_no_hardcoded_fallback_anywhere():
    """源代码里没有 wx 开头的硬编码 AppID"""
    # 老的硬编码 fallback 是 wx5f6c28819df23a00 / aa75e6b15b08547efae322554083574d
    import subprocess
    result = subprocess.run(
        ['grep', '-rE', 'wx5f6c28819df23a00|aa75e6b15b08547efae322554083574d',
         'gerenjizhang/', '--include=*.py'],
        capture_output=True, text=True
    )
    assert result.stdout == '', \
        f"硬编码 AppID/Secret 应已清除，仍在:\n{result.stdout}"
    print(f"  ✓ 源码中无硬编码 AppID/Secret fallback")


def test_overview():
    print("\n" + "=" * 60)
    print("WeChat 配置可注入性（重构后）：")
    print("  ✓ 缺 env 启动 fail-fast（生产安全）")
    print("  ✓ testing 模式跳过校验（CI 可跑）")
    print("  ✓ env var 正确注入到 config")
    print("  ✓ env 注入的凭证真传到 WeChat API")
    print("  ✓ 源码中无硬编码 fallback")
    print("=" * 60)
