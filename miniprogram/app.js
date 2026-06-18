App({
  globalData: {
    token: '',
    userinfo: null,
    baseUrl: 'https://cradle-sustained-suds.ngrok-free.dev'
  },
  onLaunch() {
    const token = wx.getStorageSync('token')
    const userinfo = wx.getStorageSync('userinfo')
    if (token && userinfo) {
      this.globalData.token = token
      this.globalData.userinfo = userinfo
    }
  }
})