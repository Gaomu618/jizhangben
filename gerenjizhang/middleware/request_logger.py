"""
中间件 - 请求日志
"""
import time
import logging

logger = logging.getLogger(__name__)


def register_request_logger(app):
    """注册请求日志中间件"""

    @app.before_request
    def before_request():
        """请求开始前记录时间"""
        from flask import request
        request.start_time = time.time()

    @app.after_request
    def after_request(response):
        """请求完成后记录日志"""
        from flask import request
        if hasattr(request, 'start_time'):
            elapsed = time.time() - request.start_time
            logger.info(
                f"{request.method} {request.path} - "
                f"Status: {response.status_code} - "
                f"Duration: {elapsed*1000:.2f}ms"
            )
        return response