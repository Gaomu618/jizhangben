/**
 * 统一日期格式化工具
 * @param {Date|string|number} date - 日期对象或可转为日期的值
 * @returns {string} YYYY-MM-DD 格式日期字符串
 */
export function formatDate(date = new Date()) {
  const d = new Date(date)
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

/**
 * 获取当前月的第一天
 * @param {Date|string|number} date - 日期对象或可转为日期的值
 * @returns {string} YYYY-MM-DD 格式
 */
export function getMonthStart(date = new Date()) {
  const d = new Date(date)
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  return `${y}-${m}-01`
}

/**
 * 获取当前月的最后一天
 * @param {Date|string|number} date - 日期对象或可转为日期的值
 * @returns {string} YYYY-MM-DD 格式
 */
export function getMonthEnd(date = new Date()) {
  const d = new Date(date)
  const y = d.getFullYear()
  const m = d.getMonth() + 1
  const lastDay = new Date(y, m, 0).getDate()
  return `${y}-${String(m).padStart(2, '0')}-${String(lastDay).padStart(2, '0')}`
}

/**
 * 获取上个月同一天
 * @param {Date|string|number} date - 日期对象或可转为日期的值
 * @returns {string} YYYY-MM-DD 格式
 */
export function getPrevMonth(date = new Date()) {
  const d = new Date(date)
  d.setMonth(d.getMonth() - 1)
  return formatDate(d)
}

/**
 * 格式化金额显示
 * @param {number} amount - 金额
 * @returns {string} 带千分位分隔符的金额字符串
 */
export function formatAmount(amount) {
  return amount.toLocaleString('zh-CN', { minimumFractionDigits: 2 })
}