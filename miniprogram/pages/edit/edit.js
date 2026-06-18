const api = require('../../utils/api.js')
const { CATEGORIES } = require('../../utils/constants.js')

Page({
  data: {
    id: null,
    date: '',
    amount: '',
    type: 'expense',
    category: '',
    categories: CATEGORIES.expense,
    note: '',
    submitting: false
  },

  onLoad(options) {
    this.setData({ id: options.id })
    this.loadBill(options.id)
  },

  async loadBill(id) {
    try {
      const bill = await api.getBillDetail(parseInt(id))
      const categories = bill.type === 'expense' ? CATEGORIES.expense : CATEGORIES.income
      this.setData({
        ...bill,
        amount: bill.amount.toString(),
        categories,
        category: bill.category
      })
    } catch (e) {
      wx.showToast({ title: '加载失败', icon: 'none' })
    }
  },

  onDateChange(e) { this.setData({ date: e.detail.value }) },
  onAmountInput(e) { this.setData({ amount: e.detail.value }) },

  onTypeChange(e) {
    const type = e.currentTarget.dataset.type
    const categories = type === 'expense' ? CATEGORIES.expense : CATEGORIES.income
    this.setData({ type, categories, category: categories[0] })
  },

  onCategoryTap(e) { this.setData({ category: e.currentTarget.dataset.cat }) },
  onNoteInput(e) { this.setData({ note: e.detail.value }) },

  async onSubmit() {
    const { id, date, amount, type, category, note } = this.data
    if (!amount || parseFloat(amount) <= 0) {
      wx.showToast({ title: '请输入正确金额', icon: 'none' })
      return
    }
    this.setData({ submitting: true })
    try {
      await api.editBill(id, { date, amount: parseFloat(amount), type, category, note })
      wx.showToast({ title: '保存成功', icon: 'success' })
      setTimeout(() => wx.switchTab({ url: '/pages/index/index' }), 1200)
    } catch (e) {
      console.error(e)
    } finally {
      this.setData({ submitting: false })
    }
  },

  onDelete() {
    wx.showModal({
      title: '确认删除',
      content: '删除后无法恢复',
      confirmText: '删除',
      confirmColor: '#d94f1e',
      success: async (res) => {
        if (res.confirm) {
          try {
            await api.deleteBill(this.data.id)
            wx.showToast({ title: '已删除', icon: 'success' })
            setTimeout(() => wx.switchTab({ url: '/pages/index/index' }), 1200)
          } catch (e) {
            console.error(e)
          }
        }
      }
    })
  }
})
