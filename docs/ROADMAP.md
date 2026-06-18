# 个人记账（gerenjizhang）半自动 + 智能分类 + 预算提醒 实施计划

> 版本：v1.2
> 日期：2026-06-11
> 目标：在 90 天内把"已实现的 80% 能力"打磨到"用户感知得到"，构建**半自动记账 + 智能分类 + 预算提醒**的产品闭环

---

## 📊 实施进度（v1.2 更新）

**总进度：约 90%**（v1.1 的 80% + 后续：banner 适配 + 左滑交互 + 基础架构）

| 章节 | 任务 | 状态 | 备注 |
|---|---|---|---|
| 一.入口 A | 聊天选文件 → 预览 → 导入 | ✅ 完成 | 复用 `dry_run`，UI 完整 |
| 一.入口 B | 剪贴板识别 | ⏸️ 跳过 | 用户决定不做 |
| 一.入口 C | 微信服务通知 | ⏸️ 不做 | 第三方不可达 |
| 二.1 | 置信度 UI | ✅ 完成 | 三档颜色（高/中/低）|
| 二.2 | 负样本学习 | ✅ 完成 | `learn_negative` + DB 持久化 + 测试通过 |
| 二.3 | 商家/商品两级分类 | ✅ 完成 | `classify_two_stage`，9 个子类细分 |
| 三.规则 1 | 80%/100% 预算预警 | ✅ 完成 | 含频率控制 |
| 三.规则 2 | 异常大额消费 | ✅ 完成 | 事件驱动（add_bill 钩子）|
| 三.规则 3 | 连续 3 天未记账 | ✅ 完成 | 日均统计 + 召回文案 |
| 三.频率控制 | notification_log 表 | ✅ 完成 | 同规则每天最多 1 次 |
| 三.定时任务 | APScheduler 集成 | ✅ 完成 | 每天 22:00 跑检查 + 4:00 清理 |
| 三.订阅消息 | 真接入 wxacode | ⏸️ 改为 Banner | 个人主体做不了订阅消息 |
| 三.Banner | 应用内提醒（替代订阅）| ✅ 完成 | 3 档严重度（over/warn/inactive）|
| 四.第 1-2 周 | 入口 A | ✅ | |
| 四.第 3-4 周 | 置信度 UI | ✅ | |
| 四.第 5-6 周 | 预算规则 1 | ✅ | |
| 四.第 7-8 周 | 入口 B | ⏸️ 跳过 | |
| 四.第 9-10 周 | 两级分类 | ✅ | 比计划提前完成 |
| 四.第 11-12 周 | 规则 2/3 + 模板 | ✅ | 模板改为 banner（个人主体限制）|

### v1.1 → v1.2 之间的额外工作（不在原计划）

| 类型 | 任务 | 备注 |
|---|---|---|
| **新功能** | 首页左滑交互（编辑/删除）| iOS 风格 0.2s 缓动，2 档按钮（蓝编辑+珊瑚红删除）|
| **新功能** | 9 个通知规则测试 | 4 个 Rule2 用例 + 2 个 Rule3 + 3 个两级分类 |
| **基础架构** | `.env` + `python-dotenv` | 凭证进 gitignore，development 自动加载 |
| **基础架构** | `base-button` 加 `customStyle/customClass` | 解决组件样式隔离 |
| **基础架构** | `app.py` 加 FLASK_ENV 切换 | development 自动 reload / production waitress |
| **UI 修复** | 预算页按钮比例 + 不溢出 | `.btn-mini` 用 `calc(50% - 6rpx)` |

### 待你手动做的 1 件事
- ~~去微信公众平台申请 3 个订阅消息模板~~ → **不需要**（个人主体做不了，已用 banner 替代）

### 已知遗留
- **Rule 2 测试需要稳定数据库**：测试数据落在本月内才算得对（详见 test 文件注释）
- **Rule 2 误报风险**：月头几天日均不稳定，触发可能偏敏感；观察一周后调阈值
- **环境变量**：`.env` 已配好，但 appid/secret 仍在 [frontend/README.md:106-107](frontend/README.md) 历史记录里——下次有空可以清掉

---

## 〇、核心原则（写代码前先读三遍）

**记账类 App 的核心 KPI 不是"用户记了多少条"，而是"用户月底还愿意打开"。**

所有功能设计都要回答一个问题：**它有没有降低用户记账的心理负担？** 没有的话不要做。

- ❌ **避免过度自动化**：用户失去掌控感 → "这啥东西记错了" → 弃用
- ❌ **避免过度打扰**：通知轰炸 → 关掉通知 → 弃用
- ✅ **追求"省心但不失控"**：让用户用得轻量，但对每笔账都有最终确认权

---

## 一、半自动录入：三个入口（按落地难度排）

### 入口 A：从聊天记录选账单文件导入 ⭐ **第一个做**

**为什么先做这个**：[gerenjizhang/api/bill.py:464](gerenjizhang/api/bill.py#L464) 的 `import` 端点已经能解析微信/支付宝 XLSX/CSV，**这个功能 80% 写完了，只差一个友好的前端入口**。把这一块打磨好，就已经是国内个人记账的"半自动"顶配。

#### 关键设计

- **入口放首页**（[miniprogram/pages/index/index.wxml](miniprogram/pages/index/index.wxml)），不埋在"我的"里
  - 用户记完账回到首页是高频路径
- **选文件后先预览再入库**
  - 让用户看到"识别了 23 笔 / 跳过 2 笔退款 / 3 笔已存在"
- **失败的行展示在弹层里**
  - 让用户改完再传，不要直接把错误吞掉

#### API 改动

[gerenjizhang/api/bill.py:478-481](gerenjizhang/api/bill.py#L478) 的 `import` 端点**已经支持 `dry_run`**：
- 前端先调 `dry_run=true` 拿预览
- 用户点确认 → 调 `dry_run=false` 真正导入
- 体验闭环就出来了

#### 前端实现要点

```js
// 用 wx.chooseMessageFile 从聊天记录选文件
wx.chooseMessageFile({
  count: 1,
  type: 'file',
  extension: ['xlsx', 'csv'],
  success: (res) => {
    const filePath = res.tempFiles[0].path
    // 先 dry_run 预览
    uploadAndPreview(filePath)
  }
})
```

---

### 入口 B：剪贴板智能识别 ⭐⭐ **第二个做**

**触发场景**：用户复制了"微信支付：28.5 元"这种文本到剪贴板（很常见的操作），下次打开小程序自动识别。

#### 实现思路

在 [miniprogram/app.js](miniprogram/app.js) 的 `onShow` 里检测：

```js
wx.getClipboardData({
  success: (res) => {
    if (looksLikePayment(res.data)) {
      // 弹一个轻量卡片 "检测到一笔支出，要记录吗？"
    }
  }
})
```

#### 关键设计（最容易踩坑的地方）

- **不要每次打开都读剪贴板**：`getClipboardData` 在 iOS 上会弹权限框，弹三次用户就烦了
- **只在首页 onShow 读一次**，识别不到就静默
- **识别规则要保守**：宁可漏掉，不要把"我刚才复制了'月付 28.5 元'"这种非支付文本误判成账单
- **必须让用户看到原文 + 解析结果**，不能黑盒入账

#### 解析逻辑

放后端 `gerenjizhang/utils/` 下的新文件 `parser.py`，前端只负责传字符串和展示。

**判断"是否像支付文本"的前置规则**（粗筛，必须满足才解析）：
1. 包含 `¥` 或 `元` 或 `￥`
2. 包含数字
3. 长度 < 100 字符
4. 包含支付/收款/到账/扣款/消费 等关键词之一

**A/B 测试策略**：
- 上线后看一周数据
- 如果用户**点弹卡片**的比例 < 30%，说明打扰大于价值
- **直接砍掉**，把精力挪到别的地方

---

### 入口 C：微信支付"服务通知" ⭐ **第三个做，最容易翻车，不建议押重注**

微信支付付款后，**微信支付小程序**会发服务通知（"微信支付"那个蓝色图标的消息）。技术上第三方小程序**没办法监听**这个通知。

**唯一可行的方案**：让用户**主动授权**订阅消息，当用户从你 App 内**跳到微信支付小程序**完成支付后，回来时触发提醒——但这个流程**用户走通的概率极低**。

**我的建议**：直接不做，把精力放在 A 和 B 上。

---

## 二、智能分类：怎么从"能用"做到"用户爱用"

[gerenjizhang/utils/classifier.py](gerenjizhang/utils/classifier.py) 已经做得很扎实了——关键词 + 用户学习 + 文本预处理，方向正确。**继续打磨以下几个点**：

### 1. 置信度分级展示（最高优先级）

分类不要只给一个结果，给**置信度 + 解释**：

```
┌─────────────────────────────┐
│ 美团外卖 -¥28.50            │
│ 推测分类: 餐饮  (92% ✓)    │  ← 高置信度，绿色
│ 匹配关键词: 美团            │
└─────────────────────────────┘

┌─────────────────────────────┐
│ 便利店付款 -¥15.00          │
│ 推测分类: 购物  (45% ?)    │  ← 低置信度，黄色
│ 建议核对                   │
└─────────────────────────────┘
```

**这样做的价值**：
- 高置信度 → 用户**改都懒得改** → 记账 0 摩擦
- 低置信度 → 用户**主动确认** → 你的用户学习数据更准

**代码上**：[classifier.py:411](gerenjizhang/utils/classifier.py#L411) 的 `classify` 函数已经返回了 `confidence`，**前端要消费这个字段**。当前最大的浪费是没用到这个字段。

### 2. 写"负样本"——教分类器什么**不**是

现在 `classify` 只学"这条应该归到 X 类"，**没学"这条不应该归到 Y 类"**。

#### 反例场景

- "美团退款 28.5" → 智能分类给"餐饮"（因为美团），但实际是**收入/退款**
- "信用卡还款 5000" → 智能分类给"居住"（命中"还款"），误判

#### 建议

在 [classifier.py](gerenjizhang/utils/classifier.py) 加 `learn_negative(user_id, text, wrong_category)` 接口：
- 用户改分类时如果是因为"分类器太自信了分错"
- 就记一条负样本
- 下次该文本+该分类**降权**

**这是从"有监督关键词"进化到"个性化分类器"的关键一步。**

### 3. 商家识别 vs 商品识别

[gerenjizhang/api/bill.py:580](gerenjizhang/api/bill.py#L580) 的 import 逻辑现在把"交易对方 + 商品"拼起来识别，**这个对的**。但建议**拆开识别**：

- **商家识别**（高权重）→ 决定大类（餐饮/购物/...）
- **商品识别**（低权重）→ 决定细分类（"超市"细分到"日用品" vs "食品"）

**实操**：[classifier.py](gerenjizhang/utils/classifier.py) 加 `classify_two_stage(text)` 函数，先商家后商品，**准确率能再上一档**。

---

## 三、预算提醒：最容易做错的功能

**见一个记账 App 死一个**的"通知策略错误"，先列出来：

### ❌ 反模式（绝对不要做）

| 反模式 | 后果 |
|---|---|
| 每笔消费都推 | 第二天用户关订阅 |
| 月初推"本月预算 5000 元" | 纯粹是噪音 |
| 超额了才推 | 用户已经花了 6000 / 5000，推了也没用 |

### ✅ 我会做的三条触发规则

#### 规则 1：单分类进度预警（80% / 100%）

- 餐饮预算 2000，已花 1620 → 推"餐饮本月已用 81%"
- **阈值 80% 是黄金点**，再早就没用，再晚就晚了

#### 规则 2：异常大额消费

- 单笔 > 当月日均消费的 5 倍 → 推"刚有一笔 -XXX 元，超出日常水平"
- 例：日均 80 块，付了 1500 → 推

#### 规则 3：连续未记账提醒

- 连续 3 天没记 → 推"3 天没记了，是不是漏了几笔？"
- 这是**召回**用户的钩子，不是**打扰**

### 频率控制（比规则本身更重要）

**同一个规则对同一用户，每天最多触发 1 次**。

#### 数据库设计

加一个 `notification_log` 表：

```sql
CREATE TABLE notification_log (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  rule_type VARCHAR(32) NOT NULL,  -- 'budget_80' / 'large_amount' / 'inactive'
  triggered_at DATETIME NOT NULL,
  INDEX idx_user_time (user_id, triggered_at)
);
```

推之前先查这条记录**今天有没有推过同类型**——**有就不推**。

### 订阅消息模板设计

微信订阅消息需要模板，前端用 [`wx.requestSubscribeMessage`](https://developers.weixin.qq.com/miniprogram/dev/api/open-api/subscribe-message/wx.requestSubscribeMessage.html) 一次性拉授权。

#### 建议申请 3 个模板

| 模板 | 字段 |
|---|---|
| `预算进度提醒` | `{{thing.DATA}}` + `{{amount.DATA}}` + `{{phrase.DATA}}` |
| `大额消费提醒` | 同上 |
| `记账提醒` | 简单的 `{{thing.DATA}}` + `{{date.DATA}}` |

#### 关键 UX

**在用户设置预算成功时顺便拉授权，转化率最高。** 不要冷启动时弹"是否允许通知"——没人会答应。

### 定时任务实现

推荐用 **APScheduler** 集成到 Flask：

```python
# 每天 22:00 跑一次
scheduler.add_job(
    check_budget_alerts,
    'cron',
    hour=22,
    minute=0,
    args=[app]
)
```

---

## 四、90 天开发顺序

| 周 | 任务 | 价值 |
|---|---|---|
| 1-2 | **入口 A 打磨**：聊天选文件 → 预览 → 导入 | 把已有的 80% 能力变成可用功能 |
| 3-4 | **分类置信度 UI**：让 [classifier.py](gerenjizhang/utils/classifier.py) 的 `confidence` 字段用起来 | 记账摩擦下降 50% |
| 5-6 | **预算提醒规则 1**（80% 预警）+ 频率控制 | 用户回头率提升 |
| 7-8 | **入口 B**：剪贴板识别（**A/B 测试**） | 体验升级，但要小心 |
| 9-10 | **商家/商品两级分类器** | 准确率提升 |
| 11-12 | **规则 2、规则 3** 上线 + 订阅消息模板 | 提醒体系完整 |

### 风险点

- **第 7-8 周的剪贴板识别是个赌注**：上线后看一周数据
  - 如果用户**点弹卡片**的比例 < 30% → 砍掉
  - 不要在功能上"沉没成本"

---

## 五、技术栈与代码改动清单

### 后端（[gerenjizhang/](gerenjizhang/)）

| 文件 | 改动 |
|---|---|
| [gerenjizhang/api/bill.py](gerenjizhang/api/bill.py) | `import` 端点保持现状，前端用 `dry_run` 即可 |
| [gerenjizhang/utils/classifier.py](gerenjizhang/utils/classifier.py) | 新增 `learn_negative`、新增 `classify_two_stage` |
| [gerenjizhang/utils/parser.py](gerenjizhang/utils/parser.py) | **新建**：剪贴板文本解析 |
| [gerenjizhang/api/notification.py](gerenjizhang/api/notification.py) | **新建**：预算提醒检查 + 订阅消息推送 |
| [gerenjizhang/db.py](gerenjizhang/db.py) | 新增 `notification_log` 表的 CRUD |

### 前端（[miniprogram/](miniprogram/)）

| 文件 | 改动 |
|---|---|
| [miniprogram/pages/index/index.wxml](miniprogram/pages/index/index.wxml) | 首页加"导入账单"按钮 |
| [miniprogram/pages/add/add.js](miniprogram/pages/add/add.js) | 展示分类置信度 + 匹配关键词 |
| [miniprogram/app.js](miniprogram/app.js) | `onShow` 加剪贴板检测（入口 B） |
| [miniprogram/utils/api.js](miniprogram/utils/api.js) | 新增 `/api/notification/*` 调用 |

---

## 六、关键数据指标

上线后**每周看一次**这些数据，决定下一步投入：

| 指标 | 目标 | 含义 |
|---|---|---|
| 入口 A 选文件率 | > 20% | 首页按钮是否有价值 |
| 入口 B 卡片点击率 | > 30% | 剪贴板识别是否打扰 > 价值 |
| 分类准确率 | > 85% | 高置信度结果中被用户改的比例 < 15% |
| 订阅消息授权率 | > 40% | 预算设置时的授权转化 |
| 通知点击率 | > 25% | 通知文案是否有信息量 |
| 月活/月启动 | 持续 > 4 次 | 召回是否有效 |

---

## 七、最终总结

**你的 App 缺的不是新功能，而是把"已实现的 80%"打磨到"用户感知得到"的程度。**

- **入口 A** 让你 90% 的代码发挥 100% 价值
- **置信度 UI** 让你的 [classifier.py](gerenjizhang/utils/classifier.py) 从"功能"变成"产品力"
- **预算提醒的"克制"比提醒本身更重要**

> 原则优先级：**半自动 > 智能分类 > 预算提醒**
>
> 半自动解决"用户愿不愿意记"，智能分类解决"用户记起来累不累"，预算提醒解决"用户月底还记不记得这个 App"。三者缺一不可，但先后顺序不能反。
