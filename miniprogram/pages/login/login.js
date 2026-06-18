const api = require('../../utils/api.js')
const app = getApp()

Page({
  data: {
    loading: false
  },

  onWechatLogin() {
    if (this.data.loading) return
    this.setData({ loading: true })

    const fail = (msg) => {
      this.setData({ loading: false })
      wx.showToast({ title: msg, icon: 'none' })
      console.error('[wechatLogin]', msg)
    }
    const timer = setTimeout(() => fail('登录超时，请重试'), 8000)

    wx.login({
      success: async (res) => {
        if (!res.code) {
          clearTimeout(timer)
          fail('wx.login 未返回 code')
          return
        }
        try {
          const data = await api.wechatLogin(res.code)
          if (!data || !data.token) {
            clearTimeout(timer)
            fail('后端未返回 token')
            return
          }
          app.globalData.token = data.token
          app.globalData.userinfo = data.userinfo
          wx.setStorageSync('token', data.token)
          wx.setStorageSync('userinfo', data.userinfo)
          clearTimeout(timer)
          this.setData({ loading: false })

          // #C 决策：默认用户名 → 跳 profile-setup；否则直接进账本
          // 后端 getUserinfo 已返 is_default_username 字段（参考 auth.py）
          if (data.userinfo && data.userinfo.is_default_username) {
            wx.reLaunch({ url: '/pages/profile-setup/profile-setup' })
          } else {
            wx.switchTab({ url: '/pages/index/index' })
          }
        } catch (e) {
          clearTimeout(timer)
          fail(`登录失败: ${e.message || JSON.stringify(e)}`)
        }
      },
      fail: (err) => {
        clearTimeout(timer)
        fail(`wx.login 失败: ${err.errMsg}`)
      }
    })
  }
})
