// Tests for #4: 空状态/加载/错误统一组件 (base-empty-state.js)
const {
  describe, it, assertEqual, assertTruthy, assertFalsy, assertMatch, assertDeepEqual
} = require('./runner')

let createEmptyState, EMPTY_TYPES
try {
  const mod = require('../miniprogram/utils/empty-state.js')
  createEmptyState = mod.createEmptyState
  EMPTY_TYPES = mod.EMPTY_TYPES
} catch (e) {
  createEmptyState = () => { throw new Error('utils/empty-state.js not implemented') }
  EMPTY_TYPES = []
}

describe('#4 EMPTY_TYPES 枚举', () => {
  it('应该包含 4 种类型: loading/empty/error/no-permission', () => {
    assertEqual(EMPTY_TYPES.length, 4, '应有 4 种类型')
    assertTruthy(EMPTY_TYPES.includes('loading'))
    assertTruthy(EMPTY_TYPES.includes('empty'))
    assertTruthy(EMPTY_TYPES.includes('error'))
    assertTruthy(EMPTY_TYPES.includes('no-permission'))
  })
})

describe('#4 createEmptyState - loading', () => {
  it('应该有 loading 提示', () => {
    const s = createEmptyState('loading')
    assertTruthy(s.title, 'loading 应该有 title')
    assertMatch(s.title, /加载中|加载/)
  })

  it('不应该显示 CTA 按钮', () => {
    const s = createEmptyState('loading')
    assertFalsy(s.cta, 'loading 不应该有 cta')
  })

  it('应该默认有 loading icon', () => {
    const s = createEmptyState('loading')
    assertTruthy(s.icon, 'loading 应该默认有 icon')
  })
})

describe('#4 createEmptyState - empty', () => {
  it('应该有友好提示', () => {
    const s = createEmptyState('empty')
    assertTruthy(s.title)
    assertTruthy(s.message)
  })

  it('应该接受自定义 title 和 message', () => {
    const s = createEmptyState('empty', {
      title: '本月还没有账单',
      message: '记一笔吧'
    })
    assertEqual(s.title, '本月还没有账单')
    assertEqual(s.message, '记一笔吧')
  })

  it('应该默认有重试 CTA', () => {
    const s = createEmptyState('empty')
    assertTruthy(s.cta, 'empty 默认应有 cta')
    assertTruthy(s.cta.text)
    assertTruthy(s.cta.handler, 'cta 应有 handler')
  })

  it('CTA handler 应该是函数', () => {
    const s = createEmptyState('empty')
    assertEqual(typeof s.cta.handler, 'function')
  })

  it('可以禁用 CTA', () => {
    const s = createEmptyState('empty', { cta: null })
    assertFalsy(s.cta, 'cta: null 应禁用')
  })
})

describe('#4 createEmptyState - error', () => {
  it('默认显示"出错了"', () => {
    const s = createEmptyState('error')
    assertMatch(s.title, /错误|出错|失败/)
  })

  it('应该有"重试"按钮', () => {
    const s = createEmptyState('error')
    assertTruthy(s.cta, 'error 应有 cta')
    assertMatch(s.cta.text, /重试/)
  })

  it('应该接受自定义 error 消息', () => {
    const s = createEmptyState('error', { message: '网络断了' })
    assertEqual(s.message, '网络断了')
  })
})

describe('#4 createEmptyState - no-permission', () => {
  it('应该显示"无权限"提示', () => {
    const s = createEmptyState('no-permission')
    assertMatch(s.title, /权限|登录/)
  })

  it('应该有"去登录"按钮', () => {
    const s = createEmptyState('no-permission')
    assertTruthy(s.cta)
    assertMatch(s.cta.text, /登录/)
  })
})

describe('#4 createEmptyState - 默认值', () => {
  it('未知 type 应该 fallback 到 empty', () => {
    const s = createEmptyState('unknown-type')
    assertTruthy(s.title, '未知 type 应有 title')
  })

  it('不传 type 应该用 empty', () => {
    const s = createEmptyState()
    assertTruthy(s.title)
  })

  it('应该返回纯数据对象（不含 WXML 标签）', () => {
    const s = createEmptyState('empty')
    // 数据对象不应有 view/text 等标签
    assertFalsy(s.tagName, '不应有 tagName 字段')
    assertFalsy(s.children, '不应有 children 字段')
  })
})