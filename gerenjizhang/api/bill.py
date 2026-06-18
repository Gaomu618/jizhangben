"""
账单相关路由 — 兼容 facade。

路由实际定义已拆分到：
  - bill_crud    : list / detail / add / edit / delete / batch-delete / classify
  - bill_budget  : budget CRUD
  - bill_trash   : 回收站 list / restore / purge / empty / batch-restore
  - bill_import  : CSV / XLSX 导入
  - bill_export  : CSV / XLSX / PDF 导出

app.py 仍按 `from gerenjizhang.api.bill import bill_bp` 注册，保持兼容。
本文件只做两件事：
  1. 显式 import 5 个子模块（副作用：触发它们的 @bill_bp.route 注册）
  2. re-export bill_bp
"""
from gerenjizhang.api.bill_bp import bill_bp

# 触发各子模块的 @bill_bp.route(...) 装饰器执行，把路由挂到 bill_bp 上
from gerenjizhang.api import (  # noqa: F401  副作用 import
    bill_crud,
    bill_budget,
    bill_trash,
    bill_import,
    bill_export,
)

__all__ = ['bill_bp']
