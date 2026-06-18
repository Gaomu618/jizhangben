"""
验证负样本学习：把"美团退款 28.5"标记为不该归到餐饮后，分类器要降权

不在 DB 里建真实数据（避免污染），而是手动调 classify + learn_negative 验证行为
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

# 先 init DB（确保新表存在）
from gerenjizhang.db import init_db, Database
init_db()

# 建一个测试用户（有外键约束必须先有 users 行）
TEST_USERNAME = '__test_negative_sample__'
with Database() as db:
    db.c.execute('DELETE FROM users WHERE username=%s', (TEST_USERNAME,))
    db.c.execute(
        "INSERT INTO users (username, password) VALUES (%s, 'x')",
        (TEST_USERNAME,)
    )
    db.c.execute('SELECT id FROM users WHERE username=%s', (TEST_USERNAME,))
    TEST_USER_ID = db.c.fetchone()[0]

from gerenjizhang.utils.classifier import classify, learn_negative, clear_user_learned, preprocess


def cleanup():
    """清理测试用户的所有学习数据"""
    with Database() as db:
        db.c.execute('DELETE FROM user_memory WHERE user_id=%s', (TEST_USER_ID,))
        db.c.execute('DELETE FROM user_memory_negatives WHERE user_id=%s', (TEST_USER_ID,))


# 测试 1：未学习时，"美团退款 28.5" 应该归到餐饮（命中"美团"）
def test_default_classification():
    cleanup()
    result = classify("美团退款 28.5", user_id=TEST_USER_ID)
    assert result is not None, "默认应该能识别"
    assert result['category'] == '餐饮', f"默认应该归到餐饮，实际是 {result['category']}"
    print(f"[OK] 测试1：默认分类 = {result['category']}, confidence={result['confidence']:.2f}")


# 测试 2：学了负样本后，"美团退款 28.5" 应该不再归到餐饮
def test_negative_sample_overrides():
    cleanup()

    text = "美团退款 28.5"
    cleaned = preprocess(text).lower().strip()  # 用真实的预处理结果
    print(f"  [debug] preprocess('{text}') = '{cleaned}'")

    # 先学一条负样本（用真实清理后的文本）
    learn_negative(TEST_USER_ID, cleaned, "餐饮")

    # 重新分类 → 应该返回 None 或归到其他类别
    result = classify(text, user_id=TEST_USER_ID)
    if result is None:
        print(f"[OK] 测试2：学了负样本后，返回 None（餐饮被降权到阈值以下）")
    elif result['category'] != '餐饮':
        print(f"[OK] 测试2：学了负样本后，归到 {result['category']}（不再是餐饮）")
    else:
        raise AssertionError(f"测试2 失败：归到 {result['category']}, confidence={result['confidence']:.2f}")

    cleanup()


# 测试 3：负样本不影响正向学习（"美团外卖 30" 仍归餐饮）
def test_positive_not_affected():
    cleanup()

    learn_negative(TEST_USER_ID, "美团 退款", "餐饮")

    result = classify("美团外卖 30", user_id=TEST_USER_ID)
    assert result is not None and result['category'] == '餐饮', \
        f"正向分类应该不受负样本影响，实际是 {result and result['category']}"
    print(f"[OK] 测试3：'美团外卖 30' 仍归 {result['category']}")

    cleanup()


# 清理：删测试用户
def teardown():
    with Database() as db:
        db.c.execute('DELETE FROM user_memory WHERE user_id=%s', (TEST_USER_ID,))
        db.c.execute('DELETE FROM user_memory_negatives WHERE user_id=%s', (TEST_USER_ID,))
        db.c.execute('DELETE FROM users WHERE id=%s', (TEST_USER_ID,))


if __name__ == '__main__':
    print("=" * 60)
    print("负样本学习验证")
    print("=" * 60)
    passed = 0
    failed = 0
    for t in [test_default_classification, test_negative_sample_overrides, test_positive_not_affected]:
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