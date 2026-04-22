const app = getApp()

function request(options) {
  return new Promise((resolve, reject) => {
    const token = app.globalData.token

    wx.request({
      url: app.globalData.baseUrl + options.url,
      method: options.method || 'GET',
      data: options.data || {},
      header: {
        'Content-Type': 'application/json',
        'Authorization': token ? `Bearer ${token}` : ''
      },
      success: (res) => {
        if (res.data.code === 0) {
          resolve(res.data.data)
        } else if (res.data.code === 1001 || res.data.code === 1002) {
          wx.removeStorageSync('token')
          wx.removeStorageSync('userinfo')
          app.globalData.token = ''
          app.globalData.userinfo = null
          wx.reLaunch({ url: '/pages/login/login' })
        } else {
          wx.showToast({ title: res.data.message, icon: 'none' })
          reject(res.data)
        }
      },
      fail: (err) => {
        wx.showToast({ title: '网络请求失败', icon: 'none' })
        reject(err)
      }
    })
  })
}

module.exports = {
  wechatLogin: (code) => request({ url: '/auth/wechat/login', method: 'POST', data: { code } }),
  login: (username, password) => request({ url: '/auth/login', method: 'POST', data: { username, password } }),
  logout: () => request({ url: '/auth/logout', method: 'POST' }),
  getUserinfo: () => request({ url: '/auth/userinfo' }),

  getBillList: (params) => request({ url: '/bill/list', data: params }),
  getBillDetail: (id) => request({ url: `/bill/${id}` }),
  addBill: (data) => request({ url: '/bill/add', method: 'POST', data }),
  editBill: (id, data) => request({ url: `/bill/edit/${id}`, method: 'POST', data }),
  deleteBill: (id) => request({ url: `/bill/delete/${id}`, method: 'POST' }),

  getMonthlyStats: (year, month) => request({ url: '/stats/monthly', data: { year, month } }),
  getCategoryStats: (year, month) => request({ url: '/stats/category', data: { year, month } })
}