// #5 页面切换动效
// 统一封装，避免每个页面重复写 wx.navigateTo / wx.switchTab / wx.redirectTo
// 用法:
//   import { navTo } from '../../utils/navigation'
//   import { VALID_ANIMATION_TYPES } from '../../utils/motion'

const { VALID_ANIMATION_TYPES } = require('./motion')

// 当前 app.json 的 tabBar.list 路径（硬编码或从 app.json 动态读）
// 注意：必须与 miniprogram/app.json 的 tabBar.list 保持一致
const TAB_PAGES = new Set([
  'pages/index/index',
  'pages/stats/stats',
  'pages/mine/mine'
])

/**
 * 判断一个路径是否是 tab 页
 * @param {string} url - '/pages/index/index' 形式
 */
function isTabPage(url) {
  if (!url) return false
  // url 可能是 '/pages/...' 或 'pages/...'，归一化
  const normalized = url.replace(/^\//, '')
  return TAB_PAGES.has(normalized)
}

/**
 * 智能页面跳转
 * - tab 页自动用 switchTab
 * - 非 tab 页用 navigateTo
 * - 可选动画类型
 *
 * @param {string} url - 目标路径，如 '/pages/trash/trash'
 * @param {object} [opts] - { animation, success, fail }
 * @returns {Promise}
 */
function navTo(url, opts = {}) {
  if (!url || typeof url !== 'string') {
    console.warn('[navTo] url is required')
    return Promise.reject(new Error('url is required'))
  }

  // 验证 animationType（白名单）
  let animationType = opts.animation
  if (animationType && !VALID_ANIMATION_TYPES.has(animationType)) {
    console.warn(`[navTo] invalid animation "${animationType}", ignored`)
    animationType = undefined
  }

  const baseOpts = { url }
  if (animationType) baseOpts.animationType = animationType
  if (opts.success) baseOpts.success = opts.success
  if (opts.fail) baseOpts.fail = opts.fail

  return new Promise((resolve, reject) => {
    const finalOpts = {
      ...baseOpts,
      success: (res) => {
        if (opts.success) opts.success(res)
        resolve(res)
      },
      fail: (err) => {
        if (opts.fail) opts.fail(err)
        reject(err)
      }
    }
    // wx 调用可能同步抛错（如测试 mock），用 try/catch 包住
    try {
      if (isTabPage(url)) {
        wx.switchTab(finalOpts)
      } else {
        wx.navigateTo(finalOpts)
      }
    } catch (err) {
      // 同步抛错：走 fail 路径
      if (opts.fail) opts.fail(err)
      reject(err)
    }
  })
}

/**
 * 关闭当前页，跳转到目标（不能跳 tab）
 */
function redirectTo(url, opts = {}) {
  if (!url) return Promise.reject(new Error('url is required'))
  let animationType = opts.animation
  if (animationType && !VALID_ANIMATION_TYPES.has(animationType)) {
    animationType = undefined
  }
  return new Promise((resolve, reject) => {
    wx.redirectTo({
      url,
      animationType,
      success: (res) => { if (opts.success) opts.success(res); resolve(res) },
      fail: (err) => { if (opts.fail) opts.fail(err); reject(err) }
    })
  })
}

/**
 * 关闭所有页，打开新页（通常用于登录、退出）
 */
function reLaunch(url) {
  return new Promise((resolve, reject) => {
    wx.reLaunch({
      url,
      success: resolve,
      fail: reject
    })
  })
}

module.exports = {
  navTo,
  redirectTo,
  reLaunch,
  isTabPage,
  TAB_PAGES
}