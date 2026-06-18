from flask import Blueprint, request
from gerenjizhang.db import get_monthly_summary, get_category_summary, get_summary, get_daily_expense, get_top_records
from gerenjizhang.utils.response import success_response, error_response
from gerenjizhang.utils.decorators import login_required
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from collections import defaultdict

stats_bp = Blueprint('stats', __name__, url_prefix='/api/stats')


@stats_bp.route('/trend', methods=['GET'])
@login_required
def trend_stats(user_id):
    """近 N 月趋势（含按分类的支出明细）"""
    months = request.args.get('months', 6, type=int)
    now = datetime.now()
    result = {
        "months": [],
        "income": [],
        "expense": [],
        "by_category": defaultdict(list),  # {category: [amount_month1, ...]}
    }

    # 收集每个月每个分类的支出
    all_categories = set()
    monthly_by_cat = {}  # {(year, month): {category: amount}}

    for i in range(months - 1, -1, -1):
        d = (now - relativedelta(months=i+1)).replace(day=1)
        income, expense = get_monthly_summary(user_id, d.year, d.month)
        result["months"].append(f"{d.year}-{d.month:02d}")
        result["income"].append(float(income))
        result["expense"].append(float(expense))

        # 该月按分类汇总
        cats = get_category_summary(user_id, d.year, d.month, 'expense')
        cat_dict = {c[0]: float(c[1]) for c in cats}
        monthly_by_cat[(d.year, d.month)] = cat_dict
        all_categories.update(cat_dict.keys())

    # 按分类填充每个月的金额（没有的填 0）
    for cat in all_categories:
        for i in range(months - 1, -1, -1):
            d = (now - relativedelta(months=i+1)).replace(day=1)
            amount = monthly_by_cat.get((d.year, d.month), {}).get(cat, 0)
            result["by_category"][cat].append(amount)

    # 排序：按总金额倒序
    result["by_category"] = dict(
        sorted(result["by_category"].items(), key=lambda x: -sum(x[1]))
    )

    return success_response(result)


@stats_bp.route('/monthly', methods=['GET'])
@login_required
def monthly_stats(user_id):
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)

    if not year or not month:
        now = datetime.now()
        year = year or now.year
        month = month or now.month

    income, expense = get_monthly_summary(user_id, year, month)

    return success_response({
        "income": float(income),
        "expense": float(expense),
        "balance": float(income - expense)
    })


@stats_bp.route('/category', methods=['GET'])
@login_required
def category_stats(user_id):
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    start = request.args.get('start')
    end = request.args.get('end')
    bill_type = request.args.get('type')  # 'income' | 'expense' | None

    # 优先 start/end；缺则回落到 year/month；再缺则用当前月
    if start and end:
        categories = get_category_summary(user_id, bill_type=bill_type, start_date=start, end_date=end)
    else:
        if not year or not month:
            now = datetime.now()
            year = year or now.year
            month = month or now.month
        categories = get_category_summary(user_id, year, month, bill_type=bill_type)

    result = []
    total = sum(float(c[1]) for c in categories)

    for c in categories:
        amount = float(c[1])
        # c 可能是 (category, amount) 或 (category, amount, type) 两种形态
        type_ = c[2] if len(c) >= 3 else None
        result.append({
            "category": c[0],
            "amount": amount,
            "type": type_,
            "percent": round(amount / total * 100, 1) if total > 0 else 0
        })

    return success_response(result)


@stats_bp.route('/summary', methods=['GET'])
@login_required
def summary_stats(user_id):
    """区间汇总：日均、最大单笔、最高频分类、笔数、对比上一周期"""
    start = request.args.get('start')
    end = request.args.get('end')

    if not start or not end:
        now = datetime.now()
        year = request.args.get('year', now.year, type=int)
        month = request.args.get('month', now.month, type=int)
        start = f"{year}-{month:02d}-01"
        end = f"{year}-{month+1:02d}-01" if month < 12 else f"{year+1}-01-01"

    current = get_summary(user_id, start, end)
    if not current:
        return error_response(500, "汇总失败")

    # 计算上一周期做对比
    try:
        s = datetime.strptime(start, '%Y-%m-%d')
        e = datetime.strptime(end, '%Y-%m-%d')
        days = (e - s).days
        prev_end = s.strftime('%Y-%m-%d')
        prev_start = (s - timedelta(days=days)).strftime('%Y-%m-%d')
        previous = get_summary(user_id, prev_start, prev_end)
    except Exception:
        previous = None

    if previous:
        def delta(curr, prev):
            if prev == 0:
                return None
            return round((curr - prev) / prev * 100, 1)

        current['expense_delta'] = delta(current['expense'], previous['expense'])
        current['income_delta'] = delta(current['income'], previous['income'])
        current['avg_daily_delta'] = delta(current['avg_daily_expense'], previous['avg_daily_expense'])
        current['previous'] = {
            'expense': previous['expense'],
            'income': previous['income'],
        }
    else:
        current['expense_delta'] = None
        current['income_delta'] = None
        current['avg_daily_delta'] = None
        current['previous'] = None

    return success_response(current)


@stats_bp.route('/daily', methods=['GET'])
@login_required
def daily_stats(user_id):
    """区间内每日支出（热力图）"""
    start = request.args.get('start')
    end = request.args.get('end')

    if not start or not end:
        now = datetime.now()
        year = request.args.get('year', now.year, type=int)
        month = request.args.get('month', now.month, type=int)
        start = f"{year}-{month:02d}-01"
        end = f"{year}-{month+1:02d}-01" if month < 12 else f"{year+1}-01-01"

    days = get_daily_expense(user_id, start, end)
    return success_response(days)


@stats_bp.route('/top', methods=['GET'])
@login_required
def top_stats(user_id):
    """金额最大的 N 条记录"""
    start = request.args.get('start')
    end = request.args.get('end')
    bill_type = request.args.get('type', 'expense')
    limit = request.args.get('limit', 5, type=int)

    if not start or not end:
        now = datetime.now()
        year = request.args.get('year', now.year, type=int)
        month = request.args.get('month', now.month, type=int)
        start = f"{year}-{month:02d}-01"
        end = f"{year}-{month+1:02d}-01" if month < 12 else f"{year+1}-01-01"

    records = get_top_records(user_id, start, end, bill_type, limit)
    return success_response(records)