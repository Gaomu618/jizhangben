"""
预算提醒服务

设计原则：克制 > 覆盖
- 同规则同用户每天最多推 1 次（has_notification_today）
- 只在真正有信息量的时刻推（80%、100%、大额、未记账）
- 记录所有触发的提醒，便于后续调优

包含三条规则：
  Rule 1: 单分类预算 80% / 100% 预警
  Rule 2: 单笔异常大额消费（> 月日均 5 倍）
  Rule 3: 连续 3 天没记账（召回用户）
"""
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# ===== Rule 1: 预算预警阈值 =====
BUDGET_WARN_THRESHOLD = 80   # 80% 预警
BUDGET_OVER_THRESHOLD = 100  # 100% 超支

# ===== Rule 2: 大额消费阈值 =====
LARGE_AMOUNT_MULTIPLIER = 5   # 单笔 > 月日均 * 5 倍
LARGE_AMOUNT_MIN = 500        # 单笔最少 500 元才触发（避免 10 块、20 块噪音）

# ===== Rule 3: 未记账天数阈值 =====
INACTIVE_DAYS = 3             # 连续 3 天没记账才触发


def check_budget_alerts(user_id, year=None, month=None):
    """检查某用户的预算，触发该推的提醒（Rule 1）

    Args:
        user_id: 用户 ID
        year, month: 检查哪个月份（默认当月）

    Returns:
        list[dict]: 本次触发的提醒列表
    """
    if not user_id:
        return []

    from gerenjizhang.db import (
        get_budgets, get_records,
        has_notification_today, save_notification_log
    )

    now = datetime.now()
    year = year or now.year
    month = month or now.month

    budgets = get_budgets(user_id, f"{year}-{month:02d}")
    if not budgets:
        return []

    # 计算当月每个分类的实际支出
    start = f"{year}-{month:02d}-01"
    end = f"{year+1}-01-01" if month == 12 else f"{year}-{month+1:02d}-01"
    records = get_records(user_id, start_date=start, end_date=end, type_filter='expense')
    spent_map = {}
    for r in records:
        cat = r[4]
        spent_map[cat] = spent_map.get(cat, 0) + float(r[2])

    triggered = []
    for cat, budget_amount in budgets:
        amt = float(budget_amount)
        spent = spent_map.get(cat, 0)
        if amt <= 0:
            continue
        percent = round(spent / amt * 100, 1)

        rule_type = None
        msg = None
        if percent >= BUDGET_OVER_THRESHOLD:
            rule_type = 'budget_over'
            over_amount = spent - amt
            msg = f"{cat}本月已超支 ¥{over_amount:.0f}（预算 ¥{amt:.0f}）"
        elif percent >= BUDGET_WARN_THRESHOLD:
            rule_type = 'budget_warn'
            remaining = max(0, amt - spent)
            msg = f"{cat}本月已用 {percent:.0f}%，剩 ¥{remaining:.0f}"

        if not rule_type:
            continue

        if has_notification_today(user_id, rule_type):
            continue

        save_notification_log(user_id, rule_type)
        triggered.append({
            'rule_type': rule_type,
            'category': cat,
            'percent': percent,
            'spent': spent,
            'budget': amt,
            'message': msg
        })
        _try_send(user_id, rule_type, msg, category=cat, percent=percent)

    if triggered:
        logger.info(f"[rule1 budget] user={user_id} 触发 {len(triggered)} 条")
    return triggered


def check_large_amount(user_id, year=None, month=None):
    """Rule 2: 检测异常大额消费

    触发条件：本月某笔支出 > 当月日均支出 * LARGE_AMOUNT_MULTIPLIER
             且金额本身 >= LARGE_AMOUNT_MIN

    注意：**当天**已经产生了一笔大额就要推，不要等月底看。
    所以本规则不是扫历史，而是由"新建账单"事件实时触发（参见 record_added hook）。
    """
    # 这里保留入口给 cron 调用，但默认实现是空（事件驱动更准）
    return []


def check_large_amount_for_record(user_id, amount, category, note=''):
    """Rule 2 实时版本：刚加了一笔账单时调用，判断是否构成大额

    Args:
        user_id, amount, category: 新增账单的字段
        note: 备注（用于过滤退款等场景）

    Returns:
        dict or None: 触发的提醒详情（不触发则返回 None）
    """
    if not user_id or amount is None or amount < LARGE_AMOUNT_MIN:
        return None

    # 排除退款 / 收入类大额（误报率高）
    if note:
        nl = note.lower()
        if any(k in nl for k in ('退款', '退还', '红包退回', '转账收入')):
            return None

    from gerenjizhang.db import (
        get_records, has_notification_today, save_notification_log
    )

    now = datetime.now()
    start = f"{now.year}-{now.month:02d}-01"
    end = f"{now.year+1}-01-01" if now.month == 12 else f"{now.year}-{now.month+1:02d}-01"

    # 算本月至今的日均支出（不含这一笔）
    records = get_records(user_id, start_date=start, end_date=end, type_filter='expense')
    if not records:
        return None
    total_spent = sum(float(r[2]) for r in records)
    days_passed = max(1, now.day)  # 至少算 1 天
    daily_avg = total_spent / days_passed

    # 判断是不是异常大额
    if amount < daily_avg * LARGE_AMOUNT_MULTIPLIER:
        return None

    rule_type = 'large_amount'

    # 频率控制
    if has_notification_today(user_id, rule_type):
        return None

    msg = f"刚有一笔 ¥{amount:.0f}（{category}），超出本月日均 ¥{daily_avg:.0f} 的 {LARGE_AMOUNT_MULTIPLIER} 倍"
    save_notification_log(user_id, rule_type)
    triggered = {
        'rule_type': rule_type,
        'category': category,
        'amount': amount,
        'daily_avg': round(daily_avg, 1),
        'message': msg
    }
    _try_send(user_id, rule_type, msg, category=category, percent=None)
    logger.info(f"[rule2 large] user={user_id} 触发：{msg}")
    return triggered


def check_inactive(user_id):
    """Rule 3: 检测连续 N 天没记账

    Returns:
        dict or None
    """
    if not user_id:
        return None

    from gerenjizhang.db import get_records, has_notification_today, save_notification_log

    # 找用户最近一笔账的日期
    # 复用 get_records，按日期倒序取 1 条
    records = get_records(user_id, limit=1, offset=0)  # 不传日期范围 → 全部记录
    if not records:
        # 从未记过账的新用户不打扰（让他自己玩够了再推）
        return None

    last_date_str = records[0][1]  # 第 2 列是 date（YYYY-MM-DD）
    try:
        last_date = datetime.strptime(last_date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None

    days_idle = (datetime.now().date() - last_date).days
    if days_idle < INACTIVE_DAYS:
        return None

    rule_type = 'inactive'
    if has_notification_today(user_id, rule_type):
        return None

    msg = f"已经 {days_idle} 天没记账了，是不是漏了几笔？"
    save_notification_log(user_id, rule_type)
    triggered = {
        'rule_type': rule_type,
        'days_idle': days_idle,
        'last_date': last_date_str,
        'message': msg
    }
    _try_send(user_id, rule_type, msg, category=None, percent=None)
    logger.info(f"[rule3 inactive] user={user_id} 触发：{msg}")
    return triggered


def check_all_for_user(user_id, year=None, month=None):
    """统一入口：一次跑完三条规则

    Returns:
        list[dict]: 本次触发的所有提醒
    """
    if not user_id:
        return []

    triggered = []
    triggered.extend(check_budget_alerts(user_id, year=year, month=month))
    # 大额规则改成事件驱动，不在这里跑（避免重复推）
    inactive = check_inactive(user_id)
    if inactive:
        triggered.append(inactive)
    return triggered


def check_all_users(year=None, month=None):
    """遍历所有用户跑检查（定时任务入口）

    Returns:
        int: 触发的提醒总条数
    """
    from gerenjizhang.db import Database

    try:
        with Database() as db:
            db.c.execute('SELECT id FROM users')
            user_ids = [row[0] for row in db.c.fetchall()]
    except Exception as e:
        logger.error(f"check_all_users 取用户列表失败: {e}")
        return 0

    total = 0
    for uid in user_ids:
        try:
            triggered = check_all_for_user(uid, year=year, month=month)
            total += len(triggered)
        except Exception as e:
            logger.error(f"check_all_for_user user={uid} 失败: {e}")
            continue

    logger.info(f"[scheduler] 扫了 {len(user_ids)} 个用户，触发 {total} 条提醒")
    return total


# ============ 内部工具 ============
def _try_send(user_id, rule_type, message, category=None, percent=None):
    """调用下发（占位，捕获异常不让定时任务崩）"""
    try:
        send_subscribe_message(user_id, rule_type, message, category, percent)
    except Exception as e:
        logger.error(f"下发订阅消息失败: {e}")


def send_subscribe_message(user_id, rule_type, message, category, percent):
    """下发微信订阅消息（占位实现）

    上线时需要：
    1. 服务端用 appid + secret 拿 access_token（缓存 7200s）
    2. POST https://api.weixin.qq.com/cgi-bin/message/subscribe/send
    3. 传 touser (openid)、template_id、data { thing, amount, phrase }

    当前阶段：仅写日志，等模板申请下来再接
    """
    logger.info(
        f"[subscribe_message stub] user={user_id} rule={rule_type} "
        f"category={category} percent={percent} msg={message}"
    )