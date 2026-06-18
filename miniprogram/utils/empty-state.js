// 纯数据工具：生成空状态对象
// 测试和页面 JS 共用
// 组件本身在 components/base/base-empty-state/

const EMPTY_TYPES = ['loading', 'empty', 'error', 'no-permission']

const noop = () => {}
const DEFAULTS = {
  loading: {
    icon: '⏳',
    title: '加载中…',
    message: '',
    cta: null
  },
  empty: {
    icon: '📭',
    title: '暂无数据',
    message: '这里还是空的',
    cta: { text: '刷新', handler: noop }
  },
  error: {
    icon: '⚠️',
    title: '出错了',
    message: '请稍后重试',
    cta: { text: '重试', handler: noop }
  },
  'no-permission': {
    icon: '🔒',
    title: '需要登录',
    message: '请先登录后查看',
    cta: { text: '去登录', handler: noop }
  }
}

function createEmptyState(type, opts = {}) {
  const t = EMPTY_TYPES.includes(type) ? type : 'empty'
  const base = DEFAULTS[t]

  let cta = base.cta
  if (opts.cta === null || opts.cta === false) {
    cta = null
  } else if (typeof opts.cta === 'object') {
    cta = { ...base.cta, ...opts.cta }
  }

  return {
    type: t,
    icon: opts.icon !== undefined ? opts.icon : base.icon,
    title: opts.title !== undefined ? opts.title : base.title,
    message: opts.message !== undefined ? opts.message : base.message,
    cta
  }
}

module.exports = { EMPTY_TYPES, DEFAULTS, createEmptyState }
