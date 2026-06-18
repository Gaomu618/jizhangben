"""
账单导入：支持 CSV / XLSX（微信 + 支付宝 + 通用格式）。
"""
from flask import request

from gerenjizhang.api.bill_bp import bill_bp
from gerenjizhang.middleware.limiter import limiter
from gerenjizhang.utils.classifier import classify as smart_classify
from gerenjizhang.utils.decorators import login_required
from gerenjizhang.utils.response import success_response, error_response


@bill_bp.route('/import', methods=['POST'])
@login_required
@limiter.limit("5 per minute")
def import_bill(user_id):
    """导入账单（支持 CSV 和 XLSX）"""
    from gerenjizhang.db import add_record_batch, get_existing_record_hashes, save_import_history

    if 'file' not in request.files:
        return error_response(4001, "请选择文件")

    file = request.files['file']
    if not file.filename:
        return error_response(4002, "文件名为空")

    filename = file.filename.lower()
    # dry_run 同时支持 form 和 query：前端 FormData 发 form,curl/SDK 经常发 query
    dry_run_raw = request.form.get('dry_run') or request.args.get('dry_run') or 'false'
    dry_run = dry_run_raw.lower() == 'true'

    try:
        if filename.endswith('.csv'):
            import csv
            import io
            content = file.read().decode('utf-8-sig')
            lines = content.split('\n')
            data_lines = [line for line in lines if line.strip()]
            # 微信CSV跳过前16行说明，从第17行开始是表头
            if len(data_lines) > 16:
                header_line = data_lines[16]
                stream = io.StringIO('\n'.join(data_lines[16:]))
                reader = csv.reader(stream)
                rows = [header_line.split(',')] + list(reader)[1:]
            else:
                stream = io.StringIO(content)
                reader = csv.reader(stream)
                rows = list(reader)
        elif filename.endswith('.xlsx'):
            import openpyxl
            from io import BytesIO
            file.seek(0)  # 确保从头读取
            wb = openpyxl.load_workbook(BytesIO(file.read()), data_only=True)
            ws = wb.active
            # 只调用一次 list(ws.values)，避免迭代器问题
            all_rows = list(ws.values)
            # 跳过前面的说明行，查找真实表头
            header_row_idx = 0
            for i, row in enumerate(all_rows):
                row_header = [str(cell).strip() if cell else '' for cell in row]
                if '收/支' in row_header and any('金额' in h for h in row_header):
                    header_row_idx = i
                    break
            rows = all_rows[header_row_idx:]
        else:
            return error_response(4003, "仅支持 CSV 和 XLSX 格式")
    except Exception as e:
        return error_response(4004, f"文件读取失败: {str(e)}")

    if len(rows) < 2:
        return error_response(4005, "文件数据为空")

    records = []
    errors = []

    # 微信格式表头: 交易时间,交易类型,交易对方,商品,收/支,金额(元),支付方式,当前状态,交易单号
    # 在XLSX中查找真实表头行的索引
    header_row_idx = 0
    for i, row in enumerate(rows):
        row_header = [str(h).strip() if h else '' for h in row]
        if '收/支' in row_header and any('金额' in h for h in row_header) and '交易时间' in row_header:
            header_row_idx = i
            break

    # 如果表头不在第0行，说明前面有说明行，需要跳过
    if header_row_idx > 0:
        rows = rows[header_row_idx:]
        header = [str(h).strip() if h else '' for h in rows[0]]
    else:
        header = [str(h).strip() if h else '' for h in rows[0]]

    is_wechat = '收/支' in header and any('金额' in h for h in header) and '交易时间' in header
    is_alipay = '交易时间' in header and any('金额' in h for h in header) and '状态' in header

    def parse_amount(val):
        if val is None:
            return None
        s = str(val).replace('¥', '').replace(',', '').strip()
        try:
            return float(s)
        except:
            return None

    def parse_date(date_str):
        from datetime import datetime
        date_str = date_str.strip()
        formats = ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%Y/%m/%d %H:%M:%S', '%Y/%m/%d', '%m/%d/%Y %H:%M:%S', '%m/%d/%Y']
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).strftime('%Y-%m-%d')
            except ValueError:
                continue
        try:
            return datetime.strptime(date_str[:10], '%Y-%m-%d').strftime('%Y-%m-%d')
        except:
            return None

    def guess_category(row_data, type_, trans_type='', user_id=None):
        # 转账/红包：直接归「转账」类，不走智能分类（避免被覆盖成"其他"）
        if trans_type == '转账':
            return '转账'

        # 微信/支付宝格式：把交易对方、商品、交易类型等拼起来
        text = ' '.join(str(c) for c in row_data if c)
        # 加入 trans_type（微信的交易类型字段）
        if trans_type:
            text = f"{trans_type} {text}"
        if not text.strip():
            return '其他' if type_ == 'expense' else '其他'

        # 优先用「收款方/商品」+ 类型字段（更精准）
        # 微信：row_data[2] 是交易对方，row_data[3] 是商品
        if is_wechat and len(row_data) >= 4:
            counterparty = row_data[2] or ''
            product = row_data[3] or ''
            focus_text = f"{counterparty} {product}"
        else:
            focus_text = text

        # 调用智能分类（80+ 关键词 + 用户学习 + 文本预处理）
        result = smart_classify(focus_text, user_id=user_id)
        if result:
            cat = result['category']
            # 智能分类给出的 type 优先，否则用 trans_type/type 推断
            if result.get('type') == 'income' and type_ != 'income':
                # 分类说收入，但流水说支出 → 可能是退款
                pass
            return cat

        # 智能分类没识别出来 → fallback
        if type_ == 'income':
            return '其他'
        return '其他'

    for idx, row in enumerate(rows[1:], start=2):
        try:
            row_data = [str(cell).strip() if cell else '' for cell in row]

            if is_wechat:
                # 微信格式列: 交易时间(0), 交易类型(1), 交易对方(2), 商品(3), 收/支(4), 金额(元)(5), 支付方式(6), 当前状态(7), 交易单号(8)
                if len(row_data) < 6:
                    errors.append(f"行{idx}: 数据列数不足")
                    continue

                date_str = row_data[0]
                trans_type = row_data[1]  # 交易类型
                counterparty = row_data[2]  # 交易对方
                product = row_data[3]  # 商品
                in_out = row_data[4]  # 收/支
                amount_str = row_data[5]
                status = row_data[7] if len(row_data) > 7 else ''

                # 跳过已退款/已撤销
                if '已退款' in status or '已撤销' in status:
                    continue

                amount = parse_amount(amount_str)
                if amount is None:
                    errors.append(f"行{idx}: 金额格式错误")
                    continue

                # 类型判断
                if in_out == '收入':
                    type_ = 'income'
                    amount = abs(amount)
                elif in_out == '支出':
                    type_ = 'expense'
                    amount = abs(amount)
                elif trans_type in ('零钱提现', '信用卡还款', '理财通'):
                    # 过路钱：跳过不导入（不计入收支）
                    continue
                elif trans_type == '转账':
                    # 微信/支付宝转账：单独成类（保留记录，但不污染"餐饮/购物"统计）
                    if in_out == '收入':
                        type_ = 'income'
                    else:
                        type_ = 'expense'
                    amount = abs(amount)
                    category = '转账'  # 强制归类为「转账」
                elif trans_type == '退款':
                    type_ = 'income'
                    amount = abs(amount)
                else:
                    # 无法识别，默认跳过
                    errors.append(f"行{idx}: 无法识别的类型 trans_type={trans_type} in_out={in_out}")
                    continue

                if amount == 0:
                    continue

                date_parsed = parse_date(date_str)
                if not date_parsed:
                    errors.append(f"行{idx}: 日期格式错误")
                    continue

                category = guess_category([counterparty, product], type_, trans_type, user_id)
                records.append((date_parsed, amount, type_, category, counterparty))

            elif is_alipay:
                # 支付宝格式
                date_str = row_data[0]
                trans_type = row_data[1]
                amount_str = row_data[4] if len(row_data) > 4 else ''
                status = row_data[5] if len(row_data) > 5 else ''

                if '已退款' in status or '已撤销' in status:
                    continue

                amount = parse_amount(amount_str)
                if amount is None or amount == 0:
                    continue

                if amount > 0:
                    type_ = 'income'
                else:
                    type_ = 'expense'
                    amount = abs(amount)

                date_parsed = parse_date(date_str)
                if not date_parsed:
                    errors.append(f"行{idx}: 日期格式错误")
                    continue

                category = guess_category(row_data, type_, '', user_id)
                records.append((date_parsed, amount, type_, category, ''))
            else:
                # 通用格式: 日期, 类型, 分类, 金额, 备注
                if len(row_data) >= 4:
                    date_str = row_data[0]
                    amount = parse_amount(row_data[3])
                    if amount is None:
                        continue
                    type_str = row_data[1].lower()
                    type_ = 'income' if type_str in ('收入', 'income') else 'expense'
                    category = row_data[2] if len(row_data) > 2 else '其他'
                    note = row_data[4] if len(row_data) > 4 else ''
                    date_parsed = parse_date(date_str)
                    if not date_parsed:
                        continue
                    records.append((date_parsed, abs(amount), type_, category, note))
                else:
                    errors.append(f"行{idx}: 格式无法识别")
                    continue

        except Exception as e:
            errors.append(f"行{idx}: {str(e)}")

    if not records:
        err_msg = "未能解析出有效记录"
        if errors:
            err_msg += f"，前3条: {errors[:3]}"
        return error_response(4006, err_msg)

    # 去重
    existing = get_existing_record_hashes(user_id)
    # 统一金额格式：去掉小数点后的尾随 0，与 DB 端 hash 对齐
    def _amt(s):
        return f"{float(s):g}"
    new_records = [r for r in records if hash((r[0], _amt(r[1]), r[2], r[3], r[4])) not in existing]

    if dry_run:
        preview = [(r[0], r[1], r[2], r[3], r[4]) for r in new_records[:10]]
        return success_response({
            "preview": preview,
            "total": len(new_records),
            "duplicate": len(records) - len(new_records),
            "errors": errors[:10]  # 同步返回解析失败行，让前端预览时就能展示
        })

    # 实际导入
    imported = add_record_batch(new_records, user_id)
    save_import_history(user_id, 'wechat' if is_wechat else ('alipay' if is_alipay else 'csv'), len(records), imported)

    return success_response({
        "imported": imported,
        "duplicate": len(records) - len(new_records),
        "errors": errors[:10]
    })
