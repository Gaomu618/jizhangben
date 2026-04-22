# service.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from gerenjizhang.db import *
from datetime import datetime


def add_bill_record(user_id, date, amount, type_, category, note=""):
    if amount <= 0:
        return False, "金额必须大于0"
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        return False, "日期格式错误"
    add_record(date, amount, type_, category, note, user_id)
    return True, "添加成功"


def edit_bill_record(record_id, date, amount, type_, category, note="", user_id=None):
    if amount <= 0:
        return False, "金额必须大于0"
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        return False, "日期格式错误"
    edit_record(record_id, date, amount, type_, category, note, user_id)
    return True, "修改成功"


def delete_bill_record(record_id, user_id):
    delete_record(record_id, user_id)
    return True, "删除成功"


def query_records(user_id, start_date=None, end_date=None, type_filter=None, category_filter=None, limit=None, offset=None):
    return get_records(user_id, start_date, end_date, type_filter, category_filter, limit, offset)


def get_monthly_balance(user_id, year, month):
    income, expense = get_monthly_summary(user_id, year, month)
    return income, expense, income - expense


def get_expense_by_category(user_id, year, month):
    return get_category_summary(user_id, year, month)
