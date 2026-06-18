"""
中间件 - 错误处理
"""
import logging
from flask import jsonify
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    """注册错误处理器"""

    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({
            "code": 400,
            "message": "请求参数错误",
            "data": None
        }), 400

    @app.errorhandler(401)
    def unauthorized(e):
        return jsonify({
            "code": 401,
            "message": "未授权，请先登录",
            "data": None
        }), 401

    @app.errorhandler(403)
    def forbidden(e):
        return jsonify({
            "code": 403,
            "message": "禁止访问",
            "data": None
        }), 403

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({
            "code": 404,
            "message": "资源不存在",
            "data": None
        }), 404

    @app.errorhandler(429)
    def rate_limit(e):
        return jsonify({
            "code": 429,
            "message": "请求过于频繁，请稍后再试",
            "data": None
        }), 429

    @app.errorhandler(500)
    def internal_error(e):
        logger.error(f"Internal server error: {e}")
        return jsonify({
            "code": 500,
            "message": "服务器内部错误",
            "data": None
        }), 500

    @app.errorhandler(Exception)
    def handle_exception(e):
        # 处理 HTTP 异常
        if isinstance(e, HTTPException):
            return jsonify({
                "code": e.code,
                "message": e.description,
                "data": None
            }), e.code

        # 处理业务异常
        if isinstance(e, ValueError):
            return jsonify({
                "code": 400,
                "message": str(e),
                "data": None
            }), 400

        #记录未知异常
        logger.exception(f"Unhandled exception: {e}")
        return jsonify({
            "code": 500,
            "message": "服务器内部错误",
            "data": None
        }), 500