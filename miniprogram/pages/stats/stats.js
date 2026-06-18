const api = require('../../utils/api.js')
const { createEmptyState } = require('../../utils/empty-state.js')
const { buildTooltip, TIP_TYPES } = require('../../utils/chart-tooltip.js')

// ============== 常量 ==============
const CATEGORY_EMOJIS = {
  '餐饮': '🍜', '交通': '🚗', '购物': '🛒', '娱乐': '🎮',
  '医疗': '💊', '居住': '🏠', '教育': '📚', '其他': '📝',
  '工资': '💰', '奖金': '🎁', '投资': '📈', '兼职': '💼', '红包': '🧧'
}

const CATEGORY_COLORS = [
  '#ef4444', '#f59e0b', '#10b981', '#3b82f6',
  '#8b5cf6', '#ec4899', '#14b8a6', '#f97316',
  '#84cc16', '#06b6d4'
]

const HEAT_COLORS = ['#faf7f2', '#fde7dc', '#f5a98a', '#d94f1e', '#7a1f0a']

// ============== Page ==============
Page({
  data: {
    year: new Date().getFullYear(),
    month: new Date().getMonth() + 1,

    // 时间范围
    rangePresets: [
      { value: 'month', label: '本月' },
      { value: 'last_month', label: '上月' },
      { value: '7d', label: '近7天' },
      { value: '30d', label: '近30天' },
      { value: '90d', label: '近90天' },
      { value: 'year', label: '今年' }
    ],
    activeRange: 'month',
    showCustom: false,
    customStart: '',
    customEnd: '',

    rangeStart: '',
    rangeEnd: '',
    loading: false,

    // 图表数据
    summary: null,
    daily: [],
    categoryData: [],
    trendData: null,
    topList: [],
    budgetList: [],

    // 工具
    categoryEmojis: CATEGORY_EMOJIS,

    // #4 空状态：初始 loading
    emptyState: createEmptyState('loading'),

    // #6 数据点睛：tooltip 状态
    tooltip: { visible: false, chartId: '', title: '', value: '', subText: '', x: 0, y: 0 },

    // 详情弹窗
    detailModal: { show: false, title: '', records: [], loading: false }
  },

  // ============== 生命周期 ==============
  onShow() {
    this.computeRange()
    this.loadAll()
    if (typeof this.getTabBar === 'function' && this.getTabBar()) {
      this.getTabBar().setData({ selected: 1 })
    }
  },

  // ============== 时间范围 ==============
  computeRange() {
    const now = new Date()
    const fmt = (d) => {
      const y = d.getFullYear()
      const m = String(d.getMonth() + 1).padStart(2, '0')
      const day = String(d.getDate()).padStart(2, '0')
      return `${y}-${m}-${day}`
    }
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
    let s, e
    const v = this.data.activeRange
    if (v === 'month') {
      s = new Date(now.getFullYear(), now.getMonth(), 1)
      e = new Date(now.getFullYear(), now.getMonth() + 1, 1)
    } else if (v === 'last_month') {
      s = new Date(now.getFullYear(), now.getMonth() - 1, 1)
      e = new Date(now.getFullYear(), now.getMonth(), 1)
    } else if (v === '7d') {
      s = new Date(today.getTime() - 6 * 86400000)
      e = new Date(today.getTime() + 86400000)
    } else if (v === '30d') {
      s = new Date(today.getTime() - 29 * 86400000)
      e = new Date(today.getTime() + 86400000)
    } else if (v === '90d') {
      s = new Date(today.getTime() - 89 * 86400000)
      e = new Date(today.getTime() + 86400000)
    } else if (v === 'year') {
      s = new Date(now.getFullYear(), 0, 1)
      e = new Date(now.getFullYear() + 1, 0, 1)
    } else {
      return
    }
    this.setData({ rangeStart: fmt(s), rangeEnd: fmt(e) })
  },

  onRangeChip(e) {
    const v = e.currentTarget.dataset.value
    if (v === 'custom') {
      this.setData({ showCustom: true })
      return
    }
    this.setData({ activeRange: v, showCustom: false }, () => {
      this.computeRange()
      this.loadAll()
    })
  },

  onCustomStartChange(e) { this.setData({ customStart: e.detail.value }) },
  onCustomEndChange(e) { this.setData({ customEnd: e.detail.value }) },

  applyCustom() {
    if (!this.data.customStart || !this.data.customEnd) {
      wx.showToast({ title: '请选择起止日期', icon: 'none' })
      return
    }
    const end = new Date(this.data.customEnd)
    end.setDate(end.getDate() + 1)
    const fmt = (d) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
    this.setData({
      activeRange: 'custom',
      showCustom: false,
      rangeStart: this.data.customStart,
      rangeEnd: fmt(end)
    })
    this.loadAll()
  },

  // ============== 数据加载 ==============
  async loadAll() {
    if (!this.data.rangeStart) this.computeRange()
    this.setData({ loading: true })
    try {
      const { rangeStart, rangeEnd, year, month } = this.data
      const [summary, daily, catRes, trend, top, budget] = await Promise.all([
        api.getSummary({ start: rangeStart, end: rangeEnd }),
        api.getDaily({ start: rangeStart, end: rangeEnd }),
        api.getCategory({ start: rangeStart, end: rangeEnd }),
        api.getTrend({ months: 6 }),
        api.getTop({ start: rangeStart, end: rangeEnd, type: 'expense', limit: 5 }),
        api.getBudget({ year, month }).catch(() => [])
      ])
      // 预计算 summary 展示字段（WXML 不支持 .toFixed/.slice）
      const summaryView = summary ? {
        ...summary,
        avgDisplay: (summary.avg_daily_expense || 0).toFixed(2),
        maxAmountDisplay: summary.max_expense ? summary.max_expense.amount.toFixed(0) : null,
        maxDateShort: summary.max_expense ? summary.max_expense.date.slice(5) : null,
        topTotalDisplay: summary.top_category ? summary.top_category.total.toFixed(0) : null
      } : null
      // 预算行 + TOP 5 预计算
      const budgetListView = (budget || []).map(b => ({
        ...b,
        spentRmb: (b.spent || 0).toFixed(0),
        budgetRmb: (b.budget || 0).toFixed(0)
      }))
      const topListView = (top || []).map((item, i) => ({
        ...item,
        rankClass: i === 0 ? 'gold' : i === 1 ? 'silver' : i === 2 ? 'bronze' : '',
        dateShort: (item.date || '').slice(5),
        amountRmb: (item.amount || 0).toFixed(2)
      }))
      // #4 数据加载成功：根据是否空决定 emptyState
      const hasData = (daily && daily.length) || (catRes && catRes.length) || (top && top.length)
      this.setData({
        summary: summaryView,
        daily: daily || [],
        categoryData: catRes || [],
        trendData: trend || null,
        topList: topListView,
        budgetList: budgetListView,
        emptyState: hasData ? null : createEmptyState('empty', {
          title: '本区间暂无账单',
          message: '记一笔之后这里会显示统计图表',
          cta: { text: '去记一笔', handler: () => {
            this.openAdd ? this.openAdd() : wx.switchTab({ url: '/pages/index/index' })
          } }
        })
      })
      // 延迟到下一个渲染周期再画图（数据已 setData）
      setTimeout(() => this.drawAllCharts(), 50)
    } catch (e) {
      console.error('[stats loadAll]', e)
      // #4 数据加载失败：error 状态
      this.setData({
        emptyState: createEmptyState('error', {
          message: (e && e.message) || '请稍后重试',
          cta: { text: '重试', handler: () => this.loadAll() }
        })
      })
    } finally {
      this.setData({ loading: false })
    }
  },

  // ============== Canvas 通用 ==============
  // 同时返回 canvas 节点 + 真实布局尺寸（CSS 像素）
  // 关键：canvas node 没有 getBoundingClientRect（web API），
  //       必须用 selectorQuery.boundingClientRect()
  _queryCanvas(id) {
    return new Promise(resolve => {
      const query = wx.createSelectorQuery()
      query.select('#' + id).node()
      query.select('#' + id).boundingClientRect()
      query.exec(res => {
        const canvas = res[0] ? res[0].node : null
        const rect = res[1] || null
        resolve({ canvas, rect })
      })
    })
  },

  _setupCanvas(canvas, rect) {
    // <canvas type="2d"> 默认 width=300/height=150（HTML 规范），
    // 与 CSS width/height 无关；图变形就是因为用了这个默认值。
    // 真实显示尺寸来自 selectorQuery.boundingClientRect()。
    const info = (wx.getWindowInfo && wx.getWindowInfo()) || wx.getSystemInfoSync()
    const dpr = info.pixelRatio || 2
    if (!rect || rect.width === 0 || rect.height === 0) {
      return null
    }
    const w = rect.width
    const h = rect.height
    canvas.width = w * dpr
    canvas.height = h * dpr
    const ctx = canvas.getContext('2d')
    ctx.scale(dpr, dpr)
    return { ctx, w, h, dpr }
  },

  async drawAllCharts() {
    // 元素可能还没布局（rect=0），失败时下一帧重试
    const results = await Promise.all([
        this.drawBar(),
      this.drawTrend(),
      this.drawDonut(),
      this.drawPie('incomePie', 'income'),
      this.drawPie('expensePie', 'expense'),
      this.drawExpenseBar()
    ])
    if (results.some(r => r === false)) {
      // 至少一个图因 layout 未就绪被跳过 → 下一帧再画
      setTimeout(() => this.drawAllCharts(), 100)
    }
  },

  _roundRect(ctx, x, y, w, h, r) {
    ctx.beginPath()
    ctx.moveTo(x + r, y)
    ctx.arcTo(x + w, y, x + w, y + h, r)
    ctx.arcTo(x + w, y + h, x, y + h, r)
    ctx.arcTo(x, y + h, x, y, r)
    ctx.arcTo(x, y, x + w, y, r)
    ctx.closePath()
  },

  onPieTap(e) {
    // 通用 hit-test：兼容 incomePie 和 expensePie
    const canvasId = e.currentTarget.dataset.pieId
    const data = this._pieHitTest && this._pieHitTest[canvasId]
    if (!data) return
    const { x, y } = e.detail
    const dx = x - data.cx
    const dy = y - data.cy
    const dist = Math.sqrt(dx * dx + dy * dy)
    if (dist > data.r || dist < data.inner) return
    // atan2(dy, dx) 在 screen 坐标系里 = 与 drawPie 同向的角度（-π/2 起）
    let angle = Math.atan2(dy, dx)
    while (angle < -Math.PI / 2) angle += 2 * Math.PI
    while (angle >= 3 * Math.PI / 2) angle -= 2 * Math.PI
    for (const s of data.slices) {
      if (angle >= s.startAngle && angle < s.endAngle) {
        this.openCategoryDetail(s.category, data.type)
        return
      }
    }
  },

  // ============== 2. Bar (本期 vs 上期) ==============
  async drawBar() {
    const { canvas, rect } = await this._queryCanvas('barChart')
    if (!canvas || !this.data.summary) return
    const setup = this._setupCanvas(canvas, rect)
    if (!setup) return false
    const { ctx, w, h } = setup
    ctx.clearRect(0, 0, w, h)
    const s = this.data.summary
    const labels = ['收入', '支出']
    const cur = [s.income, s.expense]
    const prev = [s.previous.income, s.previous.expense]
    const max = Math.max(...cur, ...prev, 1)
    const pad = 48
    const chartW = w - pad * 2
    const chartH = h - pad * 2
    const groupW = chartW / 2
    const barW = 40
    const gap = 8
    for (let i = 0; i < 2; i++) {
      const x0 = pad + i * groupW + (groupW - barW * 2 - gap) / 2
      // 本期
      const cH = (cur[i] / max) * chartH
      ctx.fillStyle = i === 0 ? '#10b981' : '#ef4444'
      this._roundRect(ctx, x0, pad + chartH - cH, barW, cH, 6)
      ctx.fill()
      // 上期
      const pH = (prev[i] / max) * chartH
      ctx.fillStyle = '#d4d4d8'
      this._roundRect(ctx, x0 + barW + gap, pad + chartH - pH, barW, pH, 6)
      ctx.fill()
      // 标签
      ctx.fillStyle = '#0f172a'
      ctx.font = '14px sans-serif'
      ctx.textAlign = 'center'
      ctx.fillText(labels[i], x0 + barW + gap / 2, h - 16)
      // 数值
      if (cur[i] > 0) {
        ctx.fillStyle = i === 0 ? '#10b981' : '#ef4444'
        ctx.font = 'bold 12px sans-serif'
        ctx.fillText('¥' + cur[i].toFixed(0), x0 + barW / 2, pad + chartH - cH - 6)
      }
    }
    // 缓存 hit-test：两个柱组的 x 范围（用于 onBarTap）
    this._barHitTest = {
      groups: [
        { type: 'income', x0: pad + 0 * groupW, x1: pad + 0 * groupW + groupW },
        { type: 'expense', x0: pad + 1 * groupW, x1: pad + 1 * groupW + groupW }
      ]
    }
    // 图例
    ctx.fillStyle = '#10b981'; ctx.fillRect(pad, 12, 10, 10)
    ctx.fillStyle = '#0f172a'; ctx.font = '11px sans-serif'; ctx.textAlign = 'left'
    ctx.fillText('本期', pad + 14, 21)
    ctx.fillStyle = '#d4d4d8'; ctx.fillRect(pad + 60, 12, 10, 10)
    ctx.fillStyle = '#0f172a'; ctx.fillText('上期', pad + 74, 21)
  },

  onBarTap(e) {
    // hit-test：点收入柱组 → 全部收入；点支出柱组 → 全部支出
    const data = this._barHitTest
    if (!data) {
      this.openCategoryDetail('all', 'expense')
      return
    }
    const x = (e && e.detail && e.detail.x) || 0
    for (const g of data.groups) {
      if (x >= g.x0 && x <= g.x1) {
        this.openCategoryDetail('all', g.type)
        return
      }
    }
    this.openCategoryDetail('all', 'expense')
  },

  // ============== 3. Trend (6m line) ==============
  async drawTrend() {
    const { canvas, rect } = await this._queryCanvas('trendChart')
    if (!canvas || !this.data.trendData) return
    const setup = this._setupCanvas(canvas, rect)
    if (!setup) return false
    const { ctx, w, h } = setup
    ctx.clearRect(0, 0, w, h)
    const t = this.data.trendData
    const months = t.months || []
    const income = t.income || []
    const expense = t.expense || []
    if (months.length === 0) return
    const balance = income.map((v, i) => v - expense[i])
    const pad = 48
    const chartW = w - pad * 2
    const chartH = h - pad * 2
    const max = Math.max(...income, ...expense, ...balance, 100)
    const min = Math.min(...balance, 0)
    const xStep = chartW / Math.max(months.length - 1, 1)

    // 网格
    ctx.strokeStyle = '#e7e1d4'
    ctx.lineWidth = 1
    for (let i = 0; i <= 4; i++) {
      const y = pad + (chartH / 4) * i
      ctx.beginPath()
      ctx.moveTo(pad, y)
      ctx.lineTo(pad + chartW, y)
      ctx.stroke()
    }
    // X 轴标签
    ctx.fillStyle = '#9a9081'
    ctx.font = '10px sans-serif'
    ctx.textAlign = 'center'
    months.forEach((m, i) => {
      const x = pad + i * xStep
      ctx.fillText(m.slice(5), x, h - 12)
    })

    const drawLine = (vals, color, dashed) => {
      ctx.strokeStyle = color
      ctx.lineWidth = 2
      if (dashed) ctx.setLineDash([4, 4])
      else ctx.setLineDash([])
      ctx.beginPath()
      vals.forEach((v, i) => {
        const x = pad + i * xStep
        const y = pad + chartH - ((v - min) / (max - min)) * chartH
        if (i === 0) ctx.moveTo(x, y)
        else ctx.lineTo(x, y)
      })
      ctx.stroke()
      // 圆点
      vals.forEach((v, i) => {
        const x = pad + i * xStep
        const y = pad + chartH - ((v - min) / (max - min)) * chartH
        ctx.fillStyle = color
        ctx.beginPath()
        ctx.arc(x, y, 3, 0, Math.PI * 2)
        ctx.fill()
      })
    }
    drawLine(income, '#10b981', false)
    drawLine(expense, '#ef4444', false)
    drawLine(balance, '#4f46e5', true)
  },

  // ============== 4. Donut (收支占比) ==============
  async drawDonut() {
    const { canvas, rect } = await this._queryCanvas('ratioDonut')
    if (!canvas || !this.data.summary) return
    const setup = this._setupCanvas(canvas, rect)
    if (!setup) return false
    const { ctx, w, h } = setup
    ctx.clearRect(0, 0, w, h)
    const s = this.data.summary
    const income = s.income || 0
    const expense = s.expense || 0
    const total = income + expense
    const cx = w / 2
    const cy = h / 2
    const r = Math.min(w, h) * 0.35
    const inner = r * 0.7
    if (total === 0) {
      ctx.fillStyle = '#e7e1d4'
      ctx.beginPath()
      ctx.arc(cx, cy, r, 0, Math.PI * 2)
      ctx.arc(cx, cy, inner, 0, Math.PI * 2, true)
      ctx.fill('evenodd')
      ctx.fillStyle = '#9a9081'
      ctx.font = '12px sans-serif'
      ctx.textAlign = 'center'
      ctx.fillText('暂无数据', cx, cy)
      return
    }
    // 收入
    const startAngle = -Math.PI / 2
    const incomeAngle = (income / total) * Math.PI * 2
    const expenseAngle = (expense / total) * Math.PI * 2
    ctx.fillStyle = '#10b981'
    ctx.beginPath()
    ctx.moveTo(cx, cy)
    ctx.arc(cx, cy, r, startAngle, startAngle + incomeAngle)
    ctx.closePath()
    ctx.fill()
    ctx.fillStyle = '#ef4444'
    ctx.beginPath()
    ctx.moveTo(cx, cy)
    ctx.arc(cx, cy, r, startAngle + incomeAngle, startAngle + incomeAngle + expenseAngle)
    ctx.closePath()
    ctx.fill()
    // 中间文字
    ctx.fillStyle = '#0f172a'
    ctx.font = '11px sans-serif'
    ctx.textAlign = 'center'
    ctx.fillText('结余', cx, cy - 8)
    const bal = income - expense
    ctx.fillStyle = bal >= 0 ? '#047857' : '#d94f1e'
    ctx.font = 'bold 18px sans-serif'
    ctx.fillText((bal >= 0 ? '+' : '') + '¥' + bal.toFixed(0), cx, cy + 14)
  },

  // ============== 5/6. Pie (收入/支出分类) ==============
  // 横向布局：左侧饼图 + 右侧图例（节省垂直空间，留白均衡）
  async drawPie(canvasId, type) {
    const { canvas, rect } = await this._queryCanvas(canvasId)
    if (!canvas) return true
    const setup = this._setupCanvas(canvas, rect)
    if (!setup) return false
    const { ctx, w, h } = setup
    ctx.clearRect(0, 0, w, h)
    const data = this.data.categoryData.filter(d => d.type === type)

    // 布局：左 50% 饼图，右 50% 图例
    const pieCx = w * 0.25
    const cy = h / 2
    const pieR = Math.min(w * 0.22, h * 0.36)
    const inner = pieR * 0.6

    if (data.length === 0) {
      ctx.fillStyle = '#e7e1d4'
      ctx.beginPath()
      ctx.arc(pieCx, cy, pieR, 0, Math.PI * 2)
      ctx.arc(pieCx, cy, inner, 0, Math.PI * 2, true)
      ctx.fill('evenodd')
      ctx.fillStyle = '#9a9081'
      ctx.font = '10px sans-serif'
      ctx.textAlign = 'center'
      ctx.fillText('本区间无', pieCx, cy - 6)
      ctx.fillText(type === 'income' ? '收入记录' : '支出记录', pieCx, cy + 8)
      return true
    }

    const total = data.reduce((sum, d) => sum + d.amount, 0)

    // 饼图扇形 + hit-test 数据
    let angle = -Math.PI / 2
    const slices = []
    data.forEach((d, i) => {
      const slice = (d.amount / total) * Math.PI * 2
      ctx.fillStyle = CATEGORY_COLORS[i % CATEGORY_COLORS.length]
      ctx.beginPath()
      ctx.moveTo(pieCx, cy)
      ctx.arc(pieCx, cy, pieR, angle, angle + slice)
      ctx.closePath()
      ctx.fill()
      slices.push({ category: d.category, startAngle: angle, endAngle: angle + slice })
      angle += slice
    })
    this._pieHitTest = this._pieHitTest || {}
    this._pieHitTest[canvasId] = { cx: pieCx, cy, r: pieR, inner, slices, type }

    // 抠空 + 中心文字
    ctx.fillStyle = '#ffffff'
    ctx.beginPath()
    ctx.arc(pieCx, cy, inner, 0, Math.PI * 2)
    ctx.fill()
    ctx.fillStyle = '#0f172a'
    ctx.font = '9px sans-serif'
    ctx.textAlign = 'center'
    ctx.fillText('总计', pieCx, cy - 4)
    ctx.font = 'bold 11px sans-serif'
    ctx.fillText('¥' + total.toFixed(0), pieCx, cy + 8)

    // ===== 右侧图例 =====
    const legendX = w * 0.5 + 8
    const rowH = Math.min(h / Math.max(data.length, 1), 22)
    const colorW = 8
    const textX = legendX + colorW + 6
    const amountX = w - 6

    data.forEach((d, i) => {
      const y = (i + 0.5) * rowH + (h - data.length * rowH) / 2
      ctx.fillStyle = CATEGORY_COLORS[i % CATEGORY_COLORS.length]
      ctx.fillRect(legendX, y - 4, colorW, 8)
      ctx.fillStyle = '#0f172a'
      ctx.font = '10px sans-serif'
      ctx.textAlign = 'left'
      ctx.textBaseline = 'middle'
      ctx.fillText(d.category, textX, y)
      ctx.fillStyle = '#9a9081'
      ctx.textAlign = 'right'
      ctx.fillText('¥' + d.amount.toFixed(0), amountX, y)
    })
  },

  onPieTap(e) {
    // 通用 hit-test：兼容 incomePie 和 expensePie
    const canvasId = e.currentTarget.dataset.pieId
    const data = this._pieHitTest && this._pieHitTest[canvasId]
    if (!data) return
    const { x, y } = e.detail
    const dx = x - data.cx
    const dy = y - data.cy
    const dist = Math.sqrt(dx * dx + dy * dy)
    if (dist > data.r || dist < data.inner) return
    // atan2(dy, dx) 在 screen 坐标系里 = 与 drawPie 同向的角度（-π/2 起）
    let angle = Math.atan2(dy, dx)
    while (angle < -Math.PI / 2) angle += 2 * Math.PI
    while (angle >= 3 * Math.PI / 2) angle -= 2 * Math.PI
    for (const s of data.slices) {
      if (angle >= s.startAngle && angle < s.endAngle) {
        this.openCategoryDetail(s.category, data.type)
        return
      }
    }
  },

// ============== 7. Expense bar (top 8 排行) ==============
  async drawExpenseBar() {
    const { canvas, rect } = await this._queryCanvas('expenseBar')
    if (!canvas) return
    const setup = this._setupCanvas(canvas, rect)
    if (!setup) return false
    const { ctx, w, h } = setup
    ctx.clearRect(0, 0, w, h)
    const data = this.data.categoryData
      .filter(d => d.type === 'expense')
      .sort((a, b) => a.amount - b.amount)  // 反转：少的在上
      .slice(0, 8)
    if (data.length === 0) {
      ctx.fillStyle = '#9a9081'
      ctx.font = '12px sans-serif'
      ctx.textAlign = 'center'
      ctx.fillText('暂无分类支出数据', w / 2, h / 2)
      return
    }
    const max = Math.max(...data.map(d => d.amount), 1)
    const padX = 100
    const padY = 16
    const chartW = w - padX - 32
    const rowH = (h - padY * 2) / data.length
    const barH = Math.min(rowH * 0.6, 24)
    data.forEach((d, i) => {
      const y = padY + i * rowH + (rowH - barH) / 2
      const barW = (d.amount / max) * chartW
      // 标签
      ctx.fillStyle = '#0f172a'
      ctx.font = '12px sans-serif'
      ctx.textAlign = 'right'
      ctx.textBaseline = 'middle'
      ctx.fillText(d.category, padX - 8, y + barH / 2)
      // 柱
      ctx.fillStyle = '#ef4444'
      this._roundRect(ctx, padX, y, barW, barH, 6)
      ctx.fill()
      // 数值
      ctx.fillStyle = '#0f172a'
      ctx.font = '11px sans-serif'
      ctx.textAlign = 'left'
      ctx.fillText('¥' + d.amount.toFixed(0), padX + barW + 6, y + barH / 2)
    })
  },

  // ============== 详情弹窗 ==============
  async openDateDetail(date) {
    this.setData({
      detailModal: { show: true, title: date, records: [], loading: true }
    })
    try {
      const res = await api.getBillList({ start: date, end: date, page_size: 100 })
      const records = (res.list || []).map(r => ({
        ...r,
        amountDisplay: (r.amount || 0).toFixed(2)
      }))
      this.setData({
        detailModal: { show: true, title: date, records, loading: false }
      })
    } catch (e) {
      this.setData({ detailModal: { show: false, title: '', records: [], loading: false } })
    }
  },

  async openCategoryDetail(category, type) {
    const title = category === 'all'
      ? (type === 'income' ? '全部收入' : '全部支出')
      : `${category} · ${type === 'income' ? '收入' : '支出'}`
    this.setData({
      detailModal: { show: true, title, records: [], loading: true }
    })
    try {
      const params = { type, page_size: 100, start: this.data.rangeStart, end: this.data.rangeEnd }
      if (category !== 'all') params.category = category
      const res = await api.getBillList(params)
      const records = (res.list || []).map(r => ({
        ...r,
        amountDisplay: (r.amount || 0).toFixed(2)
      }))
      this.setData({
        detailModal: { show: true, title, records, loading: false }
      })
    } catch (e) {
      this.setData({ detailModal: { show: false, title: '', records: [], loading: false } })
    }
  },

  closeDetail() {
    this.setData({ detailModal: { show: false, title: '', records: [], loading: false } })
  },

  onOpenBudget() {
    wx.navigateTo({ url: '/pages/budget/budget' })
  },

  // ============== #6 数据点睛：触摸处理 ==============
  onChartTouchStart(e) {
    const { chartId, chartType } = e.currentTarget.dataset
    const t = e.touches[0]
    const x = t.x
    const y = t.y
    this._showTooltipAt(chartId, chartType, x, y)
  },

  onChartTouchEnd() {
    // 触摸结束：保留 tooltip 一小段时间（让用户看清）然后消失
    // 简单实现：直接消失；如果想要更柔和，setTimeout 200ms 再隐藏
    this.setData({ tooltip: { ...this.data.tooltip, visible: false } })
  },

  _showTooltipAt(chartId, chartType, x, y) {
    const hit = this._hitTestChart(chartId, chartType, x, y)
    if (!hit) {
      this.setData({ tooltip: { ...this.data.tooltip, visible: false, chartId } })
      return
    }
    const data = this._getChartData(chartId)
    const tip = buildTooltip(chartType, hit, data)
    if (!tip) {
      this.setData({ tooltip: { ...this.data.tooltip, visible: false, chartId } })
      return
    }
    // tooltip 显示在触碰点上方
    this.setData({
      tooltip: {
        visible: true,
        chartId,
        title: tip.title,
        value: tip.value,
        subText: tip.subText,
        x,
        y
      }
    })
  },

  _getChartData(chartId) {
    if (chartId === 'incomePie') return this.data.categoryData.filter(d => d.type === 'income')
    if (chartId === 'expensePie') return this.data.categoryData.filter(d => d.type === 'expense')
    if (chartId === 'barChart') {
      const s = this.data.summary
      if (!s) return null
      return {
        labels: ['收入', '支出'],
        current: [s.income || 0, s.expense || 0],
        previous: [(s.previous && s.previous.income) || 0, (s.previous && s.previous.expense) || 0]
      }
    }
    if (chartId === 'expenseBar') {
      // 横条排行：按 category + amount
      return this.data.categoryData
        .filter(d => d.type === 'expense')
        .sort((a, b) => b.amount - a.amount)
        .slice(0, 8)
    }
    if (chartId === 'trendChart') return this.data.trendData
    return null
  },

  _hitTestChart(chartId, chartType, x, y) {
    if (chartType === 'pie') {
      const data = this._pieHitTest && this._pieHitTest[chartId]
      if (!data) return null
      const dx = x - data.cx
      const dy = y - data.cy
      const dist = Math.sqrt(dx * dx + dy * dy)
      if (dist > data.r || dist < data.inner) return null
      let angle = Math.atan2(dy, dx)
      while (angle < -Math.PI / 2) angle += 2 * Math.PI
      while (angle >= 3 * Math.PI / 2) angle -= 2 * Math.PI
      for (let i = 0; i < data.slices.length; i++) {
        const s = data.slices[i]
        if (angle >= s.startAngle && angle < s.endAngle) {
          const total = this._getChartData(chartId).reduce((sum, d) => sum + d.amount, 0)
          return { index: i, total }
        }
      }
      return null
    }

    if (chartType === 'bar') {
      // 柱图：2 组（收入/支出），每组 2 柱（本期/上期）
      // 用 _barHitTest 找组，再判断本期/上期
      const data = this._barHitTest
      if (!data) return null
      let group = -1
      for (let i = 0; i < data.groups.length; i++) {
        if (x >= data.groups[i].x0 && x <= data.groups[i].x1) {
          group = i
          break
        }
      }
      if (group < 0) return null
      // 判断本期/上期：bar 中心 x0 + barW/2
      // 简单：先取 bar 中心，再判断
      const s = this.data.summary
      if (!s) return null
      const sData = this._getChartData(chartId)
      if (!sData || !sData.current || !sData.previous) return null
      const groupW = (sData.current.length > 0)
        ? (data.groups[group].x1 - data.groups[group].x0)
        : 0
      // 重算 bar 中心位置（与 drawBar 一致）
      // 简单方案：x 在 group 左半 → cur，右半 → prev
      const midX = (data.groups[group].x0 + data.groups[group].x1) / 2
      const period = x < midX ? 'cur' : 'prev'
      return { group, period }
    }

    if (chartType === 'trend') {
      // 6 月趋势：3 条线（收入/支出/结余），x 找最近月份
      const t = this.data.trendData
      if (!t || !t.months || t.months.length === 0) return null
      // canvas 的 chart 区域 = x ∈ [pad, w-pad]，[y] 方向任意
      // 假设 pad ≈ 48（与 drawTrend 一致）
      const pad = 48
      const w = this.data.tooltip._lastW || 300  // 拿不到准确 w，用近似
      const chartW = w - pad * 2
      const xStep = chartW / Math.max(t.months.length - 1, 1)
      if (x < pad || xStep <= 0) return null
      const relX = x - pad
      let idx = Math.round(relX / xStep)
      idx = Math.max(0, Math.min(t.months.length - 1, idx))
      // 简单：固定显示 income（实际可按 y 找最近线）
      return { index: idx, lineType: 'income' }
    }

    if (chartType === 'expenseBar') {
      // 横条：每行一个分类。y 找行号
      const data = this._getChartData(chartId)
      if (!data || data.length === 0) return null
      // canvas 高度、padX 估算（与 drawExpenseBar 一致：padY=16, barH 由 rowH 决定）
      // canvas 在 _queryCanvas 里拿过，但这里简化：用 _canvasRect 缓存
      const rect = this._canvasRects && this._canvasRects.expenseBar
      if (!rect) return null
      const h = rect.height
      const padY = 16
      const rowH = (h - padY * 2) / data.length
      if (y < padY || y > h - padY) return null
      const idx = Math.floor((y - padY) / rowH)
      if (idx < 0 || idx >= data.length) return null
      return { index: idx, total: data.reduce((s, d) => s + d.amount, 0) }
    }

    return null
  },

  // ============== 导出图表为 PNG ==============
  async onExportChart(e) {
    const id = e.currentTarget.dataset.id
    const { canvas } = await this._queryCanvas(id)
    if (!canvas) {
      wx.showToast({ title: '图表未就绪', icon: 'none' })
      return
    }
    wx.showLoading({ title: '正在导出…' })
    try {
      // canvasToTempFilePath：type="2d" 模式下传 node
      const tempFilePath = await new Promise((resolve, reject) => {
        wx.canvasToTempFilePath({
          canvas,
          fileType: 'png',
          quality: 1,
          success: res => resolve(res.tempFilePath),
          fail: reject
        })
      })
      wx.hideLoading()
      // 保存到相册（需要用户授权）
      const saveRes = await new Promise((resolve, reject) => {
        wx.saveImageToPhotosAlbum({
          filePath: tempFilePath,
          success: resolve,
          fail: reject
        })
      })
      wx.showToast({ title: '已保存到相册', icon: 'success' })
    } catch (e) {
      wx.hideLoading()
      const msg = e.errMsg || ''
      if (msg.includes('auth') || msg.includes('authorize')) {
        wx.showModal({
          title: '需要相册权限',
          content: '请在设置中允许保存图片到相册',
          confirmText: '去设置',
          success: r => {
            if (r.confirm) wx.openSetting()
          }
        })
      } else {
        wx.showToast({ title: '导出失败', icon: 'none' })
      }
    }
  }
})
