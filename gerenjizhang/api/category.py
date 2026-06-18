"""
分类管理 API
- GET    /api/category           列出当前用户所有分类
- POST   /api/category           新增自定义分类
- DELETE /api/category/<id>      删除自定义分类
- GET    /api/category/<id>/keywords    列出某分类的关键词
- POST   /api/category/<id>/keywords    给某分类加关键词
- DELETE /api/category/keywords/<id>   删一个关键词
"""
import logging
from flask import Blueprint, request, current_app
from gerenjizhang.utils.response import success_response, error_response
from gerenjizhang.utils.decorators import login_required
from gerenjizhang.db import (
    list_user_categories,
    get_user_category,
    get_user_category_by_id,
    create_user_category,
    delete_user_category,
    list_user_category_keywords,
    add_user_category_keyword,
    delete_user_category_keyword,
)

logger = logging.getLogger(__name__)
category_bp = Blueprint('category', __name__, url_prefix='/api/category')


# ================ 安全的上限常量 ================
MAX_CATEGORIES_PER_USER = 50
MAX_KEYWORDS_PER_CATEGORY = 200


@category_bp.route('', methods=['GET'])
@login_required
def list_categories(user_id):
    """列出当前用户所有分类（系统 + 自定义）"""
    cats = list_user_categories(user_id)
    return success_response({
        'categories': cats,
        'total': len(cats),
        'system_count': sum(1 for c in cats if c['is_system']),
        'custom_count': sum(1 for c in cats if not c['is_system']),
    })


@category_bp.route('', methods=['POST'])
@login_required
def create_category(user_id):
    """新增自定义分类

    Body: { "name": "宠物", "icon": "🐶", "type": "expense" }
    """
    data = request.get_json() or {}
    name = (data.get('name') or '').strip()
    icon = (data.get('icon') or '').strip() or None
    type_ = (data.get('type') or 'expense').strip()
    if type_ not in ('expense', 'income'):
        return error_response(5101, "type 必须是 expense 或 income")

    cat, err = create_user_category(user_id, name, icon=icon, type_=type_)
    if err:
        # 区分不同错误码
        if '上限' in err:
            return error_response(5102, err)
        if '同名' in err:
            return error_response(5103, err)
        return error_response(5104, err)
    return success_response(cat, message="分类已添加")


@category_bp.route('/<int:cat_id>', methods=['DELETE'])
@login_required
def remove_category(user_id, cat_id):
    """删除自定义分类（系统分类不可删）"""
    ok, err = delete_user_category(user_id, cat_id)
    if not ok:
        if '系统分类' in err:
            return error_response(5110, err)
        if '不存在' in err:
            return error_response(5111, err)
        return error_response(5112, err)
    return success_response(message="分类已删除")


@category_bp.route('/<int:cat_id>/keywords', methods=['GET'])
@login_required
def list_keywords(user_id, cat_id):
    """列出某分类的关键词"""
    cat = get_user_category_by_id(cat_id, user_id)
    if not cat:
        return error_response(5120, "分类不存在")
    kws = list_user_category_keywords(user_id, cat_id)
    return success_response({
        'category': cat,
        'keywords': kws,
        'total': len(kws),
    })


@category_bp.route('/<int:cat_id>/keywords', methods=['POST'])
@login_required
def add_keyword(user_id, cat_id):
    """给某分类加一个关键词

    Body: { "keyword": "猫粮" }
    """
    cat = get_user_category_by_id(cat_id, user_id)
    if not cat:
        return error_response(5120, "分类不存在")

    data = request.get_json() or {}
    keyword = (data.get('keyword') or '').strip()
    kw, err = add_user_category_keyword(user_id, cat_id, keyword)
    if err:
        if '上限' in err:
            return error_response(5130, err)
        if '相同' in err:
            return error_response(5131, err)
        return error_response(5132, err)
    return success_response(kw, message="关键词已添加")


@category_bp.route('/keywords/<int:kw_id>', methods=['DELETE'])
@login_required
def remove_keyword(user_id, kw_id):
    """删除一个关键词"""
    if delete_user_category_keyword(user_id, kw_id):
        return success_response(message="关键词已删除")
    return error_response(5140, "关键词不存在或已被删除")
