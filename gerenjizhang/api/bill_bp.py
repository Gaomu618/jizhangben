"""
账单相关路由共用的 Blueprint 定义。

按职责拆分到子模块：
  bill_crud     - 增删改查 / 列表 / 智能分类
  bill_budget   - 预算管理
  bill_trash    - 回收站
  bill_import   - CSV / XLSX 导入
  bill_export   - CSV / XLSX / PDF 导出
"""
from flask import Blueprint

bill_bp = Blueprint('bill', __name__, url_prefix='/api/bill')
