"""
预算管理：get / set / delete。
"""
import logging

from flask import request

from gerenjizhang.api.bill_bp import bill_bp
from gerenjizhang.db import get_budgets, save_budget, delete_budget, get_records
from gerenjizhang.utils.decorators import login_required
from gerenjizhang.utils.response import success_response, error_response

logger = logging.getLogger(__name__)


def _calc_budget_spent(user_id, year, month, bill_type='expense'):
    """计算某月某类型分类的支出总额，返回 {category: total}"""
    start = f"{year}-{month:02d}-01"
    end = f"{year}-{month+1:02d}-01" if month < 12 else f"{year+1}-01-01"
    records = get_records(user_id, start_date=start, end_date=end, type_filter=bill_type)
    sums = {}
    for r in records:
        cat = r[4]
        sums[cat] = sums.get(cat, 0) + float(r[2])
    return sums


@bill_bp.route('/budget', methods=['GET'])
@login_required
def get_user_budget(user_id):
    """获取当月所有预算（含 spent/percent/remaining）"""
    from datetime import datetime
    year = request.args.get('year', type=int) or datetime.now().year
    month = request.args.get('month', type=int) or datetime.now().month
    month_str = f"{year}-{month:02d}"

    budgets = get_budgets(user_id, month_str)
    spent_map = _calc_budget_spent(user_id, year, month)

    result = []
    for cat, amount in budgets:
        amt = float(amount)
        spent = spent_map.get(cat, 0)
        percent = round(spent / amt * 100, 1) if amt > 0 else 0
        result.append({
            'category': cat,
            'budget': amt,
            'spent': spent,
            'remaining': max(0, amt - spent),
            'percent': percent,
        })

    return success_response(result)


@bill_bp.route('/budget', methods=['POST'])
@login_required
def set_user_budget(user_id):
    """设置/更新某分类的预算（upsert）"""
    from datetime import datetime
    data = request.get_json() or {}
    category = (data.get('category') or '').strip()
    amount = data.get('amount')
    bill_type = data.get('type', 'expense')
    month = data.get('month') or f"{datetime.now().year}-{datetime.now().month:02d}"

    if not category:
        return error_response(3001, "请选择分类")
    try:
        amount = float(amount)
    except (ValueError, TypeError):
        return error_response(3002, "金额格式错误")
    if amount < 0:
        return error_response(3003, "金额不能为负数")

    try:
        save_budget(user_id, bill_type, category, amount, month)
        return success_response(message=f"已保存 {category} 预算 ¥{amount:.2f}")
    except Exception as e:
        logger.error(f"保存预算错误: {e}")
        return error_response(3004, f"保存失败: {str(e)}")


@bill_bp.route('/delete-budget', methods=['POST'])
@login_required
def delete_user_budget(user_id):
    """删除某分类某月的预算"""
    from datetime import datetime
    data = request.get_json() or {}
    category = (data.get('category') or '').strip()
    month = data.get('month') or f"{datetime.now().year}-{datetime.now().month:02d}"

    if not category:
        return error_response(3005, "请指定分类")

    try:
        affected = delete_budget(user_id, category, month)
        if affected == 0:
            return error_response(3007, "该分类当月未设置预算")
        if affected < 0:
            return error_response(3006, f"删除失败: 数据库错误")
        return success_response(message=f"已删除 {category} 预算")
    except Exception as e:
        logger.error(f"删除预算错误: {e}")
        return error_response(3006, f"删除失败: {str(e)}")
