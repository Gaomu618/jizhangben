"""
智能分类：根据备注文字判断属于哪个分类
策略：关键词匹配 + 评分（命中越多越确定）

升级点：
1. 文本预处理（剥离金额、时间、订单号等干扰）
2. 用户学习（用户修正后自动记忆，未来优先推荐）
"""
import re

# ==================== 文本预处理 ====================
# 这些模式不携带分类信息，识别出来直接剥掉
# 注意：金额在中文账单里经常带 ¥、￥、( ) 等符号
NOISE_PATTERNS = [
    # 金额（含 ¥、￥、元、$、小数）
    r'[¥￥$]\s*\d+(?:[.,]\d+)?',
    r'\d+(?:[.,]\d+)?\s*元',
    r'\(\d+(?:[.,]\d+)?\)',  # (28.5)
    # 时间
    r'\d{1,2}[-/.:]\d{1,2}(?:[-/.:]\d{1,4})?(?:\s*\d{1,2}:\d{1,2}(?::\d{1,2})?)?',
    r'\d{4}[-/年]\d{1,2}[-/月]\d{1,2}',
    r'\d{1,2}[-/.]\d{1,2}[-/.](?:\d{2,4})?',
    # 订单号（纯数字 8+ 位 / 含字母的混合）
    r'\b\d{8,}\b',
    r'[A-Z0-9]{10,}',
    r'订单号?\s*[:：]?\s*\S+',
    r'NO\.\s*\S+',
    # 银行卡号
    r'\d{4}\s*\d{4}\s*\d{4}\s*\d{4}',
    # 状态词
    r'(支付成功|支付失败|已支付|未支付|交易成功|交易失败|退款成功|订单关闭)',
    r'(余额|可用|冻结|积分)\s*[:：]?\s*\S*',
    # 微信/支付宝 特有的格式
    r'(微信支付|支付宝|花呗|借呗|信用卡)',
    # 数字标号
    r'第\s*\d+\s*[单笔期]?',
    # 收款方后缀
    r'[\(（][^\)）]*商户[\)）]',
    r'[\(（][^\)）]*商家[\)）]',
]

NOISE_RE = re.compile('|'.join(NOISE_PATTERNS), re.IGNORECASE)


def preprocess(text):
    """清理文字：去除金额、时间、订单号等干扰信息"""
    if not text:
        return ''
    cleaned = NOISE_RE.sub(' ', text)
    # 多余空格合并
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned


# ==================== 关键词字典 ====================
KEYWORDS = {
    '餐饮': {
        'strong': [
            # 外卖平台
            '美团', '饿了么', '口碑', '大众点评', '口碑外卖', '美团外卖', '美团到店',
            # 西式快餐
            '麦当劳', '肯德基', 'kfc', 'mcdonald', '必胜客', 'pizzahut', '达美乐', 'dominos',
            '汉堡王', 'burgerking', 'subway', '赛百味', '棒约翰', 'pizzahut',
            # 咖啡奶茶
            '星巴克', 'starbucks', '瑞幸', 'luckin', 'costa', 'tims', 'timhortons',
            '蜜雪冰城', '喜茶', 'heytea', '奈雪', '奈雪的茶', '茶百道', '古茗',
            '一点点', 'coco', '益禾堂', '乐乐茶', '7分甜', '沪上阿姨', 'CoCo',
            '一点点', '鹿角巷', 'the alley', '快乐柠檬', 'happy lemon',
            # 中餐
            '海底捞', '西贝', '外婆家', '全聚德', '狗不理', '呷哺呷哺',
            '南京大牌档', '绿茶餐厅', '外婆家', '新白鹿', '弄堂里',
            '黄焖鸡', '沙县小吃', '兰州拉面', '螺蛳粉', '麻辣烫', '冒菜',
            '小龙坎', '大龙燚', '钢管厂五区', '谭鸭血', '珮姐',
            # 通用
            '餐厅', '饭店', '食堂', '咖啡', '奶茶', '饮料', '午餐', '晚餐',
            '早餐', '宵夜', '夜宵', '外卖', '套餐', '堂食', '打包', '订餐',
            '美食', '小吃', '烘焙', '面包', '甜品', '蛋糕', '火锅', '烧烤',
            # 用户场景补充（2026-06 微信账单）
            '鼎味包点', '可口可乐', '太古可口可乐', '广东职业技术学院', '餐费',
        ],
        'category': '餐饮',
        'type': 'expense',
    },
    '交通': {
        'strong': [
            # 网约车
            '滴滴', 'didi', '嘀嗒', '嘀嗒出行', 't3', 't3出行',
            '高德', 'amap', '高德地图', '高德打车', '高德出行',
            '曹操出行', '首汽约车', '享道出行', '如祺出行', 'T3出行',
            '花小猪', '花小猪打车',
            # 公共交通
            '出租车', '的士', '网约车', '顺风车', '专车', '快车', '拼车',
            '地铁', '公交', '巴士', '大巴', '高铁', '动车', '火车', '城际',
            '12306', '铁路',
            '一卡通', '羊城通', '深圳通', '北京一卡通', '上海公共交通卡',
            '公交卡充值', '地铁充值',
            # 航空
            '航空', '机票', '航班', '登机牌', '值机',
            '东方航空', '国航', '南航', '海航', '国泰航空', '厦航', '深航',
            '携程', 'ctrip', '飞猪', '去哪儿', '同程', '艺龙', '携程旅行',
            '春秋航空', '吉祥航空', '华夏航空',
            # 加油
            '加油', '中石化', '中石油', '壳牌', 'bp', 'bp加油站',
            '中化石油', '中海油', '延长石油', '道达尔',
            # 停车/高速
            '停车', '停车费', '高速', 'etc', '通行费', '路桥费',
            '咪表', '停车宝', '停简单', 'ETCP',
            # 共享出行
            '共享单车', '摩拜', '美团单车', '哈啰单车', 'hellobike', '青桔',
            '滴滴青桔', 'ofo', '小蓝单车', '小鸣单车',
            '打车', '网约', '顺路',
        ],
        'category': '交通',
        'type': 'expense',
    },
    '购物': {
        'strong': [
            # 电商平台
            '淘宝', 'taobao', '天猫', 'tmall',
            '京东', 'jd', 'jd.com', '京东商城', '京东到家', '京东超市', '京东便利店',
            '拼多多', 'pdd', 'pinduoduo',
            '苏宁', 'suning', '国美', 'gome',
            '亚马逊', 'amazon', '当当', 'dangdang', '考拉', '网易考拉',
            '唯品会', 'vipshop', '网易严选', '严选', '小米有品', '有品',
            # 线下零售
            '超市', '便利店', '全家', 'lawson', '罗森', '7-eleven', '711', 'seveneleven',
            '屈臣氏', 'watsons', '万宁', 'mannings', '莎莎', 'sasa',
            '沃尔玛', 'walmart', '家乐福', 'carrefour', '永辉', '大润发', 'rt-mart',
            '盒马', '盒马鲜生', 'freshippo', '山姆', 'sams club', '麦德龙', 'metro',
            '华润万家', 'ole', 'blt', 'city shop',
            '名创优品', 'miniso', 'nomi', '无印良品', 'muji',
            '优衣库', 'uniqlo', 'zara', 'h&m', 'gap', '优百库', '优库',
            '宜家', 'ikea',
            '迪卡侬', 'decathlon',
            # 数字服务 / 订阅 / App 内购
            'apple.com/bill', 'apple.com', 'icloud', 'app store', 'appstore',
            'google play', 'googleone', 'google one',
            '网盘', '云盘', '会员',
        ],
        'category': '购物',
        'type': 'expense',
    },
    '娱乐': {
        'strong': [
            # 电影
            '电影院', '影城', '猫眼', 'maoyan', '淘票票', 'taopiaopiao',
            '万达影城', '横店', '金逸', '中影', '大地影院', '博纳影城',
            'imax', '中国巨幕', 'cgs',
            # 游戏
            'steam', 'playstation', 'psn', 'xbox', '任天堂', 'nintendo',
            'switch', 'epic games', '战网', '暴雪', '暴雪战网',
            '英雄联盟', 'lol', '王者', '王者荣耀', '原神', 'genshin', '米哈游',
            '崩坏', '星穹铁道', '蛋仔派对', 'pubg', '吃鸡', '和平精英',
            # 音乐/视频会员
            '网易云', '网易云音乐', 'qq音乐', 'qqmusic', '酷狗', 'kugou',
            '酷我', 'kuwo', '虾米', 'spotify', 'apple music', 'youtubepremium',
            '腾讯视频', '爱奇艺', '优酷', '哔哩哔哩', 'bilibili', '大会员', 'b站',
            '网易vip', 'qq会员', '喜马拉雅', '得到', '樊登', '混沌大学',
            # 运动/健身
            'keep', '健身', '瑜伽', '热瑜伽', '动感单车', '普拉提', 'pilates',
            '威尔士', 'will', '一兆韦德', '舒适堡', '舒适堡健身',
            # 娱乐活动
            'ktv', '卡拉ok', '密室', '剧本杀', '桌游', '保龄球', '射箭',
            '电玩城', '游戏厅', '网吧', '网咖', '电竞馆',
            '滑雪', '滑冰', '蹦极', '攀岩', '卡丁车',
            # 用户场景补充（2026-06 微信账单）
            '广州桔子红电竞', '桔子红电竞', '桔上电竞', '电竞',
            '红果短剧', '短剧',
        ],
        'category': '娱乐',
        'type': 'expense',
    },
    '居住': {
        'strong': [
            '房租', '租金', '押金', '中介费',
            '物业', '物业费', '管理费',
            '水费', '电费', '燃气', '煤气', '暖气', '供热',
            '宽带', '光纤', '电信', '联通', '移动',
            '话费', '手机充值', '流量', '流量包', '月租',
            '房租水电', '公寓', '自如', '链家', '贝壳', '贝壳找房', '我爱我家',
            '蛋壳', '青客', '泊寓', '魔方', 'v领地',
            '水务', '供电', '国家电网', '南方电网',
        ],
        'category': '居住',
        'type': 'expense',
    },
    '医疗': {
        'strong': [
            '医院', '诊所', '门诊', '急诊', '住院', '出院', '病房',
            '药房', '药店', '同仁堂', '老百姓大药房', '大参林', '益丰药房', '一心堂',
            '海王星辰', '健民', '千金', '老百姓', '益丰', '漱玉平民',
            '平安好医生', '丁香医生', '丁香园', '微医', '好大夫', '春雨医生',
            '美团买药', '饿了么买药', '京东健康', '阿里健康',
            '医保', '挂号', '门诊费', '住院费', '手术费', '检查费', '化验费',
            '体检', '体检中心', '美年大健康', '爱康国宾', '慈铭',
            '种牙', '正畸', '牙科', '眼科', '皮肤科',
        ],
        'category': '医疗',
        'type': 'expense',
    },
    '教育': {
        'strong': [
            '学费', '培训费', '补课', '辅导班', '家教', '一对一',
            '新东方', '学而思', '好未来', '猿辅导', '作业帮', '跟谁学',
            '网易云课堂', '腾讯课堂', '慕课网', 'imooc', 'coursera', 'udemy', 'edx',
            '极客时间', '掘金', '知乎会员', 'b站大会员',
            '书', '图书', 'kindle', '微信读书', '掌阅', '得到', '樊登', '混沌大学',
            '中国大学mooc', '学堂在线',
            '雅思', '托福', 'gre', 'gmat', 'bec', 'bec商务英语',
            '英语', '日语', '韩语', '法语', '德语', '西班牙语',
        ],
        'category': '教育',
        'type': 'expense',
    },
    '工资': {
        'strong': [
            '工资', '薪资', '月薪', '年薪', '薪水', '工钱', '报酬',
            '工资入账', '工资发放', '薪资发放', '代发工资',
            '有限公司', '公司发放', '对公转账', '对公汇款',
        ],
        'category': '工资',
        'type': 'income',
    },
    '奖金': {
        'strong': [
            '奖金', '年终奖', '绩效', '提成', '分红', '季度奖',
            '红包', '中奖', '彩票', '奖励', '嘉奖', '绩效奖金',
        ],
        'category': '奖金',
        'type': 'income',
    },
    '理财': {
        'strong': [
            '余额宝', '零钱通', '理财通', '京东金融', '度小满', '度小满理财',
            '股票', '基金', '债券', '理财', '投资收益', '黄金etf',
            '招商银行', '工商银行', '建设银行', '中国银行', '农业银行', '交通银行',
            '兴业银行', '浦发银行', '民生银行', '光大银行', '平安银行',
            '利息', '余额', '转入', '转出', '赎回', '申购',
            '支付宝理财', '微信理财', '京东小金库', '小米金融',
        ],
        'category': '理财',
        'type': 'income',
    },
    '副业': {
        'strong': [
            '兼职', '稿费', '咨询费', '服务费', '外包',
            '私单', '项目款', '项目结算', '劳务', '劳务费',
            '咨询', '顾问费', '讲课费', '稿酬', '版税', '打赏',
        ],
        'category': '副业',
        'type': 'income',
    },
    '转账': {
        # 微信/支付宝转账、红包 — 单独成类，方便追溯
        # 同时支持"转出"（expense）和"转入"（income），由 bill.py 根据 in_out 字段决定
        'strong': [
            '微信转账', '转账备注', '转账',
            '微信红包', '红包', '收钱码',
            '转账给', '转账收',
        ],
        'category': '转账',
        # 默认 type 让 bill.py 根据 in_out 覆盖；这里给个合理默认
        'type': 'expense',
    },
}

# 优先排除词（出现这些词时降低其他分类的置信度）
NEGATIVE_HINTS = {
    '收到': ['餐饮', '购物', '娱乐'],  # "收到退款"不应归到消费类
    '退款': ['餐饮', '购物', '娱乐'],
    '退货': ['购物'],
    '还款': ['居住'],
    '充值': ['居住', '餐饮'],
}


# ==================== 用户学习缓存（DB + 进程内） ====================
# 进程内缓存：{user_id: {keyword: (category, type)}}
# 启动时从 DB 加载，用户改了立刻写回 DB 并更新缓存
# 避免每次都查数据库（虽然现在没存数据库，但接口已经留好）
_user_learned_cache = {}
_user_negative_cache = {}  # 新增：负样本缓存 {user_id: {keyword: {wrong_cat: use_count}}}
_cache_loaded_users = set()  # 已经从 DB 加载过的 user_id


def _ensure_cache_loaded(user_id):
    """懒加载：第一次访问某用户时从 DB 加载到缓存"""
    if user_id in _cache_loaded_users:
        return
    try:
        from gerenjizhang.db import get_user_memory_dict, get_user_negatives
        _user_learned_cache[user_id] = get_user_memory_dict(user_id)
        _user_negative_cache[user_id] = get_user_negatives(user_id)
        _cache_loaded_users.add(user_id)
    except Exception:
        _user_learned_cache[user_id] = {}
        _user_negative_cache[user_id] = {}


def remember_correction(user_id, note, category, bill_type='expense', old_category=None):
    """用户修正了一条账单的分类 → 持久化到 DB
    提取清理后的关键词文本，关联到 category + type
    下次分类时优先用这些

    Args:
        old_category: 修正前的分类。如果传了，会同时记一条**负样本**，
                     避免分类器下次再把这条文本判到那个错的分类
    """
    if not user_id or not note or not category:
        return
    text = preprocess(note).lower().strip()
    if not text:
        return

    # 写 DB
    try:
        from gerenjizhang.db import save_user_memory
        save_user_memory(user_id, text, category, bill_type)
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"保存用户记忆失败: {e}")

    # 同步更新缓存
    _ensure_cache_loaded(user_id)
    if user_id not in _user_learned_cache:
        _user_learned_cache[user_id] = {}
    _user_learned_cache[user_id][text] = (category, bill_type)

    # 负样本：如果用户**明确改了**分类（旧→新），记住"这段文本不该归到旧分类"
    if old_category and old_category != category:
        learn_negative(user_id, text, old_category)


def learn_negative(user_id, keyword, wrong_category):
    """记录一条负样本：这段文本**不**应该归到 wrong_category

    典型场景：用户把"美团退款 28.5"从"餐饮"改到"其他"
    → learn_negative(user_id, "美团 退款", "餐饮")
    → 下次再分类时，分类器想归到"餐饮"会降权
    """
    if not user_id or not keyword or not wrong_category:
        return
    try:
        from gerenjizhang.db import save_negative_memory
        save_negative_memory(user_id, keyword, wrong_category)
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"保存负样本失败: {e}")

    # 同步更新缓存
    _ensure_cache_loaded(user_id)
    if user_id not in _user_negative_cache:
        _user_negative_cache[user_id] = {}
    _user_negative_cache[user_id].setdefault(keyword, {})[wrong_category] = \
        _user_negative_cache[user_id].get(keyword, {}).get(wrong_category, 0) + 1


def get_user_learned(user_id):
    """获取用户学习过的映射 {keyword: (category, type)}"""
    if not user_id:
        return {}
    _ensure_cache_loaded(user_id)
    return _user_learned_cache.get(user_id, {})


def get_user_negatives_cached(user_id):
    """获取用户负样本 {keyword: {wrong_category: use_count}}"""
    if not user_id:
        return {}
    _ensure_cache_loaded(user_id)
    return _user_negative_cache.get(user_id, {})


def clear_user_learned(user_id):
    """清空某用户的学习缓存（也清 DB）。返回删除的记忆条数"""
    _user_learned_cache.pop(user_id, None)
    _user_negative_cache.pop(user_id, None)  # 同时清负样本
    _cache_loaded_users.discard(user_id)
    deleted = 0
    try:
        from gerenjizhang.db import clear_user_memory, clear_user_negatives
        deleted = clear_user_memory(user_id) or 0
        deleted += clear_user_negatives(user_id) or 0
    except Exception:
        pass
    return deleted


def invalidate_cache(user_id):
    """缓存失效（删除某条记忆后调用，下次用时重新从 DB 加载）"""
    _user_learned_cache.pop(user_id, None)
    _user_negative_cache.pop(user_id, None)
    _cache_loaded_users.discard(user_id)


def classify(text, fallback=None, user_id=None):
    """根据备注文字智能分类

    Args:
        text: 备注文字（如"美团 28.5"）
        fallback: 无法分类时返回的分类
        user_id: 用户 ID（启用个性化学习）

    Returns:
        dict: {'category': '餐饮', 'type': 'expense', 'confidence': 0.95, 'matched': '美团'}
        或 None
    """
    if not text or not isinstance(text, str):
        return None

    # 1. 文本预处理（去金额、时间、订单号等干扰）
    raw_text = text
    cleaned = preprocess(text)
    text_lower = cleaned.lower().strip()
    if not text_lower:
        return None

    # 2. 优先用用户学习过的（最高优先级）
    if user_id:
        learned = get_user_learned(user_id)  # {kw: (category, type)}
        # 2.0 用户自定义分类的关键词（来自 user_category_keyword 表）
        try:
            from gerenjizhang.db import get_user_keywords_for_classifier
            user_custom_kw = get_user_keywords_for_classifier(user_id)
            # 合并到 learned（用户自定义分类的关键词优先级等同于 user_memory）
            for kw, info in user_custom_kw.items():
                learned[kw.lower()] = (info['category'], info['type'])
        except Exception:
            pass

        if text_lower in learned:
            cat, type_ = learned[text_lower]
            # ✅ 异步 +1 引用计数（fire-and-forget，不阻塞响应）
            from gerenjizhang.db import increment_memory_use
            increment_memory_use(user_id, text_lower)
            return {
                'category': cat,
                'type': type_,
                'confidence': 0.95,  # 用户自己定的，最高
                'matched': ['[用户记忆]'],
                'source': 'user_memory',
            }
        # 部分匹配（学习过包含这段文字）
        for mem_text, (mem_cat, mem_type) in learned.items():
            if mem_text in text_lower or text_lower in mem_text:
                from gerenjizhang.db import increment_memory_use
                increment_memory_use(user_id, mem_text)
                return {
                    'category': mem_cat,
                    'type': mem_type,
                    'confidence': 0.9,
                    'matched': [f'[部分匹配:{mem_text}]'],
                    'source': 'user_memory',
                }

    # 3. 关键词字典匹配 + 评分
    scores = {}

    for category, info in KEYWORDS.items():
        matched = []
        for kw in info['strong']:
            kw_lower = kw.lower()
            if kw_lower in text_lower:
                matched.append(kw)

        if matched:
            # 强匹配：每个 10 分；多关键词加分
            scores[category] = {
                'score': len(matched) * 10,
                'matched': matched,
                'type': info['type'],
            }

    if not scores:
        return None

    # 4. 排除词处理（静态词典，跨用户生效）
    for neg_word, exclude_cats in NEGATIVE_HINTS.items():
        if neg_word in text:
            for cat in exclude_cats:
                if cat in scores:
                    scores[cat]['score'] -= 5

    # 4.5 个性化负样本降权（per-user learning）
    # 用户改分类时记住的"不该归到 X 类"在此处应用
    if user_id:
        negatives = get_user_negatives_cached(user_id)  # {kw: {wrong_cat: use_count}}
        if negatives:
            for kw, wrong_cats in negatives.items():
                # 完全匹配优先降权
                if text_lower == kw:
                    for wc, cnt in wrong_cats.items():
                        if wc in scores:
                            scores[wc]['score'] -= 15 * cnt  # 强降权
                # 部分匹配也降权（弱一些）
                elif kw in text_lower or text_lower in kw:
                    for wc, cnt in wrong_cats.items():
                        if wc in scores:
                            scores[wc]['score'] -= 8 * cnt

            # 任意一个分类被降权到 < 5 阈值以下 → 该分类作废
            scores = {c: s for c, s in scores.items() if s['score'] >= 5}
            if not scores:
                return None

    # 5. 选最高分
    best = max(scores.items(), key=lambda x: x[1]['score'])

    if best[1]['score'] < 5:  # 阈值太低，放弃
        return None

    return {
        'category': best[0],
        'type': best[1]['type'],
        'confidence': min(best[1]['score'] / 20, 1.0),
        'matched': best[1]['matched'],
        'source': 'keyword_dict',
    }


# ==================== 两级分类（商家 → 商品）====================
# 第一级：决定大类（餐饮/购物/...）— 高权重，强匹配
# 第二级：决定细分类（"超市"→日用品/食品，"餐饮"→外卖/堂食）— 低权重
#
# 当前 key 字典里只有"大类"层。这一层补充一些"大类内细分"的二级规则
SUB_CATEGORY_RULES = {
    '餐饮': {
        '外卖': ['美团外卖', '饿了么', '外卖', '配送', '美团', '美团到店'],
        '堂食': ['餐厅', '饭店', '堂食', '店内', '门店'],
        '咖啡奶茶': ['咖啡', '奶茶', '星巴克', '瑞幸', '喜茶', '奈雪', '蜜雪', '一点点'],
        '快餐': ['麦当劳', '肯德基', 'kfc', '汉堡王', '必胜客', '达美乐', 'subway'],
        '正餐': ['火锅', '烧烤', '烤肉', '中餐', '西餐', '日料', '海底捞', '西贝'],
    },
    '购物': {
        '日用品': ['日用', '洗护', '纸巾', '牙膏', '洗发水', '沐浴露', '洗衣液'],
        '食品': ['零食', '饮料', '水果', '蔬菜', '生鲜'],
        '服装': ['优衣库', 'uniqlo', 'zara', 'h&m', 'gap', '服装', '衣服', '裤子', '裙子'],
        '数码': ['京东', '数码', '手机', '电脑', '耳机', '充电器', 'kindle'],
        '化妆品': ['化妆品', '口红', '粉底', 'skii', '雅诗兰黛', '兰蔻'],
    },
    '交通': {
        '网约车': ['滴滴', 'didi', '嘀嗒', '曹操', '花小猪', '高德打车'],
        '公共交通': ['地铁', '公交', '巴士', '一卡通', '深圳通', '羊城通'],
        '加油': ['加油', '中石化', '中石油', '壳牌'],
        '停车': ['停车', '停车费'],
        '高速': ['高速', 'etc', '通行费'],
    },
    '居住': {
        '房租': ['房租', '租金', '自如', '链家', '贝壳'],
        '水电': ['水费', '电费', '燃气', '煤'],
        '通讯': ['话费', '宽带', '流量', '手机充值'],
    },
}


def classify_two_stage(text, user_id=None):
    """两级分类：先商家大类，再商品细分

    Returns:
        dict: {
          'category': '餐饮',      # 大类
          'sub_category': '外卖',  # 细分（可空）
          'type': 'expense',
          'confidence': 0.9,
          'matched': ['美团'],
          'sub_matched': ['美团外卖'],
          'source': 'two_stage'
        }
        或 None（识别不出来）
    """
    # 第一级：复用 classify 拿大类
    primary = classify(text, user_id=user_id)
    if not primary:
        return None

    result = {
        'category': primary['category'],
        'sub_category': None,
        'type': primary['type'],
        'confidence': primary['confidence'],
        'matched': primary['matched'],
        'sub_matched': [],
        'source': 'two_stage'
    }

    # 第二级：在大类下找细分
    sub_rules = SUB_CATEGORY_RULES.get(primary['category'])
    if not sub_rules:
        return result

    text_lower = preprocess(text).lower()
    best_sub = None
    best_count = 0
    for sub_name, kws in sub_rules.items():
        hits = [kw for kw in kws if kw.lower() in text_lower]
        if hits and len(hits) > best_count:
            best_count = len(hits)
            best_sub = (sub_name, hits)

    if best_sub:
        result['sub_category'] = best_sub[0]
        result['sub_matched'] = best_sub[1]
        # 细分命中提一点置信度（说明分得更准）
        result['confidence'] = min(result['confidence'] + 0.1, 1.0)

    return result

