"""
通知提醒 API
- /api/notification/check: 手动触发当前用户的预算检查（用户主动行为）
- /api/notification/subscribe-budget: 申请订阅消息授权（前端拉授权时调用，拿 openid 等）
"""
from flask import Blueprint, request
from gerenjizhang.utils.response import success_response, error_response
from gerenjizhang.utils.decorators import login_required
from gerenjizhang.services.notification_service import check_budget_alerts

notification_bp = Blueprint('notification', __name__, url_prefix='/api/notification')


@notification_bp.route('/check', methods=['POST'])
@login_required
def check_alerts(user_id):
    """手动触发：检查当前用户的预算预警

    前端在用户打开 App、进入首页或设置预算后调用。
    服务端判断要不要推（已经在频率控制内就不推）。
    """
    data = request.get_json(silent=True) or {}
    year = data.get('year')
    month = data.get('month')

    try:
        triggered = check_budget_alerts(user_id, year=year, month=month)
        return success_response({
            'triggered_count': len(triggered),
            'triggered': triggered  # 前端可以用它做本地弹窗提示
        }, message=f"检查完成，触发 {len(triggered)} 条")
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"check_alerts 失败: {e}")
        return error_response(7001, f"检查失败: {str(e)}")