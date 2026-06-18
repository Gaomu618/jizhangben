"""
账单导出：CSV / XLSX / PDF 财报。
"""
from datetime import datetime

from flask import Response, request

from gerenjizhang.api.bill_bp import bill_bp
from gerenjizhang.db import get_records
from gerenjizhang.utils.decorators import login_required
from gerenjizhang.utils.response import error_response


@bill_bp.route('/export', methods=['GET'])
@login_required
def export_bill(user_id):
    """导出账单（支持 CSV / XLSX / PDF）"""
    year = request.args.get('year', type=int) or datetime.now().year
    month = request.args.get('month', type=int) or datetime.now().month
    fmt = (request.args.get('format') or 'csv').lower()

    # 格式白名单校验：避免静默 fallback 到 csv（之前传 pdf 会下载乱码文件）
    if fmt not in ('csv', 'xlsx', 'pdf'):
        return error_response(4003, f"不支持的导出格式: {fmt}，仅支持 csv / xlsx / pdf")

    start = f"{year}-{month:02d}-01"
    end = f"{year}-{month+1:02d}-01" if month < 12 else f"{year+1}-01-01"

    records = get_records(user_id, start_date=start, end_date=end)

    if fmt == 'xlsx':
        return _export_xlsx(records, year, month)
    elif fmt == 'pdf':
        return _export_pdf(records, year, month)
    else:
        return _export_csv(records, year, month)


def _export_csv(records, year, month):
    """纯文本 CSV"""
    import csv
    from io import StringIO

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['日期', '类型', '分类', '金额', '备注'])
    for r in records:
        type_text = '收入' if r[3] == 'income' else '支出'
        writer.writerow([r[1], type_text, r[4], float(r[2]) if r[2] else 0, r[5] or ''])
    csv_content = output.getvalue()
    output.close()

    filename = f"bill_{year}_{month}.csv"
    return Response(csv_content, mimetype='text/csv',
                    headers={'Content-Disposition': f'attachment; filename="{filename}"'})


def _export_xlsx(records, year, month):
    """Excel 工作表"""
    import openpyxl
    from io import BytesIO

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"{year}年{month}月账单"
    ws.append(['日期', '类型', '分类', '金额', '备注'])
    for r in records:
        type_text = '收入' if r[3] == 'income' else '支出'
        ws.append([r[1], type_text, r[4], float(r[2]) if r[2] else 0, r[5] or ''])
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    filename = f"bill_{year}_{month}.xlsx"
    return Response(
        output.getvalue(),
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'}
    )


def _export_pdf(records, year, month):
    """PDF 月度财报（含饼图 / 排行 / 详细账单）"""
    if not records:
        return error_response(4010, f"{year}年{month}月没有账单可导出")

    from io import BytesIO
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image,
    )
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from collections import defaultdict

    # 注册中文字体（Windows 默认有 Microsoft YaHei / SimHei）
    import os as _os
    font_paths = [
        ('YaHei', 'C:/Windows/Fonts/msyh.ttc'),
        ('YaHei', 'C:/Windows/Fonts/msyh.ttf'),
        ('SimHei', 'C:/Windows/Fonts/simhei.ttf'),
    ]
    chinese_font = 'Helvetica'  # fallback
    chinese_font_path = None
    for name, path in font_paths:
        if _os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont(name, path))
                chinese_font = name
                chinese_font_path = path
                break
            except Exception:
                pass

    # 准备数据
    total_income = sum(float(r[2]) for r in records if r[3] == 'income')
    total_expense = sum(float(r[2]) for r in records if r[3] == 'expense')
    cat_summary = defaultdict(float)
    cat_count = defaultdict(int)
    for r in records:
        if r[3] == 'expense':
            cat_summary[r[4]] += float(r[2])
            cat_count[r[4]] += 1

    # 生成 2 张图（PNG 临时）— 分类饼图 / 分类柱状（TOP 8）
    import tempfile
    tmpfiles = []
    palette = ['#5B8FF9', '#5AD8A6', '#5D7092', '#F6BD16', '#E86452',
               '#6DC8EC', '#945FB9', '#FF9D4D', '#269A99']
    # matplotlib 字体配置：直接用 TTC 路径注册（解决方块问题）
    if chinese_font_path:
        from matplotlib import font_manager as _fm
        try:
            _fm.fontManager.addfont(chinese_font_path)
            _chinese_name = _fm.FontProperties(fname=chinese_font_path).get_name()
            plt.rcParams['font.sans-serif'] = [_chinese_name, 'DejaVu Sans']
        except Exception:
            plt.rcParams['font.sans-serif'] = [chinese_font, 'DejaVu Sans']
    else:
        plt.rcParams['font.sans-serif'] = [chinese_font, 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False

    # 1) 分类饼图
    fig, ax = plt.subplots(figsize=(6, 4), dpi=120)
    labels = list(cat_summary.keys())
    sizes = list(cat_summary.values())
    explode = [0.05] + [0] * (len(labels) - 1)
    ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90,
           colors=palette[:len(labels)], explode=explode,
           textprops={'fontsize': 9})
    ax.set_title(f'{year}年{month}月 · 支出分类', fontsize=12)
    pie_path = tempfile.NamedTemporaryFile(suffix='.png', delete=False).name
    fig.savefig(pie_path, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    tmpfiles.append(pie_path)

    # 2) 分类柱状（横向）
    sorted_cats = sorted(cat_summary.items(), key=lambda x: -x[1])[:8]
    fig, ax = plt.subplots(figsize=(6, 4), dpi=120)
    names = [c[0] for c in sorted_cats]
    vals = [c[1] for c in sorted_cats]
    bars = ax.barh(names, vals, color=palette[:len(names)])
    for bar, v in zip(bars, vals):
        ax.text(v + max(vals) * 0.01, bar.get_y() + bar.get_height() / 2,
                f'¥{v:,.0f}', va='center', fontsize=9)
    ax.set_title('支出排行（Top 8 分类）', fontsize=12)
    ax.set_xlabel('金额 (¥)')
    bar_path = tempfile.NamedTemporaryFile(suffix='.png', delete=False).name
    fig.savefig(bar_path, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    tmpfiles.append(bar_path)

    # 构建 PDF
    output = BytesIO()
    doc = SimpleDocTemplate(
        output, pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=2 * cm, bottomMargin=2 * cm,
        title=f'记账本财报分析系统 - {year}年{month}月账单'
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Title'], fontName=chinese_font, fontSize=20, spaceAfter=12)
    h1_style = ParagraphStyle('H1', parent=styles['Heading1'], fontName=chinese_font, fontSize=14, spaceAfter=8, spaceBefore=12)
    body_style = ParagraphStyle('Body', parent=styles['BodyText'], fontName=chinese_font, fontSize=10, leading=14)

    story = []

    # 标题页
    story.append(Spacer(1, 4 * cm))
    story.append(Paragraph('记账本财报分析系统', title_style))
    story.append(Paragraph(f'{year} 年 {month} 月 · 财务报告', title_style))
    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph(f'生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M")}', body_style))
    story.append(Paragraph(f'账单笔数：{len(records)} 笔', body_style))
    story.append(Paragraph(f'报告期：{year}年{month}月', body_style))
    story.append(PageBreak())

    # 1. 概览
    story.append(Paragraph('一、本月概览', h1_style))
    overview_data = [
        ['指标', '数值'],
        ['本月收入', f'¥{total_income:,.2f}'],
        ['本月支出', f'¥{total_expense:,.2f}'],
        ['净结余', f'¥{total_income - total_expense:,.2f}'],
        ['笔均支出', f'¥{total_expense / cat_count.__len__() if cat_count else 0:,.2f}'],
        ['支出笔数', f'{sum(cat_count.values())} 笔'],
        ['分类数', f'{len(cat_summary)} 个'],
    ]
    t = Table(overview_data, colWidths=[6 * cm, 8 * cm])
    t.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), chinese_font),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#5B8FF9')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F8FA')]),
    ]))
    story.append(t)
    story.append(Spacer(1, 1 * cm))

    # 2. 分类明细
    story.append(Paragraph('二、分类支出明细', h1_style))
    cat_data = [['分类', '笔数', '金额', '占比']]
    total_e = sum(cat_summary.values()) or 1
    for cat, amt in sorted(cat_summary.items(), key=lambda x: -x[1]):
        cat_data.append([
            cat,
            str(cat_count[cat]),
            f'¥{amt:,.2f}',
            f'{amt / total_e * 100:.1f}%',
        ])
    t2 = Table(cat_data, colWidths=[5 * cm, 3 * cm, 5 * cm, 3 * cm])
    t2.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), chinese_font),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#5AD8A6')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F8FA')]),
    ]))
    story.append(t2)
    story.append(Spacer(1, 1 * cm))

    # 3. 分类饼图
    story.append(PageBreak())
    story.append(Paragraph('三、分类占比图', h1_style))
    story.append(Image(pie_path, width=15 * cm, height=10 * cm))
    story.append(Spacer(1, 1 * cm))

    # 4. 支出排行
    story.append(PageBreak())
    story.append(Paragraph('四、支出排行（Top 8）', h1_style))
    story.append(Image(bar_path, width=15 * cm, height=10 * cm))
    story.append(Spacer(1, 1 * cm))

    # 5. 详细账单
    story.append(PageBreak())
    story.append(Paragraph('五、详细账单', h1_style))
    detail_data = [['日期', '类型', '分类', '金额', '备注']]
    for r in records:
        type_text = '收入' if r[3] == 'income' else '支出'
        detail_data.append([
            r[1] or '-',
            type_text,
            r[4] or '-',
            f'¥{float(r[2]):.2f}' if r[2] else '-',
            (r[5] or '-')[:30],
        ])
    t3 = Table(detail_data, colWidths=[3.2 * cm, 1.6 * cm, 2.5 * cm, 2.5 * cm, 6.2 * cm])
    t3.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), chinese_font),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F6BD16')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.3, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#FFFBF0')]),
    ]))
    story.append(t3)

    # 构建
    doc.build(story)

    # 清理临时图片
    for f in tmpfiles:
        try:
            _os.unlink(f)
        except Exception:
            pass

    pdf_content = output.getvalue()
    output.close()

    filename = f"bill_{year}_{month}.pdf"
    return Response(
        pdf_content,
        mimetype='application/pdf',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'}
    )
