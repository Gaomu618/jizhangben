<template>
  <div class="min-h-screen app-bg">
    <!-- Top Bar -->
    <header class="nav">
      <div class="nav-inner">
        <div class="nav-left">
          <span class="nav-icon"><IconStats :size="22" /></span>
          <h1 class="nav-title display">{{ t('stats.title') }}</h1>
        </div>
        <div class="nav-actions">
          <select :value="lang" @change="setLanguage($event.target.value)" class="lang-select-inline">
            <option v-for="l in SUPPORTED_LANGUAGES" :key="l.code" :value="l.code">{{ l.label }}</option>
          </select>
          <BaseButton variant="ghost" size="sm" @click="router.push('/')">{{ t('stats.back') }}</BaseButton>
        </div>
      </div>
    </header>

    <!-- Main Content -->
    <div class="max-w-2xl mx-auto px-4 pb-24">

      <!-- 时间范围选择器 -->
      <BaseCard padding="md" class="mb-4">
        <BaseEyebrow tone="default">Range · 时间</BaseEyebrow>
        <div class="range-row" style="margin-top: 10px;">
          <button v-for="r in rangePresets" :key="r.value"
                  @click="selectRange(r.value)"
                  :class="['range-chip', { active: activeRange === r.value }]">
            {{ r.label }}
          </button>
          <button @click="showCustom = !showCustom" :class="['range-chip', { active: activeRange === 'custom' }]">
            自定义
          </button>
        </div>
        <div v-if="showCustom || activeRange === 'custom'" class="custom-row">
          <input v-model="customStart" type="date" class="input" />
          <span class="filter-dash">~</span>
          <input v-model="customEnd" type="date" class="input" />
          <BaseButton variant="primary" @click="applyCustom">应用</BaseButton>
        </div>
      </BaseCard>

      <!-- 4 个核心指标卡片：1+3 不对称布局（左侧主指标 + 右侧 3 个 mini 指标） -->
      <div v-if="summary" class="stats-hero-row mb-4">
        <!-- 左侧主指标：日均支出（深色引导卡） -->
        <BaseCard variant="dark" padding="lg" class="stats-hero-main">
          <BaseEyebrow tone="ink">Daily Average · 日均</BaseEyebrow>
          <p class="hero-value numeric text-expense">¥{{ summary.avg_daily_expense.toFixed(2) }}</p>
          <p v-if="summary.avg_daily_delta !== null" class="hero-delta"
             :class="summary.avg_daily_delta > 0 ? 'text-expense' : 'text-positive'">
            {{ summary.avg_daily_delta > 0 ? '↑' : '↓' }} {{ Math.abs(summary.avg_daily_delta) }}% · vs 上期
          </p>
          <p v-else class="hero-delta muted">首期无对比</p>
          <BaseSparkline
            v-if="summarySparkData.length"
            :data="summarySparkData"
            tone="accent"
            :height="48"
            :width="240"
          />
        </BaseCard>

        <!-- 右侧 3 个 mini 指标：1+2 + 1（不对称） -->
        <div class="stats-hero-side">
          <BaseCard padding="md" class="stats-mini-card">
            <BaseEyebrow>Max · 最大单笔</BaseEyebrow>
            <p v-if="summary.max_expense" class="mini-value numeric text-expense">¥{{ summary.max_expense.amount.toFixed(0) }}</p>
            <p v-else class="mini-value numeric muted">-</p>
            <p v-if="summary.max_expense" class="mini-meta muted">{{ summary.max_expense.category }} · {{ summary.max_expense.date.slice(5) }}</p>
            <p v-else class="mini-meta muted">暂无</p>
          </BaseCard>

          <BaseCard padding="md" class="stats-mini-card">
            <BaseEyebrow>Top Category · 最高频</BaseEyebrow>
            <p v-if="summary.top_category" class="mini-value text-accent display">{{ summary.top_category.name }}</p>
            <p v-else class="mini-value numeric muted">-</p>
            <p v-if="summary.top_category" class="mini-meta muted">{{ summary.top_category.count }}笔 · ¥{{ summary.top_category.total.toFixed(0) }}</p>
            <p v-else class="mini-meta muted">暂无</p>
          </BaseCard>

          <BaseCard padding="md" class="stats-mini-card stats-mini-wide">
            <BaseEyebrow>Records · 笔数</BaseEyebrow>
            <p class="mini-value numeric">
              <span class="text-positive">{{ summary.income_count }}</span>
              <span class="muted mx-1">/</span>
              <span class="text-expense">{{ summary.expense_count }}</span>
            </p>
            <p class="mini-meta muted">收/支 · {{ summary.days }} 天</p>
          </BaseCard>
        </div>
      </div>

      <!-- 每日热力图 -->
      <div class="card mb-4">
        <div class="chart-header">
          <div class="flex items-center gap-2">
            <span class="dot" style="background: var(--color-action-accent);"></span>
            <p class="text-sm font-semibold display">每日支出热力图（点击查看当天明细）</p>
          </div>
          <div class="flex items-center gap-2">
            <div class="flex items-center gap-1 text-xs muted">
              <span>少</span>
              <div class="heatmap-cell" style="background: #F3F4F6; border: 1px solid #E5E7EB;"></div>
              <div class="heatmap-cell" style="background: #FEF3C7;"></div>
              <div class="heatmap-cell" style="background: #FDE68A;"></div>
              <div class="heatmap-cell" style="background: #F97316;"></div>
              <div class="heatmap-cell" style="background: #DC2626;"></div>
              <span>多</span>
            </div>
            <button @click="exportChart('heatmap')" class="export-btn" title="导出图片"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M21 19V8a2 2 0 0 0-2-2h-3.5l-1-2h-5l-1 2H5a2 2 0 0 0-2 2v11a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2zM12 17a4 4 0 1 1 0-8 4 4 0 0 1 0 8z" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg></button>
          </div>
        </div>
        <div v-if="daily.length" class="heatmap-grid">
          <div v-for="d in daily" :key="d.date"
               class="heatmap-cell clickable"
               :style="{ background: getHeatColor(d.amount) }"
               :title="`${d.date}: ¥${d.amount} (${d.count}笔) - 点击查看`"
               @click="openDateDetail(d.date)">
          </div>
        </div>
        <p v-else class="empty-msg">本区间暂无支出</p>
      </div>

      <!-- 收支对比柱状图 -->
      <div class="card mb-4">
        <div class="chart-header">
          <div class="flex items-center gap-2">
            <span class="dot" style="background: linear-gradient(90deg, #10B981, #EF4444);"></span>
            <p class="text-sm font-semibold">收支对比 {{ activeRange !== 'custom' ? `· ${rangePresets.find(r => r.value === activeRange)?.label}` : '' }}</p>
          </div>
          <button @click="exportChart('bar')" class="export-btn" title="导出图片"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M21 19V8a2 2 0 0 0-2-2h-3.5l-1-2h-5l-1 2H5a2 2 0 0 0-2 2v11a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2zM12 17a4 4 0 1 1 0-8 4 4 0 0 1 0 8z" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg></button>
        </div>
        <div ref="barChartRef" class="chart-canvas"></div>
      </div>

      <!-- 趋势折线图 -->
      <div class="card mb-4">
        <div class="chart-header">
          <div class="flex items-center gap-2">
            <span class="dot" style="background: #4F46E5;"></span>
            <p class="text-sm font-semibold">近6个月趋势</p>
          </div>
          <button @click="exportChart('trend')" class="export-btn" title="导出图片"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M21 19V8a2 2 0 0 0-2-2h-3.5l-1-2h-5l-1 2H5a2 2 0 0 0-2 2v11a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2zM12 17a4 4 0 1 1 0-8 4 4 0 0 1 0 8z" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg></button>
        </div>
        <div ref="trendChartRef" class="chart-canvas"></div>
      </div>

      <!-- 各分类月度趋势（堆叠柱图） -->
      <div class="card mb-4">
        <div class="chart-header">
          <div class="flex items-center gap-2">
            <span class="dot" style="background: #EF4444;"></span>
            <p class="text-sm font-semibold">各分类月度支出（堆叠）</p>
          </div>
          <button @click="exportChart('categoryStack')" class="export-btn" title="导出图片"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M21 19V8a2 2 0 0 0-2-2h-3.5l-1-2h-5l-1 2H5a2 2 0 0 0-2 2v11a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2zM12 17a4 4 0 1 1 0-8 4 4 0 0 1 0 8z" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg></button>
        </div>
        <div v-if="!hasCategoryData" class="empty-msg">暂无分类支出数据</div>
        <div v-else ref="categoryStackRef" class="chart-canvas"></div>
      </div>

      <!-- 收支占比环形图 -->
      <BaseCard padding="md" class="mb-4">
        <BaseSectionHeader eyebrow="Ratio · 占比" eyebrow-tone="accent" title="收支占比">
          <template #aside>
            <BaseButton variant="ghost" size="sm" @click="exportChart('donut')">导出</BaseButton>
          </template>
        </BaseSectionHeader>
        <div ref="ratioDonutRef" class="chart-canvas"></div>
      </BaseCard>

      <!-- 分类饼图：1+1 不对称 -->
      <div class="stats-pie-row mb-4">
        <BaseCard padding="md" class="stats-pie-card">
          <BaseSectionHeader eyebrow="Income · 收入" eyebrow-tone="accent" title="收入分类">
            <template #aside>
              <BaseButton variant="ghost" size="sm" @click="exportChart('incomePie')">导出</BaseButton>
            </template>
          </BaseSectionHeader>
          <div ref="incomePieRef" class="chart-canvas-sm"></div>
        </BaseCard>

        <BaseCard padding="md" class="stats-pie-card">
          <BaseSectionHeader eyebrow="Expense · 支出" eyebrow-tone="accent" title="支出分类">
            <template #aside>
              <BaseButton variant="ghost" size="sm" @click="exportChart('expensePie')">导出</BaseButton>
            </template>
          </BaseSectionHeader>
          <div ref="expensePieRef" class="chart-canvas-sm"></div>
        </BaseCard>
      </div>

      <!-- 支出分类排行 -->
      <BaseCard padding="md" class="mb-4">
        <BaseSectionHeader eyebrow="Ranking · 排行" eyebrow-tone="accent" title="支出分类排行">
          <template #aside>
            <BaseButton variant="ghost" size="sm" @click="exportChart('expenseBar')">导出</BaseButton>
          </template>
        </BaseSectionHeader>
        <div ref="expenseBarRef" class="chart-canvas-lg"></div>
      </BaseCard>

      <!-- 预算概览 -->
      <BaseCard padding="md" class="mb-4">
        <BaseSectionHeader eyebrow="Budget · 预算" eyebrow-tone="accent" title="本月预算概览" />
        <div v-if="budgetList.length" class="budget-list">
          <div v-for="b in budgetList" :key="b.category" class="budget-row">
            <div class="budget-row-head">
              <span class="budget-cat">{{ b.category }}</span>
              <span class="budget-amount numeric"
                    :class="b.percent >= 80 ? 'text-expense' : b.percent >= 60 ? 'text-warn' : 'text-income'">
                ¥{{ b.spent.toFixed(0) }} / ¥{{ b.budget.toFixed(0) }}
              </span>
            </div>
            <BaseProgress
              :value="b.percent"
              :variant="b.percent >= 80 ? 'warning' : 'accent'"
              :show-label="false"
            />
            <p class="budget-tip">
              <BaseTag v-if="b.percent >= 100" variant="negative" style="soft">已超支 ¥{{ (b.spent - b.budget).toFixed(0) }}</BaseTag>
              <BaseTag v-else-if="b.percent >= 80" variant="warning" style="soft">还剩 ¥{{ (b.budget - b.spent).toFixed(0) }}，快用完了</BaseTag>
              <span v-else class="muted">还剩 ¥{{ (b.budget - b.spent).toFixed(0) }} ({{ (100 - b.percent).toFixed(0) }}%)</span>
            </p>
          </div>
        </div>
        <BaseEmpty
          v-else
          title="本月还没有设置预算"
          message="设置预算后，超支时会有提示"
        >
          <template #cta>
            <BaseButton variant="primary" @click="goBudget">前往设置</BaseButton>
          </template>
        </BaseEmpty>
      </BaseCard>

      <!-- TOP 5 最高支出 -->
      <BaseCard padding="md" class="mb-4">
        <BaseSectionHeader eyebrow="Top · 排行" eyebrow-tone="accent" :title="`最高支出 TOP ${topList.length}`" />
        <div v-if="topList.length" class="top-list">
          <div v-for="(item, i) in topList" :key="item.id"
               class="top-item"
               :class="{ gold: i === 0, silver: i === 1, bronze: i === 2 }">
            <div class="top-rank">{{ i + 1 }}</div>
            <BaseAvatar :name="item.category" shape="square" size="sm" />
            <div class="top-info">
              <p class="top-title">{{ item.note || item.category }}</p>
              <p class="top-meta">{{ item.category }} · {{ item.date.slice(5) }}</p>
            </div>
            <div class="top-amount numeric text-expense">¥{{ item.amount.toFixed(2) }}</div>
          </div>
        </div>
        <BaseEmpty v-else title="本区间暂无支出记录" message="添加几笔支出后，这里会按金额排序" />
      </BaseCard>

      <div v-if="loading" class="loading-box">
        <div class="loading-spinner mx-auto mb-2"></div>
        <p class="text-sm muted">加载中...</p>
      </div>
    </div>

    <!-- 记录详情弹窗 -->
    <div v-if="detailModal.show" class="modal-overlay" @click.self="closeDetail">
      <div class="modal card">
        <div class="modal-header">
          <span class="modal-title">{{ detailModal.title }}</span>
          <span class="modal-close" @click="closeDetail">×</span>
        </div>
        <p class="text-xs muted mb-2">共 {{ detailModal.records.length }} 条</p>
        <div v-if="detailModal.loading" class="text-center py-6 muted">加载中...</div>
        <div v-else-if="!detailModal.records.length" class="text-center py-6 muted">没有记录</div>
        <div v-else class="detail-list">
          <div v-for="r in detailModal.records" :key="r.id" class="detail-item">
            <span class="detail-emoji">{{ getCategoryEmoji(r.category) }}</span>
            <div class="detail-info">
              <p class="detail-title">{{ r.note || r.category }}</p>
              <p class="detail-meta">{{ r.category }} · {{ r.date }}</p>
            </div>
            <span class="detail-amount mono" :class="r.type === 'income' ? 'text-income' : 'text-expense'">
              {{ r.type === 'income' ? '+' : '-' }}¥{{ Number(r.amount).toFixed(2) }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { t, useI18n, SUPPORTED_LANGUAGES } from '../i18n'
import IconStats from '../components/IconStats.vue'
import { statsAPI, billAPI } from '../api'
import {
  BaseButton, BaseCard, BaseInput, BaseSelect, BaseTag,
  BaseProgress, BaseSparkline, BaseEyebrow, BaseEmpty,
  BaseSectionHeader, BaseToggle, BaseAvatar
} from '../components/base'

const { lang, setLanguage } = useI18n()

const router = useRouter()
const currentDate = new Date()
const currentYear = ref(currentDate.getFullYear())
const currentMonth = ref(currentDate.getMonth() + 1)

const rangePresets = [
  { value: 'month', label: '本月' },
  { value: 'last_month', label: '上月' },
  { value: '7d', label: '近7天' },
  { value: '30d', label: '近30天' },
  { value: '90d', label: '近90天' },
  { value: 'year', label: '今年' },
]
const activeRange = ref('month')
const showCustom = ref(false)
const customStart = ref('')
const customEnd = ref('')
const loading = ref(false)

const rangeStart = ref('')
const rangeEnd = ref('')

function computeRange() {
  const now = new Date()
  const fmt = (d) => d.toISOString().slice(0, 10)
  let s, e
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())

  if (activeRange.value === 'month') {
    s = new Date(now.getFullYear(), now.getMonth(), 1)
    e = new Date(now.getFullYear(), now.getMonth() + 1, 1)
  } else if (activeRange.value === 'last_month') {
    s = new Date(now.getFullYear(), now.getMonth() - 1, 1)
    e = new Date(now.getFullYear(), now.getMonth(), 1)
  } else if (activeRange.value === '7d') {
    s = new Date(today.getTime() - 6 * 86400000)
    e = new Date(today.getTime() + 86400000)
  } else if (activeRange.value === '30d') {
    s = new Date(today.getTime() - 29 * 86400000)
    e = new Date(today.getTime() + 86400000)
  } else if (activeRange.value === '90d') {
    s = new Date(today.getTime() - 89 * 86400000)
    e = new Date(today.getTime() + 86400000)
  } else if (activeRange.value === 'year') {
    s = new Date(now.getFullYear(), 0, 1)
    e = new Date(now.getFullYear() + 1, 0, 1)
  } else {
    return
  }
  rangeStart.value = fmt(s)
  rangeEnd.value = fmt(e)
}

function selectRange(val) {
  activeRange.value = val
  if (val !== 'custom') {
    computeRange()  // 关键：每次切换 preset 都重算日期（之前忘了 → 不同 chip 查同一天）
    loadAll()
  } else {
    showCustom.value = true
  }
}

function applyCustom() {
  if (!customStart.value || !customEnd.value) return
  activeRange.value = 'custom'
  showCustom.value = false
  const end = new Date(customEnd.value)
  end.setDate(end.getDate() + 1)
  rangeStart.value = customStart.value
  rangeEnd.value = end.toISOString().slice(0, 10)
  loadAll()
}

const summary = ref(null)
const daily = ref([])
const categoryData = ref([])
const trendData = ref(null)
const topList = ref([])
const budgetList = ref([])

// Sparkline 数据：基于 daily 数据（每日支出金额，最多 30 天）
const summarySparkData = computed(() => daily.value.slice(-30).map(d => d.amount))

// 记录详情弹窗
const detailModal = ref({ show: false, title: '', records: [], loading: false })

// ECharts 引用映射（用于导出）
const chartMap = {
  bar: null, trend: null, incomePie: null, expensePie: null,
  donut: null, expenseBar: null, categoryStack: null
}

const barChartRef = ref(null), trendChartRef = ref(null)
const incomePieRef = ref(null), expensePieRef = ref(null)
const ratioDonutRef = ref(null), expenseBarRef = ref(null)
const categoryStackRef = ref(null)
let barChart = null, trendChart = null, incomePie = null, expensePie = null, ratioDonut = null, expenseBar = null, categoryStack = null

const hasCategoryData = computed(() => {
  if (!trendData.value) return false
  const bc = trendData.value.by_category
  return bc && Object.values(bc).some(arr => arr.some(v => v > 0))
})

const categoryEmojis = {
  '餐饮': '🍜', '交通': '🚗', '购物': '🛒', '娱乐': '🎮',
  '医疗': '💊', '居住': '🏠', '教育': '📚', '其他': '📝',
  '工资': '💰', '奖金': '🎁', '理财': '📈', '副业': '💼',
}
function getCategoryEmoji(c) { return categoryEmojis[c] || '📝' }

async function loadAll() {
  // 防御：万一 rangeStart 还没设置（直接调 loadAll），先算
  if (!rangeStart.value) computeRange()
  loading.value = true
  try {
    const params = { start: rangeStart.value, end: rangeEnd.value }
    // 并发拉 5 个统计端点（用封装好的 statsAPI 替代 raw axios）
    const [sumRes, dailyRes, catRes, trendRes, topRes] = await Promise.all([
      statsAPI.getSummary(params),
      statsAPI.getDaily(params),
      statsAPI.getCategory(params),
      statsAPI.getTrend({ months: 6 }),
      statsAPI.getTop({ ...params, type: 'expense', limit: 5 }),
    ])
    // 关键：拦截器在 api/index.js 已 return res（body），所以 .data 已经是真数据，.data.data 是 undefined
    summary.value = sumRes.data
    daily.value = dailyRes.data || []
    categoryData.value = catRes.data || []
    trendData.value = trendRes.data
    topList.value = topRes.data || []

    renderBarChart()
    renderPieCharts()
    renderTrendChart()
    renderRatioDonut()
    renderExpenseBar()
    // 关键修复：categoryStackRef 在 v-else 分支里，DOM 还没更新前 ref.value=null
    // 必须等 nextTick 让 Vue 渲染完成
    await nextTick()
    renderCategoryStack()
    await loadBudget()
  } catch (e) {
    console.error('loadAll error:', e)
  } finally {
    loading.value = false
  }
}

async function loadBudget() {
  try {
    const res = await billAPI.getBudget()
    budgetList.value = res.data || []
  } catch (e) {
    console.error('loadBudget error:', e)
  }
}

function goBudget() {
  // 简单跳到主页，让用户在那里设置预算
  router.push('/')
}

// 打开某天的记录详情
async function openDateDetail(date) {
  detailModal.value = { show: true, title: `${date} 支出明细`, records: [], loading: true }
  try {
    const res = await billAPI.getList({ start: date, end: date, type: 'expense', page_size: 100 })
    detailModal.value.records = res.data.list || []
  } catch (e) {
    console.error('openDateDetail error:', e)
  } finally {
    detailModal.value.loading = false
  }
}

// 打开某分类的记录详情
async function openCategoryDetail(category, type) {
  detailModal.value = { show: true, title: `${category}（${type === 'income' ? '收入' : '支出'}）`, records: [], loading: true }
  try {
    const res = await billAPI.getList({
      start: rangeStart.value, end: rangeEnd.value,
      category, type, page_size: '100'
    })
    detailModal.value.records = res.data.list || []
  } catch (e) {
    console.error('openCategoryDetail error:', e)
  } finally {
    detailModal.value.loading = false
  }
}

function closeDetail() {
  detailModal.value.show = false
}

// 导出图表为 PNG
function exportChart(name) {
  const inst = chartMap[name]
  if (!inst) return
  const url = inst.getDataURL({
    type: 'png',
    pixelRatio: 2,
    backgroundColor: '#FFFFFF'
  })
  const a = document.createElement('a')
  a.href = url
  a.download = `统计图_${name}_${new Date().toISOString().slice(0, 10)}.png`
  a.click()
}

function getHeatColor(amount) {
  if (!amount) return '#F3F4F6'
  const max = daily.value.length ? Math.max(...daily.value.map(d => d.amount)) : 1
  if (max === 0 || amount === 0) return '#F3F4F6'
  const ratio = amount / max
  if (ratio < 0.2) return '#FEF3C7'
  if (ratio < 0.4) return '#FDE68A'
  if (ratio < 0.6) return '#FCD34D'
  if (ratio < 0.8) return '#F97316'
  return '#DC2626'
}

const tooltipBase = {
  trigger: 'axis',
  backgroundColor: '#FFFFFF',
  borderColor: '#E5E7EB',
  borderWidth: 1,
  textStyle: { color: '#1F2937', fontSize: 12 },
  extraCssText: 'box-shadow: 0 4px 12px rgba(0,0,0,0.08); border-radius: 8px;'
}
const tooltipItem = {
  trigger: 'item',
  backgroundColor: '#FFFFFF',
  borderColor: '#E5E7EB',
  borderWidth: 1,
  textStyle: { color: '#1F2937', fontSize: 12 },
  extraCssText: 'box-shadow: 0 4px 12px rgba(0,0,0,0.08); border-radius: 8px;'
}

function renderBarChart() {
  if (!barChartRef.value || !summary.value) return
  if (!barChart) barChart = window.echarts.init(barChartRef.value)
  chartMap.bar = barChart
  const cur = summary.value
  const prev = cur.previous || { expense: 0, income: 0 }
  barChart.setOption({
    tooltip: { ...tooltipBase, formatter: '{b}<br/>{a}: ¥{c}' },
    legend: { data: ['本期', '上期'], textStyle: { color: '#6B7280' }, top: 0 },
    grid: { left: '3%', right: '4%', bottom: '3%', top: '15%', containLabel: true },
    xAxis: { type: 'category', data: ['收入', '支出'], axisLine: { lineStyle: { color: '#E5E7EB' } }, axisLabel: { color: '#6B7280' } },
    yAxis: { type: 'value', axisLine: { show: false }, axisTick: { show: false }, axisLabel: { color: '#9CA3AF' }, splitLine: { lineStyle: { color: '#F3F4F6' } } },
    series: [
      {
        name: '本期', type: 'bar', data: [cur.income, cur.expense],
        itemStyle: { borderRadius: [6, 6, 0, 0], color: (p) => p.dataIndex === 0 ? '#10B981' : '#EF4444' },
        barWidth: 28,
        label: { show: true, position: 'top', color: '#1F2937', fontSize: 11, fontWeight: 600, formatter: (p) => '¥' + p.value.toFixed(0) }
      },
      {
        name: '上期', type: 'bar', data: [prev.income, prev.expense],
        itemStyle: { borderRadius: [6, 6, 0, 0], color: '#D1D5DB' },
        barWidth: 28
      }
    ]
  })
  barChart.on('click', (params) => {
    if (params.componentType === 'series') {
      const type = params.dataIndex === 0 ? 'income' : 'expense'
      openCategoryDetail(type === 'income' ? 'all-income' : 'all-expense', type)
    }
  })
}

function renderPieCharts() {
  const incomeData = categoryData.value.filter(d => d.type === 'income')
  const expenseData = categoryData.value.filter(d => d.type === 'expense')

  if (incomePieRef.value) {
    if (!incomePie) incomePie = window.echarts.init(incomePieRef.value)
    chartMap.incomePie = incomePie
    incomePie.setOption({
      tooltip: { ...tooltipItem, formatter: '{b}: ¥{c} ({d}%)' },
      legend: { bottom: 0, textStyle: { color: '#6B7280', fontSize: 11 } },
      series: [{
        type: 'pie', radius: ['38%', '62%'], center: ['50%', '45%'],
        itemStyle: { borderColor: '#FFFFFF', borderWidth: 2 },
        label: { show: false },
        data: incomeData.length ? incomeData.map(d => ({ name: d.category, value: d.amount })) : [{ name: '暂无', value: 1, itemStyle: { color: '#F3F4F6' } }]
      }]
    })
    incomePie.on('click', (params) => {
      if (params.componentType === 'series' && params.name !== '暂无') {
        openCategoryDetail(params.name, 'income')
      }
    })
  }

  if (expensePieRef.value) {
    if (!expensePie) expensePie = window.echarts.init(expensePieRef.value)
    chartMap.expensePie = expensePie
    expensePie.setOption({
      tooltip: { ...tooltipItem, formatter: '{b}: ¥{c} ({d}%)' },
      legend: { bottom: 0, textStyle: { color: '#6B7280', fontSize: 11 } },
      series: [{
        type: 'pie', radius: ['38%', '62%'], center: ['50%', '45%'],
        itemStyle: { borderColor: '#FFFFFF', borderWidth: 2 },
        label: { show: false },
        data: expenseData.length ? expenseData.map(d => ({ name: d.category, value: d.amount })) : [{ name: '暂无', value: 1, itemStyle: { color: '#F3F4F6' } }]
      }]
    })
    expensePie.on('click', (params) => {
      if (params.componentType === 'series' && params.name !== '暂无') {
        openCategoryDetail(params.name, 'expense')
      }
    })
  }
}

function renderTrendChart() {
  if (!trendChartRef.value || !trendData.value) return
  if (!trendChart) trendChart = window.echarts.init(trendChartRef.value)
  chartMap.trend = trendChart
  const data = trendData.value
  const balance = data.income.map((inc, i) => (inc - (data.expense[i] || 0)).toFixed(2))
  trendChart.setOption({
    tooltip: {
      ...tooltipBase,
      formatter: (params) => {
        let result = params[0].name + '<br/>'
        params.forEach(p => { result += p.marker + p.seriesName + ': ¥' + p.value + '<br/>' })
        const idx = params[0].dataIndex
        const b = (data.income[idx] - (data.expense[idx] || 0)).toFixed(2)
        result += '<b>结余: ¥' + b + '</b>'
        return result
      }
    },
    legend: { data: ['收入', '支出', '结余'], textStyle: { color: '#6B7280' }, top: 0 },
    grid: { left: '3%', right: '4%', bottom: '3%', top: '15%', containLabel: true },
    xAxis: { type: 'category', data: data.months, axisLine: { lineStyle: { color: '#E5E7EB' } }, axisLabel: { color: '#6B7280' } },
    yAxis: { type: 'value', axisLine: { show: false }, axisTick: { show: false }, axisLabel: { color: '#9CA3AF' }, splitLine: { lineStyle: { color: '#F3F4F6' } } },
    series: [
      { name: '收入', type: 'line', data: data.income, smooth: true, itemStyle: { color: '#10B981' }, lineStyle: { width: 2.5 }, areaStyle: { color: 'rgba(16,185,129,0.08)' } },
      { name: '支出', type: 'line', data: data.expense, smooth: true, itemStyle: { color: '#EF4444' }, lineStyle: { width: 2.5 }, areaStyle: { color: 'rgba(239,68,68,0.08)' } },
      { name: '结余', type: 'line', data: balance, smooth: true, itemStyle: { color: '#4F46E5' }, lineStyle: { width: 2.5, type: 'dashed' } }
    ]
  })
}

function renderRatioDonut() {
  if (!ratioDonutRef.value || !summary.value) return
  if (!ratioDonut) ratioDonut = window.echarts.init(ratioDonutRef.value)
  chartMap.donut = ratioDonut
  const cur = summary.value
  const income = cur.income || 0
  const expense = cur.expense || 0
  const total = income + expense
  const balance = (income - expense).toFixed(2)
  const hasData = total > 0

  ratioDonut.setOption({
    tooltip: { ...tooltipItem, formatter: hasData ? '{b}: ¥{c} ({d}%)' : '本区间暂无数据' },
    legend: hasData ? { bottom: 0, textStyle: { color: '#6B7280' } } : { show: false },
    series: [{
      type: 'pie', radius: ['55%', '78%'], center: ['50%', '45%'],
      itemStyle: { borderColor: '#FFFFFF', borderWidth: 4 },
      label: { show: false },
      data: hasData
        ? [{ name: '收入', value: income, itemStyle: { color: '#10B981' } }, { name: '支出', value: expense, itemStyle: { color: '#EF4444' } }]
        : [{ name: '暂无数据', value: 1, itemStyle: { color: '#F3F4F6' } }]
    }],
    graphic: hasData ? [
      { type: 'text', left: 'center', top: '38%', style: { text: '结余', fontSize: 12, fill: '#6B7280' } },
      { type: 'text', left: 'center', top: '48%', style: { text: '¥' + balance, fontSize: 18, fontWeight: 'bold', fill: income - expense >= 0 ? '#10B981' : '#EF4444' } }
    ] : []
  })
}

function renderExpenseBar() {
  if (!expenseBarRef.value) return
  if (!expenseBar) expenseBar = window.echarts.init(expenseBarRef.value)
  chartMap.expenseBar = expenseBar
  const expenseData = categoryData.value.filter(d => d.type === 'expense').slice(0, 8)
  const hasData = expenseData.length > 0
  const categories = hasData ? expenseData.map(d => d.category).reverse() : ['暂无']
  const amounts = hasData ? expenseData.map(d => Number(d.amount)).reverse() : [0]

  expenseBar.setOption({
    tooltip: { ...tooltipBase, formatter: (p) => `${p[0].name}<br/><b>¥${p[0].value.toFixed(2)}</b>` },
    grid: { left: '3%', right: '12%', top: '3%', bottom: '3%', containLabel: true },
    xAxis: { type: 'value', axisLine: { show: false }, axisTick: { show: false }, axisLabel: { color: '#9CA3AF', formatter: (v) => v >= 1000 ? (v / 1000).toFixed(1) + 'k' : v }, splitLine: { lineStyle: { color: '#F3F4F6', type: 'dashed' } } },
    yAxis: { type: 'category', data: categories, axisLine: { show: false }, axisTick: { show: false }, axisLabel: { color: '#1F2937', fontSize: 12 } },
    series: [{
      type: 'bar', data: amounts, barWidth: 14,
      itemStyle: { borderRadius: [0, 6, 6, 0], color: hasData ? '#EF4444' : '#E5E7EB' },
      label: { show: hasData, position: 'right', color: '#1F2937', fontSize: 11, fontWeight: 600, formatter: (p) => '¥' + Number(p.value).toFixed(0) }
    }]
  })
  expenseBar.on('click', (params) => {
    if (params.componentType === 'series' && hasData) {
      openCategoryDetail(params.name, 'expense')
    }
  })
}

function handleResize() {
  [barChart, trendChart, incomePie, expensePie, ratioDonut, expenseBar, categoryStack].forEach(c => c && c.resize())
}

// 各分类月度趋势（堆叠柱图）
function renderCategoryStack() {
  if (!categoryStackRef.value || !trendData.value) return
  if (!categoryStack) categoryStack = window.echarts.init(categoryStackRef.value)
  chartMap.categoryStack = categoryStack

  const data = trendData.value
  const byCat = data.by_category || {}
  const hasData = hasCategoryData.value

  // 配色
  const palette = ['#EF4444', '#F59E0B', '#10B981', '#3B82F6', '#8B5CF6', '#EC4899', '#14B8A6', '#F97316']
  const series = Object.entries(byCat).map(([cat, amounts], idx) => ({
    name: cat,
    type: 'bar',
    stack: 'expense',
    data: amounts,
    barWidth: '50%',
    itemStyle: { color: palette[idx % palette.length] },
    emphasis: { focus: 'series' }
  }))

  categoryStack.setOption({
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: 'rgba(15,18,30,0.95)',
      borderColor: '#4F46E5',
      textStyle: { color: '#fff', fontSize: 12 },
      formatter: (params) => {
        const idx = params[0].dataIndex
        const total = params.reduce((s, p) => s + p.value, 0)
        let result = `${params[0].name}<br/><b>总计: ¥${total.toFixed(2)}</b>`
        params.filter(p => p.value > 0).forEach(p => {
          result += `<br/>${p.marker} ${p.seriesName}: ¥${p.value.toFixed(2)}`
        })
        return result
      }
    },
    legend: hasData ? {
      bottom: 0,
      textStyle: { color: '#6B7280', fontSize: 11 },
      icon: 'circle'
    } : { show: false },
    grid: { left: '3%', right: '4%', bottom: '15%', top: '5%', containLabel: true },
    xAxis: {
      type: 'category',
      data: data.months,
      axisLine: { lineStyle: { color: '#E5E7EB' } },
      axisLabel: { color: '#6B7280' }
    },
    yAxis: {
      type: 'value',
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: '#9CA3AF', formatter: (v) => v >= 1000 ? (v / 1000).toFixed(1) + 'k' : v },
      splitLine: { lineStyle: { color: '#F3F4F6' } }
    },
    series
  })
}

onMounted(() => {
  computeRange()
  loadAll()
  window.addEventListener('resize', handleResize)
})
onUnmounted(() => {
  [barChart, trendChart, incomePie, expensePie, ratioDonut, expenseBar, categoryStack].forEach(c => c && c.dispose())
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.nav {
  background: #FFFFFF;
  border-bottom: 1px solid #E5E7EB;
  padding: 12px 16px;
  position: sticky;
  top: 0;
  z-index: 100;
}
.nav-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  max-width: 672px;
  margin: 0 auto;
}
.nav-actions { display: flex; align-items: center; gap: 8px; }
.lang-select-inline {
  background: #F9FAFB;
  border: 1px solid #E5E7EB;
  color: #6B7280;
  border-radius: 8px;
  padding: 6px 10px;
  font-size: 12px;
  font-family: inherit;
  cursor: pointer;
  outline: none;
}
.nav-left { display: flex; align-items: center; gap: 8px; }
.nav-icon {
  font-size: 18px;
  width: 32px;
  height: 32px;
  background: #EEF2FF;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.nav-title { font-size: 16px; font-weight: 700; color: #1F2937; }

.range-row {
  display: flex;
  gap: 6px;
  overflow-x: auto;
  scrollbar-width: none;
}
.range-row::-webkit-scrollbar { display: none; }

.range-chip {
  padding: 6px 12px;
  font-size: 12px;
  font-weight: 500;
  border-radius: 8px;
  background: #F9FAFB;
  border: 1px solid #E5E7EB;
  color: #6B7280;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.15s;
}
.range-chip:hover { background: #F3F4F6; }
.range-chip.active {
  background: #4F46E5;
  border-color: #4F46E5;
  color: #FFFFFF;
}

.custom-row {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 10px;
}
.custom-row .input { margin-bottom: 0; padding: 6px 10px; font-size: 13px; }
.custom-row .btn-primary { padding: 7px 14px; font-size: 13px; white-space: nowrap; }

.grid-2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

/* ==================== Hero 1+3 布局 ==================== */
.stats-hero-row {
  display: grid;
  grid-template-columns: 1.5fr 1fr;
  gap: 16px;
  align-items: stretch;
}
.stats-hero-main {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.hero-value {
  font-size: 44px;
  font-weight: 600;
  letter-spacing: -0.03em;
  line-height: 1;
  margin: 8px 0;
}
.hero-delta {
  font-size: 12px;
  font-weight: 500;
  margin: 0;
}
.stats-hero-side {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}
.stats-mini-card {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-height: 92px;
}
.stats-mini-wide { grid-column: 1 / -1; }
.mini-value {
  font-size: 22px;
  font-weight: 600;
  letter-spacing: -0.02em;
  color: var(--color-text-primary);
  margin: 4px 0;
  line-height: 1.1;
}
.mini-meta { font-size: 11px; color: var(--color-text-muted); margin: 0; }

/* ==================== 1+1 不对称饼图 ==================== */
.stats-pie-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}
.stats-pie-card { display: flex; flex-direction: column; }

/* ==================== 响应式 ==================== */
@media (max-width: 540px) {
  .stats-hero-row { grid-template-columns: 1fr; }
  .stats-hero-side { grid-template-columns: 1fr; }
  .hero-value { font-size: 36px; }
  .stats-pie-row { grid-template-columns: 1fr; }
}

.metric-card { padding: 14px; }
.metric-label { font-size: 11px; color: #6B7280; margin-bottom: 6px; font-weight: 500; }
.metric-value { font-size: 20px; font-weight: 700; line-height: 1.1; margin-bottom: 4px; }
.metric-delta { font-size: 11px; margin-top: 4px; font-family: "SF Mono", monospace; }
.metric-delta.up { color: #EF4444; }
.metric-delta.down { color: #10B981; }
.metric-delta.muted { color: #9CA3AF; }

.muted { color: #9CA3AF; }

.chart-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}
.dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; }
.flex { display: flex; }
.items-center { align-items: center; }
.gap-1 { gap: 4px; }
.gap-2 { gap: 8px; }
.mx-1 { margin-left: 4px; margin-right: 4px; }
.text-sm { font-size: 13px; }
.font-semibold { font-weight: 600; }
.mb-2 { margin-bottom: 8px; }
.mb-4 { margin-bottom: 16px; }
.mx-auto { margin-left: auto; margin-right: auto; }

.chart-canvas { width: 100%; height: 220px; }
.chart-canvas-sm { width: 100%; height: 180px; }
.chart-canvas-lg { width: 100%; height: 280px; }

.heatmap-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(12px, 1fr));
  gap: 2px;
  max-height: 200px;
  overflow-y: auto;
}
.heatmap-cell {
  width: 12px;
  height: 12px;
  border-radius: 2px;
  transition: transform 0.1s;
}
.heatmap-cell:hover { transform: scale(1.3); }
.heatmap-cell.clickable { cursor: pointer; }
.heatmap-cell.clickable:hover { box-shadow: 0 0 0 2px #4F46E5; }

/* 导出按钮 */
.export-btn {
  background: transparent;
  border: 1px solid #E5E7EB;
  color: #6B7280;
  width: 28px;
  height: 28px;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s;
  display: flex;
  align-items: center;
  justify-content: center;
}
.export-btn:hover { background: #F3F4F6; color: #1F2937; border-color: #4F46E5; }

/* 预算概览 */
.budget-list { display: flex; flex-direction: column; gap: 12px; }
.budget-row { }
.budget-row-head {
  display: flex;
  justify-content: space-between;
  margin-bottom: 6px;
  font-size: 13px;
}
.budget-cat { color: #1F2937; font-weight: 500; }
.budget-amount { font-size: 13px; }
.budget-bar { height: 6px; background: #F3F4F6; border-radius: 3px; overflow: hidden; }
.budget-fill { height: 100%; border-radius: 3px; transition: width 0.3s; }
.budget-fill.normal { background: #10B981; }
.budget-fill.warning { background: #F97316; }
.budget-fill.over { background: #EF4444; }
.budget-tip { font-size: 11px; margin-top: 4px; }

.cursor-pointer { cursor: pointer; }
.text-warn { color: #F97316; }

/* 详情弹窗 */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
  padding: 16px;
}
.modal {
  width: 100%;
  max-width: 420px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  border-radius: 16px;
  padding: 20px;
  animation: scaleIn 0.2s ease;
}
@keyframes scaleIn {
  from { transform: scale(0.95); opacity: 0; }
  to { transform: scale(1); opacity: 1; }
}
.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.modal-title { font-size: 16px; font-weight: 600; color: #1F2937; }
.modal-close {
  font-size: 24px;
  color: #9CA3AF;
  cursor: pointer;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
}
.modal-close:hover { background: #F3F4F6; color: #1F2937; }

.detail-list { overflow-y: auto; max-height: 60vh; }
.detail-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 0;
  border-bottom: 1px solid #F3F4F6;
}
.detail-item:last-child { border-bottom: none; }
.detail-emoji {
  font-size: 18px;
  width: 32px;
  height: 32px;
  background: #F9FAFB;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.detail-info { flex: 1; min-width: 0; }
.detail-title { font-size: 13px; font-weight: 500; color: #1F2937; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.detail-meta { font-size: 11px; color: #9CA3AF; }
.detail-amount { font-size: 13px; font-weight: 600; white-space: nowrap; }

.empty-msg {
  text-align: center;
  color: #9CA3AF;
  font-size: 13px;
  padding: 20px 0;
}

.top-list { display: flex; flex-direction: column; gap: 6px; }
.top-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  background: #F9FAFB;
  border: 1px solid #E5E7EB;
  border-radius: 10px;
  transition: all 0.15s;
}
.top-item:hover { background: #F3F4F6; }

.top-rank {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: #E5E7EB;
  color: #6B7280;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  flex-shrink: 0;
}
.top-item.gold .top-rank { background: #F59E0B; color: white; }
.top-item.silver .top-rank { background: #9CA3AF; color: white; }
.top-item.bronze .top-rank { background: #B45309; color: white; }

.top-emoji {
  width: 32px;
  height: 32px;
  background: #FFFFFF;
  border: 1px solid #E5E7EB;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  flex-shrink: 0;
}
.top-info { flex: 1; min-width: 0; }
.top-title { font-size: 13px; font-weight: 500; margin-bottom: 2px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: #1F2937; }
.top-meta { font-size: 11px; color: #9CA3AF; }
.top-amount { font-size: 13px; font-weight: 600; white-space: nowrap; }

.loading-box { text-align: center; padding: 30px; }
.loading-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid #E5E7EB;
  border-top-color: #4F46E5;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
</style>
