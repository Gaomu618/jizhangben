from flask import Blueprint, request
from gerenjizhang.db import get_monthly_summary, get_category_summary
from gerenjizhang.utils.response import success_response, error_response
from gerenjizhang.utils.decorators import login_required

stats_bp = Blueprint('stats', __name__, url_prefix='/api/stats')


@stats_bp.route('/monthly', methods=['GET'])
@login_required
def monthly_stats(user_id):
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)

    from datetime import datetime
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

    from datetime import datetime
    if not year or not month:
        now = datetime.now()
        year = year or now.year
        month = month or now.month

    categories = get_category_summary(user_id, year, month)

    result = []
    total = sum(float(c[1]) for c in categories)

    for c in categories:
        amount = float(c[1])
        result.append({
            "category": c[0],
            "amount": amount,
            "percent": round(amount / total * 100, 1) if total > 0 else 0
        })

    return success_response(result)