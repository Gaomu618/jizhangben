// Tests for #3: 微动效统一 (motion.js)
const {
  describe, it, assertEqual, assertTruthy, assertFalsy, assertMatch
} = require('./runner')

let getMotionClass, MOTION_CLASSES, MOTION_DURATIONS
try {
  const mod = require('../miniprogram/utils/motion')
  getMotionClass = mod.getMotionClass
  MOTION_CLASSES = mod.MOTION_CLASSES
  MOTION_DURATIONS = mod.MOTION_DURATIONS
} catch (e) {
  getMotionClass = () => { throw new Error('motion.js not implemented') }
  MOTION_CLASSES = {}
  MOTION_DURATIONS = {}
}

describe('#3 MOTION_CLASSES 注册表', () => {
  it('应该至少包含 4 种基础动效', () => {
    assertTruthy(MOTION_CLASSES.fadeIn)
    assertTruthy(MOTION_CLASSES.fadeOut)
    assertTruthy(MOTION_CLASSES.slideUp)
    assertTruthy(MOTION_CLASSES.slideDown)
  })

  it('应该包含 pulse 和 shimmer', () => {
    assertTruthy(MOTION_CLASSES.pulse, 'pulse 用于重要数据点睛')
    assertTruthy(MOTION_CLASSES.shimmer, 'shimmer 用于骨架屏')
  })

  it('所有 class 名应该以 motion- 开头', () => {
    for (const [key, val] of Object.entries(MOTION_CLASSES)) {
      assertMatch(val, /^motion-/, `${key} 类的类名应以 motion- 开头`)
    }
  })
})

describe('#3 getMotionClass', () => {
  it('应该返回正确的 class 名', () => {
    assertEqual(getMotionClass('fadeIn'), 'motion-fade-in')
    assertEqual(getMotionClass('slideUp'), 'motion-slide-up')
    assertEqual(getMotionClass('pulse'), 'motion-pulse')
    assertEqual(getMotionClass('shimmer'), 'motion-shimmer')
  })

  it('未知动效应该返回空字符串', () => {
    assertEqual(getMotionClass('nonexistent'), '')
    assertEqual(getMotionClass(''), '')
  })

  it('接受速记别名', () => {
    assertEqual(getMotionClass('fade'), 'motion-fade-in')
    assertEqual(getMotionClass('up'), 'motion-slide-up')
  })

  it('支持 duration 后缀: fadeIn-fast / fadeIn-slow', () => {
    assertMatch(getMotionClass('fadeIn-fast'), /^motion-fade-in motion-fade-in-fast$/)
    assertMatch(getMotionClass('fadeIn-slow'), /^motion-fade-in motion-fade-in-slow$/)
  })
})

describe('#3 MOTION_DURATIONS 时长配置', () => {
  it('应该有 fast/base/slow 三个档位', () => {
    assertTruthy(MOTION_DURATIONS.fast, 'fast 档位')
    assertTruthy(MOTION_DURATIONS.base, 'base 档位')
    assertTruthy(MOTION_DURATIONS.slow, 'slow 档位')
  })

  it('fast < base < slow', () => {
    assertTruthy(MOTION_DURATIONS.fast < MOTION_DURATIONS.base)
    assertTruthy(MOTION_DURATIONS.base < MOTION_DURATIONS.slow)
  })

  it('时长应该在 100-500ms 之间（人眼感知范围）', () => {
    assertTruthy(MOTION_DURATIONS.fast >= 100 && MOTION_DURATIONS.fast <= 200)
    assertTruthy(MOTION_DURATIONS.base >= 200 && MOTION_DURATIONS.base <= 350)
    assertTruthy(MOTION_DURATIONS.slow >= 300 && MOTION_DURATIONS.slow <= 500)
  })
})

describe('#3 WXSS 兼容性', () => {
  it('运动 class 不应该使用 WeChat 组件 wxss 禁用的选择器', () => {
    const validClassNames = Object.values(MOTION_CLASSES)
    for (const name of validClassNames) {
      // WeChat 组件 wxss 不允许: 标签/ID/属性选择器
      // 但 .motion-xxx 类选择器是允许的
      assertMatch(name, /^motion-[a-z-]+$/, `${name} 必须是纯类选择器（小写字母+连字符）`)
    }
  })
})