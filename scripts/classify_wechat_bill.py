"""
classify_wechat_bill.py
读取微信支付账单 XLSX，按项目分类流程跑一遍，输出分类报告
"""
import sys
import os
from pathlib import Path
from collections import Counter, defaultdict
import openpyxl
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))
os.environ.setdefault('FLASK_ENV', 'development')

from gerenjizhang.utils.classifier import classify as smart_classify, classify_two_stage
from gerenjizhang.utils.profile import is_default_username

OUTPUT_DIR = Path("reports")
OUTPUT_DIR.mkdir(exist_ok=True)


def parse_amount(val):
    if val is None:
        return None
    s = str(val).replace('¥', '').replace(',', '').strip()
    try:
        return float(s)
    except:
        return None


def parse_date(date_str):
    date_str = str(date_str).strip()
    formats = ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%Y/%m/%d %H:%M:%S', '%Y/%m/%d', '%m/%d/%Y %H:%M:%S', '%m/%d/%Y']
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except (ValueError, TypeError):
            continue
    try:
        return datetime.strptime(date_str[:10], '%Y-%m-%d')
    except:
        return None


def load_wechat_xlsx(filepath):
    """加载微信 XLSX，解析为行列表（与 import_bill 一致的逻辑）"""
    wb = openpyxl.load_workbook(filepath, data_only=True)
    ws = wb.active
    all_rows = list(ws.values)

    # 找真实表头（含 '收/支' 和 '金额'）
    header_idx = 0
    for i, row in enumerate(all_rows):
        row_header = [str(c).strip() if c else '' for c in row]
        if '收/支' in row_header and any('金额' in h for h in row_header) and '交易时间' in row_header:
            header_idx = i
            break
    return all_rows[header_idx:], header_idx


def main():
    bill_path = sys.argv[1] if len(sys.argv) > 1 else "gerenjizhang/微信支付账单流水文件(20260531-20260607)_20260607005638.xlsx"
    print(f"📂 加载账单: {bill_path}")

    rows, header_skip = load_wechat_xlsx(bill_path)
    print(f"📋 表头位置: 第 {header_skip} 行")
    print(f"📊 数据行数: {len(rows) - 1}")

    header = [str(h).strip() if h else '' for h in rows[0]]
    print(f"📑 列名: {header}\n")

    is_wechat = '收/支' in header and any('金额' in h for h in header) and '交易时间' in header
    if not is_wechat:
        print("❌ 不是微信格式账单")
        return

    # 解析每行
    parsed = []
    skipped_refund = 0
    skipped_transfer = 0
    skipped_other = 0
    skipped_zero = 0

    for idx, row in enumerate(rows[1:], start=2):
        row_data = [str(cell).strip() if cell else '' for cell in row]
        if len(row_data) < 6:
            continue

        date_str = row_data[0]
        trans_type = row_data[1]
        counterparty = row_data[2]
        product = row_data[3]
        in_out = row_data[4]
        amount_str = row_data[5]
        status = row_data[7] if len(row_data) > 7 else ''

        # 跳过退款
        if '已退款' in status or '已撤销' in status:
            skipped_refund += 1
            continue

        amount = parse_amount(amount_str)
        if amount is None or amount == 0:
            skipped_zero += 1
            continue

        # 类型判断
        if in_out == '收入':
            type_ = 'income'
            amount = abs(amount)
        elif in_out == '支出':
            type_ = 'expense'
            amount = abs(amount)
        elif trans_type in ('零钱提现', '信用卡还款', '理财通', '转账'):
            skipped_transfer += 1
            continue
        elif trans_type == '退款':
            type_ = 'income'
            amount = abs(amount)
        else:
            skipped_other += 1
            continue

        # 跑项目里的分类器（user_id=None 跳过用户学习）
        focus_text = f"{counterparty} {product}".strip() or f"{trans_type} {counterparty}".strip()
        result = smart_classify(focus_text, user_id=None)

        # 也跑两级分类（商家 + 商品）拿子分类
        two_stage = classify_two_stage(focus_text, user_id=None)

        date_parsed = parse_date(date_str)

        parsed.append({
            'idx': idx,
            'date': date_parsed.strftime('%Y-%m-%d') if date_parsed else date_str,
            'trans_type': trans_type,
            'counterparty': counterparty,
            'product': product,
            'in_out': in_out,
            'amount': amount,
            'type': type_,
            'focus_text': focus_text,
            'category': result['category'] if result else '其他',
            'confidence': round(result.get('confidence', 0), 2) if result else 0,
            'matched': result.get('matched', '') if result else '',
            'sub_category': two_stage.get('sub_category') if two_stage else None,
        })

    # ===== 汇总 =====
    print("=" * 60)
    print("📊 分类结果汇总")
    print("=" * 60)
    print(f"原始数据行: {len(rows) - 1}")
    print(f"  ↳ 跳过（退款/撤销）: {skipped_refund}")
    print(f"  ↳ 跳过（过路钱）: {skipped_transfer}")
    print(f"  ↳ 跳过（金额 0 / 无法解析）: {skipped_zero}")
    print(f"  ↳ 跳过（其他原因）: {skipped_other}")
    print(f"实际分类: {len(parsed)}")
    print()

    # 按分类聚合
    cat_summary = defaultdict(lambda: {'count': 0, 'amount': 0.0, 'items': []})
    for p in parsed:
        c = p['category']
        cat_summary[c]['count'] += 1
        cat_summary[c]['amount'] += p['amount']
        cat_summary[c]['items'].append(p)

    total = sum(p['amount'] for p in parsed)
    print(f"💰 总金额: ¥{total:,.2f}")
    print()
    print(f"{'分类':<8} {'笔数':<6} {'总额':<12} {'占比':<8} {'笔均'}")
    print("-" * 60)
    for cat in sorted(cat_summary.keys(), key=lambda k: -cat_summary[k]['amount']):
        info = cat_summary[cat]
        pct = info['amount'] / total * 100 if total > 0 else 0
        avg = info['amount'] / info['count']
        flag = ' ⚠️低置信度' if any(i['confidence'] < 0.5 for i in info['items']) else ''
        print(f"{cat:<8} {info['count']:<6} ¥{info['amount']:>9,.2f}  {pct:>5.1f}%   ¥{avg:,.2f}{flag}")

    # ===== 子分类汇总 =====
    sub_summary = defaultdict(lambda: {'count': 0, 'amount': 0.0})
    for p in parsed:
        if p['sub_category']:
            key = f"{p['category']} / {p['sub_category']}"
            sub_summary[key]['count'] += 1
            sub_summary[key]['amount'] += p['amount']

    if sub_summary:
        print()
        print(f"{'二级分类':<20} {'笔数':<6} {'总额':<12}")
        print("-" * 45)
        for k in sorted(sub_summary.keys(), key=lambda x: -sub_summary[x]['amount']):
            info = sub_summary[k]
            print(f"{k:<20} {info['count']:<6} ¥{info['amount']:>9,.2f}")

    # ===== 写报告 =====
    md = []
    md.append("# 微信账单智能分类报告")
    md.append("")
    md.append(f"> 📂 账单文件：`{Path(bill_path).name}`")
    md.append(f"> 📅 时间范围：{min((p['date'] for p in parsed), default='?')} ~ {max((p['date'] for p in parsed), default='?')}")
    md.append(f"> 🕐 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
    md.append(f"> 📊 总记录：{len(parsed)} 条")
    md.append("")

    md.append("## 📋 跳过统计")
    md.append("")
    md.append(f"| 类型 | 数量 | 原因 |")
    md.append(f"|---|---|---|")
    md.append(f"| 退款/撤销 | {skipped_refund} | 重复入账 |")
    md.append(f"| 过路钱 | {skipped_transfer} | 提现/信用卡还款/转账 |")
    md.append(f"| 金额 0 / 无法解析 | {skipped_zero} | 异常数据 |")
    md.append(f"| 其他 | {skipped_other} | 类型无法识别 |")
    md.append("")

    md.append("## 💰 分类总览")
    md.append("")
    md.append("| 分类 | 笔数 | 总额 | 笔均 | 占比 |")
    md.append("|---|---|---|---|---|")
    for cat in sorted(cat_summary.keys(), key=lambda k: -cat_summary[k]['amount']):
        info = cat_summary[cat]
        pct = info['amount'] / total * 100 if total > 0 else 0
        avg = info['amount'] / info['count']
        md.append(f"| {cat} | {info['count']} | ¥{info['amount']:,.2f} | ¥{avg:,.2f} | {pct:.1f}% |")
    md.append(f"| **合计** | **{len(parsed)}** | **¥{total:,.2f}** | — | 100% |")
    md.append("")

    if sub_summary:
        md.append("## 🌳 二级分类细分")
        md.append("")
        md.append("> 项目里实现了 `classify_two_stage`（商家 → 子类），下面是识别到子类的记录")
        md.append("")
        md.append("| 二级分类 | 笔数 | 总额 |")
        md.append("|---|---|---|")
        for k in sorted(sub_summary.keys(), key=lambda x: -sub_summary[x]['amount']):
            info = sub_summary[k]
            md.append(f"| {k} | {info['count']} | ¥{info['amount']:,.2f} |")
        md.append("")

    md.append("## 📜 逐条明细")
    md.append("")
    md.append("| 日期 | 商家 | 商品 | 类型 | 分类 | 置信度 | 金额 |")
    md.append("|---|---|---|---|---|---|---|")
    # 按日期降序排
    parsed_sorted = sorted(parsed, key=lambda x: x['date'], reverse=True)
    for p in parsed_sorted:
        conf_icon = '🟢' if p['confidence'] >= 0.7 else '🟡' if p['confidence'] >= 0.4 else '🔴'
        md.append(f"| {p['date']} | {p['counterparty']} | {p['product']} | {p['in_out']} | {p['category']} | {conf_icon} {p['confidence']:.2f} | ¥{p['amount']:.2f} |")
    md.append("")

    md.append("## 💡 关键洞察")
    md.append("")
    top_cat = max(cat_summary.keys(), key=lambda k: cat_summary[k]['amount'])
    top_amt = cat_summary[top_cat]['amount']
    top_pct = top_amt / total * 100
    other_count = cat_summary.get('其他', {}).get('count', 0)
    other_pct = other_count / len(parsed) * 100 if parsed else 0

    md.append(f"1. **最大开销分类是「{top_cat}」**，¥{top_amt:,.2f}（{top_pct:.1f}%）")
    if other_count > 0:
        md.append(f"2. **「其他」类共 {other_count} 笔（{other_pct:.0f}%）** — 智能分类没识别出来")
    # 找出低置信度记录
    low_conf = [p for p in parsed if p['confidence'] < 0.5]
    if low_conf:
        md.append(f"3. **低置信度（< 0.5）共 {len(low_conf)} 条**，建议核对：")
        for p in low_conf[:5]:
            md.append(f"   - `{p['counterparty']} {p['product']}` → {p['category']}（{p['confidence']:.2f}）")
    md.append("")

    report_path = OUTPUT_DIR / "wechat-bill-classification.md"
    report_path.write_text("\n".join(md), encoding="utf-8")
    print()
    print("=" * 60)
    print(f"✅ 报告已生成：{report_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
