"""
限流中间件 — Flask-Limiter 集成
- 默认 200/分钟 保护 API
- 认证端点（login / wechat-login / register）收紧到 10/分钟
- 导入端点（import）收紧到 5/分钟（重操作，单独限流）
- 失败响应统一从 error_handler 走 429 路径
"""
import logging
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

logger = logging.getLogger(__name__)

# 延迟初始化（避免 import 时就绑死 app）
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per minute"],
    storage_uri="memory://",  # 单进程内存；多进程/多机部署时换 Redis
    headers_enabled=True,  # 在响应里加 X-RateLimit-* 头，方便客户端调试
)


def init_limiter(app):
    """把 limiter 绑到 app + 注册错误处理"""
    limiter.init_app(app)

    @app.errorhandler(429)
    def rate_limit_handler(e):
        # 让 error_handler 的 429 接管；这里只打日志
        logger.warning(f"[rate-limit] {e.description}")
        from flask import jsonify
        return jsonify({
            "code": 429,
            "message": "请求过于频繁，请稍后再试",
            "data": None
        }), 429
