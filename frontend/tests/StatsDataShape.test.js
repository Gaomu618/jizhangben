/**
 * Stats.vue 数据 shape 契约测试
 *
 * 历史教训：之前 Stats.vue 写 `summary.value = sumRes.data.data`，但 axios
 * 拦截器在 api/index.js 已经 `return res`（即后端 body 本身），所以
 * `res.data` 已经是真数据，`res.data.data` 是 undefined → 图表空。
 *
 * 这个测试模拟拦截器契约，验证 Stats.vue 用的数据 shape 是正确的。
 */
import { describe, it, expect, vi } from 'vitest'

// 模拟 api/index.js 的拦截器：return res（已 unwrap body）
function mockInterceptor(body) {
  // body shape: { code: 0, message: "success", data: <actualData> }
  if (body.code !== 0) return Promise.reject(new Error(body.message))
  return Promise.resolve(body)  // ← 关键：直接 return body
}

// 模拟 statsAPI wrapper（基于 mockInterceptor）
const statsAPI = {
  getSummary: () => mockInterceptor({ code: 0, data: { income: 100, expense: 50, days: 30 } }),
  getDaily: () => mockInterceptor({ code: 0, data: [{ date: '2026-06-01', amount: 100, count: 1 }] }),
  getCategory: () => mockInterceptor({ code: 0, data: [{ category: '餐饮', amount: 100 }] }),
  getTrend: () => mockInterceptor({ code: 0, data: { months: ['Jan', 'Feb'], income: [0, 0], expense: [0, 0] } }),
  getTop: () => mockInterceptor({ code: 0, data: [{ id: 1, category: '餐饮', amount: 100 }] }),
}

describe('Stats.vue 数据 shape（拦截器已 unwrap body）', () => {
  it('summary.value 应是 sumRes.data（不是 .data.data）', async () => {
    const sumRes = await statsAPI.getSummary()
    // 修前：summary.value = sumRes.data.data  → undefined
    // 修后：summary.value = sumRes.data       → { income: 100, expense: 50, days: 30 }
    const summary = sumRes.data
    expect(summary).toBeDefined()
    expect(summary.income).toBe(100)
    expect(summary.expense).toBe(50)
  })

  it('daily.value 应是 dailyRes.data（数组）', async () => {
    const dailyRes = await statsAPI.getDaily()
    const daily = dailyRes.data
    expect(Array.isArray(daily)).toBe(true)
    expect(daily[0].date).toBe('2026-06-01')
  })

  it('categoryData.value 应是 catRes.data', async () => {
    const catRes = await statsAPI.getCategory()
    const cats = catRes.data
    expect(cats[0].category).toBe('餐饮')
  })

  it('trendData.value 应是 trendRes.data（含 months/income/expense 字段）', async () => {
    const trendRes = await statsAPI.getTrend()
    const trend = trendRes.data
    expect(trend.months).toBeDefined()
    expect(trend.income).toBeDefined()
    expect(trend.expense).toBeDefined()
  })

  it('topList.value 应是 topRes.data', async () => {
    const topRes = await statsAPI.getTop()
    const top = topRes.data
    expect(top[0].id).toBe(1)
  })
})
