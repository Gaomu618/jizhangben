// #3 微动效统一配置
// 配套 WXSS 在 design/motion-classes.wxss（如果不存在，需要补）

// 时长档位（毫秒）—— 人眼感知范围 100-500ms
const MOTION_DURATIONS = {
  fast: 150,
  base: 250,
  slow: 400
}

// 注册表：动效名 → 实际 class 名
// 所有 class 名以 motion- 开头，方便识别且不被样式工具类冲突
const MOTION_CLASSES = {
  // 淡入淡出
  fadeIn: 'motion-fade-in',
  fadeOut: 'motion-fade-out',

  // 滑动
  slideUp: 'motion-slide-up',
  slideDown: 'motion-slide-down',
  slideLeft: 'motion-slide-left',
  slideRight: 'motion-slide-right',

  // 缩放
  zoomIn: 'motion-zoom-in',
  zoomOut: 'motion-zoom-out',

  // 强调
  pulse: 'motion-pulse',
  shake: 'motion-shake',

  // 加载
  shimmer: 'motion-shimmer',
  spin: 'motion-spin'
}

// 速记别名（开发友好）
const ALIAS = {
  fade: 'fadeIn',
  up: 'slideUp',
  down: 'slideDown',
  left: 'slideLeft',
  right: 'slideRight',
  in: 'zoomIn',
  out: 'zoomOut'
}

// 合法 duration 后缀
const VALID_DURATIONS = new Set(['fast', 'base', 'slow'])

// 合法 animationType（用于 navTo）
const VALID_ANIMATION_TYPES = new Set([
  'slide-up', 'fade', 'slide-left', 'slide-right', 'pop-in'
])

/**
 * 获取动效 class 名（支持速记和 duration 后缀）
 * @param {string} name - 动效名或速记
 * @returns {string} 完整 class 名（可能含多个 class，空字符串表示无效）
 */
function getMotionClass(name) {
  if (!name || typeof name !== 'string') return ''

  // 解析 duration 后缀（如 fadeIn-fast → motion-fade-in motion-fade-in-fast）
  let base = name
  let durationSuffix = ''
  const lastDash = name.lastIndexOf('-')
  if (lastDash > 0) {
    const suffix = name.slice(lastDash + 1)
    if (VALID_DURATIONS.has(suffix)) {
      base = name.slice(0, lastDash)
      durationSuffix = suffix
    }
  }

  // 解析速记别名
  const resolved = ALIAS[base] || base

  // 查注册表
  const baseClass = MOTION_CLASSES[resolved]
  if (!baseClass) return ''

  // 拼接 duration class（如果需要）
  if (durationSuffix) {
    return `${baseClass} ${baseClass}-${durationSuffix}`
  }
  return baseClass
}

module.exports = {
  MOTION_DURATIONS,
  MOTION_CLASSES,
  ALIAS,
  VALID_ANIMATION_TYPES,
  VALID_DURATIONS,
  getMotionClass
}