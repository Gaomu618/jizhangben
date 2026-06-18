// #6 图表数据点睛：根据 hit-test 结果生成 tooltip 数据
// 纯数据函数，不依赖 WXML/canvas

const TIP_TYPES = {
  pie: 'pie',
  bar: 'bar',
  trend: 'trend'
}

// 子标签（用于 trend 的三种线）
const TREND_LABELS = {
  income: '收入',
  expense: '支出',
  balance: '结余'
}

// 柱图分组的标签
const BAR_LABELS = ['收入', '支出']
const BAR_PERIODS = ['本期', '上期']

/**
 * 安全除法（避免 NaN）
 */
function safePercent(part, total) {
  if (!total || total <= 0) return 0
  return Math.round((part / total) * 1000) / 10
}

/**
 * 安全数值显示
 */
function fmt(n) {
  if (n === undefined || n === null || isNaN(n)) return '¥0'
  return '¥' + Number(n).toFixed(0)
}

/**
 * 构建 tooltip 数据对象
 * @param {string} type - 'pie' | 'bar' | 'trend'
 * @param {object} hit - hit-test 结果（不同 type 结构不同）
 * @param {object} data - 图表数据
 * @returns {object|null} tooltip 数据，null 表示不显示
 */
function buildTooltip(type, hit, data) {
  if (!type || !TIP_TYPES[type]) return null
  if (!hit) return null

  if (type === TIP_TYPES.pie) return buildPieTip(hit, data)
  if (type === TIP_TYPES.bar) return buildBarTip(hit, data)
  if (type === TIP_TYPES.trend) return buildTrendTip(hit, data)
  return null
}

function buildPieTip(hit, data) {
  if (!data || !Array.isArray(data) || data.length === 0) return null
  const idx = hit.index
  if (typeof idx !== 'number' || idx < 0 || idx >= data.length) return null
  const item = data[idx]
  if (!item || typeof item.amount !== 'number') return null

  const total = typeof hit.total === 'number' && hit.total > 0
    ? hit.total
    : data.reduce((s, d) => s + (d.amount || 0), 0)
  const percentNum = safePercent(item.amount, total)
  // 总是 1 位小数：75 → 75.0，33.3 → 33.3
  const percentStr = (percentNum % 1 === 0 ? percentNum.toFixed(1) : String(percentNum))
  const typeLabel = item.type === 'income' ? '收入' : '支出'

  return {
    visible: true,
    title: item.category || '未分类',
    value: fmt(item.amount),
    subText: `${typeLabel} · ${percentStr}%`
  }
}

function buildBarTip(hit, data) {
  if (!data || typeof data !== 'object') return null
  // 校验必要字段
  if (!data.current || !data.previous) return null
  if (typeof hit.group !== 'number' || !BAR_LABELS[hit.group]) return null
  if (hit.period !== 'cur' && hit.period !== 'prev') return null

  const label = BAR_LABELS[hit.group]
  const period = BAR_PERIODS[hit.period === 'cur' ? 0 : 1]
  const cur = data.current[hit.group] || 0
  const prev = data.previous[hit.group] || 0
  const value = hit.period === 'cur' ? cur : prev
  const other = hit.period === 'cur' ? prev : cur

  // 变化 %（本期 vs 上期）
  let delta = '0%'
  if (other > 0) {
    const diff = safePercent(value - other, other)
    const sign = diff >= 0 ? '+' : ''
    delta = `${sign}${diff}%`
  } else if (value > 0) {
    delta = '+∞%'
  }

  return {
    visible: true,
    title: label,
    value: fmt(value),
    subText: `${period} · 对比上期 ${delta}`,
    delta  // 单独字段，方便测试/UI 使用
  }
}

function buildTrendTip(hit, data) {
  if (!data || !data.months || !Array.isArray(data.months)) return null
  if (typeof hit.index !== 'number' || hit.index < 0 || hit.index >= data.months.length) return null
  const lineType = hit.lineType
  if (!TREND_LABELS[lineType]) return null

  const month = data.months[hit.index]
  let value = 0
  if (lineType === 'income') value = (data.income && data.income[hit.index]) || 0
  else if (lineType === 'expense') value = (data.expense && data.expense[hit.index]) || 0
  else if (lineType === 'balance') {
    const inc = (data.income && data.income[hit.index]) || 0
    const exp = (data.expense && data.expense[hit.index]) || 0
    value = inc - exp
  }

  return {
    visible: true,
    title: month,
    value: fmt(value),
    subText: TREND_LABELS[lineType]
  }
}

module.exports = {
  TIP_TYPES,
  TREND_LABELS,
  BAR_LABELS,
  BAR_PERIODS,
  buildTooltip,
  fmt,
  safePercent
}