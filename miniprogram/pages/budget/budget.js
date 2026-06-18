const api = require('../../utils/api.js')

const ALL_EXPENSE_CATEGORIES = ['餐饮', '交通', '购物', '居住', '娱乐', '医疗', '教育', '其他']
const QUICK_AMOUNTS = [300, 500, 1000, 2000]

Page({
  data: {
    year: new Date().getFullYear(),
    month: new Date().getMonth() + 1,
    budgets: [],
    availableCategories: [...ALL_EXPENSE_CATEGORIES],
    newCategory: '',
    newCategoryIndex: 0,
    newAmount: '',
    editingCategory: null,
    editAmount: '',
    quickAmounts: QUICK_AMOUNTS
  },

  onShow() {
    this.loadBudgets()
  },

  async loadBudgets() {
    try {
      const res = await api.getBudget({ year: this.data.year, month: this.data.month })
      const budgets = (res || []).map(b => {
        const percent = (b.percent !== undefined && b.percent !== null)
  ? b.percent
  : (b.spent && b.budget ? Math.round(b.spent / b.budget * 1000) / 10 : 0)
        const spent = b.spent || 0
        const budget = b.budget || 0
        // 预计算提示文字 + 金额字符串（WXML 不支持 .toFixed()）
        let tipText = ''
        let tipClass = ''
        if (percent >= 100) {
          tipText = `已超支 ¥${(spent - budget).toFixed(0)}`
          tipClass = 'tip-over'
        } else if (percent >= 80) {
          tipText = `还剩 ¥${(budget - spent).toFixed(0)}，快用完了`
          tipClass = 'tip-warn'
        } else {
          tipText = `还剩 ¥${(budget - spent).toFixed(0)} (${(100 - percent).toFixed(0)}%)`
          tipClass = 'tip-muted'
        }
        return {
          ...b,
          percent,
          tipText,
          tipClass,
          spentRmb: spent.toFixed(0),
          budgetRmb: budget.toFixed(0)
        }
      })
      const used = new Set(budgets.map(b => b.category))
      this.setData({
        budgets,
        availableCategories: ALL_EXPENSE_CATEGORIES.filter(c => !used.has(c))
      })
    } catch (e) {
      console.error('[budget loadBudgets]', e)
    }
  },

  get monthStr() {
    return `${this.data.year}-${String(this.data.month).padStart(2, '0')}`
  },

  prevMonth() {
    let { year, month } = this.data
    if (month === 1) { year--; month = 12 } else { month-- }
    this.setData({ year, month }, () => this.loadBudgets())
  },

  nextMonth() {
    let { year, month } = this.data
    if (month === 12) { year++; month = 1 } else { month++ }
    this.setData({ year, month }, () => this.loadBudgets())
  },

  onNewCategoryChange(e) {
    const idx = e.detail.value
    const cat = this.data.availableCategories[idx] || ''
    this.setData({ newCategory: cat, newCategoryIndex: idx })
  },

  onNewAmountInput(e) {
    this.setData({ newAmount: e.detail.value })
  },

  onQuickAmount(e) {
    this.setData({ newAmount: String(e.currentTarget.dataset.amt) })
  },

  async onAdd() {
    const { newCategory, newAmount, year, month } = this.data
    const amount = parseFloat(newAmount)
    if (!newCategory || !amount || amount <= 0) {
      wx.showToast({ title: '请填写分类和金额', icon: 'none' })
      return
    }
    try {
      await api.setBudget({
        category: newCategory,
        amount,
        type: 'expense',
        month: `${year}-${String(month).padStart(2, '0')}`
      })
      wx.showToast({ title: '已保存', icon: 'success' })
      this.setData({ newCategory: '', newCategoryIndex: 0, newAmount: '' })
      this.loadBudgets()
    } catch (e) {
      console.error(e)
    }
  },

  onStartEdit(e) {
    this.setData({
      editingCategory: e.currentTarget.dataset.cat,
      editAmount: String(e.currentTarget.dataset.amount)
    })
  },

  onEditAmountInput(e) {
    this.setData({ editAmount: e.detail.value })
  },

  onCancelEdit() {
    this.setData({ editingCategory: null, editAmount: '' })
  },

  async onSaveEdit(e) {
    const cat = e.currentTarget.dataset.cat
    const amount = parseFloat(this.data.editAmount)
    if (!amount || amount <= 0) {
      wx.showToast({ title: '请输入正确金额', icon: 'none' })
      return
    }
    try {
      await api.setBudget({
        category: cat,
        amount,
        type: 'expense',
        month: this.monthStr
      })
      wx.showToast({ title: '已更新', icon: 'success' })
      this.setData({ editingCategory: null, editAmount: '' })
      this.loadBudgets()
    } catch (e) {
      console.error(e)
    }
  },

  onDelete(e) {
    const cat = e.currentTarget.dataset.cat
    wx.showModal({
      title: '删除预算',
      content: `确定要删除「${cat}」的预算吗？`,
      confirmText: '删除',
      confirmColor: '#d94f1e',
      success: async (res) => {
        if (!res.confirm) return
        try {
          await api.deleteBudget({ category: cat, month: this.monthStr })
          wx.showToast({ title: '已删除', icon: 'success' })
          this.loadBudgets()
        } catch (e) {
          console.error(e)
        }
      }
    })
  }
})
