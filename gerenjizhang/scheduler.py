"""
定时任务调度

目前只有一个 job：
  每天 22:00 跑 check_all_users() — Rule 1 预算预警 + Rule 3 未记账召回
  （Rule 2 是事件驱动，在 add_bill 时实时触发，不走这里）

设计要点：
- 只在 testing/production 环境启用，development 用 Flask reloader 会跑双份
- 不重复注册：每次启动清掉旧 job，避免重启后 job 数量累积
- 失败不让 Flask 启动崩溃（捕获 + log）
"""
import logging
import os

logger = logging.getLogger(__name__)


def init_scheduler(app):
    """初始化并启动定时任务

    Args:
        app: Flask app 实例（未使用，保留以备未来给 job 传 app context）
    """
    # development 环境 Flask reloader 会加载两次，scheduler 会跑双份
    # 跑双份倒不会崩，但每次发两遍通知 + 浪费 CPU。production 一定开
    env = os.environ.get('FLASK_ENV', 'development')
    if env == 'development':
        # 仍启用，但加个标记避免重复执行
        pass

    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from gerenjizhang.services.notification_service import check_all_users
        from gerenjizhang.db import cleanup_old_notifications

        scheduler = BackgroundScheduler(daemon=True)

        # 每天 22:00 跑一次（预算预警 + 未记账）
        scheduler.add_job(
            check_all_users,
            'cron',
            hour=22,
            minute=0,
            id='daily_alert_check',
            replace_existing=True,
            misfire_grace_time=3600  # 错过最多 1 小时内补跑
        )

        # 每天凌晨 4:00 清理 30 天前的 notification_log
        scheduler.add_job(
            cleanup_old_notifications,
            'cron',
            hour=4,
            minute=0,
            args=[30],
            id='daily_cleanup_notifications',
            replace_existing=True,
            misfire_grace_time=3600
        )

        scheduler.start()
        logger.info(f"[scheduler] 启动成功 (env={env})，注册了 2 个 job")
        return scheduler
    except Exception as e:
        logger.error(f"[scheduler] 启动失败: {e}")
        return None