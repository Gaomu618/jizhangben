// Tests for #C profile frontend integration
// - api.updateProfile 调用 PUT /api/auth/profile
// - 头像/昵称在前端能正常显示（用 emoji 简化）
// - 登录后判断 is_default_username → 跳 profile-setup
const {
  describe, it, assertEqual, assertTruthy, assertFalsy, assertMatch
} = require('./runner')

// ============ api.updateProfile ============
describe('api.updateProfile', () => {
  let api
  try {
    api = require('../miniprogram/utils/api.js')
  } catch (e) {
    api = {}
  }

  it('应该是 api 模块的一个方法', () => {
    assertEqual(typeof api.updateProfile, 'function', 'updateProfile 必须存在')
  })

  it('应该调用 PUT /api/auth/profile（method=PUT）', () => {
    let called = null
    global.wx = {
      request: (opts) => {
        called = opts
        // 模拟成功响应
        return {
          success: (cb) => cb({ data: { code: 0, data: { nickname: '张三' } } })
        }
      },
      getStorageSync: () => '',
      removeStorageSync: () => {}
    }
    global.getApp = () => ({ globalData: { token: 'tok', baseUrl: 'http://x' } })

    return api.updateProfile({ nickname: '张三', avatar_url: '🍜' }).then(() => {
      assertEqual(called.url, '/api/auth/profile')
      assertEqual(called.method, 'PUT')
      assertMatch(called.data, /nickname.*张三/)
    })
  })

  it('应该把 Authorization header 带上', () => {
    let called = null
    global.wx = {
      request: (opts) => { called = opts; return { success: () => {} } },
      getStorageSync: () => ''
    }
    global.getApp = () => ({ globalData: { token: 'my-jwt', baseUrl: 'http://x' } })
    return api.updateProfile({ nickname: 'x' }).then(() => {
      assertMatch(called.header.Authorization, /Bearer my-jwt/)
    })
  })

  it('应该把 nickname/avatar_url 原样传过去', () => {
    let sent
    global.wx = {
      request: (opts) => { sent = opts; return { success: () => {} } },
      getStorageSync: () => ''
    }
    global.getApp = () => ({ globalData: { token: '', baseUrl: '' } })
    return api.updateProfile({ nickname: '测试', avatar_url: '💰' }).then(() => {
      assertMatch(sent.data, /测试/)
      assertMatch(sent.data, /💰/)
    })
  })

  it('后端 400 错误应该 reject（不弹 toast，由调用方处理）', () => {
    global.wx = {
      request: (opts) => ({
        success: (cb) => cb({ data: { code: 1020, message: '昵称最多 20 个字符' } })
      }),
      getStorageSync: () => '',
      showToast: () => {}  // 不能调
    }
    global.getApp = () => ({ globalData: { token: 'tok', baseUrl: '' } })

    let rejected = false
    return api.updateProfile({ nickname: 'a'.repeat(25) })
      .then(() => { throw new Error('should not resolve') })
      .catch(err => { rejected = true; assertMatch(err.message, /20/) })
      .then(() => { assertTruthy(rejected, '应该被 reject') })
  })
})


// ============ avatar 渲染逻辑 ============
// 头像简化方案：avatar_url 字段直接存 emoji 字符
describe('Avatar 渲染（emoji 方案）', () => {
  // 纯函数：判断 avatar_url 是不是 emoji
  function isEmojiAvatar(avatarUrl) {
    if (!avatarUrl) return false
    // emoji 通常 1-4 字节 UTF-8，对应 1-2 个码点
    return /^[\u{1F000}-\u{1FFFF}\u{2600}-\u{27BF}]{1,4}$/u.test(avatarUrl)
  }

  it('emoji 头像应被识别', () => {
    assertTruthy(isEmojiAvatar('💰'))
    assertTruthy(isEmojiAvatar('🍜'))
    assertTruthy(isEmojiAvatar('💼'))
    assertTruthy(isEmojiAvatar('📈'))
  })

  it('空字符串和 http URL 不是 emoji 头像', () => {
    assertFalsy(isEmojiAvatar(''))
    assertFalsy(isEmojiAvatar(null))
    assertFalsy(isEmojiAvatar('https://x.com/a.jpg'))
    assertFalsy(isEmojiAvatar('plain text'))
  })
})


// ============ 登录后跳转逻辑 ============
describe('登录后跳转决策', () => {
  // 纯函数：根据 userinfo 决定跳哪里
  function getPostLoginRoute(userinfo) {
    if (!userinfo) return '/pages/login/login'
    // 简易判断：username 看起来像 wx_xxxx 默认格式 → 跳 profile-setup
    if (/^wx_[a-zA-Z0-9]{8}$/.test(userinfo.username || '')) {
      return '/pages/profile-setup/profile-setup'
    }
    return '/pages/index/index'
  }

  it('默认 wx_xxxx 用户名 → 跳 profile-setup', () => {
    assertEqual(
      getPostLoginRoute({ username: 'wx_a1b2c3d4' }),
      '/pages/profile-setup/profile-setup'
    )
  })

  it('真实用户名 → 跳账本', () => {
    assertEqual(
      getPostLoginRoute({ username: '张三' }),
      '/pages/index/index'
    )
    assertEqual(
      getPostLoginRoute({ username: 'budget_test' }),
      '/pages/index/index'
    )
  })

  it('空 userinfo → 跳登录', () => {
    assertEqual(getPostLoginRoute(null), '/pages/login/login')
    assertEqual(getPostLoginRoute(undefined), '/pages/login/login')
  })
})


// ============ 显示名称：优先 nickname 回落 username 回落 "微信用户" ============
describe('mine 页显示名', () => {
  // 纯函数：拿到 userinfo 返回 best display name
  function getDisplayName(userinfo) {
    if (!userinfo) return '微信用户'
    if (userinfo.nickname) return userinfo.nickname
    if (userinfo.username) return userinfo.username
    return '微信用户'
  }

  it('有 nickname → 用 nickname', () => {
    assertEqual(getDisplayName({ nickname: '测试昵称', username: 'budget_test' }), '测试昵称')
  })

  it('无 nickname 但有 username → 用 username', () => {
    assertEqual(getDisplayName({ username: 'budget_test' }), 'budget_test')
  })

  it('都没有 → 用 "微信用户" fallback', () => {
    assertEqual(getDisplayName({}), '微信用户')
    assertEqual(getDisplayName(null), '微信用户')
  })
})


// ============ 头像显示：nickname 首字母 + emoji fallback ============
describe('mine 页头像字符', () => {
  // 头像优先级：emoji avatar_url → nickname/username 首字母
  function getAvatarChar(userinfo) {
    if (!userinfo) return '微'
    if (userinfo.avatar_url && /[\u{1F000}-\u{1FFFF}\u{2600}-\u{27BF}]/u.test(userinfo.avatar_url)) {
      return userinfo.avatar_url
    }
    const name = userinfo.nickname || userinfo.username || '微'
    return name.charAt(0)
  }

  it('有 emoji avatar_url → 用 emoji', () => {
    assertEqual(getAvatarChar({ avatar_url: '💰', nickname: '张三' }), '💰')
  })

  it('无 emoji → 用 nickname 首字母', () => {
    assertEqual(getAvatarChar({ nickname: '张三' }), '张')
    assertEqual(getAvatarChar({ username: 'budget_test' }), 'b')
  })

  it('完全没数据 → 用 "微"', () => {
    assertEqual(getAvatarChar({}), '微')
    assertEqual(getAvatarChar(null), '微')
  })
})