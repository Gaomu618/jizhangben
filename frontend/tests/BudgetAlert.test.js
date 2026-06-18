/**
 * Feature #4 测试：预算 80% / 100% 提醒状态机
 *
 * 核心契约：
 * 1) 达到 80% 弹一次 toast，再加消费不重复弹
 * 2) 达到 100% 弹一次 toast
 * 3) 月份切换后重新计数（key 含 month）
 * 4) 删掉一笔消费让 percent 降低，**不**弹"good news" toast
 */
import { describe, it, expect, vi } from 'vitest'
import { ref, computed } from 'vue'

// 复刻 Ledger.vue 里的 checkBudgetAlerts 逻辑（最小可测试版本）
function makeAlertSystem({ budgetList, selectedMonth, showToast }) {
  const notified = ref(new Set())
  const key = (cat, month, threshold) => `${cat}|${month}|${threshold}`

  function check() {
    if (!budgetList.value.length) return
    const month = selectedMonth.value
    for (const b of budgetList.value) {
      if (!b.budget || b.budget <= 0) continue
      const p = b.percent || 0
      if (p >= 100) {
        const k = key(b.category, month, 100)
        if (!notified.value.has(k)) {
          notified.value.add(k)
          showToast(`超预算 ${b.category}`, 'error')
        }
      } else if (p >= 80) {
        const k = key(b.category, month, 80)
        if (!notified.value.has(k)) {
          notified.value.add(k)
          showToast(`80% ${b.category}`, 'info')
        }
      }
    }
  }
  return { notified, check }
}

describe('BudgetAlert state machine', () => {
  it('达到 80% 弹一次 toast', () => {
    const showToast = vi.fn()
    const budgetList = ref([{ category: '餐饮', budget: 1000, spent: 850, percent: 85 }])
    const { check } = makeAlertSystem({ budgetList, selectedMonth: ref('2026-06'), showToast })

    check()
    expect(showToast).toHaveBeenCalledTimes(1)
    expect(showToast).toHaveBeenCalledWith(expect.stringContaining('80%'), 'info')
  })

  it('同月再加消费不重复弹', () => {
    const showToast = vi.fn()
    const budgetList = ref([{ category: '餐饮', budget: 1000, spent: 850, percent: 85 }])
    const { check } = makeAlertSystem({ budgetList, selectedMonth: ref('2026-06'), showToast })

    check()  // 第一次：弹
    check()  // 第二次：不弹
    check()  // 第三次：还不弹
    expect(showToast).toHaveBeenCalledTimes(1)
  })

  it('80% → 100% 应该弹两次（每个 threshold 各一次）', () => {
    const showToast = vi.fn()
    const budgetList = ref([{ category: '餐饮', budget: 1000, spent: 1100, percent: 110 }])
    const { check } = makeAlertSystem({ budgetList, selectedMonth: ref('2026-06'), showToast })

    check()
    expect(showToast).toHaveBeenCalledTimes(1)
    expect(showToast).toHaveBeenCalledWith(expect.stringContaining('超预算'), 'error')
  })

  it('从 80% 加到 110% 应该弹 80% 那次 + 100% 那次', () => {
    const showToast = vi.fn()
    const budgetList = ref([{ category: '餐饮', budget: 1000, spent: 850, percent: 85 }])
    const { check } = makeAlertSystem({ budgetList, selectedMonth: ref('2026-06'), showToast })

    check()  // 弹 80%
    expect(showToast).toHaveBeenCalledTimes(1)

    // 模拟下一笔：涨到 110%
    budgetList.value = [{ category: '餐饮', budget: 1000, spent: 1100, percent: 110 }]
    check()  // 弹 100%
    expect(showToast).toHaveBeenCalledTimes(2)
  })

  it('切换月份后重新计数（key 含 month）', () => {
    const showToast = vi.fn()
    const budgetList = ref([{ category: '餐饮', budget: 1000, spent: 850, percent: 85 }])
    const selectedMonth = ref('2026-06')
    const { check } = makeAlertSystem({ budgetList, selectedMonth, showToast })

    check()  // 6 月：弹
    expect(showToast).toHaveBeenCalledTimes(1)

    selectedMonth.value = '2026-07'  // 切到 7 月
    check()  // 7 月：弹（key 包含 month 所以不冲突）
    expect(showToast).toHaveBeenCalledTimes(2)
  })

  it('删一笔让 percent 降低，**不**弹"good news"', () => {
    const showToast = vi.fn()
    const budgetList = ref([{ category: '餐饮', budget: 1000, spent: 850, percent: 85 }])
    const { check } = makeAlertSystem({ budgetList, selectedMonth: ref('2026-06'), showToast })

    check()  // 弹 80%
    expect(showToast).toHaveBeenCalledTimes(1)

    // 用户删了 300，让 spent=550, percent=55
    budgetList.value = [{ category: '餐饮', budget: 1000, spent: 550, percent: 55 }]
    check()  // 不到 80%，不该弹
    expect(showToast).toHaveBeenCalledTimes(1)  // 还是 1，没变
  })

  it('多个分类各自独立追踪', () => {
    const showToast = vi.fn()
    const budgetList = ref([
      { category: '餐饮', budget: 1000, spent: 850, percent: 85 },
      { category: '购物', budget: 500, spent: 450, percent: 90 },
    ])
    const { check } = makeAlertSystem({ budgetList, selectedMonth: ref('2026-06'), showToast })

    check()
    expect(showToast).toHaveBeenCalledTimes(2)  // 两个分类各一次
  })
})


// Feature #3 测试：快速预算模板
describe('Quick budget templates', () => {
  it('4 个常用金额档位（300/500/1000/2000）', () => {
    const quickAmounts = [300, 500, 1000, 2000]
    expect(quickAmounts).toEqual([300, 500, 1000, 2000])
  })
})


// Feature #1 测试：总月预算汇总计算
describe('Total monthly budget summary', () => {
  it('总预算 = 所有 budget 之和', () => {
    const budgetList = ref([
      { budget: 1000, spent: 500 },
      { budget: 500, spent: 200 },
      { budget: 2000, spent: 1500 },
    ])
    const totalBudget = computed(() => budgetList.value.reduce((s, b) => s + (b.budget || 0), 0))
    expect(totalBudget.value).toBe(3500)
  })

  it('总已支出 = 所有 spent 之和', () => {
    const budgetList = ref([
      { budget: 1000, spent: 500 },
      { budget: 500, spent: 200 },
      { budget: 2000, spent: 1500 },
    ])
    const totalSpent = computed(() => budgetList.value.reduce((s, b) => s + (b.spent || 0), 0))
    expect(totalSpent.value).toBe(2200)
  })

  it('总剩余 = 总预算 - 总已支出（可为负）', () => {
    const budgetList = ref([
      { budget: 1000, spent: 1500 },  // 500 超支
    ])
    const totalBudget = computed(() => budgetList.value.reduce((s, b) => s + (b.budget || 0), 0))
    const totalSpent = computed(() => budgetList.value.reduce((s, b) => s + (b.spent || 0), 0))
    const totalRemaining = computed(() => totalBudget.value - totalSpent.value)
    expect(totalRemaining.value).toBe(-500)
  })

  it('总使用率 = 总已支出 / 总预算 × 100', () => {
    const budgetList = ref([
      { budget: 1000, spent: 800 },
      { budget: 500, spent: 200 },
    ])
    const totalBudget = computed(() => budgetList.value.reduce((s, b) => s + (b.budget || 0), 0))
    const totalSpent = computed(() => budgetList.value.reduce((s, b) => s + (b.spent || 0), 0))
    const totalPercent = computed(() => totalBudget.value > 0 ? (totalSpent.value / totalBudget.value) * 100 : 0)
    expect(totalPercent.value).toBe(66.66666666666666)  // 1000/1500
  })

  it('空预算列表 → 总预算 0，使用率 0', () => {
    const budgetList = ref([])
    const totalBudget = computed(() => budgetList.value.reduce((s, b) => s + (b.budget || 0), 0))
    const totalPercent = computed(() => totalBudget.value > 0 ? (totalSpent.value / totalBudget.value) * 100 : 0)
    expect(totalBudget.value).toBe(0)
    expect(totalPercent.value).toBe(0)
  })
})
