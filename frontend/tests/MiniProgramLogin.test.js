/**
 * 小程序登录流端到端测试
 *
 * 测试目的：模拟 wx.login + wx.request 完整流，验证 miniprogram/utils/api.js
 * 真的能：① 调后端 wechat_login 拿 token ② 把 token 存到 wx.setStorage ③ 用
 * token 调受保护 API 拿数据。
 *
 * 设计：mock wx.request 返回合成响应（不依赖真实后端）—— 这样测试不依赖
 * 真实 Flask 后端 / MySQL / 微信 API，CI 上能直接跑。
 *
 * 真实后端契约已经在 tests/test_wechat_login.py 里测了（mock 微信 API 调真实 Flask）。
 * 本文件只测前端 api.js 的行为（URL 拼接、token 注入、错误处理、storage 清理）。
 */
function createMockWx() {
  const storage = {}
  return {
    request: vi.fn(({ url, method, data, header, success, fail }) => {
      // 合成后端响应（不调真实网络）
      const fullUrl = url
      const code = (data && data.code) || ''

      let response = { code: 1004, message: 'mock: unknown endpoint', data: null }

      // wechatLogin 路径
      if (url.endsWith('/api/auth/wechat/login') && method === 'POST') {
        if (code.startsWith('mock_')) {
          response = {
            code: 0,
            data: {
              token: 'mock_token_64_chars_' + 'x'.repeat(40),
              userinfo: { id: 1234, username: 'wx_user', openid: 'fake_openid_' + code },
            },
            message: 'success',
          }
        } else if (code === 'invalid') {
          response = { code: 1004, message: 'invalid code', data: null }
        }
      }
      // bill list 路径
      else if (url.endsWith('/api/bill/list') || url.endsWith('/api/bill/list?year=2026&month=6')) {
        const auth = (header && header.Authorization) || ''
        if (auth.startsWith('Bearer ')) {
          response = {
            code: 0,
            data: { list: [{ id: 1, category: '餐饮', amount: 100 }], total: 1, page: 1, total_pages: 1 },
            message: 'success',
          }
        } else {
          // 模拟 401：后端 login_required 装饰器
          response = { code: 401, message: '请先登录', data: null }
        }
      }
      // userinfo 路径
      else if (url.endsWith('/api/auth/userinfo')) {
        const auth = (header && header.Authorization) || ''
        if (auth.startsWith('Bearer ')) {
          response = { code: 0, data: { id: 1234, username: 'wx_user' }, message: 'success' }
        } else {
          response = { code: 401, message: '请先登录', data: null }
        }
      }

      // 模拟 wx.request 异步回调
      setTimeout(() => success({ data: response }), 0)
    }),
    setStorageSync: vi.fn((key, val) => { storage[key] = val }),
    getStorageSync: vi.fn((key) => storage[key]),
    removeStorageSync: vi.fn((key) => { delete storage[key] }),
    showToast: vi.fn(),
    reLaunch: vi.fn(),
    login: vi.fn(({ success }) => {
      setTimeout(() => success({ code: 'mock_wx_login_code_123' }), 0)
    }),
    _storage: storage,
  }
}

describe('小程序登录流（mock wx + 合成后端响应）', () => {
  let mockWx, mockApp

  beforeEach(() => {
    vi.resetModules()
    mockWx = createMockWx()
    globalThis.wx = mockWx
    mockApp = {
      globalData: {
        token: '',
        userinfo: null,
        baseUrl: 'http://mock.host',  // 不实际调，mock request 拦
      },
    }
    globalThis.getApp = () => mockApp
  })

  afterEach(() => {
    delete globalThis.wx
    delete globalThis.getApp
  })

  it('1) wechatLogin → 后端返回 token → 存到 wx.setStorage + app.globalData', async () => {
    const apiMod = await import('../../miniprogram/utils/api.js')

    const data = await apiMod.wechatLogin('mock_wx_login_code_123')

    expect(data).toBeDefined()
    expect(data.token).toBeDefined()
    expect(data.token.length).toBeGreaterThanOrEqual(32)
    expect(data.userinfo.id).toBeGreaterThan(0)
    expect(data.userinfo.openid).toBeDefined()

    // token 真存到 wx.setStorageSync
    expect(mockWx.setStorageSync).toHaveBeenCalledWith('token', data.token)
    expect(mockWx.setStorageSync).toHaveBeenCalledWith('userinfo', data.userinfo)
    // token 也存到 app.globalData（接口契约）
    expect(mockApp.globalData.token).toBe(data.token)
    expect(mockApp.globalData.userinfo).toEqual(data.userinfo)

    console.log(`  ✓ 登录后 token=${data.token.slice(0,8)}... user_id=${data.userinfo.id}`)
  })

  it('2) 登录后用 token 调受保护 API 真的能拿数据', async () => {
    const apiMod = await import('../../miniprogram/utils/api.js')

    const loginData = await apiMod.wechatLogin('mock_code_xyz')
    expect(loginData.token).toBeDefined()

    // 调 bill list — 模拟 request 抓到调用
    const callsBefore = mockWx.request.mock.calls.length
    await apiMod.getBillList({ year: 2026, month: 6 })
    const lastCall = mockWx.request.mock.calls[callsBefore]
    const reqOptions = lastCall[0]

    // URL 路径必须含 /api/bill/list
    expect(reqOptions.url).toContain('/api/bill/list')
    // GET 方法（默认）
    expect(reqOptions.method || 'GET').toBe('GET')
    // Authorization 头带 Bearer token
    expect(reqOptions.header.Authorization).toBe(`Bearer ${loginData.token}`)

    console.log(`  ✓ 调 /api/bill/list 带 Bearer ${loginData.token.slice(0,8)}...`)
  })

  it('3) 后端返回 401 → 触发清理 + 跳登录页', async () => {
    const apiMod = await import('../../miniprogram/utils/api.js')

    // 不登录直接调受保护 API → 后端 mock 返回 401
    try {
      await apiMod.getBillList({ year: 2026, month: 6 })
      throw new Error('应 reject')
    } catch (e) {
      // 应触发清理
      expect(mockWx.removeStorageSync).toHaveBeenCalledWith('token')
      expect(mockWx.removeStorageSync).toHaveBeenCalledWith('userinfo')
      expect(mockApp.globalData.token).toBe('')
      expect(mockApp.globalData.userinfo).toBeNull()
      // 应跳登录页
      expect(mockWx.reLaunch).toHaveBeenCalledWith({ url: '/pages/login/login' })
    }

    console.log(`  ✓ 401 → 清 storage + 跳 /pages/login/login`)
  })

  it('4) API URL 路径以 /api/ 开头（不是 /auth/ 这种裸路径）', async () => {
    const apiMod = await import('../../miniprogram/utils/api.js')

    await apiMod.wechatLogin('mock_code_xyz')
    const reqOptions = mockWx.request.mock.calls[0][0]
    // 关键：前端要拼 /api 前缀，否则 404
    expect(reqOptions.url).toContain('/api/auth/wechat/login')
    // 同时验证其他 endpoint 也带 /api/
    await apiMod.getUserinfo()
    const lastCall = mockWx.request.mock.calls[mockWx.request.mock.calls.length - 1][0]
    expect(lastCall.url).toContain('/api/auth/userinfo')

    console.log(`  ✓ 所有 URL 含 /api/ 前缀`)
  })
})
