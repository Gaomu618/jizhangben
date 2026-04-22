const api = require('../../utils/api.js')
const { CATEGORIES } = require('../../utils/constants.js')

Page({
  data: {
    date: '',
    amount: '',
    type: 'expense',
    category: '',
    categories: CATEGORIES.expense,
    note: ''
  },

  onLoad() {
    const now = new Date()
    const year = now.getFullYear()
    const month = String(now.getMonth() + 1).padStart(2, '0')
    const day = String(now.getDate()).padStart(2, '0')
    this.setData({
      date: `${year}-${month}-${day}`,
      category: CATEGORIES.expense[0]
    })
  },

  bindDateChange(e) {
    this.setData({ date: e.detail.value })
  },

  bindAmountInput(e) {
    this.setData({ amount: e.detail.value })
  },

  typeChange(e) {
    const type = e.detail.value
    const categories = type === 'expense' ? CATEGORIES.expense : CATEGORIES.income
    this.setData({
      type: type,
      categories: categories,
      category: categories[0]
    })
  },

  tapCategory(e) {
    const index = e.currentTarget.dataset.index
    const cat = this.data.categories[index]
    this.setData({ category: cat })
  },

  bindNoteInput(e) {
    this.setData({ note: e.detail.value })
  },

  async submit() {
    const { date, amount, type, category, note } = this.data
    if (!amount || parseFloat(amount) <= 0) {
      wx.showToast({ title: '请输入正确金额', icon: 'none' })
      return
    }
    try {
      await api.addBill({ date, amount: parseFloat(amount), type, category, note })
      wx.showToast({ title: '添加成功', icon: 'success' })
      setTimeout(() => wx.switchTab({ url: '/pages/index/index' }), 1500)
    } catch (e) {
      console.error(e)
    }
  }
})