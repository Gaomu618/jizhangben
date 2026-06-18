// 不在顶层调 getApp()，让 Node 测试环境能 require
// 关键：wrapper 不能叫 getApp —— 会遮蔽小程序的全局 getApp()，整个文件再也拿不到 App 实例
// 而且小程序里没有 wx.getApp，只有全局 getApp()
function _app() {
  // 小程序运行时：全局 getApp() 是函数（这里不会撞 local 定义，因为本函数叫 _app）
  if (typeof getApp === 'function') return getApp()
  // Node 测试环境：允许通过 global.getApp 注入 mock
  if (typeof global !== 'undefined' && global.getApp) return global.getApp()
  return null
}

// Fallback：app.globalData.baseUrl 缺失时用这个（与 app.js 同步）
const FALLBACK_BASE_URL = 'https://cradle-sustained-suds.ngrok-free.dev'

function request(options) {
  return new Promise((resolve, reject) => {
    const app = _app()
    // token 优先级：globalData → storage（兜底：onLaunch 之外的 getApp() 可能拿不到最新 globalData）
    let token = (app && app.globalData && app.globalData.token) || ''
    if (!token) {
      try { token = wx.getStorageSync('token') || '' } catch (e) { /* ignore */ }
    }
    // baseUrl 必须有值；空字符串 fallback 到默认（避免 url 拼出 "/api/..." 相对路径）
    const baseUrl = (app && app.globalData && app.globalData.baseUrl) || FALLBACK_BASE_URL

    wx.request({
      url: baseUrl + options.url,
      method: options.method || 'GET',
      data: options.data || {},
      header: {
        'Content-Type': 'application/json',
        'Authorization': token ? `Bearer ${token}` : '',
        // ngrok 免费版：浏览器 UA 会被拦截返回 ERR_NGROK_6024 HTML 提示页
        // 加这个头告诉 ngrok 这是 API 请求，直接代理
        'ngrok-skip-browser-warning': 'true'
      },
      success: (res) => {
        if (res.data.code === 0) {
          // 成功：如果是 wechatLogin / login，把 token+userinfo 持久化
          if (res.data.data && res.data.data.token) {
            const { token, userinfo } = res.data.data
            app.globalData.token = token
            app.globalData.userinfo = userinfo
            wx.setStorageSync('token', token)
            if (userinfo) wx.setStorageSync('userinfo', userinfo)
          }
          resolve(res.data.data)
        } else if (res.data.code === 401 || res.data.code === 1001 || res.data.code === 1002) {
          // 后端 login_required 装饰器返回 401；1001/1002 保留兼容
          wx.removeStorageSync('token')
          wx.removeStorageSync('userinfo')
          app.globalData.token = ''
          app.globalData.userinfo = null
          wx.reLaunch({ url: '/pages/login/login' })
          reject(res.data)
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
  wechatLogin: (code) => request({ url: '/api/auth/wechat/login', method: 'POST', data: { code } }),
  login: (username, password) => request({ url: '/api/auth/login', method: 'POST', data: { username, password } }),
  logout: () => request({ url: '/api/auth/logout', method: 'POST' }),
  getUserinfo: () => request({ url: '/api/auth/userinfo' }),
  // 更新用户昵称/头像（Phase C: 自填资料）
  updateProfile: (data) => request({ url: '/api/auth/profile', method: 'PUT', data }),
  // 上传头像（multipart, 走 wx.uploadFile）
  uploadAvatar: (filePath) => new Promise((resolve, reject) => {
    const a = _app()
    const baseUrl = (a && a.globalData && a.globalData.baseUrl) || FALLBACK_BASE_URL
    const token = (a && a.globalData && a.globalData.token) || ''
    wx.uploadFile({
      url: baseUrl + '/api/auth/avatar',
      filePath,
      name: 'file',
      header: {
        'Authorization': `Bearer ${token}`,
        'ngrok-skip-browser-warning': 'true'
      },
      success: (res) => {
        try { resolve(JSON.parse(res.data)) } catch (e) { reject(new Error('响应解析失败')) }
      },
      fail: (err) => reject(new Error(err.errMsg || '上传失败'))
    })
  }),

  getBillList: (params) => request({ url: '/api/bill/list', data: params }),
  getBillDetail: (id) => request({ url: `/api/bill/${id}` }),
  addBill: (data) => request({ url: '/api/bill/add', method: 'POST', data }),
  editBill: (id, data) => request({ url: `/api/bill/edit/${id}`, method: 'POST', data }),
  deleteBill: (id) => request({ url: `/api/bill/delete/${id}`, method: 'POST' }),

  // 智能分类：根据备注文本返回 { category, type, confidence, matched }
  classifyText: (text) => request({ url: '/api/bill/classify', method: 'POST', data: { text } }),

  getMonthlyStats: (year, month) => request({ url: '/api/stats/monthly', data: { year, month } }),
  getCategoryStats: (year, month) => request({ url: '/api/stats/category', data: { year, month } }),
  // 别名：stats 页用，参数风格更灵活（接受 { start, end } 范围）
  getCategory: (params) => request({ url: '/api/stats/category', data: params }),

  // 回收站
  getTrash: (params) => request({ url: '/api/bill/trash', data: params }),
  getTrashCount: () => request({ url: '/api/bill/trash/count' }),
  restore: (id) => request({ url: `/api/bill/restore/${id}`, method: 'POST' }),
  purge: (id) => request({ url: `/api/bill/purge/${id}`, method: 'POST' }),
  emptyTrash: () => request({ url: '/api/bill/trash/empty', method: 'POST' }),
  restoreBatchTrash: (ids) => request({ url: '/api/bill/trash/restore-batch', method: 'POST', data: { ids } }),

  // 预算
  getBudget: (params) => request({ url: '/api/bill/budget', data: params }),
  setBudget: (data) => request({ url: '/api/bill/budget', method: 'POST', data }),
  deleteBudget: (data) => request({ url: '/api/bill/delete-budget', method: 'POST', data }),

  // 通知提醒检查（首页加载时调一次，触发本地弹窗 + 订阅消息）
  checkNotifications: (data = {}) => request({ url: '/api/notification/check', method: 'POST', data }),

  // 统计扩展
  getSummary: (params) => request({ url: '/api/stats/summary', data: params }),
  getDaily: (params) => request({ url: '/api/stats/daily', data: params }),
  getTrend: (params) => request({ url: '/api/stats/trend', data: params }),
  getTop: (params) => request({ url: '/api/stats/top', data: params }),

  // 导出：binary blob → 写文件 → 返回 filePath
  exportFile: (format = 'csv') => new Promise((resolve, reject) => {
    const app = _app()
    const baseUrl = (app && app.globalData && app.globalData.baseUrl) || FALLBACK_BASE_URL
    const token = (app && app.globalData && app.globalData.token) || ''
    wx.request({
      url: baseUrl + `/api/bill/export?format=${format}`,
      method: 'GET',
      responseType: 'arraybuffer',
      header: {
        'Authorization': `Bearer ${token}`,
        'ngrok-skip-browser-warning': 'true'
      },
      success: (res) => {
        if (res.statusCode === 200) {
          const fsm = wx.getFileSystemManager()
          const filePath = `${wx.env.USER_DATA_PATH}/账单记录.${format}`
          fsm.writeFile({
            filePath,
            data: res.data,
            encoding: 'binary',
            success: () => resolve({ filePath, filename: `账单记录.${format}` }),
            fail: (e) => reject(new Error(e.errMsg || '写入失败'))
          })
        } else {
          reject(new Error(`HTTP ${res.statusCode}`))
        }
      },
      fail: (err) => reject(new Error(err.errMsg || '网络错误'))
    })
  }),

  // 导入：multipart upload，dry_run 模式可预览
  importFile: (filePath, dryRun = false) => new Promise((resolve, reject) => {
    const app = _app()
    const baseUrl = (app && app.globalData && app.globalData.baseUrl) || FALLBACK_BASE_URL
    const token = (app && app.globalData && app.globalData.token) || ''
    wx.uploadFile({
      url: baseUrl + '/api/bill/import',
      filePath,
      name: 'file',
      formData: { dry_run: dryRun ? 'true' : 'false' },
      header: {
        'Authorization': `Bearer ${token}`,
        'ngrok-skip-browser-warning': 'true'
      },
      success: (res) => {
        try {
          const data = JSON.parse(res.data)
          resolve(data)
        } catch (e) {
          reject(new Error('响应解析失败'))
        }
      },
      fail: (err) => reject(new Error(err.errMsg || '上传失败'))
    })
  })
}
