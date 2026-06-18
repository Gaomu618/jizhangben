# HTTPS 部署指南

> 适用：个人记账（gerenjizhang）后端生产环境
> 最后更新：2026-06-12

---

## 🎯 为什么必须 HTTPS

| 风险 | 后果 |
|---|---|
| JWT 走 HTTP | 中间人抓包直接拿走 token → 假冒用户 |
| 微信 code 走 HTTP | 中间人替换 code → 登录态被劫持 |
| 用户密码走 HTTP | 中间人直接拿到明文密码 |

**生产环境**（FLASK_ENV=production）**必须**走 HTTPS，**dev** 可以用 HTTP localhost。

---

## 📋 上线前清单

### 环境变量（强校验已在 config.py 里）

```bash
# 1. 生成强随机密钥（生产用）
python -c "import secrets; print(secrets.token_hex(32))"
# 输出形如：a4f8b2c9...64 个字符
```

复制到 `.env`：

```bash
FLASK_ENV=production
SECRET_KEY=<上面生成的字符串1>
JWT_SECRET=<上面生成的字符串2>  # 与 SECRET_KEY 不同
WECHAT_APPID=wx_your_real_appid
WECHAT_SECRET=your_real_secret
CORS_ALLOWED_ORIGINS=https://your-domain.com,*.weixin.qq.com
```

启动时 `config.validate()` 会**自动校验**：

- ✅ `WECHAT_APPID` / `WECHAT_SECRET` 不能为空
- ✅ `SECRET_KEY` / `JWT_SECRET` 必须 ≥32 字符且不是弱值
- ❌ 检测到 fallback / 弱值 → 启动失败

---

## 🏗️ 推荐架构：Nginx 反向代理

**最简单、最稳的方案**：Nginx 负责 HTTPS 终结，Flask 用 waitress 跑在 localhost。

```
┌────────────────┐   HTTPS    ┌──────────┐   HTTP    ┌──────────┐
│ 微信小程序     │ ────────► │ Nginx    │ ────────► │ Flask    │
│ 浏览器         │   :443     │ :443     │  :5002    │ :5002    │
└────────────────┘            └──────────┘  localhost └──────────┘
```

### 1. 安装 Nginx + Certbot（Let's Encrypt）

```bash
# Ubuntu / Debian
sudo apt install nginx certbot python3-certbot-nginx

# CentOS / RHEL
sudo yum install nginx certbot python3-certbot-nginx
```

### 2. 申请证书（Let's Encrypt 免费）

```bash
sudo certbot --nginx -d your-domain.com -d api.your-domain.com
# 自动改 Nginx 配置 + 自动续期
```

### 3. Nginx 配置（`/etc/nginx/sites-available/jizhang`）

```nginx
# HTTP → HTTPS 强制跳转
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$host$request_uri;
}

# HTTPS 主配置
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # 证书（Certbot 自动生成）
    ssl_certificate     /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # SSL 强化（OWASP 推荐）
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1d;
    ssl_session_tickets off;

    # HSTS（强制浏览器用 HTTPS）
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header Referrer-Policy "no-referrer" always;

    # 上传大小限制（导入账单 CSV/XLSX 可能 5-10MB）
    client_max_body_size 10M;

    # 代理到 Flask
    location / {
        proxy_pass http://127.0.0.1:5002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;  # 关键！让 Flask 知道是 https
        proxy_http_version 1.1;
        proxy_redirect off;

        # 超时
        proxy_connect_timeout 30s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # 健康检查（不走日志）
    location /api/health {
        proxy_pass http://127.0.0.1:5002;
        access_log off;
    }

    # 上传文件缓存
    location /uploads/ {
        proxy_pass http://127.0.0.1:5002;
        proxy_cache_valid 200 7d;  # 头像缓存 7 天
        add_header X-Cache-Status $upstream_cache_status;
    }
}
```

启用：

```bash
sudo ln -s /etc/nginx/sites-available/jizhang /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 4. Flask 启动（systemd 服务）

**`/etc/systemd/system/jizhang.service`**：

```ini
[Unit]
Description=gerenjizhang Flask backend
After=network.target mysql.service

[Service]
Type=simple
User=jizhang
Group=jizhang
WorkingDirectory=/opt/jizhang
Environment="PATH=/opt/jizhang/.venv/bin"
EnvironmentFile=/opt/jizhang/.env
ExecStart=/opt/jizhang/.venv/bin/python gerenjizhang/app.py
Restart=always
RestartSec=5

# 安全加固
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/jizhang/uploads /opt/jizhang/logs

[Install]
WantedBy=multi-user.target
```

启用：

```bash
sudo systemctl daemon-reload
sudo systemctl enable jizhang
sudo systemctl start jizhang
sudo systemctl status jizhang
```

---

## ✅ 验证 HTTPS 工作正常

### 1. 基础检查

```bash
# 应该 301 → https
curl -I http://your-domain.com/api/health

# 应该 200
curl https://your-domain.com/api/health
```

### 2. SSL 评分（应 ≥ A）

https://www.ssllabs.com/ssltest/analyze.html?d=your-domain.com

### 3. HSTS 头检查

```bash
curl -I https://your-domain.com/api/health | grep -i strict-transport
# 应看到：Strict-Transport-Security: max-age=31536000; includeSubDomains
```

### 4. 证书自动续期

```bash
# 测试续期
sudo certbot renew --dry-run

# 添加 cron 续期（certbot 一般自动加）
0 3 * * * certbot renew --quiet
```

---

## 🔒 微信小程序域名白名单

去微信公众平台 → 开发管理 → 开发设置 → **服务器域名**：

| 类别 | 域名 |
|---|---|
| request 合法域名 | `https://your-domain.com` |
| uploadFile 合法域名 | `https://your-domain.com` |
| downloadFile 合法域名 | `https://your-domain.com` |

⚠️ **必须 HTTPS**，HTTP 域名在生产环境会被微信拒绝。

---

## 🛡️ 进阶安全（可选）

### 1. 限流存储升级到 Redis

单进程内存限流在多 worker 下会失效。改 Redis：

```python
# gerenjizhang/middleware/limiter.py
storage_uri="redis://localhost:6379/1"
```

```bash
pip install redis
sudo apt install redis-server
```

### 2. fail2ban 防 SSH 爆破

```bash
sudo apt install fail2ban
sudo systemctl enable fail2ban
```

### 3. 自动安全更新

```bash
sudo apt install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

### 4. 数据库只允许本地连接

`/etc/mysql/mysql.conf.d/mysqld.cnf`：

```ini
bind-address = 127.0.0.1
```

### 5. 防火墙

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

---

## 🆘 故障排查

| 现象 | 原因 | 解决 |
|---|---|---|
| 启动报 `RuntimeError: [SECURITY] SECRET_KEY 在生产环境下必须设置强随机值` | 用了 fallback 密钥 | 重新生成并填到 `.env` |
| 启动报 `缺少必需环境变量: WECHAT_APPID` | 没设 env | 填到 `.env` 或 systemd EnvironmentFile |
| 启动报 `unknown storage scheme: memory` | 旧版 limits 库 | 升级 `pip install -U limits` |
| 401 不断 | JWT_SECRET 改了，老 token 失效 | 用户重新登录即可 |
| 微信小程序请求失败 | 域名没加白名单 / 不是 HTTPS | 微信公众平台 + Nginx 都查 |
| 413 Request Entity Too Large | Nginx 限 1M | `client_max_body_size 10M;` |

---

## 📚 参考

- [Let's Encrypt 文档](https://letsencrypt.org/docs/)
- [Mozilla SSL Configuration Generator](https://ssl-config.mozilla.org/)
- [OWASP TLS Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Transport_Layer_Protection_Cheat_Sheet.html)
- [Flask 部署选项](https://flask.palletsprojects.com/en/stable/deploying/)
