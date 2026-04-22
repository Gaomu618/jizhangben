const api = require('../../utils/api.js')
const app = getApp()

Page({
  data: {},

  wechatLogin() {
    wx.login({
      success: async (res) => {
        if (!res.code) {
          wx.showToast({ title: '登录失败', icon: 'none' })
          return
        }
        try {
          const data = await api.wechatLogin(res.code)
          app.globalData.token = data.token
          app.globalData.userinfo = data.userinfo
          wx.setStorageSync('token', data.token)
          wx.setStorageSync('userinfo', data.userinfo)
          wx.switchTab({ url: '/pages/index/index' })
        } catch (e) {
          console.error(e)
        }
      }
    })
  }
})