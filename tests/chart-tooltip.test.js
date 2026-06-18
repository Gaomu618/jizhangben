// Tests for #6: 图表数据点睛 (chart-tooltip.js)
const {
  describe, it, assertEqual, assertTruthy, assertFalsy, assertMatch
} = require('./runner')

let buildTooltip, TIP_TYPES
try {
  const mod = require('../miniprogram/utils/chart-tooltip.js')
  buildTooltip = mod.buildTooltip
  TIP_TYPES = mod.TIP_TYPES
} catch (e) {
  buildTooltip = () => { throw new Error('chart-tooltip.js not implemented') }
  TIP_TYPES = {}
}

describe('#6 TIP_TYPES 枚举', () => {
  it('应该支持 3 种图表类型: pie / bar / trend', () => {
    assertTruthy(TIP_TYPES.pie, 'pie 类型')
    assertTruthy(TIP_TYPES.bar, 'bar 类型')
    assertTruthy(TIP_TYPES.trend, 'trend 类型')
  })
})

describe('#6 buildTooltip - pie (饼图扇形)', () => {
  it('应该返回完整的 tooltip 数据', () => {
    const data = [
      { category: '餐饮', amount: 300, type: 'expense' },
      { category: '交通', amount: 100, type: 'expense' }
    ]
    const tip = buildTooltip('pie', { index: 0, total: 400 }, data)
    assertEqual(tip.title, '餐饮')
    assertEqual(tip.value, '¥300')
    assertMatch(tip.subText, /75\.0%/)
  })

  it('应该处理小数百分比（四舍五入到 1 位）', () => {
    const data = [
      { category: '餐饮', amount: 333, type: 'expense' },
      { category: '交通', amount: 667, type: 'expense' }
    ]
    const tip = buildTooltip('pie', { index: 0, total: 1000 }, data)
    // 333/1000 = 33.3%
    assertMatch(tip.subText, /33\.3%/)
  })

  it('income 类型应该标注"收入"', () => {
    const data = [{ category: '工资', amount: 15000, type: 'income' }]
    const tip = buildTooltip('pie', { index: 0, total: 15000 }, data)
    assertMatch(tip.title, /工资/)
    assertEqual(tip.value, '¥15000')
  })

  it('无效 index 应该返回 null', () => {
    const data = [{ category: '餐饮', amount: 100, type: 'expense' }]
    assertFalsy(buildTooltip('pie', { index: -1, total: 100 }, data))
    assertFalsy(buildTooltip('pie', { index: 999, total: 100 }, data))
  })

  it('缺数据应该返回 null（不崩溃）', () => {
    assertFalsy(buildTooltip('pie', { index: 0, total: 100 }, null))
    assertFalsy(buildTooltip('pie', { index: 0, total: 100 }, []))
  })
})

describe('#6 buildTooltip - bar (柱图)', () => {
  it('income 本期应该显示"收入"', () => {
    const data = {
      labels: ['收入', '支出'],
      current: [15000, 1000],
      previous: [12000, 800],
      types: ['income', 'expense']
    }
    // hit: { group: 0, period: 'cur' }  →  收入 本期
    const tip = buildTooltip('bar', { group: 0, period: 'cur' }, data)
    assertEqual(tip.title, '收入')
    assertEqual(tip.value, '¥15000')
    assertMatch(tip.subText, /本期/)
  })

  it('expense 上期应该显示"支出 + 上期"', () => {
    const data = {
      labels: ['收入', '支出'],
      current: [15000, 1000],
      previous: [12000, 800],
      types: ['income', 'expense']
    }
    const tip = buildTooltip('bar', { group: 1, period: 'prev' }, data)
    assertEqual(tip.title, '支出')
    assertEqual(tip.value, '¥800')
    assertMatch(tip.subText, /上期/)
  })

  it('应该有变化提示（增减 %）', () => {
    const data = {
      labels: ['收入'],
      current: [15000],
      previous: [10000],
      types: ['income']
    }
    const tip = buildTooltip('bar', { group: 0, period: 'cur' }, data)
    // 10000 → 15000, +50%
    assertTruthy(tip.delta, '应该有 delta 字段')
    assertMatch(tip.delta, /\+50\.0%|50%/)
  })

  it('缺数据字段不应该崩溃', () => {
    const tip = buildTooltip('bar', { group: 0, period: 'cur' }, {})
    assertFalsy(tip)
  })
})

describe('#6 buildTooltip - trend (6 个月趋势线)', () => {
  it('应该显示月份和金额', () => {
    const data = {
      months: ['2025-12', '2026-01', '2026-02'],
      income: [0, 12000, 15000],
      expense: [500, 800, 1000]
    }
    const tip = buildTooltip('trend', { index: 1, lineType: 'income' }, data)
    assertEqual(tip.title, '2026-01')
    assertEqual(tip.value, '¥12000')
    assertMatch(tip.subText, /收入/)
  })

  it('lineType=expense 时显示支出', () => {
    const data = {
      months: ['2026-01'],
      income: [12000],
      expense: [800]
    }
    const tip = buildTooltip('trend', { index: 0, lineType: 'expense' }, data)
    assertMatch(tip.subText, /支出/)
    assertEqual(tip.value, '¥800')
  })

  it('lineType=balance 时显示结余（=收入-支出）', () => {
    const data = {
      months: ['2026-01'],
      income: [15000],
      expense: [5000]
    }
    const tip = buildTooltip('trend', { index: 0, lineType: 'balance' }, data)
    assertEqual(tip.value, '¥10000')
    assertMatch(tip.subText, /结余/)
  })

  it('无效 index 返回 null', () => {
    const data = { months: ['2026-01'], income: [100], expense: [50] }
    assertFalsy(buildTooltip('trend', { index: -1, lineType: 'income' }, data))
    assertFalsy(buildTooltip('trend', { index: 999, lineType: 'income' }, data))
  })
})

describe('#6 buildTooltip - 通用', () => {
  it('未知 type 应该返回 null', () => {
    assertFalsy(buildTooltip('unknown', {}, {}))
  })

  it('缺 type 参数应该返回 null', () => {
    assertFalsy(buildTooltip(undefined, {}, {}))
  })

  it('返回的 tooltip 应该有 visible=true 标记', () => {
    const tip = buildTooltip('pie', { index: 0, total: 100 },
      [{ category: '餐饮', amount: 100, type: 'expense' }])
    assertTruthy(tip.visible, 'visible 标记让 WXML 控制显示')
  })
})