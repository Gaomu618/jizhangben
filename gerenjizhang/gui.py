# gui.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

MATPLOTLIB_AVAILABLE = True
try:
    import matplotlib.pyplot as plt
except ImportError:
    MATPLOTLIB_AVAILABLE = False

INCOME_CATE = ["工资", "奖金", "投资", "其他"]
EXPENSE_CATE = ["餐饮", "交通", "购物", "住房", "通讯", "娱乐", "其他"]

INITIALIZED = False


def init_gui():
    global INITIALIZED
    if not INITIALIZED:
        from gerenjizhang.db import init_db
        init_db()
        INITIALIZED = True


class BillApp:
    def __init__(self, root):
        self.root = root
        self.root.title("个人记账本")
        self.root.geometry("900x600")
        self.year = datetime.now().year
        self.month = datetime.now().month
        self.user_id = None
        self._ask_login()
        if self.user_id:
            self.create_ui()
            self.refresh_all()

    def _ask_login(self):
        w = tk.Toplevel(self.root)
        w.title("登录")
        w.geometry("300x150")
        w.transient(self.root)
        w.grab_set()

        ttk.Label(w, text="用户名").grid(row=0, column=0, padx=10, pady=10)
        u_var = tk.StringVar()
        ttk.Entry(w, textvariable=u_var).grid(row=0, column=1)

        ttk.Label(w, text="密码").grid(row=1, column=0, padx=10, pady=10)
        p_var = tk.StringVar()
        ttk.Entry(w, textvariable=p_var, show="*").grid(row=1, column=1)

        def do_login():
            from gerenjizhang.db import get_user_by_username
            from werkzeug.security import check_password_hash
            user = get_user_by_username(u_var.get())
            if user and check_password_hash(user[2], p_var.get()):
                self.user_id = user[0]
                w.destroy()
            else:
                messagebox.showerror("错误", "用户名或密码错误")

        ttk.Button(w, text="登录", command=do_login).grid(row=2, column=0, columnspan=2, pady=10)

        self.root.wait_window(w)

    def create_ui(self):
        top = ttk.Frame(self.root)
        top.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(top, text="年").pack(side=tk.LEFT)
        self.y_var = tk.StringVar(value=str(self.year))
        ttk.Entry(top, textvariable=self.y_var, width=8).pack(side=tk.LEFT, padx=5)

        ttk.Label(top, text="月").pack(side=tk.LEFT)
        self.m_var = tk.StringVar(value=f"{self.month:02d}")
        ttk.Entry(top, textvariable=self.m_var, width=5).pack(side=tk.LEFT, padx=5)

        ttk.Button(top, text="刷新", command=self.refresh_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(top, text="图表", command=self.show_pie).pack(side=tk.LEFT, padx=5)

        frame = ttk.Frame(self.root)
        frame.pack(fill=tk.BOTH, expand=1, padx=10, pady=5)

        self.tree = ttk.Treeview(frame, columns=("id", "date", "amount", "type", "cate", "note"), show="headings")
        self.tree.heading("id", text="ID")
        self.tree.heading("date", text="日期")
        self.tree.heading("amount", text="金额")
        self.tree.heading("type", text="类型")
        self.tree.heading("cate", text="分类")
        self.tree.heading("note", text="备注")
        self.tree.column("id", width=50)
        self.tree.column("amount", width=80)
        self.tree.column("type", width=80)
        self.tree.column("cate", width=100)

        sb = ttk.Scrollbar(frame, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(fill=tk.BOTH, expand=1)

        btns = ttk.Frame(self.root)
        btns.pack(fill=tk.X, padx=10, pady=5)
        ttk.Button(btns, text="新增", command=self.add).pack(side=tk.LEFT, padx=5)
        ttk.Button(btns, text="编辑", command=self.edit).pack(side=tk.LEFT, padx=5)
        ttk.Button(btns, text="删除", command=self.delete).pack(side=tk.LEFT, padx=5)

        self.info = ttk.Label(self.root, text="")
        self.info.pack(pady=5)

    def _get_month_range(self):
        y = int(self.y_var.get())
        m = int(self.m_var.get())
        start = f"{y}-{m:02d}-01"
        end = f"{y}-{m+1:02d}-01" if m < 12 else f"{y+1}-01-01"
        return start, end

    def refresh_list(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        start, end = self._get_month_range()
        from gerenjizhang.service import query_records
        for r in query_records(self.user_id, start_date=start, end_date=end):
            self.tree.insert("", "end", values=r)

    def refresh_summary(self):
        try:
            y = int(self.y_var.get())
            m = int(self.m_var.get())
        except ValueError:
            messagebox.showwarning("错误", "年月无效")
            return
        from gerenjizhang.service import get_monthly_balance
        in_, ex, bal = get_monthly_balance(self.user_id, y, m)
        self.info.config(text=f"收入：{in_:.2f} | 支出：{ex:.2f} | 结余：{bal:.2f}")

    def refresh_all(self):
        self.refresh_list()
        self.refresh_summary()

    def add(self):
        w = tk.Toplevel(self.root)
        w.title("新增")
        w.geometry("400x300")

        ttk.Label(w, text="日期").grid(row=0, column=0, padx=10, pady=5)
        d_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        ttk.Entry(w, textvariable=d_var).grid(row=0, column=1)

        ttk.Label(w, text="金额").grid(row=1, column=0, pady=5)
        a_var = tk.DoubleVar()
        ttk.Entry(w, textvariable=a_var).grid(row=1, column=1)

        ttk.Label(w, text="类型").grid(row=2, column=0, pady=5)
        t_var = tk.StringVar(value="expense")
        ttk.Radiobutton(w, text="支出", variable=t_var, value="expense").grid(row=2, column=1)
        ttk.Radiobutton(w, text="收入", variable=t_var, value="income").grid(row=2, column=2)

        ttk.Label(w, text="分类").grid(row=3, column=0, pady=5)
        cate_var = tk.StringVar()
        cb = ttk.Combobox(w, textvariable=cate_var, width=18)
        cb.grid(row=3, column=1)

        def switch_type(*args):
            if t_var.get() == "income":
                cb.config(values=INCOME_CATE)
                cb.current(0)
            else:
                cb.config(values=EXPENSE_CATE)
                cb.current(0)
        t_var.trace_add("write", switch_type)
        switch_type()

        ttk.Label(w, text="备注").grid(row=4, column=0, pady=5)
        n_var = tk.StringVar()
        ttk.Entry(w, textvariable=n_var).grid(row=4, column=1)

        def save():
            from gerenjizhang.service import add_bill_record
            ok, msg = add_bill_record(self.user_id, d_var.get(), a_var.get(), t_var.get(), cate_var.get(), n_var.get())
            if ok:
                messagebox.showinfo("成功", msg)
                w.destroy()
                self.refresh_all()
            else:
                messagebox.showerror("失败", msg)
        ttk.Button(w, text="保存", command=save).grid(row=5, column=1, pady=10)

    def edit(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请选择一条记录")
            return
        data = self.tree.item(selected[0])["values"]
        rid, date, amt, tp, cate, note = data

        w = tk.Toplevel(self.root)
        w.title("编辑")
        w.geometry("400x300")

        ttk.Label(w, text="日期").grid(row=0, column=0, padx=10, pady=5)
        d_var = tk.StringVar(value=date)
        ttk.Entry(w, textvariable=d_var).grid(row=0, column=1)

        ttk.Label(w, text="金额").grid(row=1, column=0, pady=5)
        a_var = tk.DoubleVar(value=amt)
        ttk.Entry(w, textvariable=a_var).grid(row=1, column=1)

        ttk.Label(w, text="类型").grid(row=2, column=0, pady=5)
        t_var = tk.StringVar(value=tp)
        ttk.Radiobutton(w, text="支出", variable=t_var, value="expense").grid(row=2, column=1)
        ttk.Radiobutton(w, text="收入", variable=t_var, value="income").grid(row=2, column=2)

        ttk.Label(w, text="分类").grid(row=3, column=0, pady=5)
        cate_var = tk.StringVar(value=cate)
        cb = ttk.Combobox(w, textvariable=cate_var, width=18)
        cb.grid(row=3, column=1)

        def switch_type(*args):
            if t_var.get() == "income":
                cb.config(values=INCOME_CATE)
            else:
                cb.config(values=EXPENSE_CATE)
        t_var.trace_add("write", switch_type)
        switch_type()

        ttk.Label(w, text="备注").grid(row=4, column=0, pady=5)
        n_var = tk.StringVar(value=note)
        ttk.Entry(w, textvariable=n_var).grid(row=4, column=1)

        def update():
            from gerenjizhang.service import edit_bill_record
            ok, msg = edit_bill_record(rid, d_var.get(), a_var.get(), t_var.get(), cate_var.get(), n_var.get(), self.user_id)
            if ok:
                messagebox.showinfo("成功", msg)
                w.destroy()
                self.refresh_all()
            else:
                messagebox.showerror("失败", msg)
        ttk.Button(w, text="更新", command=update).grid(row=5, column=1, pady=10)

    def delete(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请选择")
            return
        if messagebox.askyesno("确认", "确定删除？"):
            rid = self.tree.item(selected[0])["values"][0]
            from gerenjizhang.service import delete_bill_record
            delete_bill_record(rid, self.user_id)
            self.refresh_all()

    def show_pie(self):
        if not MATPLOTLIB_AVAILABLE:
            messagebox.showwarning("提示", "请先安装 matplotlib！\n命令：pip install matplotlib")
            return

        try:
            y = int(self.y_var.get())
            m = int(self.m_var.get())
        except ValueError:
            messagebox.showwarning("错误", "请输入正确年份月份")
            return

        from gerenjizhang.service import get_expense_by_category
        data = get_expense_by_category(self.user_id, y, m)
        if not data:
            messagebox.showinfo("提示", "该月暂无支出记录，无法生成图表")
            return

        cats = [x[0] for x in data]
        vals = [x[1] for x in data]

        plt.rcParams['font.sans-serif'] = ['SimHei']
        plt.rcParams['axes.unicode_minus'] = False

        plt.figure(figsize=(6, 6))
        plt.pie(vals, labels=cats, autopct="%.1f%%")
        plt.title(f"{y}年{m}月支出分类饼图")
        plt.show()
