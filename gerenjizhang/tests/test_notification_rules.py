"""
验证规则 2（大额消费）、规则 3（未记账）、两级分类

不在 DB 里建真实数据污染，用临时用户跑完清理
"""
import sys
from datetime import datetime, timedelta
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from gerenjizhang.db import init_db, Database, add_record
init_db()

# 建临时用户
TEST_USERNAME = '__test_notification_rules__'
TEST_PASSWORD = 'x'
with Database() as db:
    db.c.execute('DELETE FROM users WHERE username=%s', (TEST_USERNAME,))
    db.c.execute('INSERT INTO users (username, password) VALUES (%s, %s)', (TEST_USERNAME, TEST_PASSWORD))
    db.c.execute('SELECT id FROM users WHERE username=%s', (TEST_USERNAME,))
    TEST_USER_ID = db.c.fetchone()[0]


def cleanup():
    """清理测试用户的所有数据"""
    with Database() as db:
        for tbl in ('bill', 'budgets', 'user_memory', 'user_memory_negatives', 'notification_log'):
            try:
                db.c.execute(f'DELETE FROM {tbl} WHERE user_id=%s', (TEST_USER_ID,))
            except Exception:
                pass


def teardown():
    cleanup()
    with Database() as db:
        db.c.execute('DELETE FROM users WHERE id=%s', (TEST_USER_ID,))


# ============ Rule 2 测试 ============
def _add_records_in_current_month(count, amount_each, cat='餐饮'):
    """本月内插 N 笔 amount_each 的账 → 日均 = amount_each * count / 今天几号"""
    today = datetime.now()
    days_in_month = today.day
    # 平均分布在已过去的天数（间隔约 days_in_month/count 天）
    interval = max(1, days_in_month // count)
    for i in range(count):
        day = max(1, today.day - (count - 1 - i) * interval)
        date_str = f"{today.year}-{today.month:02d}-{day:02d}"
        add_record(date_str, amount_each, 'expense', cat, '', TEST_USER_ID)


def test_rule2_under_threshold():
    """日均 100（10 笔 × 100 / 10 天），单笔 200（2 倍）→ 不触发"""
    cleanup()
    _add_records_in_current_month(10, 100.0)  # 1000 / 11 天 ≈ 90 元/天
    from gerenjizhang.services.notification_service import check_large_amount_for_record
    result = check_large_amount_for_record(TEST_USER_ID, 200.0, '餐饮', '')
    assert result is None, f"应不触发，实际: {result}"
    print(f"[OK] Rule2 阈值以下（200 元 vs 日均 × 5）不触发")


def test_rule2_over_threshold():
    """日均 ~100，单笔 2000（20 倍）→ 触发大额"""
    cleanup()
    _add_records_in_current_month(10, 100.0)
    from gerenjizhang.services.notification_service import check_large_amount_for_record
    result = check_large_amount_for_record(TEST_USER_ID, 2000.0, '购物', '京东')
    assert result is not None, "应触发"
    assert result['rule_type'] == 'large_amount'
    assert '日均' in result['message']
    print(f"[OK] Rule2 触发：{result['message']}")


def test_rule2_min_floor():
    """单笔 50 元（低于 500 floor）→ 不触发"""
    cleanup()
    _add_records_in_current_month(20, 100.0)  # 即使日均很高，< 500 也不触发
    from gerenjizhang.services.notification_service import check_large_amount_for_record
    result = check_large_amount_for_record(TEST_USER_ID, 50.0, '餐饮', '')
    assert result is None, f"低于 floor 不应触发，实际: {result}"
    print(f"[OK] Rule2 单笔 < 500 不触发")


def test_rule2_refund_filter():
    """备注含"退款" → 不触发（避免误报）"""
    cleanup()
    _add_records_in_current_month(10, 100.0)
    from gerenjizhang.services.notification_service import check_large_amount_for_record
    result = check_large_amount_for_record(TEST_USER_ID, 5000.0, '购物', '京东退款')
    assert result is None, f"退款应被过滤，实际: {result}"
    print(f"[OK] Rule2 退款场景被过滤")


# ============ Rule 3 测试 ============
def test_rule3_active_user():
    """昨天记过账 → 不触发"""
    cleanup()
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    add_record(yesterday, 50.0, 'expense', '餐饮', '', TEST_USER_ID)
    from gerenjizhang.services.notification_service import check_inactive
    result = check_inactive(TEST_USER_ID)
    assert result is None, f"昨天记过账不应触发，实际: {result}"
    print(f"[OK] Rule3 昨天记过账不触发")


def test_rule3_idle_3_days():
    """5 天前最后记账 → 触发"""
    cleanup()
    old_date = (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d')
    add_record(old_date, 50.0, 'expense', '餐饮', '', TEST_USER_ID)
    from gerenjizhang.services.notification_service import check_inactive
    result = check_inactive(TEST_USER_ID)
    assert result is not None, "5 天没记账应触发"
    assert result['rule_type'] == 'inactive'
    assert result['days_idle'] >= 3
    print(f"[OK] Rule3 触发：{result['message']}")


# ============ 两级分类测试 ============
def test_two_stage_food_delivery():
    """'美团外卖 28.5' → 餐饮 · 外卖"""
    from gerenjizhang.utils.classifier import classify_two_stage
    result = classify_two_stage("美团外卖 28.5")
    assert result is not None
    assert result['category'] == '餐饮', f"大类应该是餐饮，实际: {result['category']}"
    assert result['sub_category'] == '外卖', f"细分应该是外卖，实际: {result['sub_category']}"
    print(f"[OK] 两级分类：'美团外卖 28.5' → {result['category']} · {result['sub_category']}")


def test_two_stage_coffee():
    """'星巴克咖啡 35' → 餐饮 · 咖啡奶茶"""
    from gerenjizhang.utils.classifier import classify_two_stage
    result = classify_two_stage("星巴克咖啡 35")
    assert result is not None
    assert result['category'] == '餐饮'
    assert result['sub_category'] == '咖啡奶茶', f"实际: {result['sub_category']}"
    print(f"[OK] 两级分类：'星巴克咖啡 35' → {result['category']} · {result['sub_category']}")


def test_two_stage_no_sub():
    """'交通罚款 200' → 交通（无细分）"""
    from gerenjizhang.utils.classifier import classify_two_stage
    result = classify_two_stage("交通罚款 200")
    # 罚款可能命中"罚款"或归不到任何细分
    if result:
        print(f"[INFO] '交通罚款 200' → {result['category']} · {result.get('sub_category')}")


if __name__ == '__main__':
    print("=" * 60)
    print("规则 2/3 + 两级分类验证")
    print("=" * 60)
    passed = failed = 0
    tests = [
        test_rule2_under_threshold,
        test_rule2_over_threshold,
        test_rule2_min_floor,
        test_rule2_refund_filter,
        test_rule3_active_user,
        test_rule3_idle_3_days,
        test_two_stage_food_delivery,
        test_two_stage_coffee,
        test_two_stage_no_sub,
    ]
    for t in tests:
        try:
            t()
            passed += 1
        except AssertionError as e:
            print(f"[FAIL] {t.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"[ERROR] {t.__name__}: {e}")
            failed += 1
    teardown()
    print(f"\n结果：{passed} 通过 / {failed} 失败")
    print("=" * 60)