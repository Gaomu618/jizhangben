"""
输入校验工具
- validate_image_content: 校验上传文件确实是合法图片（防 .php.jpg 这种）
- validate_password: 密码强度策略
"""
import io
import logging

logger = logging.getLogger(__name__)


def validate_image_content(file_storage, max_size_mb=2):
    """
    用 Pillow 校验文件内容确实是合法图片
    @param file_storage: werkzeug FileStorage 对象（request.files['xxx']）
    @param max_size_mb: 最大尺寸（MB）
    @returns: (ok: bool, error: str|None, img_format: str|None, size: int)

    校验策略：
    - open() 解析文件头（魔数）+ 元数据
    - load() 强制解码至少一帧像素（捕获结构损坏的假图片）
    - 不使用 verify()（太严格：会拒绝非严格校验和的合法 PNG）
    """
    try:
        # 1. 读全部字节
        data = file_storage.read()
        size = len(data)
        if size == 0:
            return False, "空文件", None, 0
        if size > max_size_mb * 1024 * 1024:
            return False, f"文件过大（>{max_size_mb}MB）", None, size

        # 2. Pillow 打开 + load（解析头 + 真正解码像素）
        from PIL import Image, UnidentifiedImageError
        try:
            img = Image.open(io.BytesIO(data))
            img.load()  # 强制解码（捕获"魔数对但内容损坏"的攻击文件）
        except UnidentifiedImageError:
            return False, "不是有效的图片文件", None, size
        except Exception as e:
            # load() 失败 = 文件结构损坏 / 像素数据伪造
            logger.warning(f"[avatar] image load failed: {e}")
            return False, "图片文件已损坏或不是合法图片", None, size

        fmt = (img.format or '').lower()
        if fmt not in ('png', 'jpeg', 'jpg', 'gif', 'webp'):
            return False, f"不支持的图片格式: {fmt}", None, size

        # 3. 重置 file_storage 指针（让后续 save() 能正常写入）
        file_storage.seek(0)
        return True, None, fmt, size
    except Exception as e:
        logger.exception(f"[avatar] validate_image_content error: {e}")
        return False, "图片校验失败", None, 0


def validate_password(password):
    """
    密码强度校验
    策略：
    - 长度 >= 8
    - 至少包含 字母 + 数字
    宽松但够用（避免用户随便 12345678）
    @returns: (ok: bool, message: str|None)
    """
    if not password or not isinstance(password, str):
        return False, "密码不能为空"
    if len(password) < 8:
        return False, "密码至少 8 位"
    if len(password) > 128:
        return False, "密码过长（最多 128 位）"

    has_letter = any(c.isalpha() for c in password)
    has_digit = any(c.isdigit() for c in password)

    if not (has_letter and has_digit):
        return False, "密码必须同时包含字母和数字"

    return True, None


def validate_username(username):
    """
    用户名校验
    - 长度 3-20
    - 允许字母、数字、下划线、中文
    """
    if not username or not isinstance(username, str):
        return False, "用户名不能为空"
    username = username.strip()
    if len(username) < 3 or len(username) > 20:
        return False, "用户名长度需在 3-20 字符之间"
    # 字母/数字/下划线/中文
    import re
    if not re.match(r'^[A-Za-z0-9_一-龥]+$', username):
        return False, "用户名只能包含字母、数字、下划线、中文"
    return True, None
