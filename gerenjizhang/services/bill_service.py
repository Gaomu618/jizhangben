"""
账单服务层
处理账单相关的业务逻辑
"""
from datetime import datetime
from gerenjizhang.models import Bill
from gerenjizhang.db import (
    add_record, edit_record, delete_record, get_record_by_id,
    get_records, get_monthly_summary, get_category_summary
)


class BillService:
    """账单服务"""

    @staticmethod
    def add_bill(user_id, date, amount, type_, category, note=''):
        """添加账单"""
        if not all([date, amount, type_, category]):
            raise ValueError("参数不完整")

        try:
            amount = float(amount)
        except (ValueError, TypeError):
            raise ValueError("金额格式错误")

        if amount <= 0:
            raise ValueError("金额必须大于0")

        if type_ not in ('income', 'expense'):
            raise ValueError("类型错误")

        # 验证日期格式
        try:
            datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            raise ValueError("日期格式错误，应为 YYYY-MM-DD")

        add_record(date, amount, type_, category, note, user_id)
        return True

    @staticmethod
    def edit_bill(bill_id, user_id, date, amount, type_, category, note=''):
        """编辑账单"""
        if not all([date, amount, type_, category]):
            raise ValueError("参数不完整")

        try:
            amount = float(amount)
        except (ValueError, TypeError):
            raise ValueError("金额格式错误")

        # 检查账单是否存在
        bill = get_record_by_id(bill_id, user_id)
        if not bill:
            raise ValueError("账单不存在")

        edit_record(bill_id, date, amount, type_, category, note, user_id)
        return True

    @staticmethod
    def delete_bill(bill_id, user_id):
        """删除账单"""
        bill = get_record_by_id(bill_id, user_id)
        if not bill:
            raise ValueError("账单不存在")

        delete_record(bill_id, user_id)
        return True

    @staticmethod
    def get_bill_list(user_id, year=None, month=None, page=1, page_size=20, type_filter=None):
        """获取账单列表（分页）"""
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
        total_pages = (total + page_size - 1) // page_size if total > 0 else 1

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

        return {
            "list": bill_list,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }

    @staticmethod
    def get_monthly_summary(user_id, year, month):
        """获取月度汇总"""
        income, expense = get_monthly_summary(user_id, year, month)
        return {
            "income": float(income),
            "expense": float(expense),
            "balance": float(income) - float(expense)
        }

    @staticmethod
    def get_category_summary(user_id, year, month):
        """获取分类汇总"""
        categories = get_category_summary(user_id, year, month)
        return [
            {"category": cat, "amount": float(amount)}
            for cat, amount in categories
        ]