# 前端联调指南

## 环境要求

- Node.js 16+
- npm 或 yarn

## 启动顺序

### 1. 启动后端（先启动）

```bash
cd C:\Users\dlf\PycharmProjects\PythonProject
python -m gerenjizhang.app
```

后端启动后会运行在 `http://localhost:5000`。

### 2. 启动前端

```bash
cd C:\Users\dlf\PycharmProjects\PythonProject\frontend
npm install
npm run dev
```

前端启动后会运行在 `http://localhost:3000`。

## Vite 代理配置

`vite.config.js` 中已配置代理：

```javascript
server: {
  port: 3000,
  proxy: {
    '/api': {
      target: 'http://localhost:5000',
      changeOrigin: true
    }
  }
}
```

这意味着：
- 前端请求 `/api/*` 会被代理到 `http://localhost:5000/api/*`
- 避免了浏览器的 CORS 问题
- 开发时无需修改 API 地址

## API 调用流程

### 登录流程

1. 用户在 `Login.vue` 输入用户名密码
2. 调用 `authAPI.login(data)`
3. 请求被发送到 `/api/auth/login`（通过 Vite 代理到后端）
4. 后端验证并返回 `{ token, userinfo }`
5. 前端将 token 存入 localStorage
6. 后续请求通过 `api/index.js` 的请求拦截器自动添加 `Authorization: Bearer <token>` header

### API 端点说明

| 模块 | 端点 | 方法 | 说明 |
|------|------|------|------|
| Auth | `/api/auth/login` | POST | 用户登录 |
| Auth | `/api/auth/register` | POST | 用户注册 |
| Auth | `/api/auth/logout` | POST | 退出登录 |
| Auth | `/api/auth/userinfo` | GET | 获取用户信息 |
| Bill | `/api/bill/list` | GET | 获取账单列表 |
| Bill | `/api/bill/<id>` | GET | 获取账单详情 |
| Bill | `/api/bill/add` | POST | 添加账单 |
| Bill | `/api/bill/edit/<id>` | POST | 编辑账单 |
| Bill | `/api/bill/delete/<id>` | POST | 删除账单 |
| Stats | `/api/stats/monthly` | GET | 月度统计 |
| Stats | `/api/stats/category` | GET | 分类统计 |

### Dashboard.vue 页面数据流

1. `onMounted` 时调用 `loadStats()` 获取月度收支统计
2. 调用 `loadBills()` 获取账单列表
3. 调用 `loadChartData()` 获取分类数据并渲染 ECharts 饼图
4. 用户操作（添加/编辑/删除）后重新加载数据

## 已知的限制和注意事项

### 1. Token 内存存储（重要）

后端 `gerenjizhang/utils/decorators.py` 中 token 存储在内存字典 `_token_store` 中：

```python
_token_store = {}
```

**影响**：
- 服务器重启后所有用户的 token 会失效
- 无法多实例部署（需要改用 Redis 等外部存储）
- 适合开发和小规模使用

**前端处理**：401 响应时会自动清除 localStorage 中的 token 并跳转到登录页

### 2. 微信 AppID/Secret 配置（**已通过 .env 管理**）

`gerenjizhang/api/auth.py` 读的是 `gerenjizhang/config.py` 的 `WECHAT_APPID` / `WECHAT_SECRET`，
**这两个值由 `app.py` 启动时从 `.env` 文件加载**（见 [gerenjizhang/app.py:1-25](gerenjizhang/app.py)）。

**.env 文件已在 `.gitignore` 中**——密钥不会进 git。

本地开发：
```bash
# 1. 复制 .env.example → .env
cp .env.example .env

# 2. 填入你的 AppID / AppSecret（从微信公众平台后台拿）
# 3. 启动（不用手敲 env vars，app.py 自动 load .env）
python gerenjizhang/app.py
```

**注意**：`app.py` 启动时会校验 `WECHAT_APPID` 和 `WECHAT_SECRET` 非空，
缺一个就 `RuntimeError` 退出（避免静默用错的值）。

### 3. CORS 配置宽松

`app.py` 中配置了：

```python
CORS(app, resources={r"/api/*": {"origins": "*"}})
```

**说明**：开发环境允许所有来源。生产环境建议限制为前端域名。

### 4. 数据库密码为空

`gerenjizhang/db.py` 中数据库配置：

```python
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "jizhangapp",
}
```

**注意**：需要确保 MySQL 中 `root` 用户无密码且数据库 `jizhangapp` 已创建。

### 5. Element Plus 依赖缺失

`package.json` 中未列出 Element Plus，但 `src/api/index.js` 中引用了：

```javascript
import { ElMessage } from 'element-plus'
```

**解决方案**：
```bash
cd frontend
npm install element-plus
```

并在 `src/main.js` 中添加：
```javascript
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
app.use(ElementPlus)
```

### 6. 搜索功能前端实现不完整

`Dashboard.vue` 中有搜索输入框 `searchKeyword`，但后端 `/api/bill/list` 不支持关键词搜索参数。前端只是重置页码，不会发送搜索关键词到后端。

## 目录结构

```
frontend/
├── index.html          # 入口 HTML
├── package.json        # 依赖配置
├── vite.config.js      # Vite 配置（含代理）
└── src/
    ├── main.js         # Vue 入口
    ├── App.vue         # 根组件
    ├── api/
    │   └── index.js    # API 封装（axios 实例）
    ├── components/     # 公共组件
    │   ├── StatCard.vue
    │   ├── RecordItem.vue
    │   ├── EditModal.vue
    │   └── BillForm.vue
    ├── router/
    │   └── index.js    # 路由配置（含守卫）
    ├── stores/
    │   └── auth.js     # 认证状态管理
    └── views/          # 页面组件
        ├── Login.vue
        ├── Register.vue
        ├── Dashboard.vue
        └── Stats.vue
```

## 快速测试

1. 启动后端和前端
2. 访问 `http://localhost:3000/register` 注册账号
3. 登录后访问 `http://localhost:3000/` 查看 Dashboard
4. 添加账单、查看统计、测试编辑和删除功能