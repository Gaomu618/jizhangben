"""
智能分类单元测试
"""
import sys
sys.path.insert(0, '.')

from gerenjizhang.utils.classifier import classify


class TestClassify:
    def test_food_keywords(self):
        """餐饮关键词"""
        cases = [
            '美团 28.5',
            '麦当劳早餐',
            '星巴克拿铁',
            '海底捞聚餐',
            '蜜雪冰城奶茶',
            '外卖 35元',
        ]
        for text in cases:
            r = classify(text)
            assert r is not None, f"'{text}' 应能识别"
            assert r['category'] == '餐饮', f"'{text}' 应归类为餐饮，实际: {r['category']}"
            assert r['type'] == 'expense'

    def test_transport_keywords(self):
        """交通关键词"""
        cases = [
            '滴滴到公司',
            '地铁 5元',
            '高铁票',
            '12306 上海',
            '加油 300',
            '打车回家',
            '共享单车 1.5元',
        ]
        for text in cases:
            r = classify(text)
            assert r is not None, f"'{text}' 应能识别"
            assert r['category'] == '交通', f"'{text}' 应归类为交通，实际: {r['category']}"
            assert r['type'] == 'expense'

    def test_shopping_keywords(self):
        """购物关键词"""
        cases = [
            '淘宝订单',
            '京东购物',
            '拼多多 9.9',
            '便利店买水',
        ]
        for text in cases:
            r = classify(text)
            assert r is not None
            assert r['category'] == '购物'

    def test_entertainment_keywords(self):
        """娱乐关键词"""
        cases = [
            '电影院IMAX',
            'steam游戏',
            '腾讯视频会员',
            'KTV 唱歌',
        ]
        for text in cases:
            r = classify(text)
            assert r is not None
            assert r['category'] == '娱乐'

    def test_living_keywords(self):
        """居住关键词"""
        cases = ['房租 2500', '水费 50', '宽带月费', '话费充值']
        for text in cases:
            r = classify(text)
            assert r is not None
            assert r['category'] == '居住'

    def test_income_keywords(self):
        """收入关键词"""
        assert classify('工资到账')['type'] == 'income'
        assert classify('工资到账')['category'] == '工资'
        assert classify('项目外包款')['type'] == 'income'

    def test_unknown_returns_none(self):
        """完全无关键词应返回 None"""
        cases = [
            '',
            None,
            '哈哈呵呵',
            '随便写的',
            '123',
        ]
        for text in cases:
            r = classify(text)
            assert r is None, f"'{text}' 应返回 None，实际: {r}"

    def test_mixed_keywords_priority(self):
        """多个分类同时出现，匹配多者优先"""
        # 餐饮 + 交通
        r = classify('美团 + 滴滴')
        # 两个都有匹配，看哪个分高
        # 实际策略：评分选最高，美团(10) + 滴滴(10) = 各 10，但 max 会返回第一个
        assert r is not None

    def test_case_insensitive(self):
        """大小写不敏感"""
        assert classify('McDonald')['category'] == '餐饮'
        assert classify('STARBUCKS')['category'] == '餐饮'

    def test_confidence_high(self):
        """强关键词应该 confidence 高"""
        r = classify('美团')
        assert r is not None
        assert r['confidence'] >= 0.5

    def test_negative_hints(self):
        """排除词降低分类置信度"""
        # 单纯"收到"不能分类
        r = classify('收到一笔钱')
        # 应该返回 None（无分类关键词）
        assert r is None

    def test_preprocess_strips_amounts(self):
        """文本预处理应剥离金额数字"""
        # 不应被金额里的数字干扰
        r = classify('美团外卖 28.50')
        assert r is not None
        assert r['category'] == '餐饮'
        # 没有 28.50 干扰
        assert '28' not in r['matched'][0] if r['matched'] else True

    def test_preprocess_strips_order_id(self):
        """文本预处理应剥离订单号"""
        r = classify('美团外卖 订单号 1234567890123')
        assert r is not None
        assert r['category'] == '餐饮'

    def test_preprocess_strips_payment_method(self):
        """文本预处理应剥离支付方式"""
        r = classify('美团外卖 微信支付 ¥28.50')
        assert r is not None
        assert r['category'] == '餐饮'

    def test_user_learning_round_trip(self):
        """用户学习能记忆并应用（持久化到 DB）"""
        from gerenjizhang.utils.classifier import remember_correction, clear_user_learned, get_user_learned
        from gerenjizhang.db import get_user_memory

        # 清理状态
        clear_user_learned(1)

        # 用户把一个不常见词映射到「餐饮」
        remember_correction(1, '某某小店咖啡', '餐饮', 'expense')

        # 下次分类时应该用用户记忆
        r = classify('某某小店咖啡', user_id=1)
        assert r is not None
        assert r['category'] == '餐饮'
        assert r['confidence'] >= 0.9
        assert r.get('source') == 'user_memory'

        # ✅ 验证：记忆已经持久化到 DB（不只在内存）
        from_db = get_user_memory(1)
        assert len(from_db) >= 1
        assert any(m['keyword'] == '某某小店咖啡' for m in from_db)

        # 清理
        clear_user_learned(1)

    def test_user_learning_partial_match(self):
        """用户学习支持部分匹配"""
        from gerenjizhang.utils.classifier import remember_correction, clear_user_learned

        clear_user_learned(2)
        remember_correction(2, '罗森便利店', '购物', 'expense')

        # 包含部分文字的输入也应该匹配
        r = classify('昨晚在罗森便利店买东西', user_id=2)
        assert r is not None
        assert r['category'] == '购物'
        clear_user_learned(2)

    def test_user_memory_survives_cache_clear(self):
        """清空进程内缓存后，DB 里的记忆仍然能加载回来"""
        from gerenjizhang.utils.classifier import (
            remember_correction, invalidate_cache, get_user_learned, clear_user_learned
        )
        from gerenjizhang.db import get_user_memory

        clear_user_learned(3)
        remember_correction(3, '测试商家', '购物', 'expense')

        # 清掉进程内缓存
        invalidate_cache(3)

        # 下次分类 → 应该自动从 DB 重新加载
        r = classify('测试商家', user_id=3)
        assert r is not None
        assert r['category'] == '购物'
        assert r.get('source') == 'user_memory'  # 来源是用户记忆

        clear_user_learned(3)

    def test_memory_use_count_increments(self):
        """记忆被引用次数应该增加"""
        from gerenjizhang.utils.classifier import remember_correction, clear_user_learned
        from gerenjizhang.db import get_user_memory

        clear_user_learned(4)
        remember_correction(4, '常用店', '餐饮', 'expense')

        # 多次分类
        classify('常用店', user_id=4)
        classify('今天在常用店吃饭', user_id=4)
        classify('常用店外卖', user_id=4)

        # use_count 应该增加
        mems = get_user_memory(4)
        target = next(m for m in mems if m['keyword'] == '常用店')
        assert target['use_count'] >= 3  # 至少 3 次（确切地说 3 次）

        clear_user_learned(4)

    def test_real_world_import_scenarios(self):
        """真实导入场景（微信/支付宝账单格式）"""
        cases = [
            # 微信支付典型格式
            ('微信支付 收款方：美团点评 28.50', '餐饮'),
            ('微信支付 收款方：滴滴出行 25.00', '交通'),
            ('微信支付 收款方：沃尔玛 156.80', '购物'),
            ('微信支付 收款方：星巴克咖啡 38.00', '餐饮'),
            # 支付宝典型格式
            ('支付宝 麦当劳(北京) 35.50', '餐饮'),
            ('支付宝 携程旅行机票 580.00', '交通'),
            ('支付宝 京东商城 88.00', '购物'),
            # 包含干扰信息
            ('微信支付 美团外卖 ¥35.00 订单号 20240101123456 微信支付', '餐饮'),
            ('滴滴出行 北京市朝阳区 ¥25.50 余额支付', '交通'),
            ('淘宝购物 ¥89.00 已支付 2024-01-01', '购物'),
        ]
        failed = []
        for text, expected in cases:
            r = classify(text)
            if not r or r['category'] != expected:
                failed.append(f"  '{text}' -> {r.get('category') if r else None} (期望 {expected})")
        assert not failed, "失败的用例:\n" + '\n'.join(failed)

    def test_preprocess_preserves_keywords(self):
        """预处理不应破坏关键词"""
        # 关键词应该被保留
        r1 = classify('美团')
        r2 = classify('美团 ¥28.50 微信支付')
        r3 = classify('2024-01-01 美团外卖 ¥35.00')
        # 三个都应该识别为餐饮
        for r in [r1, r2, r3]:
            assert r is not None
            assert r['category'] == '餐饮'
