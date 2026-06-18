"""
单元测试：db.py 核心 CRUD + 软删除 + 预算 + 清理

策略：每个测试创建一个独立的临时用户，跑完自动清理
"""
import sys
import time
import pytest

# 引入项目根目录
sys.path.insert(0, '.')

from gerenjizhang.db import (
    add_record, add_record_batch, get_records, get_record_by_id,
    edit_record, delete_record, restore_record, purge_record,
    get_trash_records, count_trash, empty_trash, cleanup_old_trash,
    save_budget, get_budgets, get_summary, get_daily_expense,
    get_top_records, get_category_summary
)
from gerenjizhang.db import Database
import mysql.connector


# ==================== Fixture ====================
@pytest.fixture
def test_user():
    """创建一个测试用户，跑完测试自动删除"""
    suffix = str(int(time.time() * 1000))[-8:]
    username = f'pytest_{suffix}'

    with Database() as db:
        db.c.execute(
            'INSERT INTO users (username, password) VALUES (%s, %s)',
            (username, 'pbkdf2_sha256$dummy')
        )
        user_id = db.c.lastrowid
        db.conn.commit()

    yield user_id

    # 清理：删除该用户的所有数据
    with Database() as db:
        db.c.execute('DELETE FROM bill WHERE user_id=%s', (user_id,))
        db.c.execute('DELETE FROM budgets WHERE user_id=%s', (user_id,))
        db.c.execute('DELETE FROM users WHERE id=%s', (user_id,))
        db.conn.commit()


# ==================== CRUD 测试 ====================
class TestCRUD:
    def test_add_and_get(self, test_user):
        """添加一条 + 查询能查到"""
        add_record('2026-06-01', 100.50, 'expense', '餐饮', '午饭', test_user)
        records = get_records(test_user)
        assert len(records) == 1
        assert records[0][1] == '2026-06-01'  # date
        assert float(records[0][2]) == 100.50  # amount
        assert records[0][3] == 'expense'
        assert records[0][4] == '餐饮'
        assert records[0][5] == '午饭'

    def test_get_records_excludes_trash(self, test_user):
        """查询时不返回已删除的"""
        add_record('2026-06-01', 100, 'expense', '餐饮', '午饭', test_user)
        add_record('2026-06-02', 50, 'expense', '交通', '地铁', test_user)
        assert len(get_records(test_user)) == 2
        # 软删一条
        records = get_records(test_user)
        delete_record(records[0][0], test_user)
        assert len(get_records(test_user)) == 1

    def test_edit_record(self, test_user):
        """编辑后金额变化"""
        rid = add_record('2026-06-01', 100, 'expense', '餐饮', '', test_user)
        records = get_records(test_user)
        original_id = records[0][0]
        edit_record(original_id, '2026-06-01', 200, 'expense', '餐饮', '改后', test_user)
        records = get_records(test_user)
        assert float(records[0][2]) == 200
        assert records[0][5] == '改后'

    def test_get_records_with_date_range(self, test_user):
        """日期范围过滤"""
        add_record('2026-06-01', 100, 'expense', '餐饮', '', test_user)
        add_record('2026-06-15', 100, 'expense', '交通', '', test_user)
        add_record('2026-06-30', 100, 'expense', '购物', '', test_user)
        recs = get_records(test_user, start_date='2026-06-10', end_date='2026-06-20')
        assert len(recs) == 1
        assert recs[0][1] == '2026-06-15'

    def test_get_records_with_category(self, test_user):
        """分类过滤"""
        add_record('2026-06-01', 100, 'expense', '餐饮', '', test_user)
        add_record('2026-06-02', 50, 'expense', '交通', '', test_user)
        recs = get_records(test_user, category_filter='交通')
        assert len(recs) == 1
        assert recs[0][4] == '交通'

    def test_get_records_with_type_filter(self, test_user):
        """收入/支出过滤"""
        add_record('2026-06-01', 100, 'expense', '餐饮', '', test_user)
        add_record('2026-06-02', 5000, 'income', '工资', '', test_user)
        recs = get_records(test_user, type_filter='income')
        assert len(recs) == 1
        assert recs[0][3] == 'income'


# ==================== 软删除 / 回收站测试 ====================
class TestRecycleBin:
    def test_soft_delete_sets_deleted_at(self, test_user):
        """软删除设置 deleted_at"""
        add_record('2026-06-01', 100, 'expense', '餐饮', '', test_user)
        rid = get_records(test_user)[0][0]
        success = delete_record(rid, test_user)
        assert success is True
        # 列表中看不到了
        assert len(get_records(test_user)) == 0
        # 但回收站能看到
        trash = get_trash_records(test_user)
        assert len(trash) == 1
        assert trash[0][7] is not None  # deleted_at 被设置了

    def test_soft_delete_returns_false_for_already_deleted(self, test_user):
        """重复软删返回 False（idempotent）"""
        add_record('2026-06-01', 100, 'expense', '餐饮', '', test_user)
        rid = get_records(test_user)[0][0]
        assert delete_record(rid, test_user) is True
        assert delete_record(rid, test_user) is False  # 第二次无效

    def test_soft_delete_returns_false_for_wrong_user(self, test_user):
        """不能删别人的记录（越权保护）"""
        add_record('2026-06-01', 100, 'expense', '餐饮', '', test_user)
        rid = get_records(test_user)[0][0]
        assert delete_record(rid, user_id=99999) is False

    def test_restore(self, test_user):
        """还原"""
        add_record('2026-06-01', 100, 'expense', '餐饮', '', test_user)
        rid = get_records(test_user)[0][0]
        delete_record(rid, test_user)
        assert len(get_records(test_user)) == 0
        assert restore_record(rid, test_user) is True
        assert len(get_records(test_user)) == 1
        assert len(get_trash_records(test_user)) == 0

    def test_restore_only_from_trash(self, test_user):
        """只能从回收站还原（不能"还原"正常记录）"""
        add_record('2026-06-01', 100, 'expense', '餐饮', '', test_user)
        rid = get_records(test_user)[0][0]
        assert restore_record(rid, test_user) is False  # 正常记录不能"还原"

    def test_purge_removes_from_db(self, test_user):
        """永久删除真的删了"""
        add_record('2026-06-01', 100, 'expense', '餐饮', '', test_user)
        rid = get_records(test_user)[0][0]
        delete_record(rid, test_user)
        assert purge_record(rid, test_user) is True
        # 不在列表、不在回收站、不在 DB
        assert len(get_records(test_user)) == 0
        assert len(get_trash_records(test_user)) == 0
        with Database() as db:
            db.c.execute('SELECT COUNT(*) FROM bill WHERE id=%s', (rid,))
            assert db.c.fetchone()[0] == 0  # 真没了

    def test_purge_only_from_trash(self, test_user):
        """只能从回收站永久删除"""
        add_record('2026-06-01', 100, 'expense', '餐饮', '', test_user)
        rid = get_records(test_user)[0][0]
        # 直接 purge 应该失败（不在回收站）
        assert purge_record(rid, test_user) is False

    def test_count_trash(self, test_user):
        """回收站计数"""
        for i in range(3):
            add_record(f'2026-06-0{i+1}', 100, 'expense', '餐饮', '', test_user)
        assert count_trash(test_user) == 0
        records = get_records(test_user)
        for r in records:
            delete_record(r[0], test_user)
        assert count_trash(test_user) == 3

    def test_empty_trash(self, test_user):
        """清空回收站"""
        for i in range(3):
            add_record(f'2026-06-0{i+1}', 100, 'expense', '餐饮', '', test_user)
        for r in get_records(test_user):
            delete_record(r[0], test_user)
        deleted = empty_trash(test_user)
        assert deleted == 3
        assert count_trash(test_user) == 0

    def test_trash_list_pagination(self, test_user):
        """回收站分页"""
        for i in range(5):
            add_record(f'2026-06-0{i+1}', 100, 'expense', '餐饮', '', test_user)
        for r in get_records(test_user):
            delete_record(r[0], test_user)
        page1 = get_trash_records(test_user, limit=2, offset=0)
        page2 = get_trash_records(test_user, limit=2, offset=2)
        assert len(page1) == 2
        assert len(page2) == 2
        # 不同页 ID 不能重叠
        page1_ids = {r[0] for r in page1}
        page2_ids = {r[0] for r in page2}
        assert page1_ids.isdisjoint(page2_ids)

    def test_cleanup_old_trash(self, test_user):
        """清理超过 N 天的回收站记录"""
        add_record('2026-06-01', 100, 'expense', '餐饮', '', test_user)
        rid = get_records(test_user)[0][0]
        delete_record(rid, test_user)
        # 手动把 deleted_at 改成 31 天前
        with Database() as db:
            db.c.execute(
                "UPDATE bill SET deleted_at = NOW() - INTERVAL 31 DAY WHERE id=%s",
                (rid,)
            )
            db.conn.commit()
        # 清理（days=30 默认）
        deleted = cleanup_old_trash(30)
        assert deleted >= 1
        assert count_trash(test_user) == 0


# ==================== 预算测试 ====================
class TestBudget:
    def test_save_and_get_budget(self, test_user):
        save_budget(test_user, 'expense', '餐饮', 500, '2026-06')
        budgets = get_budgets(test_user, '2026-06')
        assert len(budgets) == 1
        assert budgets[0][0] == '餐饮'
        assert float(budgets[0][1]) == 500

    def test_budget_upsert(self, test_user):
        """同月同分类重复设置应该更新而不是新增"""
        save_budget(test_user, 'expense', '餐饮', 500, '2026-06')
        save_budget(test_user, 'expense', '餐饮', 800, '2026-06')
        budgets = get_budgets(test_user, '2026-06')
        assert len(budgets) == 1
        assert float(budgets[0][1]) == 800

    def test_budget_different_months(self, test_user):
        """不同月份的预算独立"""
        save_budget(test_user, 'expense', '餐饮', 500, '2026-06')
        save_budget(test_user, 'expense', '餐饮', 800, '2026-07')
        assert len(get_budgets(test_user, '2026-06')) == 1
        assert len(get_budgets(test_user, '2026-07')) == 1


# ==================== 汇总 / 统计测试 ====================
class TestSummary:
    def test_get_summary_basic(self, test_user):
        add_record('2026-06-01', 100, 'expense', '餐饮', '', test_user)
        add_record('2026-06-02', 5000, 'income', '工资', '', test_user)
        s = get_summary(test_user, '2026-06-01', '2026-07-01')
        assert s['income'] == 5000
        assert s['expense'] == 100
        assert s['balance'] == 4900
        assert s['income_count'] == 1
        assert s['expense_count'] == 1
        assert s['days'] == 30
        assert s['avg_daily_expense'] == round(100/30, 2)

    def test_get_summary_max_expense(self, test_user):
        add_record('2026-06-01', 50, 'expense', '餐饮', '', test_user)
        add_record('2026-06-02', 500, 'expense', '购物', '', test_user)
        add_record('2026-06-03', 100, 'expense', '交通', '', test_user)
        s = get_summary(test_user, '2026-06-01', '2026-07-01')
        assert s['max_expense']['amount'] == 500
        assert s['max_expense']['category'] == '购物'

    def test_get_summary_top_category(self, test_user):
        for _ in range(3):
            add_record('2026-06-01', 100, 'expense', '餐饮', '', test_user)
        add_record('2026-06-02', 50, 'expense', '交通', '', test_user)
        s = get_summary(test_user, '2026-06-01', '2026-07-01')
        assert s['top_category']['name'] == '餐饮'
        assert s['top_category']['count'] == 3
        assert s['top_category']['total'] == 300

    def test_get_summary_excludes_deleted(self, test_user):
        """汇总不应包括已删除的记录"""
        add_record('2026-06-01', 100, 'expense', '餐饮', '', test_user)
        s = get_summary(test_user, '2026-06-01', '2026-07-01')
        assert s['expense'] == 100
        # 软删
        delete_record(get_records(test_user)[0][0], test_user)
        s = get_summary(test_user, '2026-06-01', '2026-07-01')
        assert s['expense'] == 0
        assert s['expense_count'] == 0

    def test_get_daily_expense(self, test_user):
        add_record('2026-06-01', 100, 'expense', '餐饮', '', test_user)
        add_record('2026-06-01', 50, 'expense', '交通', '', test_user)
        add_record('2026-06-02', 200, 'expense', '购物', '', test_user)
        daily = get_daily_expense(test_user, '2026-06-01', '2026-07-01')
        # 应该按日期聚合
        by_date = {d['date']: d for d in daily}
        assert by_date['2026-06-01']['amount'] == 150
        assert by_date['2026-06-01']['count'] == 2
        assert by_date['2026-06-02']['amount'] == 200

    def test_get_top_records(self, test_user):
        add_record('2026-06-01', 100, 'expense', '餐饮', '', test_user)
        add_record('2026-06-02', 500, 'expense', '购物', '', test_user)
        add_record('2026-06-03', 200, 'expense', '交通', '', test_user)
        top = get_top_records(test_user, '2026-06-01', '2026-07-01', 'expense', limit=2)
        assert len(top) == 2
        # 按金额降序
        assert top[0]['amount'] == 500
        assert top[1]['amount'] == 200

    def test_get_category_summary(self, test_user):
        add_record('2026-06-01', 100, 'expense', '餐饮', '', test_user)
        add_record('2026-06-02', 50, 'expense', '餐饮', '', test_user)
        add_record('2026-06-03', 200, 'expense', '购物', '', test_user)
        add_record('2026-06-04', 5000, 'income', '工资', '', test_user)
        cats = get_category_summary(test_user, 2026, 6)
        by_cat = {c[0]: c for c in cats}
        # 餐饮支出 = 150（[0]=category, [1]=amount, [2]=type）
        assert float(by_cat['餐饮'][1]) == 150
        assert by_cat['餐饮'][2] == 'expense'
        # 工资收入 = 5000
        assert float(by_cat['工资'][1]) == 5000
        assert by_cat['工资'][2] == 'income'


# ==================== 边界 / 错误处理 ====================
class TestEdgeCases:
    def test_edit_nonexistent_record(self, test_user):
        """编辑不存在的记录应该静默失败（不抛异常）"""
        # 没有异常 = 通过
        edit_record(99999, '2026-06-01', 100, 'expense', '餐饮', '', test_user)
        assert len(get_records(test_user)) == 0

    def test_delete_nonexistent_record_returns_false(self, test_user):
        """删除不存在的记录返回 False"""
        assert delete_record(99999, test_user) is False

    def test_purge_nonexistent_returns_false(self, test_user):
        assert purge_record(99999, test_user) is False

    def test_summary_empty_data(self, test_user):
        """空数据汇总"""
        s = get_summary(test_user, '2026-06-01', '2026-07-01')
        assert s['income'] == 0
        assert s['expense'] == 0
        assert s['balance'] == 0
        assert s['avg_daily_expense'] == 0
        assert s['max_expense'] is None
        assert s['top_category'] is None

    def test_add_record_with_negative_amount(self, test_user):
        """负数金额应被拒绝"""
        with pytest.raises(ValueError, match="金额必须大于 0"):
            add_record('2026-06-01', -100, 'expense', '餐饮', '', test_user)

    def test_add_record_with_invalid_type(self, test_user):
        """type 不是 income/expense 应被拒绝"""
        with pytest.raises(ValueError, match="type 必须是"):
            add_record('2026-06-01', 100, 'unknown_type', '餐饮', '', test_user)

    def test_add_record_with_empty_category(self, test_user):
        """空分类应被拒绝"""
        with pytest.raises(ValueError, match="分类不能为空"):
            add_record('2026-06-01', 100, 'expense', '', '', test_user)

    def test_add_record_with_zero_amount(self, test_user):
        """金额 0 应被拒绝（与负数同等处理）"""
        with pytest.raises(ValueError, match="金额必须大于 0"):
            add_record('2026-06-01', 0, 'expense', '餐饮', '', test_user)

    def test_add_record_with_valid_large_amount(self, test_user):
        """合理的较大金额（8 位数 = 9999999.99）应能存"""
        add_record('2026-06-01', 9999999.99, 'expense', '餐饮', '', test_user)
        records = get_records(test_user)
        assert float(records[0][2]) == 9999999.99

    def test_add_record_overflow(self, test_user):
        """超过 DECIMAL(10,2) 范围应抛异常（业务上限 ~9999999.99）"""
        # 999999999.99 = 11 位整数，超出 DECIMAL(10,2)
        with pytest.raises(Exception):  # mysql.connector.DataError
            add_record('2026-06-01', 999999999.99, 'expense', '餐饮', '', test_user)

    def test_get_records_with_invalid_date(self, test_user):
        """格式错误的日期能存"""
        add_record('not-a-date', 100, 'expense', '餐饮', '', test_user)
        # 不抛异常，但日期是字符串
        records = get_records(test_user)
        assert records[0][1] == 'not-a-date'

    def test_very_large_amount(self, test_user):
        """超过 DECIMAL(10,2) 范围应抛异常（业务上限 ~9999999.99）"""
        # 999999999.99 = 11 位整数，超出 DECIMAL(10,2)
        with pytest.raises(Exception):  # mysql.connector.DataError
            add_record('2026-06-01', 999999999.99, 'expense', '餐饮', '', test_user)
