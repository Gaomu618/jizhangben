"""
账单 CRUD：列表 / 详情 / 添加 / 编辑 / 删除 / 批量删除 / 智能分类。
"""
import logging

from flask import request

from gerenjizhang.api.bill_bp import bill_bp
from gerenjizhang.db import (
    add_record, edit_record, delete_record, get_record_by_id, get_records,
)
from gerenjizhang.utils.classifier import classify_two_stage
from gerenjizhang.utils.decorators import login_required
from gerenjizhang.utils.response import success_response, error_response

logger = logging.getLogger(__name__)


@bill_bp.route('/list', methods=['GET'])
@login_required
def get_bill_list(user_id):
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    type_filter = request.args.get('type')
    # 自定义范围或分类筛选（Stats 点击下钻用）
    start_param = request.args.get('start')
    end_param = request.args.get('end')
    category = request.args.get('category')

    from datetime import datetime
    if start_param and end_param:
        start = start_param
        end = end_param
    else:
        if not year or not month:
            now = datetime.now()
            year = year or now.year
            month = month or now.month
        start = f"{year}-{month:02d}-01"
        end = f"{year}-{month+1:02d}-01" if month < 12 else f"{year+1}-01-01"

    offset = (page - 1) * page_size

    records = get_records(user_id, start_date=start, end_date=end, type_filter=type_filter, category_filter=category, limit=page_size, offset=offset)
    total_records = get_records(user_id, start_date=start, end_date=end, type_filter=type_filter, category_filter=category)

    total = len(total_records)
    total_pages = (total + page_size - 1) // page_size if page_size else 1

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


@bill_bp.route('/classify', methods=['POST'])
@login_required
def classify_bill(user_id):
    """智能分类：根据备注文字推荐分类（支持两级：商家大类 + 商品细分）
    Body: { "text": "美团 28.5" }
    返回: {
      "category": "餐饮",
      "sub_category": "外卖",     ← 可空
      "type": "expense",
      "confidence": 0.95,
      "matched": ["美团"],
      "sub_matched": ["美团外卖"]
    }
    """
    data = request.get_json() or {}
    text = (data.get('text') or '').strip()

    if not text:
        return error_response(6001, "请输入备注文字")

    result = classify_two_stage(text, user_id=user_id)
    if not result:
        return success_response({
            'category': None,
            'sub_category': None,
            'type': None,
            'confidence': 0,
            'matched': []
        }, message="未能识别，请手动选择")

    return success_response(result)


@bill_bp.route('/classify/memory', methods=['GET'])
@login_required
def list_classify_memory(user_id):
    """查看自己学过的所有分类记忆"""
    from gerenjizhang.db import get_user_memory
    memories = get_user_memory(user_id)
    return success_response(memories)


@bill_bp.route('/classify/memory/<int:mid>', methods=['DELETE'])
@login_required
def delete_classify_memory(user_id, mid):
    """删除某条记忆（如果它分错了）"""
    from gerenjizhang.db import delete_user_memory
    from gerenjizhang.utils.classifier import invalidate_cache
    if delete_user_memory(user_id, mid):
        invalidate_cache(user_id)
        return success_response(message="记忆已删除")
    return error_response(6002, "记忆不存在或已删除")


@bill_bp.route('/classify/memory/clear', methods=['POST'])
@login_required
def clear_classify_memory(user_id):
    """清空所有记忆"""
    from gerenjizhang.utils.classifier import clear_user_learned
    deleted = clear_user_learned(user_id)
    return success_response({'deleted': deleted}, message=f"已清空 {deleted} 条记忆")


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

    if date is None or amount is None or type_ is None or category is None or category == '':
        return error_response(2002, "参数不完整")

    try:
        amount = float(amount)
    except (ValueError, TypeError):
        return error_response(2003, "金额格式错误")

    if type_ not in ('income', 'expense'):
        return error_response(2004, "类型错误")

    if amount <= 0:
        return error_response(2005, "金额必须大于 0")

    try:
        new_id = add_record(date, amount, type_, category, note, user_id)
    except ValueError as ve:
        return error_response(2006, str(ve))
    except Exception as e:
        logger.error(f"add_bill 失败: {e}")
        return error_response(2007, f"服务器错误: {str(e)}")

    # Rule 2: 异常大额消费检测（事件驱动）
    # 异步调用，记完账顺手判断；失败不影响主流程
    if type_ == 'expense':
        try:
            from gerenjizhang.services.notification_service import check_large_amount_for_record
            check_large_amount_for_record(user_id, amount, category, note)
        except Exception as e:
            logger.error(f"check_large_amount 失败: {e}")

    return success_response({'id': new_id}, message="添加成功")


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
        return error_response(2002, "参数不完整")

    try:
        amount = float(amount)
    except (ValueError, TypeError):
        return error_response(2003, "金额格式错误")

    # 编辑前先取出旧记录，对比分类是否被改了
    old_record = get_record_by_id(rid, user_id)
    affected = edit_record(rid, date, amount, type_, category, note, user_id)

    if affected == 0:
        return error_response(2001, "记录不存在或已被删除")
    if affected < 0:
        return error_response(2007, "修改失败，数据库错误")

    # 用户修正了分类 → 学习（让智能分类更准）
    # 同时传 old_category，让分类器记一条负样本，下次避免再判错
    if old_record and old_record[4] != category and note:
        from gerenjizhang.utils.classifier import remember_correction
        remember_correction(user_id, note, category, bill_type=type_, old_category=old_record[4])

    return success_response(message="修改成功")


@bill_bp.route('/delete/<int:rid>', methods=['POST'])
@login_required
def delete_bill(user_id, rid):
    affected = delete_record(rid, user_id)
    if affected == 0:
        return error_response(2001, "记录不存在或已被删除")
    if affected < 0:
        return error_response(2009, "删除失败，数据库错误")
    return success_response(message="删除成功")


@bill_bp.route('/batch-delete', methods=['POST'])
@login_required
def batch_delete_bills(user_id):
    """批量删除账单"""
    from gerenjizhang.db import Database
    from mysql.connector import Error
    data = request.get_json() or {}
    ids = data.get('ids', [])

    if not isinstance(ids, list) or not ids:
        return error_response(2010, "请选择要删除的记录")

    # 过滤非法 ID
    try:
        ids = [int(i) for i in ids if str(i).isdigit()]
    except (ValueError, TypeError):
        return error_response(2011, "ID 格式错误")

    if not ids:
        return error_response(2010, "请选择要删除的记录")

    # 限制一次最多删除 200 条，防止误操作
    if len(ids) > 200:
        return error_response(2012, "一次最多删除 200 条")

    try:
        with Database() as db:
            placeholders = ','.join(['%s'] * len(ids))
            # 软删除：标记 deleted_at 进回收站（不真删）
            db.c.execute(
                f'UPDATE bill SET deleted_at=NOW() WHERE user_id=%s AND deleted_at IS NULL AND id IN ({placeholders})',
                [user_id] + ids
            )
            deleted = db.c.rowcount
            db.conn.commit()
            return success_response({'deleted': deleted}, message=f"成功删除 {deleted} 条")
    except Error as e:
        logger.error(f"批量删除错误: {e}")
        return error_response(2009, f"删除失败: {str(e)}")
