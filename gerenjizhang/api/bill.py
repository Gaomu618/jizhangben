from flask import Blueprint, request
from gerenjizhang.db import add_record, edit_record, delete_record, get_record_by_id, get_records
from gerenjizhang.utils.response import success_response, error_response
from gerenjizhang.utils.decorators import login_required

bill_bp = Blueprint('bill', __name__, url_prefix='/api/bill')


@bill_bp.route('/list', methods=['GET'])
@login_required
def get_bill_list(user_id):
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    type_filter = request.args.get('type')

    from datetime import datetime
    if not year or not month:
        now = datetime.now()
        year = year or now.year
        month = month or now.month

    start = f"{year}-{month:02d}-01"
    end = f"{year}-{month+1:02d}-01" if month < 12 else f"{year+1}-01-01"

    offset = (page - 1) * page_size

    records = get_records(user_id, start_date=start, end_date=end, type_filter=type_filter, limit=page_size, offset=offset)
    total_records = get_records(user_id, start_date=start, end_date=end, type_filter=type_filter)

    total = len(total_records)
    total_pages = (total + page_size - 1) // page_size

    bill_list = []
    for r in records:
        bill_list.append({
            "id": r[0],
            "date": r[1],
            "amount": float(r[2]),
            "type": r[3],
            "category": r[4],
            "note": r[5] or ''
        })

    return success_response({
        "list": bill_list,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages
    })


@bill_bp.route('/<int:rid>', methods=['GET'])
@login_required
def get_bill_detail(user_id, rid):
    record = get_record_by_id(rid, user_id)
    if not record:
        return error_response(2001, "记录不存在")

    return success_response({
        "id": record[0],
        "date": record[1],
        "amount": float(record[2]),
        "type": record[3],
        "category": record[4],
        "note": record[5] or ''
    })


@bill_bp.route('/add', methods=['POST'])
@login_required
def add_bill(user_id):
    data = request.get_json() or {}

    date = data.get('date')
    amount = data.get('amount')
    type_ = data.get('type')
    category = data.get('category')
    note = data.get('note', '')

    if not all([date, amount, type_, category]):
        return error_response(2002, "参数不完整")

    try:
        amount = float(amount)
    except (ValueError, TypeError):
        return error_response(2003, "金额格式错误")

    if type_ not in ('income', 'expense'):
        return error_response(2004, "类型错误")

    add_record(date, amount, type_, category, note, user_id)
    return success_response(message="添加成功")


@bill_bp.route('/edit/<int:rid>', methods=['POST'])
@login_required
def edit_bill(user_id, rid):
    data = request.get_json() or {}

    date = data.get('date')
    amount = data.get('amount')
    type_ = data.get('type')
    category = data.get('category')
    note = data.get('note', '')

    if not all([date, amount, type_, category]):
        return error_response(2005, "参数不完整")

    try:
        amount = float(amount)
    except (ValueError, TypeError):
        return error_response(2006, "金额格式错误")

    edit_record(rid, date, amount, type_, category, note, user_id)
    return success_response(message="修改成功")


@bill_bp.route('/delete/<int:rid>', methods=['POST'])
@login_required
def delete_bill(user_id, rid):
    delete_record(rid, user_id)
    return success_response(message="删除成功")