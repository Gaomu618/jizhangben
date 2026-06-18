# 记账本财报分析系统

> 项目正式名称：**记账本财报分析系统**
> 代码目录：`gerenjizhang`（历史命名）
> 大作业：广东职业技术学院 · 人工智能学院 · 202 级软工（本）

---

## 📖 项目简介

一个**个人记账 + 财务分析**全栈应用，覆盖：
- **后端**：Flask + MySQL + JWT
- **Web 端**：Vue 3 + Vite + ECharts
- **移动端**：微信小程序原生
- **核心能力**：智能分类 / 预算提醒 / 消费可视化分析

定位为**"工具 → 平台"** 双阶段产品：
1. 工具阶段：满足个人/家庭记账
2. 平台阶段：通过**自定义分类**让用户能建自己的账本体系

---

## 🏗️ 项目结构

```
PythonProject/
├── gerenjizhang/                    # 后端主目录
│   ├── app.py                       # Flask 入口
│   ├── config.py                    # 多环境配置
│   ├── db.py                        # MySQL 全部 ORM 函数（9 张表 + 30+ CRUD）
│   ├── scheduler.py                 # APScheduler 定时任务
│   ├── main.py                      # 旧入口（保留兼容）
│   ├── api/                         # REST API 蓝图
│   │   ├── auth.py                  # 登录/注册/JWT
│   │   ├── bill.py                  # 账单 CRUD + 导入/导出
│   │   ├── stats.py                 # 统计分析端点
│   │   ├── notification.py          # 通知/预算检查
│   │   └── category.py              # 自定义分类
│   ├── services/                    # 业务服务层
│   │   └── notification_service.py  # 3 条预算规则 + 频率控制
│   ├── middleware/                  # 中间件
│   │   ├── error_handler.py         # 统一错误响应
│   │   ├── request_logger.py        # 请求日志
│   │   └── limiter.py               # Flask-Limiter 限流
│   ├── utils/                       # 工具
│   │   ├── classifier.py            # 5 级智能分类算法
│   │   ├── jwt_auth.py              # JWT 签发/校验
│   │   ├── validators.py            # 密码强度 + Pillow 图片校验
│   │   ├── decorators.py            # login_required
│   │   ├── profile.py               # 资料校验
│   │   └── response.py              # 统一响应格式
│   ├── models/                      # 数据模型（保留扩展）
│   ├── schemas/                     # 数据校验 schema
│   ├── tests/                       # 单元测试（57+ 用例）
│   │   ├── test_jwt_auth.py
│   │   ├── test_validators.py
│   │   ├── test_avatar_upload.py
│   │   └── test_category_api.py
│   ├── uploads/                     # 用户上传（头像）
│   └── templates.backup/            # 旧 HTML 模板（已废弃）
│
├── miniprogram/                    # 微信小程序端
│   ├── app.js / app.json            # 小程序入口
│   ├── pages/                       # 页面
│   │   ├── index/                   # 首页（账单列表 + 滑左编辑）
│   │   ├── add/                     # 记一笔
│   │   ├── edit/                    # 编辑账单
│   │   ├── login/                   # 登录
│   │   ├── mine/                    # 个人中心
│   │   ├── stats/                   # 统计分析
│   │   └── budget/                  # 预算管理
│   └── utils/api.js                 # 小程序 API 封装
│
├── frontend/                        # Web 端
│   ├── src/
│   │   ├── views/                   # 页面
│   │   │   ├── Ledger.vue          # 首页（账单）
│   │   │   ├── Stats.vue           # 统计
│   │   │   ├── Budget.vue          # 预算
│   │   │   ├── Profile.vue         # 个人中心
│   │   │   ├── CategoryManage.vue  # 自定义分类 🆕
│   │   │   ├── Login.vue / Register.vue
│   │   ├── api/index.js             # Axios 封装
│   │   ├── components/              # 通用组件 + base 组件库
│   │   ├── i18n/                   # 中英双语
│   │   ├── router/                  # 路由
│   │   ├── stores/                  # Pinia 状态
│   │   └── utils/                   # 工具
│   ├── vite.config.js
│   └── package.json
│
├── analyze_spending.py              # 📊 数据聚合 + 6 张图
├── classify_wechat_bill.py          # 📊 微信账单分类报告
├── simulate_students.py             # 🧪 30 大学生 + 2,234 笔账单
├── export_all_to_excel.py           # 📑 16 Sheet Excel 导出
│
├── reports/                         # 生成的报告 + 图表
│   ├── spending-analysis.md
│   ├── wechat-bill-classification.md
│   └── charts/                      # 6 张 PNG
│       ├── 01_category_pie.png
│       ├── 02_monthly_trend.png
│       ├── 03_monthly_category_stack.png
│       ├── 04_user_top.png
│       ├── 05_quarterly_compare.png
│       └── 06_merchant.png
│
├── exports/                         # Excel 导出
│   └── all_users_data_*.xlsx        # 16 Sheet（按时间戳）
│
├── HOMEWORK_DRAFT.md                # 📝 大作业草稿（4500 字 / 4 大章）
├── HOMEWORK_GUIDE.md                # 📝 撰写指南
├── AI_USAGE_成员B_数据库.md          # 验证说明（数据库视角）
├── AI_USAGE_成员C_数据处理与可视化.md # 验证说明（数据视角）
├── ROADMAP.md                       # 12 周开发计划
├── DEPLOYMENT_HTTPS.md              # 生产部署指南
│
├── .env                             # 本地环境变量（gitignore）
├── .env.example                     # 模板
└── requirements.txt                 # Python 依赖
```

---

## 🛠️ 技术栈

| 层 | 技术 |
|---|---|
| **后端** | Flask 3 · MySQL 8 · JWT (HS256 + aud/iss) · APScheduler · Pillow · Flask-Limiter |
| **前端** | Vue 3 · Vite · Pinia · Tailwind · ECharts（按需 400KB）|
| **小程序** | 微信小程序原生 · 自定义 tab-bar · 组件化 |
| **AI/算法** | 关键词规则 + 负样本学习 + 两级分类 + 用户自定义分类 |
| **安全** | 7 项 P0/P1/P2 加固（详见 [ROADMAP.md](ROADMAP.md)）|

---

## 🚀 快速开始

### 1. 后端启动

```bash
# 1) 装依赖
pip install -r requirements.txt

# 2) 复制环境变量
cp .env.example .env
# 编辑 .env：填 WECHAT_APPID / WECHAT_SECRET / DB 配置

# 3) 启动（开发模式，自动 reload）
FLASK_ENV=development python gerenjizhang/app.py
# → http://localhost:5002
```

### 2. 前端启动

```bash
cd frontend
npm install
npm run dev
# → http://localhost:3000
```

### 3. 数据库初始化

启动后端时**自动**执行 `init_db()`：
- 创建 9 张表（含外键约束 + 索引）
- 给现有用户 seed 13 个系统分类
- 启动 APScheduler（每天 22:00 跑预算检查 + 04:00 清理）

### 4. 默认账号

| 账号 | 密码 | 角色 |
|---|---|---|
| `dlf` | `test123` | 真实用户（昵称"帅烽"）|
| `budget_test` | `test123` | 老测试用户（76 笔）|
| `student_01` ~ `student_30` | `test123` | 30 个模拟大学生（画像不同）|
| `陈冠希` / `wwy` / `dlf` / `小婷` / ... | `test123` | TOP 10 用户（自定义名）|

---

## 📊 核心能力

### 1. 智能分类（5 级优先级）
```
1. 用户自定义分类的关键词        ← 最高
2. 用户学习记忆（手动修正过）
3. 强关键词命中（80+ 商家）
4. 负样本降权（不该归 X 类的）
5. 两级分类（商家→子类）
```

### 2. 预算提醒
- **规则 1**：单分类 ≥ 80% / 100% 触发
- **规则 2**：单笔 > 当月日均 × 5 倍（大额）
- **规则 3**：连续 3 天未记账（召回）
- **频率控制**：同规则每用户每天最多 1 次

### 3. 自定义分类 🆕
- 13 个系统分类（🔒 不可删）
- 最多 50 个自定义分类
- 每个自定义分类可配 200 关键词
- 关键词注入分类器（优先级最高）

### 4. 消费可视化（6 维）
- 分类饼图 / 月度趋势 / 月度×分类堆叠
- 用户 TOP 10 / 季度对比 / 商家分布

---

## 🧪 测试

```bash
FLASK_ENV=testing WECHAT_APPID=test WECHAT_SECRET=test \
  python -m unittest discover -s gerenjizhang/tests -p "test_*.py"
```

**57+ 用例** 覆盖：
- JWT 编解码 + 过期
- 密码强度（8 位 + 字母+数字）
- 用户名规范（3-20 字符）
- Pillow 图片内容校验
- 分类 API CRUD + 权限 + 上限

---

## 🔒 安全

7 项加固已落地（详见 [ROADMAP.md](ROADMAP.md)）：
1. **Flask-Limiter**（login/register/import 5-10/min）
2. **JWT_SECRET 强制强值**（生产环境）
3. **avatar 内容校验**（Pillow `Image.load()`）
4. **错误响应脱敏**（不泄露微信内部 errcode）
5. **JWT aud/iss claims**
6. **密码强度**（8 位 + 字母 + 数字）
7. **HTTPS 部署文档**（[DEPLOYMENT_HTTPS.md](DEPLOYMENT_HTTPS.md)）

---

## 📚 文档导航

| 文档 | 用途 |
|---|---|
| [HOMEWORK_DRAFT.md](HOMEWORK_DRAFT.md) | 大作业草稿（约 4500 字 / 4 大章）|
| [HOMEWORK_GUIDE.md](HOMEWORK_GUIDE.md) | 套模板指南 |
| [ROADMAP.md](ROADMAP.md) | 12 周开发计划（v1.2，90% 完成）|
| [DEPLOYMENT_HTTPS.md](DEPLOYMENT_HTTPS.md) | 生产部署指南 |
| [AI_USAGE_成员B_数据库.md](AI_USAGE_成员B_数据库.md) | AI 使用验证（数据库视角）|
| [AI_USAGE_成员C_数据处理与可视化.md](AI_USAGE_成员C_数据处理与可视化.md) | AI 使用验证（数据视角）|
| [reports/spending-analysis.md](reports/spending-analysis.md) | 48 用户 / 2,512 笔 消费分析 |
| [reports/wechat-bill-classification.md](reports/wechat-bill-classification.md) | 43 条微信账单分类报告 |

---

## 📝 协作分工

| 成员 | 角色 | 核心交付 |
|---|---|---|
| 成员 A | 代码逻辑设计 | Flask API + 7 项安全加固 + 智能分类 |
| 成员 B | 数据库建库建表与维护 | 9 张表 schema + 30+ CRUD + 索引 |
| 成员 C | 数据处理与可视化 | 6 张图 + 微信账单分类 + 16 Sheet 导出 |

---

## 📜 License

教学大作业，保留所有权利。
