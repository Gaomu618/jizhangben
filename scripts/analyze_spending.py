"""
analyze_spending.py
直接读 DB，跑月度/季度/用户三个维度的消费分析
输出：
- reports/spending-analysis.md（文字报告）
- reports/charts/*.png（6 张可视化图）
"""
import sys
import os
import mysql.connector
import pandas as pd
import re
import warnings
warnings.filterwarnings('ignore')
import matplotlib
matplotlib.use('Agg')  # 无 GUI 后端（必须）
import matplotlib.pyplot as plt
from matplotlib import font_manager
from collections import Counter
from pathlib import Path
from datetime import datetime

# 中文字体配置（Windows 默认有 msyh / SimHei；跨平台兜底）
def setup_chinese_font():
    candidates = [
        ('Microsoft YaHei', ['msyh', 'msyh.ttc', 'Microsoft YaHei']),
        ('SimHei', ['simhei', 'simhei.ttf', 'SimHei']),
        ('PingFang SC', ['PingFang', 'PingFang SC']),
        ('Noto Sans CJK SC', ['Noto Sans CJK SC', 'NotoSansCJK']),
        ('Source Han Sans CN', ['Source Han Sans']),
        ('WenQuanYi Zen Hei', ['wqy', 'WenQuanYi']),
        ('Arial Unicode MS', ['Arial Unicode']),
    ]
    installed = {f.name.lower(): f.fname for f in font_manager.fontManager.ttflist}
    for preferred, names in candidates:
        for n in names:
            if n.lower() in installed:
                plt.rcParams['font.sans-serif'] = [preferred, 'DejaVu Sans']
                plt.rcParams['axes.unicode_minus'] = False
                return preferred
    plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False
    return 'DejaVu Sans'

FONT_NAME = setup_chinese_font()
print(f'[chart] 使用中文字体: {FONT_NAME}')

# 配色（柔和不刺眼）
PALETTE = ['#5B8FF9', '#5AD8A6', '#5D7092', '#F6BD16', '#E86452',
           '#6DC8EC', '#945FB9', '#FF9D4D', '#269A99', '#FF99C3']

DB_CONFIG = {
    "host": "localhost", "user": "root", "password": "",
    "database": "jizhangapp", "charset": "utf8mb4"
}

OUTPUT_DIR = Path("reports")
OUTPUT_DIR.mkdir(exist_ok=True)
CHARTS_DIR = OUTPUT_DIR / "charts"
CHARTS_DIR.mkdir(exist_ok=True)

# 已知商家识别（轻量级关键词 → 商家映射）
MERCHANT_KEYWORDS = {
    '美团': ['美团', '外卖', '美团外卖'],
    '饿了么': ['饿了么'],
    '麦当劳': ['麦当劳', 'McDonald', '金拱门'],
    '肯德基': ['肯德基', 'KFC'],
    '瑞幸': ['瑞幸', 'luckin'],
    '星巴克': ['星巴克', 'Starbucks'],
    '淘宝': ['淘宝', '天猫'],
    '京东': ['京东'],
    '拼多多': ['拼多多', 'pdd'],
    '滴滴': ['滴滴', '打车', '高德打车'],
    '地铁': ['地铁', '公交', '一卡通'],
    '中石化': ['中石化', '加油站', '中石油'],
    '话费': ['话费', '充值', '流量'],
    'Netflix': ['Netflix', '网飞'],
    '腾讯': ['腾讯', 'QQ', '微信支付'],
    '支付宝': ['支付宝'],
    '医院': ['医院', '药房', '药店', '门诊'],
    '超市': ['超市', '便利店', '全家', '7-11', '罗森', '盒马'],
}


def detect_merchant(text):
    """从 note 文本里识别商家"""
    if not text:
        return '未识别'
    for merchant, keywords in MERCHANT_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                return merchant
    return '其他'


# ============== 6 张图表生成 ==============

def style_axes(ax):
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#999')
    ax.spines['bottom'].set_color('#999')
    ax.grid(axis='y', linestyle='--', alpha=0.3)
    ax.tick_params(colors='#666', labelsize=10)


def chart_category_pie(cat_summary, total_expense):
    fig, ax = plt.subplots(figsize=(8, 5.5), dpi=120)
    labels = cat_summary.index.tolist()
    sizes = cat_summary['总额'].tolist()
    colors = PALETTE[:len(labels)]
    explode = [0.05 if i == 0 else 0 for i in range(len(labels))]

    wedges, texts, autotexts = ax.pie(
        sizes, labels=labels, autopct='%1.1f%%',
        startangle=90, colors=colors, explode=explode,
        pctdistance=0.8, textprops={'fontsize': 10}
    )
    for t in autotexts:
        t.set_color('white')
        t.set_fontweight('bold')

    ax.set_title(f'钱花在哪 · 按分类占比（总 ¥{total_expense:,.0f}）',
                 fontsize=14, fontweight='bold', pad=20)
    fig.tight_layout()
    path = CHARTS_DIR / "01_category_pie.png"
    fig.savefig(path, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    return path


def chart_monthly_trend(monthly):
    fig, ax = plt.subplots(figsize=(9, 5), dpi=120)
    x = list(range(len(monthly)))
    labels = monthly.index.tolist()

    ax.bar(x, monthly['总额'], color='#5B8FF9', alpha=0.35, width=0.6, label='月度支出')
    ax.plot(x, monthly['总额'], color='#E86452', marker='o', linewidth=2, label='趋势')

    for i, v in enumerate(monthly['总额']):
        ax.text(i, v + max(monthly['总额']) * 0.02, f'¥{v:,.0f}',
                ha='center', fontsize=9, color='#333')

    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=0)
    ax.set_ylabel('支出金额 (¥)', fontsize=11)
    ax.set_title('月度支出趋势', fontsize=14, fontweight='bold', pad=15)
    ax.legend(loc='upper left', frameon=False, fontsize=11)
    style_axes(ax)
    fig.tight_layout()
    path = CHARTS_DIR / "02_monthly_trend.png"
    fig.savefig(path, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    return path


def chart_monthly_category_stack(pivot):
    fig, ax = plt.subplots(figsize=(10, 5.5), dpi=120)
    x = list(range(len(pivot.columns)))
    bottom = [0] * len(pivot.columns)

    for i, cat in enumerate(pivot.index):
        vals = pivot.loc[cat].tolist()
        ax.bar(x, vals, bottom=bottom, label=cat,
               color=PALETTE[i % len(PALETTE)], width=0.65)
        bottom = [b + v for b, v in zip(bottom, vals)]

    for i, total in enumerate(bottom):
        ax.text(i, total + max(bottom) * 0.02, f'¥{total:,.0f}',
                ha='center', fontsize=10, fontweight='bold', color='#333')

    ax.set_xticks(x)
    ax.set_xticklabels(pivot.columns.tolist())
    ax.set_ylabel('支出金额 (¥)', fontsize=11)
    ax.set_title('月度 × 分类堆叠（看钱流向）',
                 fontsize=14, fontweight='bold', pad=15)
    ax.legend(loc='upper left', bbox_to_anchor=(1.0, 1.0),
              frameon=False, fontsize=9)
    style_axes(ax)
    fig.tight_layout()
    path = CHARTS_DIR / "03_monthly_category_stack.png"
    fig.savefig(path, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    return path


def chart_user_top(user_summary, top_n=10):
    top = user_summary.head(top_n).sort_values('总额')
    fig, ax = plt.subplots(figsize=(8, max(4, top_n * 0.45)), dpi=120)

    bars = ax.barh(top.index, top['总额'],
                   color=[PALETTE[i % len(PALETTE)] for i in range(len(top))])

    for bar, v in zip(bars, top['总额']):
        ax.text(v + max(top['总额']) * 0.01, bar.get_y() + bar.get_height() / 2,
                f'¥{v:,.0f}', va='center', fontsize=9, color='#333')

    ax.set_xlabel('累计支出 (¥)', fontsize=11)
    ax.set_title(f'用户支出 TOP {top_n}', fontsize=14, fontweight='bold', pad=15)
    style_axes(ax)
    fig.tight_layout()
    path = CHARTS_DIR / "04_user_top.png"
    fig.savefig(path, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    return path


def chart_quarterly_compare(quarterly):
    fig, ax = plt.subplots(figsize=(8, 5), dpi=120)
    x = list(range(len(quarterly)))
    labels = quarterly.index.tolist()

    bars = ax.bar(x, quarterly['总额'], color=['#5AD8A6', '#5B8FF9'],
                  width=0.5, alpha=0.85)

    for bar, v in zip(bars, quarterly['总额']):
        ax.text(bar.get_x() + bar.get_width() / 2, v + max(quarterly['总额']) * 0.02,
                f'¥{v:,.0f}', ha='center', fontsize=12, fontweight='bold', color='#333')

    if len(quarterly) >= 2:
        delta = (quarterly['总额'].iloc[-1] - quarterly['总额'].iloc[-2]) / quarterly['总额'].iloc[-2] * 100
        sign = '+' if delta > 0 else ''
        ax.text(0.98, 0.95, f'环比 {sign}{delta:.1f}%', transform=ax.transAxes,
                ha='right', va='top', fontsize=12, color='#E86452', fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.4', facecolor='#FFF5F0', edgecolor='#E86452', alpha=0.8))

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=12)
    ax.set_ylabel('支出总额 (¥)', fontsize=11)
    ax.set_title('季度支出对比', fontsize=14, fontweight='bold', pad=15)
    style_axes(ax)
    fig.tight_layout()
    path = CHARTS_DIR / "05_quarterly_compare.png"
    fig.savefig(path, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    return path


def chart_merchant(merchant_summary):
    if len(merchant_summary) == 0:
        return None
    top = merchant_summary.sort_values('总额').tail(8)
    fig, ax = plt.subplots(figsize=(9, max(3, len(top) * 0.5)), dpi=120)

    bars = ax.barh(top.index, top['总额'],
                   color=[PALETTE[i % len(PALETTE)] for i in range(len(top))])
    for bar, v in zip(bars, top['总额']):
        ax.text(v + max(top['总额']) * 0.01, bar.get_y() + bar.get_height() / 2,
                f'¥{v:,.0f}', va='center', fontsize=9, color='#333')

    ax.set_xlabel('累计金额 (¥)', fontsize=11)
    ax.set_title('商家分布（从 note 识别）', fontsize=14, fontweight='bold', pad=15)
    style_axes(ax)
    fig.tight_layout()
    path = CHARTS_DIR / "06_merchant.png"
    fig.savefig(path, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    return path


def main():
    # 1. 读 DB
    print("=" * 60)
    print("📊 记账本财报分析系统 — 消费分析报告")
    print("=" * 60)
    print()

    conn = mysql.connector.connect(**DB_CONFIG)
    df = pd.read_sql("""
        SELECT
            b.id, b.user_id, u.username, b.date, b.amount, b.type, b.category, b.note
        FROM bill b
        LEFT JOIN users u ON b.user_id = u.id
        ORDER BY b.date
    """, conn)
    conn.close()

    print(f"📦 数据规模")
    print(f"  - 总记录数: {len(df)}")
    print(f"  - 用户数: {df['user_id'].nunique()}")
    print(f"  - 时间范围: {df['date'].min()} ~ {df['date'].max()}")
    print(f"  - 支出笔数: {(df['type'] == 'expense').sum()}")
    print(f"  - 收入笔数: {(df['type'] == 'income').sum()}")
    print()

    # 2. 基础数据清洗
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df = df.dropna(subset=['date'])
    df['year_month'] = df['date'].dt.to_period('M').astype(str)
    df['year_quarter'] = df['date'].dt.to_period('Q').astype(str)

    expense = df[df['type'] == 'expense'].copy()
    income = df[df['type'] == 'income'].copy()
    expense['merchant'] = expense['note'].apply(detect_merchant)

    # 3. 总览
    print("=" * 60)
    print("💰 总览")
    print("=" * 60)
    total_expense = expense['amount'].sum()
    total_income = income['amount'].sum()
    print(f"  总支出: ¥{total_expense:,.2f}")
    print(f"  总收入: ¥{total_income:,.2f}")
    print(f"  净结余: ¥{total_income - total_expense:,.2f}")
    print(f"  月均支出: ¥{total_expense / expense['year_month'].nunique():,.2f}")
    print(f"  笔均支出: ¥{expense['amount'].mean():,.2f}")
    print(f"  单笔最大: ¥{expense['amount'].max():,.2f}")
    print()

    # 4. 按分类聚合
    print("=" * 60)
    print("📂 钱花在哪：按分类")
    print("=" * 60)
    cat_summary = expense.groupby('category').agg(
        笔数=('amount', 'count'),
        总额=('amount', 'sum'),
        笔均=('amount', 'mean'),
    ).sort_values('总额', ascending=False)
    cat_summary['占比'] = (cat_summary['总额'] / total_expense * 100).round(2)
    print(cat_summary.to_string())
    print()

    # 5. 按月份
    print("=" * 60)
    print("📅 月度支出趋势")
    print("=" * 60)
    monthly = expense.groupby('year_month').agg(
        笔数=('amount', 'count'),
        总额=('amount', 'sum'),
    )
    monthly['环比'] = monthly['总额'].pct_change() * 100
    print(monthly.to_string())
    print()

    # 6. 按用户 TOP
    print("=" * 60)
    print("👥 用户支出 TOP 10")
    print("=" * 60)
    user_summary = expense.groupby('username').agg(
        笔数=('amount', 'count'),
        总额=('amount', 'sum'),
        笔均=('amount', 'mean'),
    ).sort_values('总额', ascending=False).head(10)
    print(user_summary.to_string())
    print()

    # 7. 季度分析
    print("=" * 60)
    print("📊 季度汇总")
    print("=" * 60)
    quarterly = expense.groupby('year_quarter').agg(
        笔数=('amount', 'count'),
        总额=('amount', 'sum'),
    )
    print(quarterly.to_string())
    print()

    # 8. 商家 TOP
    print("=" * 60)
    print("🏪 商家分布（从 note 关键词识别）")
    print("=" * 60)
    merchant_summary = expense[expense['merchant'] != '未识别'].groupby('merchant').agg(
        笔数=('amount', 'count'),
        总额=('amount', 'sum'),
    ).sort_values('总额', ascending=False)
    if len(merchant_summary):
        print(merchant_summary.to_string())
    else:
        print("  (没有可识别的商家记录)")
    print()

    # 9. 月度 × 分类（看季节性）
    print("=" * 60)
    print("🗓️ 月度 × 分类 矩阵（钱花在哪 + 哪个月）")
    print("=" * 60)
    pivot = expense.pivot_table(
        index='category', columns='year_month',
        values='amount', aggfunc='sum', fill_value=0
    )
    print(pivot.to_string())
    print()

    # 10. 生成 6 张可视化图
    print("=" * 60)
    print("🎨 生成可视化图表")
    print("=" * 60)
    paths = {
        'pie': chart_category_pie(cat_summary, total_expense),
        'trend': chart_monthly_trend(monthly),
        'stack': chart_monthly_category_stack(pivot),
        'user': chart_user_top(user_summary, top_n=10),
        'quarter': chart_quarterly_compare(quarterly),
        'merchant': chart_merchant(merchant_summary),
    }
    for name, p in paths.items():
        if p:
            print(f"  ✅ {name}: {p}")
    print()

    # 11. 写入 Markdown 报告（文字版 + 图引用）
    md = []
    md.append("# 📊 记账本财报分析系统 — 消费分析报告")
    md.append(f"\n> 🕐 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
    md.append(f"> 📅 数据范围：{df['date'].min().strftime('%Y-%m-%d')} ~ {df['date'].max().strftime('%Y-%m-%d')}")
    md.append(f"> 👥 用户数：{df['user_id'].nunique()} | 📝 总记录：{len(df)} | 💸 支出笔数：{len(expense)}\n")
    md.append("---\n")

    md.append("## 💰 总览\n")
    md.append(f"- 总支出：**¥{total_expense:,.2f}**")
    md.append(f"- 总收入：¥{total_income:,.2f}")
    md.append(f"- 净结余：¥{total_income - total_expense:,.2f}")
    md.append(f"- 月均支出：¥{total_expense / expense['year_month'].nunique():,.2f}")
    md.append(f"- 笔均支出：¥{expense['amount'].mean():,.2f}")
    md.append(f"- 单笔最大：¥{expense['amount'].max():,.2f}（来自 {expense.loc[expense['amount'].idxmax(), 'username']}）\n")

    md.append("---\n")
    md.append("## 📂 钱花在哪：按分类占比\n")
    md.append("| 分类 | 笔数 | 总额 | 笔均 | 占比 |")
    md.append("|---|---|---|---|---|")
    for cat, row in cat_summary.iterrows():
        md.append(f"| {cat} | {int(row['笔数'])} | ¥{row['总额']:,.2f} | ¥{row['笔均']:,.2f} | {row['占比']}% |")
    md.append("")

    md.append("---\n")
    md.append("## 📅 月度趋势\n")
    md.append("| 月份 | 笔数 | 总额 | 环比 |")
    md.append("|---|---|---|---|")
    for ym, row in monthly.iterrows():
        delta = f"{row['环比']:+.1f}%" if pd.notna(row['环比']) else "—"
        md.append(f"| {ym} | {int(row['笔数'])} | ¥{row['总额']:,.2f} | {delta} |")
    md.append("")

    md.append("---\n")
    md.append("## 📊 季度汇总\n")
    md.append("| 季度 | 笔数 | 总额 |")
    md.append("|---|---|---|")
    for q, row in quarterly.iterrows():
        md.append(f"| {q} | {int(row['笔数'])} | ¥{row['总额']:,.2f} |")
    md.append("")

    md.append("---\n")
    md.append("## 👥 用户支出 TOP 10\n")
    md.append("| 用户 | 笔数 | 总额 | 笔均 |")
    md.append("|---|---|---|---|")
    for u, row in user_summary.iterrows():
        md.append(f"| {u} | {int(row['笔数'])} | ¥{row['总额']:,.2f} | ¥{row['笔均']:,.2f} |")
    md.append("")

    if len(merchant_summary):
        md.append("---\n")
        md.append("## 🏪 商家分布（从 note 识别）\n")
        md.append("| 商家 | 笔数 | 总额 |")
        md.append("|---|---|---|")
        for m, row in merchant_summary.iterrows():
            md.append(f"| {m} | {int(row['笔数'])} | ¥{row['总额']:,.2f} |")
        md.append("")

    md.append("---\n")
    md.append("## 🗓️ 月度 × 分类矩阵（数据明细）\n")
    md.append("```")
    md.append(pivot.to_string())
    md.append("```\n")

    # 自动洞察
    md.append("---\n")
    md.append("## 💡 关键洞察\n")
    top_cat = cat_summary.index[0]
    top_cat_pct = cat_summary.iloc[0]['占比']
    top_user = user_summary.index[0]
    top_user_amt = user_summary.iloc[0]['总额']
    max_month = monthly['总额'].idxmax()
    max_month_amt = monthly['总额'].max()

    md.append(f"1. **最大开销分类是「{top_cat}」**，占总支出的 **{top_cat_pct}%**")
    md.append(f"2. **消费最多的用户是「{top_user}」**，累计支出 ¥{top_user_amt:,.2f}")
    md.append(f"3. **支出最高的月份是 {max_month}**，达 ¥{max_month_amt:,.2f}")
    if pd.notna(monthly['环比'].iloc[-1]):
        last_delta = monthly['环比'].iloc[-1]
        if abs(last_delta) > 20:
            direction = "上升" if last_delta > 0 else "下降"
            md.append(f"4. **最近一个月环比 {direction} {abs(last_delta):.1f}%**，需关注")
    if len(merchant_summary):
        top_mer = merchant_summary.index[0]
        top_mer_amt = merchant_summary.iloc[0]['总额']
        md.append(f"5. **最大单商家是「{top_mer}」**，累计 ¥{top_mer_amt:,.2f}")

    report_path = OUTPUT_DIR / "spending-analysis.md"
    report_path.write_text("\n".join(md), encoding="utf-8")
    print()
    print("=" * 60)
    print(f"✅ 报告已生成：{report_path}")
    print(f"📁 图表目录：{CHARTS_DIR}/")
    print("=" * 60)


if __name__ == "__main__":
    main()
