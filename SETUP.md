# 🚀 SETUP — 接收方 onboarding 指南

> **目标**:从零到能跑,30 分钟内完成。

## 0. 系统要求

| 依赖 | 版本 | 说明 |
|---|---|---|
| Python | >= 3.10 | 项目用了 PEP 604 union 语法 |
| Node.js | >= 18 | 前端构建 |
| MySQL | >= 5.7 (或 MariaDB 10.x) | 数据库 |
| Git | 任意 | 拉代码 |

## 1. 拉代码

```bash
git clone <repo-url>
cd PythonProject
```

## 2. 后端启动

```bash
# 1) 创建虚拟环境(推荐)
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# 2) 装依赖
pip install -r requirements.txt

# 3) 配环境变量
cp .env.example .env
# 用编辑器打开 .env,填 WECHAT_APPID / WECHAT_SECRET / SECRET_KEY / DB 密码
# 注意:WECHAT_APPID 和 WECHAT_SECRET 是必填,缺一启动失败
# SECRET_KEY 生产前必改:python -c "import secrets; print(secrets.token_hex(32))"

# 4) 准备 MySQL
#   创建一个名为 jizhangapp 的数据库:
#   CREATE DATABASE jizhangapp CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
#   启动时 init_db() 会自动建表 + seed 13 个系统分类

# 5) 启动(dev 模式,自动 reload)
FLASK_ENV=development python gerenjizhang/app.py
# → http://localhost:5002
```

## 3. 前端启动

```bash
cd frontend
npm install
npm run dev
# → http://localhost:3000
# Vite 代理会自动把 /api/* 转发到 5002
```

## 4. 验证

打开浏览器访问 http://localhost:3000,应该看到登录页。
注册一个新账号 → 登录 → 应该进入账本主页。

## 5. 跑测试

```bash
# Python 单元测试
pytest gerenjizhang/tests/ -v

# 前端测试
cd frontend && npm test
```

## 6. 微信小程序(可选)

1. 下载并打开「微信开发者工具」
2. 导入项目 → 选择 `miniprogram/` 目录
3. AppID 用项目自带的(在 project.config.json)
4. 设置 → 代理 → 勾选"使用代理" → 填 `http://127.0.0.1:5002`

## 7. 生产部署

参见 [`docs/DEPLOYMENT_HTTPS.md`](docs/DEPLOYMENT_HTTPS.md)。

## ❓ 常见问题

**Q: 启动报 `RuntimeError: 缺少必需环境变量: WECHAT_APPID, WECHAT_SECRET`**
A: 没填 `.env` 或者 `.env` 没被加载。检查 `.env` 在项目根目录,且格式正确(无引号包裹值)。

**Q: 数据库连不上**
A: 确认 `.env` 里的 `DB_HOST/DB_PORT/DB_USER/DB_PASSWORD/DB_NAME` 都对;MySQL 服务是否启动。

**Q: 前端 3000 端口显示空白页**
A: 打开浏览器控制台看报错。常见原因:后端没启(Vite 代理到 5002 失败)。

**Q: PDF 导出中文乱码**
A: 系统缺少中文字体。Windows 默认有,Linux 需要安装 `fonts-noto-cjk` 或类似包。
