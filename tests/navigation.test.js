// Tests for #5: 页面切换动效 (navigation.js)
const {
  describe, it, assertEqual, assertTruthy, assertFalsy, assertMatch
} = require('./runner')

// 每次测试前重置 wx mock
function setupWx() {
  const calls = { switchTab: [], navigateTo: [], redirectTo: [], reLaunch: [] }
  global.wx = {
    switchTab: (opts) => calls.switchTab.push(opts),
    navigateTo: (opts) => calls.navigateTo.push(opts),
    redirectTo: (opts) => calls.redirectTo.push(opts),
    reLaunch: (opts) => calls.reLaunch.push(opts)
  }
  return calls
}

// 测试 #5: 页面切换工具
describe('#5 navTo - 页面切换动效', () => {
  // 延迟 require，让测试能 fail-on-first-run（如果模块不存在）
  let navTo
  try {
    navTo = require('../miniprogram/utils/navigation').navTo
  } catch (e) {
    // 模块还不存在，测试会全部 fail
    navTo = () => { throw new Error('navigation.js not implemented yet') }
  }

  it('navTo 应该是一个函数', () => {
    assertEqual(typeof navTo, 'function', 'navTo must be a function')
  })

  it('tab 页应该用 wx.switchTab', () => {
    const calls = setupWx()
    navTo('/pages/index/index')
    assertEqual(calls.switchTab.length, 1)
    assertEqual(calls.switchTab[0].url, '/pages/index/index')
    assertEqual(calls.navigateTo.length, 0)
  })

  it('非 tab 页应该用 wx.navigateTo', () => {
    const calls = setupWx()
    navTo('/pages/trash/trash')
    assertEqual(calls.navigateTo.length, 1)
    assertEqual(calls.navigateTo[0].url, '/pages/trash/trash')
    assertEqual(calls.switchTab.length, 0)
  })

  it('应该支持 slide-up 动画', () => {
    const calls = setupWx()
    navTo('/pages/budget/budget', { animation: 'slide-up' })
    assertEqual(calls.navigateTo[0].animationType, 'slide-up')
  })

  it('应该支持 fade 动画', () => {
    const calls = setupWx()
    navTo('/pages/edit/edit', { animation: 'fade' })
    assertEqual(calls.navigateTo[0].animationType, 'fade')
  })

  it('不传动画时不应该有 animationType 字段', () => {
    const calls = setupWx()
    navTo('/pages/edit/edit')
    assertFalsy(calls.navigateTo[0].animationType, '默认不应有动画')
  })

  it('应该支持 success 回调', () => {
    const calls = setupWx()
    let successCalled = false
    navTo('/pages/edit/edit', { success: () => { successCalled = true } })
    if (calls.navigateTo[0].success) calls.navigateTo[0].success()
    assertTruthy(successCalled, 'success 回调应被调用')
  })

  it('应该支持 fail 回调', () => {
    const calls = setupWx()
    // simulate wx failure
    const origNav = global.wx.navigateTo
    global.wx.navigateTo = () => { throw new Error('fail') }
    let failCalled = false
    navTo('/pages/edit/edit', { fail: () => { failCalled = true } })
    assertTruthy(failCalled, 'fail 回调应被调用')
    global.wx.navigateTo = origNav
  })

  it('合法动画类型: slide-up / fade / slide-left / slide-right / pop-in', () => {
    const calls = setupWx()
    const validTypes = ['slide-up', 'fade', 'slide-left', 'slide-right', 'pop-in']
    for (const t of validTypes) {
      navTo('/pages/edit/edit', { animation: t })
      assertEqual(calls.navigateTo[calls.navigateTo.length - 1].animationType, t)
    }
  })

  it('非法动画类型应该被忽略（不传 animationType）', () => {
    const calls = setupWx()
    navTo('/pages/edit/edit', { animation: 'invalid-type' })
    assertFalsy(calls.navigateTo[0].animationType, '非法 animation 应忽略')
  })
})