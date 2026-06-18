# scripts/

一次性脚本集合。这些脚本不在主 Flask 应用启动路径上,通常用于离线分析、批处理、迁移等场景。

> **运行方式**:从项目根目录运行 — `python scripts/<name>.py`(脚本内部通过 `Path(__file__).parent.parent` 找到 `gerenjizhang/`)。

## 脚本清单

| 脚本 | 用途 | 输出 |
|---|---|---|
| [`analyze_spending.py`](./analyze_spending.py) | 直接读 MySQL,跑月度/季度/用户三维度消费分析 | `reports/spending-analysis.md` + `reports/charts/*.png` |
| [`classify_wechat_bill.py`](./classify_wechat_bill.py) | 读微信 XLSX,跑一遍智能分类流程 | `reports/wechat-bill-classification.md` |

## 与主应用的关系

这两个脚本的逻辑**已被 `/api/bill/import` 接口取代**:
- `analyze_spending.py` → 后台统计分析(可后续做成 `GET /api/stats/...`)
- `classify_wechat_bill.py` → 微信 XLSX 导入(`POST /api/bill/import` 已支持)

**当前保留价值**:
- 离线 / 一次性数据处理
- 历史回溯分析(主应用已转向前后端架构)
- 数据迁移 / 修复工具

如果你用不到,可以删除整个 `scripts/` 目录。
