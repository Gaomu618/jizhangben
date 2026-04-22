const api = require('../../utils/api.js')
const app = getApp()

Page({
  data: {
    username: ''
  },

  onLoad() {
    const userinfo = app.globalData.userinfo
    if (userinfo) {
      this.setData({ username: userinfo.username || '微信用户' })
    }
  },

  logout() {
    wx.showModal({
      title: '确认退出',
      content: '确定要退出登录吗？',
      success: async (res) => {
        if (res.confirm) {
          try {
            await api.logout()
          } catch (e) {}
          wx.removeStorageSync('token')
          wx.removeStorageSync('userinfo')
          app.globalData.token = ''
          app.globalData.userinfo = null
          wx.reLaunch({ url: '/pages/login/login' })
        }
      }
    })
  }
})