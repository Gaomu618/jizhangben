"""
应用配置管理
支持多环境：development / testing / production
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent


class Config:
    """基础配置"""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-fallback-key-change-in-prod')
    # JWT 签名密钥 — 用于无状态 token 验证（生产环境必须用强随机密钥）
    JWT_SECRET = os.environ.get('JWT_SECRET', 'dev-jwt-fallback-key-change-in-prod-please')
    JWT_ALGORITHM = 'HS256'
    JWT_EXPIRES_SECONDS = 7 * 24 * 3600  # 默认 7 天
    # JWT 受众/签发者（P2 加固：避免 token 在跨服务时被滥用）
    JWT_AUDIENCE = os.environ.get('JWT_AUDIENCE', 'gerenjizhang-app')
    JWT_ISSUER = os.environ.get('JWT_ISSUER', 'gerenjizhang')
    DEBUG = False
    TESTING = False

    # 数据库
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_PORT = int(os.environ.get('DB_PORT', 3306))
    DB_USER = os.environ.get('DB_USER', 'root')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
    DB_NAME = os.environ.get('DB_NAME', 'jizhangapp')
    DB_CHARSET = 'utf8mb4'

    # CORS 白名单（生产前必须设！）
    # 逗号分隔多个 origin，支持通配符：*.weixin.qq.com 会匹配 mp/servicewx 等子域
    # 例：https://your-app.com,*.weixin.qq.com
    # dev 模式下空字符串 → 自动允许 localhost:*
    CORS_ALLOWED_ORIGINS = [
        o.strip() for o in os.environ.get('CORS_ALLOWED_ORIGINS', '').split(',') if o.strip()
    ]

    # 微信小程序 AppID/Secret — 必须从环境变量注入，无 fallback
    # 启动时校验；缺一个就 raise，避免静默用错的值
    WECHAT_APPID = os.environ.get('WECHAT_APPID')
    WECHAT_SECRET = os.environ.get('WECHAT_SECRET')

    # 已知的弱/默认 fallback 密钥（生产环境检测到用这些就 raise）
    _WEAK_SECRETS = frozenset({
        'dev-fallback-key-change-in-prod',
        'dev-jwt-fallback-key-change-in-prod-please',
        'change-me-in-production',
        'secret',
        'password',
    })

    REQUIRED_ENV_VARS = ('WECHAT_APPID', 'WECHAT_SECRET')

    @classmethod
    def validate(cls):
        """启动时校验：缺必需 env 立刻 raise。TESTING 模式下跳过。"""
        if cls.TESTING:
            return
        missing = [k for k in cls.REQUIRED_ENV_VARS if not getattr(cls, k)]
        if missing:
            raise RuntimeError(
                f"缺少必需环境变量: {', '.join(missing)}。"
                f"请在部署环境（生产/开发）注入。测试环境（FLASK_ENV=testing）可忽略。"
            )

        # 生产环境：JWT_SECRET / SECRET_KEY 不能是 fallback 或弱值，且长度 >= 32
        # dev / testing 模式放过（开发体验优先）
        is_production = (
            os.environ.get('FLASK_ENV', 'development') == 'production'
            and not cls.TESTING
        )
        if is_production:
            for key_name in ('SECRET_KEY', 'JWT_SECRET'):
                val = getattr(cls, key_name, None)
                if not val or val in cls._WEAK_SECRETS or len(val) < 32:
                    raise RuntimeError(
                        f"[SECURITY] {key_name} 在生产环境下必须设置强随机值（>=32 字符）"
                        f"，禁止使用 fallback。生成命令："
                        f"`python -c \"import secrets; print(secrets.token_hex(32))\"`"
                    )

    # JWT
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = 3600  # 1小时
    JWT_REFRESH_TOKEN_EXPIRES = 86400 * 7  # 7天

    # API限流
    RATELIMIT_ENABLED = True
    RATELIMIT_DEFAULT = "200 per minute"

       # 日志
    LOG_LEVEL = 'INFO'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_DIR = BASE_DIR / 'logs'
    LOG_FILE = LOG_DIR / 'app.log'
    LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5

    @property
    def DB_CONFIG(self):
        return {
            "host": self.DB_HOST,
            "user": self.DB_USER,
            "password": self.DB_PASSWORD,
            "database": self.DB_NAME,
            "charset": self.DB_CHARSET,
            "port": self.DB_PORT
        }


class DevelopmentConfig(Config):
    """开发环境"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'


class TestingConfig(Config):
    """测试环境"""
    TESTING = True
    DB_NAME = 'jizhangapp_test'
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    """生产环境"""
    DEBUG = False
    LOG_LEVEL = 'WARNING'

    @property
    def SQLALCHEMY_DATABASE_URI(self):
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}


def get_config():
    """获取当前环境配置"""
    env = os.environ.get('FLASK_ENV', 'development')
    cfg = config.get(env, config['default'])
    cfg.validate()
    return cfg