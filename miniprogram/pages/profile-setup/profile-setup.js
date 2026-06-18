const api = require('../../utils/api.js')
const app = getApp()

Page({
  data: {
    nickname: '',
    nicknameFocus: false,   // 自动聚焦昵称框，唤起微信"使用微信昵称"建议条
    avatarLocalPath: '',   // 用户选完后本地的临时路径（用于即时预览）
    avatarUrl: '',          // 上传后端后拿到的 URL（保存到 userinfo）
    saving: false
  },

  onLoad(options) {
    // 如果有传入 nickname（从 my 页面编辑入口来的），用之
    if (options && options.nickname) {
      this.setData({ nickname: decodeURIComponent(options.nickname) })
    }
  },

  onReady() {
    // 必须在 onReady 之后再设 focus —— onLoad 时元素还没渲染
    // 没预填昵称时才自动聚焦（避免编辑入口进来又强弹建议条打扰）
    if (!this.data.nickname) {
      this.setData({ nicknameFocus: true })
    }
  },

  onNicknameInput(e) {
    this.setData({ nickname: e.detail.value || '' })
  },

  // 微信 chooseAvatar 回调：用户选了头像
  onChooseAvatar(e) {
    const tempFilePath = e.detail.avatarUrl
    this.setData({ avatarLocalPath: tempFilePath })
    // 立即上传到后端
    api.uploadAvatar(tempFilePath).then(res => {
      if (res && res.code === 0) {
        this.setData({ avatarUrl: res.data.avatar_url })
      }
    }).catch(err => {
      wx.showToast({ title: err.message || '上传失败', icon: 'none' })
    })
  },

  onSave() {
    if (!this.data.nickname || !this.data.nickname.trim()) {
      wx.showToast({ title: '昵称不能为空', icon: 'none' })
      return
    }
    if (this.data.saving) return
    this.setData({ saving: true })

    // payload：nickname 必有；avatar_url 选了就有，没选就不传（保留之前的）
    const payload = { nickname: this.data.nickname.trim() }
    if (this.data.avatarUrl) {
      payload.avatar_url = this.data.avatarUrl
    }

    api.updateProfile(payload).then(res => {
      // 同步更新 globalData.userinfo
      if (app && app.globalData) {
        const userinfo = app.globalData.userinfo || {}
        app.globalData.userinfo = {
          ...userinfo,
          nickname: res.nickname || payload.nickname,
          avatar_url: res.avatar_url !== undefined ? res.avatar_url : userinfo.avatar_url
        }
        wx.setStorageSync('userinfo', app.globalData.userinfo)
      }
      wx.showToast({ title: '已保存', icon: 'success' })
      setTimeout(() => this._goNext(), 600)
    }).catch(e => {
      const msg = (e && e.message) || '保存失败'
      wx.showToast({ title: msg, icon: 'none' })
      this.setData({ saving: false })
    })
  },

  onSkip() {
    this._goNext()
  },

  _goNext() {
    wx.reLaunch({ url: '/pages/index/index' })
  }
})