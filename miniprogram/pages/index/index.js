const api = require('../../utils/api.js')

Page({
  data: {
    year: new Date().getFullYear(),
    month: new Date().getMonth() + 1,
    income: '0.00',
    expense: '0.00',
    balance: '0.00',
    bills: []
  },

  onLoad() {
    this.checkLogin()
  },

  onShow() {
    this.loadData()
  },

  checkLogin() {
    const token = wx.getStorageSync('token')
    if (!token) {
      wx.reLaunch({ url: '/pages/login/login' })
    }
  },

  async loadData() {
    try {
      const [stats, listData] = await Promise.all([
        api.getMonthlyStats(this.data.year, this.data.month),
        api.getBillList({ year: this.data.year, month: this.data.month })
      ])
      this.setData({
        income: stats.income.toFixed(2),
        expense: stats.expense.toFixed(2),
        balance: stats.balance.toFixed(2),
        bills: listData.list || []
      })
    } catch (e) {
      console.error(e)
    }
  },

  prevMonth() {
    let { year, month } = this.data
    if (month === 1) {
      year--
      month = 12
    } else {
      month--
    }
    this.setData({ year, month }, () => this.loadData())
  },

  nextMonth() {
    let { year, month } = this.data
    if (month === 12) {
      year++
      month = 1
    } else {
      month++
    }
    this.setData({ year, month }, () => this.loadData())
  },

  editBill(e) {
    wx.navigateTo({ url: `/pages/edit/edit?id=${e.currentTarget.dataset.id}` })
  }
})