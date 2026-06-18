const api = require('../../utils/api.js')
const app = getApp()
const { navTo, reLaunch } = require('../../utils/navigation')

// 头像：优先用后端存的 URL（http(s) 或 /uploads/avatars/xxx.png 本地路径）
// avatar_url 以 / 开头 → 相对路径，前端拼 baseUrl；否则 http(s) URL 直接用
function pickAvatarUrl(userinfo, baseUrl) {
  if (!userinfo || !userinfo.avatar_url) return ''
  const url = userinfo.avatar_url
  if (url.startsWith('/')) return (baseUrl || '') + url
  return url  // 完整 http(s) URL
}

// 头像回落：nickname/username 首字母
function pickAvatarInitial(userinfo) {
  if (!userinfo) return '微'
  const name = userinfo.nickname || userinfo.username || '微'
  return name.charAt(0)
}

// 显示名：优先 nickname → username → 微信用户
function pickDisplayName(userinfo) {
  if (!userinfo) return '微信用户'
  if (userinfo.nickname) return userinfo.nickname
  if (userinfo.username) return userinfo.username
  return '微信用户'
}

Page({
  data: {
    username: '微信用户',
    initial: '微',
    displayName: '微信用户',
    avatarUrl: '',
    avatarInitial: '微',
    displaySubtext: '点此编辑资料',
    avatarLoadFailed: false,
    trashCount: 0,
    importing: false
  },

  onShow() {
    this._refreshUserInfo()
    // custom tabBar 同步选中态
    if (typeof this.getTabBar === 'function' && this.getTabBar()) {
      this.getTabBar().setData({ selected: 2 })
    }
    // 刷新回收站角标
    this.refreshTrashCount()
  },

  _refreshUserInfo() {
    const userinfo = app.globalData.userinfo
    const baseUrl = (app && app.globalData && app.globalData.baseUrl) || ''
    const url = pickAvatarUrl(userinfo, baseUrl)
    this.setData({
      username: (userinfo && userinfo.username) || '微信用户',
      initial: pickAvatarInitial(userinfo),
      displayName: pickDisplayName(userinfo),
      avatarUrl: this.data.avatarLoadFailed ? '' : url,
      avatarInitial: pickAvatarInitial(userinfo),
      displaySubtext: url ? '已设置头像 · 点此编辑' : '点此编辑资料'
    })
  },

  // 头像加载失败（URL 失效）→ 回退首字母
  onAvatarError() {
    this.setData({ avatarLoadFailed: true, avatarUrl: '' })
  },

  onEditProfile() {
    // 跳到资料编辑页（带预填昵称）
    const userinfo = app.globalData.userinfo
    const nickname = (userinfo && userinfo.nickname) || ''
    navTo(`/pages/profile-setup/profile-setup?nickname=${encodeURIComponent(nickname)}`)
  },

  async refreshTrashCount() {
    try {
      const res = await api.getTrashCount()
      const count = res.count || 0
      this.setData({ trashCount: count })
      app.globalData.trashCount = count
    } catch (e) {
      // 静默
    }
  },

  onOpenTrash() {
    // #5 页面切换：统一 navTo（带 slide-up 动画 + 失败回调）
    navTo('/pages/trash/trash', {
      animation: 'slide-up',
      fail: () => wx.showToast({ title: '无法打开', icon: 'none' })
    })
  },

  onOpenBudget() {
    navTo('/pages/budget/budget', { animation: 'slide-up' })
  },

  // ====== 导入 ======
  onImport() {
    wx.chooseMessageFile({
      count: 1,
      type: 'file',
      extension: ['xlsx', 'xls', 'csv']
    }).then(res => {
      const file = res.tempFiles[0]
      this._previewImport(file.path, file.name)
    }).catch(() => { /* 用户取消 */ })
  },

  async _previewImport(filePath, fileName) {
    this.setData({ importing: true })
    try {
      // 先 dry run 看预览
      const dry = await api.importFile(filePath, true)
      if (dry.code !== 0) {
        wx.showToast({ title: dry.message || '预览失败', icon: 'none' })
        return
      }
      const { preview, total } = dry.data || {}
      const previewCount = (preview || []).length
      const confirmed = await new Promise(r => {
        wx.showModal({
          title: `预览（前 ${previewCount} / 共 ${total || 0} 条）`,
          content: `文件：${fileName}\n\n确认导入这些记录吗？`,
          success: m => r(m.confirm)
        })
      })
      if (!confirmed) return
      // 正式导入
      const final = await api.importFile(filePath, false)
      if (final.code === 0) {
        const imported = (final.data && final.data.imported) || 0
        wx.showToast({ title: `已导入 ${imported} 条`, icon: 'success' })
      } else {
        wx.showToast({ title: final.message || '导入失败', icon: 'none' })
      }
    } catch (e) {
      wx.showToast({ title: e.message || '导入失败', icon: 'none' })
    } finally {
      this.setData({ importing: false })
    }
  },

  // ====== 导出 ======
  onExport() {
    // 用 success/fail 回调而不是 .then().catch()，
    // 因为 WeChat 在用户取消 ActionSheet 时会 console.error 一行
    // （即使 catch 也会打），用回调可以在 fail 里识别 cancel 并静默
    wx.showActionSheet({
      itemList: ['Excel (.xlsx)', 'CSV', 'PDF'],
      success: (res) => {
        const formats = ['xlsx', 'csv', 'pdf']
        this._doExport(formats[res.tapIndex])
      },
      fail: (err) => {
        // 用户主动取消（errMsg 含 "cancel"）→ 静默；其他错误才提示
        if (err && err.errMsg && !err.errMsg.includes('cancel')) {
          wx.showToast({ title: '操作失败', icon: 'none' })
        }
      }
    })
  },

  async _doExport(format) {
    wx.showLoading({ title: '正在导出…' })
    try {
      const { filePath } = await api.exportFile(format)
      wx.hideLoading()
      await new Promise((resolve, reject) => {
        wx.openDocument({
          filePath,
          fileType: format,
          showMenu: true,
          success: resolve,
          fail: reject
        })
      })
      wx.showToast({ title: '已导出', icon: 'success' })
    } catch (e) {
      wx.hideLoading()
      wx.showToast({ title: e.message || '导出失败', icon: 'none' })
    }
  },

  onAbout() {
    wx.showModal({
      title: '个人记账',
      content: '简洁的个人记账工具\n\nv0.2.0 · Phase 2 重做版',
      showCancel: false
    })
  },

  onClearCache() {
    wx.showModal({
      title: '清除缓存',
      content: '会清除账单列表缓存，不影响账本数据',
      success: (res) => {
        if (res.confirm) {
          wx.showToast({ title: '已清除', icon: 'success' })
        }
      }
    })
  },

  onLogout() {
    wx.showModal({
      title: '确认退出',
      content: '确定要退出登录吗？',
      confirmText: '退出',
      confirmColor: '#d94f1e',
      success: async (res) => {
        if (res.confirm) {
          try { await api.logout() } catch (e) {}
          wx.removeStorageSync('token')
          wx.removeStorageSync('userinfo')
          app.globalData.token = ''
          app.globalData.userinfo = null
          reLaunch('/pages/login/login')  // #5 统一 reLaunch
        }
      }
    })
  }
})
