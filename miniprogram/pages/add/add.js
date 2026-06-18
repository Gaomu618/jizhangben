const api = require('../../utils/api.js')
const { CATEGORIES } = require('../../utils/constants.js')

// 智能分类触发门槛：备注 >= 2 字符才发请求（避免每次按键都打）
const CLASSIFY_MIN_LEN = 2
// 防抖：停止输入 400ms 后才发请求
const CLASSIFY_DEBOUNCE_MS = 400
// 置信度等级：>= 0.7 高（绿）、>= 0.4 中（蓝）、< 0.4 低（黄）
const CONFIDENCE_THRESHOLDS = { high: 0.7, mid: 0.4 }

Page({
  data: {
    date: '',
    amount: '',
    type: 'expense',
    category: '',
    categories: CATEGORIES.expense,
    note: '',
    submitting: false,
    // 智能分类提示（点 wxml 渲染）
    classifyHint: null  // null=不显示 | { category, type, confidence, matched, level, percentText }
  },

  onLoad() {
    const now = new Date()
    const year = now.getFullYear()
    const month = String(now.getMonth() + 1).padStart(2, '0')
    const day = String(now.getDate()).padStart(2, '0')
    this.setData({
      date: `${year}-${month}-${day}`,
      category: CATEGORIES.expense[0]
    })
  },

  onUnload() {
    // 清理 debounce 定时器
    if (this._classifyTimer) clearTimeout(this._classifyTimer)
  },

  onDateChange(e) {
    this.setData({ date: e.detail.value })
  },

  onAmountInput(e) {
    this.setData({ amount: e.detail.value })
  },

  onTypeChange(e) {
    const type = e.currentTarget.dataset.type
    const categories = type === 'expense' ? CATEGORIES.expense : CATEGORIES.income
    this.setData({ type, categories, category: categories[0] })
  },

  onCategoryTap(e) {
    // 用户主动改了分类 → 隐藏智能分类提示（不再推荐）
    this.setData({
      category: e.currentTarget.dataset.cat,
      classifyHint: null
    })
  },

  onNoteInput(e) {
    const note = e.detail.value
    this.setData({ note })
    this.scheduleClassify(note)
  },

  // debounce 后调用智能分类
  scheduleClassify(note) {
    if (this._classifyTimer) clearTimeout(this._classifyTimer)
    const trimmed = (note || '').trim()
    if (trimmed.length < CLASSIFY_MIN_LEN) {
      this.setData({ classifyHint: null })
      return
    }
    this._classifyTimer = setTimeout(() => {
      this.runClassify(trimmed)
    }, CLASSIFY_DEBOUNCE_MS)
  },

  async runClassify(text) {
    try {
      const res = await api.classifyText(text)
      // 后端成功时：{ category, sub_category, type, confidence, matched, sub_matched }
      // 未能识别时 category=null
      if (!res || !res.category) {
        this.setData({ classifyHint: null })
        return
      }
      const confidence = typeof res.confidence === 'number' ? res.confidence : 0
      let level = 'low'
      if (confidence >= CONFIDENCE_THRESHOLDS.high) level = 'high'
      else if (confidence >= CONFIDENCE_THRESHOLDS.mid) level = 'mid'
      const percentText = Math.round(confidence * 100) + '%'
      const matched = (res.matched || []).slice(0, 2).join('、')  // 只展示前 2 个关键词
      // 细分用 · 隔开：餐饮 · 外卖
      const categoryText = res.sub_category
        ? `${res.category} · ${res.sub_category}`
        : res.category
      this.setData({
        classifyHint: {
          category: res.category,
          subCategory: res.sub_category || '',
          categoryText,
          type: res.type,
          confidence,
          percentText,
          level,
          matched
        }
      })
    } catch (e) {
      // 静默失败：不影响用户继续输入
      console.warn('[classify] 失败:', e && (e.message || e.code))
    }
  },

  // 点智能分类提示 → 应用推荐分类
  onApplyClassify() {
    const hint = this.data.classifyHint
    if (!hint) return
    // 如果推荐类型和当前选的类型不一致，切类型（同时切 categories）
    let { type, categories, category } = this.data
    if (type !== hint.type) {
      type = hint.type
      categories = type === 'expense' ? CATEGORIES.expense : CATEGORIES.income
    }
    // 推荐分类不在当前分类列表里（理论不该发生） → 加进去
    if (!categories.includes(hint.category)) {
      categories = [hint.category, ...categories]
    }
    category = hint.category
    this.setData({ type, categories, category })
    // 应用后 500ms 清掉提示（让用户看到"已应用"的反馈）
    setTimeout(() => {
      this.setData({ classifyHint: null })
    }, 600)
  },

  async onSubmit() {
    const { date, amount, type, category, note } = this.data
    if (!amount || parseFloat(amount) <= 0) {
      wx.showToast({ title: '请输入正确金额', icon: 'none' })
      return
    }
    if (!category) {
      wx.showToast({ title: '请选择分类', icon: 'none' })
      return
    }
    this.setData({ submitting: true })
    try {
      const res = await api.addBill({ date, amount: parseFloat(amount), type, category, note })
      wx.showToast({ title: `已记 ${res.amount || amount} 元`, icon: 'success', duration: 1500 })
      // 1.5s 后跳回首页，让 toast 显示久一点
      setTimeout(() => {
        wx.switchTab({ url: '/pages/index/index' })
        this.setData({ submitting: false })
      }, 1500)
    } catch (e) {
      // 把错误显式告诉用户（之前只 console.error，看不到）
      const msg = (e && e.message) || (e && e.code ? `错误 ${e.code}` : '网络错误，请重试')
      wx.showToast({ title: msg, icon: 'none', duration: 2500 })
      console.error('[add onSubmit]', e)
      this.setData({ submitting: false })
    }
  }
})
