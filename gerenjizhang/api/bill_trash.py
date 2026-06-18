"""
回收站：list / count / restore / purge / batch-restore / empty。
"""
from flask import request

from gerenjizhang.api.bill_bp import bill_bp
from gerenjizhang.db import (
    restore_record, purge_record, get_trash_records, count_trash, empty_trash,
)
from gerenjizhang.utils.decorators import login_required
from gerenjizhang.utils.response import success_response, error_response


@bill_bp.route('/trash', methods=['GET'])
@login_required
def list_trash(user_id):
    """列出回收站记录（按删除时间倒序）"""
    # 懒清理：每次有人打开回收站时，顺便清理超过 30 天的过期记录
    from gerenjizhang.db import cleanup_old_trash
    cleanup_old_trash(30)

    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    offset = (page - 1) * page_size
    category = request.args.get('category')
    start_date = request.args.get('start')
    end_date = request.args.get('end')

    # 简化版：先获取所有，然后前端过滤（数据量小不优化了）
    records = get_trash_records(user_id, limit=page_size * 3, offset=0)

    # bill 表列顺序：0=id, 1=date, 2=amount, 3=type, 4=category, 5=note, 6=user_id, 7=deleted_at
    # 应用日期和分类过滤（在分页前）
    if start_date:
        records = [r for r in records if r[1] >= start_date]
    if end_date:
        records = [r for r in records if r[1] <= end_date]
    if category:
        records = [r for r in records if r[4] == category]

    # total 是过滤后总数（之前用 count_trash 是 bug，会把整个回收站的数量返回）
    total = len(records)
    records = records[offset:offset + page_size]
    total_pages = (total + page_size - 1) // page_size if page_size else 1

    items = []
    for r in records:
        items.append({
            "id": r[0],
            "date": r[1],
            "amount": float(r[2]),
            "type": r[3],
            "category": r[4],
            "note": r[5] or '',
            "deleted_at": r[7].isoformat() if r[7] else None,
        })

    return success_response({
        "list": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages
    })


@bill_bp.route('/trash/count', methods=['GET'])
@login_required
def get_trash_count(user_id):
    """获取回收站记录数（用于角标）"""
    return success_response({'count': count_trash(user_id)})


@bill_bp.route('/restore/<int:rid>', methods=['POST'])
@login_required
def restore_one_bill(user_id, rid):
    """从回收站还原单条"""
    if restore_record(rid, user_id):
        return success_response(message="已还原")
    return error_response(4007, "还原失败，记录可能不在回收站")


@bill_bp.route('/purge/<int:rid>', methods=['POST'])
@login_required
def purge_one_bill(user_id, rid):
    """永久删除单条（仅回收站内）"""
    if purge_record(rid, user_id):
        return success_response(message="已永久删除")
    return error_response(4008, "删除失败，记录可能不在回收站")


@bill_bp.route('/trash/empty', methods=['POST'])
@login_required
def empty_trash_all(user_id):
    """一键清空回收站"""
    deleted = empty_trash(user_id)
    return success_response({'deleted': deleted}, message=f"已清空回收站 {deleted} 条")


@bill_bp.route('/trash/restore-batch', methods=['POST'])
@login_required
def restore_batch_bills(user_id):
    """批量还原"""
    data = request.get_json() or {}
    ids = data.get('ids', [])
    if not isinstance(ids, list) or not ids:
        return error_response(4009, "请选择要还原的记录")
    count = 0
    for rid in ids:
        try:
            rid_int = int(rid)
            if restore_record(rid_int, user_id):
                count += 1
        except (ValueError, TypeError):
            continue
    return success_response({'restored': count}, message=f"已还原 {count} 条")
