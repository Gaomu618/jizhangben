"""
统一错误码 — 按业务域分段，4 位数字。

分段约定（保留兼容,渐进迁移 — 旧代码仍可用裸数字）：
  0xxx  成功 (success_response 默认 0)
  1xxx  认证 / 用户 (auth)
  2xxx  账单 CRUD (bill_crud)
  3xxx  预算 (budget)
  4xxx  导入 / 导出 / 回收站 (import_export / trash)
  5xxx  分类 (category)   — 旧代码已用 5101-5140
  6xxx  智能分类 / 记忆 (classify)
  7xxx  通知 (notification)
  8xxx  系统 / 配置 (system)
  9xxx  HTTP 对齐 (401/403/429/500) — 顶层 / 装饰器使用

旧错误码映射说明（保留兼容用,后续可渐进替换为语义常量）：
  2005  旧用法歧义：「金额必须大于 0」(add) vs 「参数不完整」(edit)
       新版已拆分为 Bill.AMOUNT_MUST_POSITIVE / Bill.PARAMS_MISSING
  4001  旧用法歧义：「请选择文件」(import) vs 「还原失败」(restore)
       新版已拆分为 ImportExport.FILE_REQUIRED / ImportExport.RESTORE_FAIL
  5001  旧用法仅 export；新版归到 ImportExport.FORMAT_UNSUPPORTED = 4003
  5002  旧用法仅 export；新版归到 ImportExport.NO_RECORDS = 4010
"""
from .response import error_response


class Auth:
    """1xxx — 认证 / 用户"""
    WECHAT_API_FAIL        = 1001   # 微信服务调用失败
    CODE_REQUIRED          = 1003   # code 不能为空
    WECHAT_LOGIN_FAIL      = 1004   # 微信登录失败
    USER_CREATE_FAIL       = 1005   # 创建用户失败
    USERNAME_PWD_REQUIRED  = 1006   # 用户名密码不能为空
    INVALID_CRED           = 1007   # 账号或密码错误
    REGISTER_BAD_INPUT     = 1008   # 注册输入有误
    REGISTER_FAIL          = 1009   # 注册失败
    USER_EXISTS            = 1010   # 用户名已存在
    USER_NOT_FOUND         = 1011   # 用户不存在
    CODE_INVALID           = 1012   # code 无效
    WECHAT_CALL_FAIL       = 1013   # 微信服务调用失败 (binding)
    WECHAT_BIND_FAIL       = 1014   # 微信绑定失败
    BIND_FAIL              = 1015   # 绑定失败
    INVALID_EMAIL          = 1016   # 邮箱格式不正确
    EMAIL_EXISTS           = 1017   # 邮箱已被注册
    RESET_PWD_FAIL         = 1019   # 重置密码失败
    UPDATE_FAIL            = 1021   # 更新失败
    AVATAR_FILE_MISSING    = 1030   # 请选择文件
    AVATAR_INVALID         = 1031   # 文件无效
    AVATAR_FORMAT_INVALID  = 1032   # 仅支持 ... 格式
    AVATAR_VERIFY_FAIL     = 1035   # 图片校验失败


class Bill:
    """2xxx — 账单 CRUD"""
    NOT_FOUND              = 2001   # 记录不存在 / 已被删除
    PARAMS_MISSING         = 2002   # 参数不完整
    AMOUNT_FORMAT          = 2003   # 金额格式错误
    TYPE_INVALID           = 2004   # 类型错误 (非 income/expense)
    AMOUNT_MUST_POSITIVE   = 2005   # 金额必须大于 0
    ADD_VALIDATION_FAIL    = 2006   # 数据库校验失败 (ValueError)
    ADD_SERVER_ERROR       = 2007   # 服务器错误
    EDIT_DB_ERROR          = 2008   # 修改失败，数据库错误
    DELETE_DB_ERROR        = 2009   # 删除失败，数据库错误
    BATCH_IDS_REQUIRED     = 2010   # 请选择要删除的记录
    BATCH_ID_FORMAT        = 2011   # ID 格式错误
    BATCH_TOO_MANY         = 2012   # 一次最多删除 200 条


class Budget:
    """3xxx — 预算"""
    CATEGORY_REQUIRED      = 3001   # 请选择分类
    AMOUNT_FORMAT          = 3002   # 金额格式错误
    AMOUNT_NEGATIVE        = 3003   # 金额不能为负数
    SAVE_FAIL              = 3004   # 保存失败
    DELETE_NOT_FOUND       = 3005   # 请指定分类
    DELETE_FAIL            = 3006   # 删除失败，数据库错误
    NOT_SET                = 3007   # 该分类当月未设置预算


class ImportExport:
    """4xxx — 导入 / 导出 / 回收站"""
    FILE_REQUIRED          = 4001   # 请选择文件
    FILENAME_EMPTY         = 4002   # 文件名为空
    FORMAT_UNSUPPORTED     = 4003   # 不支持的格式 (导入/导出)
    READ_FAIL              = 4004   # 文件读取失败
    DATA_EMPTY             = 4005   # 文件数据为空
    PARSE_NO_VALID         = 4006   # 未能解析出有效记录
    RESTORE_FAIL           = 4007   # 还原失败，记录可能不在回收站
    PURGE_FAIL             = 4008   # 删除失败，记录可能不在回收站
    BATCH_RESTORE_EMPTY    = 4009   # 请选择要还原的记录
    NO_RECORDS             = 4010   # 当月没有账单可导出


class Category:
    """5xxx — 分类（保持旧码位 5101-5140 兼容）"""
    INVALID_TYPE           = 5101   # type 必须是 expense 或 income
    CREATE_FAIL            = 5102
    UPDATE_FAIL            = 5103
    DELETE_FAIL            = 5104
    KEYWORD_ADD_FAIL       = 5110
    KEYWORD_DELETE_FAIL    = 5111
    KEYWORD_UPDATE_FAIL    = 5112
    NOT_FOUND              = 5120   # 分类不存在
    KEYWORD_BATCH_FAIL     = 5130
    KEYWORD_BATCH_OP_FAIL  = 5131
    KEYWORD_NOT_FOUND      = 5132
    KEYWORD_NOT_EXIST      = 5140   # 关键词不存在或已被删除


class Classify:
    """6xxx — 智能分类 / 记忆"""
    TEXT_REQUIRED          = 6001   # 请输入备注文字
    MEMORY_NOT_FOUND       = 6002   # 记忆不存在或已删除


class Notify:
    """7xxx — 通知"""
    CHECK_FAIL             = 7001   # 检查失败


class System:
    """8xxx — 系统 / 配置"""
    INTERNAL               = 8000
    DB_ERROR               = 8001


class Http:
    """9xxx — HTTP 状态对齐（装饰器 / 顶层路由使用）"""
    BAD_REQUEST            = 9400
    UNAUTHORIZED           = 9401   # 请先登录
    FORBIDDEN              = 9403   # 需要管理员权限
    NOT_FOUND              = 9404
    CONFLICT               = 9409
    RATE_LIMITED           = 9429   # 登录失败次数过多
    SERVER_ERROR           = 9500


class ErrCode:
    """统一入口 — 用法：ErrCode.Bill.NOT_FOUND / ErrCode.Auth.INVALID_CRED"""
    Auth          = Auth
    Bill          = Bill
    Budget        = Budget
    ImportExport  = ImportExport
    Category      = Category
    Classify      = Classify
    Notify        = Notify
    System        = System
    Http          = Http


# ===== 默认消息（用户不传 message 时回退到这些）=====
_DEFAULT_MESSAGES = {
    # Auth
    Auth.WECHAT_API_FAIL:       "微信服务调用失败",
    Auth.CODE_REQUIRED:         "code不能为空",
    Auth.WECHAT_LOGIN_FAIL:     "微信登录失败",
    Auth.USER_CREATE_FAIL:      "创建用户失败",
    Auth.USERNAME_PWD_REQUIRED: "用户名和密码不能为空",
    Auth.INVALID_CRED:          "账号或密码错误",
    Auth.USER_EXISTS:           "用户名已存在",
    Auth.USER_NOT_FOUND:        "用户不存在",
    Auth.INVALID_EMAIL:         "邮箱格式不正确",
    Auth.EMAIL_EXISTS:          "该邮箱已被注册",
    Auth.AVATAR_FILE_MISSING:   "请选择文件",
    Auth.AVATAR_INVALID:        "文件无效",
    Auth.AVATAR_VERIFY_FAIL:    "图片校验失败",

    # Bill
    Bill.NOT_FOUND:             "记录不存在或已被删除",
    Bill.PARAMS_MISSING:        "参数不完整",
    Bill.AMOUNT_FORMAT:         "金额格式错误",
    Bill.TYPE_INVALID:          "类型错误",
    Bill.AMOUNT_MUST_POSITIVE:  "金额必须大于 0",
    Bill.BATCH_IDS_REQUIRED:    "请选择要删除的记录",
    Bill.BATCH_ID_FORMAT:       "ID 格式错误",
    Bill.BATCH_TOO_MANY:        "一次最多删除 200 条",
    Bill.EDIT_DB_ERROR:         "修改失败，数据库错误",
    Bill.DELETE_DB_ERROR:       "删除失败，数据库错误",

    # Budget
    Budget.CATEGORY_REQUIRED:   "请选择分类",
    Budget.AMOUNT_FORMAT:       "金额格式错误",
    Budget.AMOUNT_NEGATIVE:     "金额不能为负数",
    Budget.SAVE_FAIL:           "保存失败",
    Budget.DELETE_NOT_FOUND:    "请指定分类",
    Budget.DELETE_FAIL:         "删除失败，数据库错误",
    Budget.NOT_SET:             "该分类当月未设置预算",

    # ImportExport
    ImportExport.FILE_REQUIRED:      "请选择文件",
    ImportExport.FILENAME_EMPTY:     "文件名为空",
    ImportExport.FORMAT_UNSUPPORTED: "不支持的格式",
    ImportExport.READ_FAIL:          "文件读取失败",
    ImportExport.DATA_EMPTY:         "文件数据为空",
    ImportExport.PARSE_NO_VALID:     "未能解析出有效记录",
    ImportExport.RESTORE_FAIL:       "还原失败，记录可能不在回收站",
    ImportExport.PURGE_FAIL:         "删除失败，记录可能不在回收站",
    ImportExport.BATCH_RESTORE_EMPTY:"请选择要还原的记录",
    ImportExport.NO_RECORDS:         "当月没有账单可导出",

    # Category
    Category.INVALID_TYPE:      "type 必须是 expense 或 income",
    Category.NOT_FOUND:         "分类不存在",
    Category.KEYWORD_NOT_EXIST: "关键词不存在或已被删除",

    # Classify
    Classify.TEXT_REQUIRED:     "请输入备注文字",
    Classify.MEMORY_NOT_FOUND:  "记忆不存在或已删除",

    # Notify
    Notify.CHECK_FAIL:          "检查失败",

    # System
    System.INTERNAL:            "服务器内部错误",
    System.DB_ERROR:            "数据库错误",

    # Http
    Http.BAD_REQUEST:           "请求参数错误",
    Http.UNAUTHORIZED:          "请先登录",
    Http.FORBIDDEN:             "权限不足",
    Http.NOT_FOUND:             "资源不存在",
    Http.CONFLICT:              "资源冲突",
    Http.RATE_LIMITED:          "操作过于频繁，请稍后再试",
    Http.SERVER_ERROR:          "服务器错误",
}


# ===== 默认 HTTP 状态码（用于 error_response 的 status_code 参数）=====
_DEFAULT_HTTP_STATUS = {
    # 4xx
    Auth.INVALID_CRED:        401,
    Auth.WECHAT_LOGIN_FAIL:   401,
    Auth.USER_NOT_FOUND:      404,
    Auth.USER_EXISTS:         409,
    Auth.EMAIL_EXISTS:        409,
    Bill.NOT_FOUND:           404,
    Category.NOT_FOUND:       404,
    Category.KEYWORD_NOT_EXIST:404,
    Http.BAD_REQUEST:         400,
    Http.UNAUTHORIZED:        401,
    Http.FORBIDDEN:           403,
    Http.NOT_FOUND:           404,
    Http.CONFLICT:            409,
    Http.RATE_LIMITED:        429,
    # 5xx
    System.INTERNAL:          500,
    System.DB_ERROR:          500,
    Http.SERVER_ERROR:        500,
}


def err(code, message=None, data=None, status_code=None, http_status=None):
    """统一错误响应快捷方式。

    用法:
        from gerenjizhang.utils.error_codes import err, ErrCode

        # 自动用默认消息 + 默认 HTTP 状态
        return err(ErrCode.Bill.NOT_FOUND)

        # 自定义消息
        return err(ErrCode.Bill.NOT_FOUND, "记录已被删除")

        # 自定义 HTTP 状态码（如前端按 HTTP 状态路由）
        return err(ErrCode.Bill.NOT_FOUND, http_status=404)
    """
    if message is None:
        message = _DEFAULT_MESSAGES.get(code, f"错误 {code}")
    if status_code is None:
        status_code = _DEFAULT_HTTP_STATUS.get(code, 400)
    return error_response(code, message, data=data, status_code=status_code)
