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
    note: ''
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

  bindDateChange(e) {
    this.setData({ date: e.detail.value })
  },

  bindAmountInput(e) {
    this.setData({ amount: e.detail.value })
  },

  selectType(e) {
    const type = e.currentTarget.dataset.type
    const categories = type === 'expense' ? CATEGORIES.expense : CATEGORIES.income
    this.setData({ type, categories, category: categories[0] })
  },

  selectCategory(e) {
    this.setData({ category: e.currentTarget.dataset.category })
  },

  bindNoteInput(e) {
    this.setData({ note: e.detail.value })
  },

  async submit() {
    const { id, date, amount, type, category, note } = this.data
    if (!amount || parseFloat(amount) <= 0) {
      wx.showToast({ title: '请输入正确金额', icon: 'none' })
      return
    }
    try {
      await api.editBill(id, { date, amount: parseFloat(amount), type, category, note })
      wx.showToast({ title: '保存成功', icon: 'success' })
      setTimeout(() => wx.switchTab({ url: '/pages/index/index' }), 1500)
    } catch (e) {
      console.error(e)
    }
  },

  async deleteBill() {
    wx.showModal({
      title: '确认删除',
      content: '删除后无法恢复',
      success: async (res) => {
        if (res.confirm) {
          try {
            await api.deleteBill(this.data.id)
            wx.showToast({ title: '删除成功', icon: 'success' })
            setTimeout(() => wx.switchTab({ url: '/pages/index/index' }), 1500)
          } catch (e) {
            console.error(e)
          }
        }
      }
    })
  }
})