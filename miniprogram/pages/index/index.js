const api = require('../../utils/api.js')
const { CATEGORIES } = require('../../utils/constants.js')

// 左滑按钮宽度（rpx）— 两个按钮共 280rpx
const SWIPE_ACTION_WIDTH = 140
// 触发"打开"动作的阈值（一半）
const SWIPE_OPEN_THRESHOLD = SWIPE_ACTION_WIDTH  // 140rpx

Page({
  data: {
    year: new Date().getFullYear(),
    month: new Date().getMonth() + 1,
    income: '0.00',
    expense: '0.00',
    balance: '0.00',
    bills: [],
    budgets: [],
    unbudgetedCategories: [],
    loading: false,
    // 应用内提醒 banner（替代订阅消息）
    // 同一时刻只展示最严重的一条，按严重度排序：over > warn > inactive
    alertBanner: null,  // null=不显示 | { level, icon, title, message, ruleType }
    // 左滑交互状态
    isSwiping: false,           // 是否正在拖动（用于去掉 transition）
    // 导入预览弹窗状态
    importPreview: {
      visible: false,
      loading: false,
      loadingText: '',
      done: false,
      error: '',
      filePath: '',
      preview: [],   // [[date, amount, type, category, note], ...] 来自 dry_run
      total: 0,
      duplicate: 0,
      errors: [],
      submitting: false
    },
    // 编辑账单弹窗状态
    editModal: {
      visible: false,
      id: null,
      date: '',
      amount: '',
      type: 'expense',
      category: '',
      categories: CATEGORIES.expense,
      note: '',
      submitting: false
    }
  },

  // 非响应式数据：touchstart 时的起始位置（避免每次 setData）
  _swipeStartX: 0,
  _swipeStartY: 0,
  _swipingIdx: -1,

  onLoad() {
    this.checkLogin()
  },

  onShow() {
    // 从 add 页面跳回时，onShow 触发，确保新加的账单能立刻显示
    this.loadData()
    // custom tabBar 同步选中态
    if (typeof this.getTabBar === 'function' && this.getTabBar()) {
      this.getTabBar().setData({ selected: 0 })
    }
  },

  onPullDownRefresh() {
    // 用户主动下拉刷新
    this.loadData().finally(() => wx.stopPullDownRefresh())
  },

  checkLogin() {
    const token = wx.getStorageSync('token')
    if (!token) {
      wx.reLaunch({ url: '/pages/login/login' })
    }
  },

  async loadData() {
    this.setData({ loading: true })
    try {
      const [stats, listData, budgets] = await Promise.all([
        api.getMonthlyStats(this.data.year, this.data.month),
        api.getBillList({ year: this.data.year, month: this.data.month }),
        api.getBudget({ year: this.data.year, month: this.data.month }).catch(() => [])
      ])
      const bills = listData.list || []
      const budgetListRaw = budgets || []
      // 找出本月有支出但没设预算的分类
      const budgetedCats = new Set(budgetListRaw.map(b => b.category))
      const unbudgeted = []
        .concat(...bills.map(b => b.category))
        .filter((c, i, arr) => arr.indexOf(c) === i && !budgetedCats.has(c))
      // 预计算预算行的金额字符串 + 内联样式（WXML style 不支持三元/方法调用）
      const budgetList = budgetListRaw.map(b => {
        const p = b.percent || 0
        return {
          ...b,
          spentRmb: (b.spent || 0).toFixed(0),
          budgetRmb: (b.budget || 0).toFixed(0),
          widthStyle: (p > 100 ? 100 : p) + '%',
          bgStyle: p >= 80 ? 'var(--color-feedback-warning)' : 'var(--color-action-accent)'
        }
      })
      const unbudgetedHint = unbudgeted.length > 0
        ? unbudgeted.slice(0, 3).join(' / ') + (unbudgeted.length > 3 ? '…' : '')
        : ''
      this.setData({
        income: stats.income.toFixed(2),
        expense: stats.expense.toFixed(2),
        balance: stats.balance.toFixed(2),
        bills,
        budgets: budgetList,
        unbudgetedCategories: unbudgeted,
        unbudgetedHint
      })
      // 预算提醒检查（服务端去重 + 频率控制，前端只负责本地弹窗）
      // 静默失败，不影响主流程
      this.checkBudgetAlerts()
    } catch (e) {
      const msg = (e && e.message) || (e && e.code ? `错误 ${e.code}` : '加载失败')
      wx.showToast({ title: msg, icon: 'none', duration: 2500 })
      console.error('[index loadData]', e)
    } finally {
      this.setData({ loading: false })
    }
  },

  // 异步拉一次预算检查，命中时设置 alertBanner（应用内 banner，不依赖订阅消息）
  // 服务端会做频率控制（同规则每天最多 1 次），前端不需要管
  async checkBudgetAlerts() {
    try {
      const res = await api.checkNotifications({
        year: this.data.year,
        month: this.data.month
      })
      const triggered = res.triggered || []
      if (triggered.length === 0) {
        this.setData({ alertBanner: null })
        return
      }
      // 挑最严重的一条展示（同时多条时）
      // 严重度排序：budget_over > budget_warn > inactive
      const SEVERITY = {
        'budget_over': 3,
        'budget_warn': 2,
        'inactive': 1
      }
      const top = triggered
        .map(t => ({ ...t, _sev: SEVERITY[t.rule_type] || 0 }))
        .sort((a, b) => b._sev - a._sev)[0]

      this.setData({
        alertBanner: this._formatBanner(top)
      })
    } catch (e) {
      // 静默失败：提醒是增强功能，不应阻塞主页
      console.warn('[checkBudgetAlerts] 静默失败:', e && (e.message || e.code))
    }
  },

  // 把后端 triggered 转成前端展示用的 banner 数据
  _formatBanner(triggered) {
    if (!triggered) return null
    const { rule_type, message, category, percent, days_idle } = triggered
    let level, icon, title, tapType
    if (rule_type === 'budget_over') {
      level = 'danger'
      icon = '🚨'
      title = '预算已超支'
      tapType = 'budget'
    } else if (rule_type === 'budget_warn') {
      level = 'warning'
      icon = '⚠️'
      title = '预算快用完了'
      tapType = 'budget'
    } else if (rule_type === 'inactive') {
      level = 'info'
      icon = '📝'
      title = '好久没记账了'
      tapType = 'index'  // 点 banner 留在首页（引导去加账）
    } else {
      level = 'info'
      icon = 'ℹ️'
      title = '提醒'
      tapType = 'index'
    }
    return { level, icon, title, message, ruleType: rule_type, tapType }
  },

  // 点 banner 内容区：根据 ruleType 跳到对应页
  onTapAlertBanner(e) {
    const tapType = e.currentTarget.dataset.type
    if (tapType === 'budget') {
      wx.navigateTo({ url: '/pages/budget/budget' })
    }
    // 'index' 不跳转（已经在首页）
  },

  // 点 × 关闭 banner（仅本会话，下次进来还会再推）
  onDismissAlertBanner() {
    this.setData({ alertBanner: null })
  },

  // ============ 左滑交互 ============
  // 手势开始：记录起始位置
  onSwipeStart(e) {
    const t = e.touches && e.touches[0]
    if (!t) return
    this._swipeStartX = t.clientX
    this._swipeStartY = t.clientY
    this._swipingIdx = parseInt(e.currentTarget.dataset.idx)
    this.setData({ isSwiping: true })
  },

  // 手势移动：实时更新 transform
  onSwipeMove(e) {
    const t = e.touches && e.touches[0]
    if (!t || this._swipingIdx < 0) return
    const dx = t.clientX - this._swipeStartX
    const dy = t.clientY - this._swipeStartY
    // 垂直滚动为主时不处理（让位给页面滚动）
    if (Math.abs(dy) > Math.abs(dx) * 1.5) return

    const idx = this._swipingIdx
    const bills = this.data.bills
    const cur = bills[idx]
    if (!cur) return
    // 起始位置（开放/关闭）
    const startX = cur.swipeOpen ? -SWIPE_ACTION_WIDTH * 2 : 0
    let nextX = startX + dx
    // 边界限制：[-(2*按钮宽), 0]
    const minX = -SWIPE_ACTION_WIDTH * 2
    if (nextX > 0) nextX = 0
    if (nextX < minX) nextX = minX

    // 局部更新这一条，避免整个列表重渲染
    const key = `bills[${idx}].swipeX`
    this.setData({ [key]: nextX })
  },

  // 手势结束：根据最终位置 snap 到开或关
  onSwipeEnd(e) {
    if (this._swipingIdx < 0) return
    this.setData({ isSwiping: false })
    const idx = this._swipingIdx
    const cur = this.data.bills[idx]
    if (!cur) return
    const curX = cur.swipeX || 0
    // 阈值判断：超过 1 个按钮宽度 → 打开
    const willOpen = curX < -SWIPE_OPEN_THRESHOLD
    // 关闭其他已打开的（保证同时只有一个 open）
    const bills = this.data.bills.map((b, i) => {
      if (i === idx) {
        return {
          ...b,
          swipeX: willOpen ? -SWIPE_ACTION_WIDTH * 2 : 0,
          swipeOpen: willOpen
        }
      }
      return { ...b, swipeX: 0, swipeOpen: false }
    })
    this._swipingIdx = -1
    this.setData({ bills })
  },

  // 收回：行 tap 区域（不在 content / actions 内）→ 关闭所有
  onSwipeRowTap() {
    // 内部 catchtap 已处理 content / actions；这里只兜底
    this._closeAllSwipes()
  },

  // 点账单本体：open 时关闭，closed 时无操作（不再跳转旧详情页）
  onSwipeContentTap() {
    const idx = this._swipingIdx >= 0 ? this._swipingIdx : -1
    // 找当前是否有 open 的
    const hasOpen = this.data.bills.some(b => b.swipeOpen)
    if (hasOpen) {
      this._closeAllSwipes()
    }
    // closed 状态点 content 不做任何事（旧逻辑是跳转，已移除）
  },

  // 关闭所有 swipe
  _closeAllSwipes() {
    if (!this.data.bills.some(b => b.swipeOpen || (b.swipeX && b.swipeX < 0))) return
    const bills = this.data.bills.map(b => ({ ...b, swipeX: 0, swipeOpen: false }))
    this.setData({ bills })
  },

  // 点滑出的"编辑" → 打开编辑弹窗
  onSwipeEdit(e) {
    const id = parseInt(e.currentTarget.dataset.id)
    this._openEditModal(id)
  },

  // 点滑出的"删除" → 二次确认 → 删除
  onSwipeDelete(e) {
    const id = parseInt(e.currentTarget.dataset.id)
    wx.showModal({
      title: '删除这笔账单？',
      content: '删除后可在回收站恢复（30 天内）',
      confirmText: '删除',
      cancelText: '取消',
      confirmColor: '#d94f1e',
      success: async (res) => {
        if (!res.confirm) return
        try {
          await api.deleteBill(id)
          wx.showToast({ title: '已删除', icon: 'success' })
          // 关闭可能打开的 swipe + 重新加载
          this._closeAllSwipes()
          this.loadData()
        } catch (e) {
          const msg = (e && e.message) || '删除失败'
          wx.showToast({ title: msg, icon: 'none' })
        }
      }
    })
  },

  // ============ 编辑账单弹窗 ============
  async _openEditModal(id) {
    // 先收起 swipe
    this._closeAllSwipes()
    try {
      const bill = await api.getBillDetail(id)
      const categories = bill.type === 'expense' ? CATEGORIES.expense : CATEGORIES.income
      this.setData({
        editModal: {
          visible: true,
          id: bill.id,
          date: bill.date,
          amount: bill.amount.toString(),
          type: bill.type,
          category: bill.category,
          categories,
          note: bill.note || '',
          submitting: false
        }
      })
    } catch (e) {
      wx.showToast({ title: '加载失败', icon: 'none' })
    }
  },

  // 点蒙层：收起弹窗（带未保存提示）
  onEditModalMaskTap() {
    if (this.data.editModal.submitting) return
    this._maybeWarnAndCloseEdit()
  },

  // 关闭按钮 / 取消
  onCloseEditModal() {
    if (this.data.editModal.submitting) return
    this._maybeWarnAndCloseEdit()
  },

  _maybeWarnAndCloseEdit() {
    const { date, amount, type, category, note } = this.data.editModal
    // 简化：如果弹窗已加载（必填有值），点空白给个"放弃修改？"提示
    if (amount) {
      wx.showModal({
        title: '放弃修改？',
        content: '当前修改未保存',
        confirmText: '放弃',
        cancelText: '继续编辑',
        confirmColor: '#d94f1e',
        success: (res) => {
          if (res.confirm) this._forceCloseEdit()
        }
      })
    } else {
      this._forceCloseEdit()
    }
  },

  _forceCloseEdit() {
    this.setData({
      'editModal.visible': false,
      'editModal.id': null
    })
  },

  onEditTypeChange(e) {
    const type = e.currentTarget.dataset.type
    const categories = type === 'expense' ? CATEGORIES.expense : CATEGORIES.income
    this.setData({
      'editModal.type': type,
      'editModal.categories': categories,
      'editModal.category': categories[0]
    })
  },

  onEditAmountInput(e) {
    this.setData({ 'editModal.amount': e.detail.value })
  },

  onEditCategoryTap(e) {
    this.setData({ 'editModal.category': e.currentTarget.dataset.cat })
  },

  onEditDateChange(e) {
    this.setData({ 'editModal.date': e.detail.value })
  },

  onEditNoteInput(e) {
    this.setData({ 'editModal.note': e.detail.value })
  },

  async onEditSave() {
    const { id, date, amount, type, category, note } = this.data.editModal
    if (!amount || parseFloat(amount) <= 0) {
      wx.showToast({ title: '请输入正确金额', icon: 'none' })
      return
    }
    if (!category) {
      wx.showToast({ title: '请选择分类', icon: 'none' })
      return
    }
    this.setData({ 'editModal.submitting': true })
    try {
      await api.editBill(id, { date, amount: parseFloat(amount), type, category, note })
      wx.showToast({ title: '已保存', icon: 'success' })
      this._forceCloseEdit()
      this.loadData()
    } catch (e) {
      const msg = (e && e.message) || '保存失败'
      wx.showToast({ title: msg, icon: 'none' })
    } finally {
      this.setData({ 'editModal.submitting': false })
    }
  },

  // 注：旧的 editBill 跳转已被左滑"编辑"弹窗替代（见 onSwipeEdit）

  prevMonth() {
    let { year, month } = this.data
    if (month === 1) {
      year--
      month = 12
    } else {
      month--
    }
    this.setData({ year, month }, () => this.loadData())
  },

  nextMonth() {
    let { year, month } = this.data
    if (month === 12) {
      year++
      month = 1
    } else {
      month++
    }
    this.setData({ year, month }, () => this.loadData())
  },

  // 注：旧的 editBill 跳转已被左滑"编辑"弹窗替代（见 onSwipeEdit）

  goAdd() {
    // 悬浮 + 按钮：跳转记一笔页
    wx.navigateTo({ url: '/pages/add/add' })
  },

  onOpenBudget() {
    wx.navigateTo({ url: '/pages/budget/budget' })
  },

  // ============ 导入账单（入口 A）============
  // 流程：选文件 → dry_run 预览 → 用户确认 → 真导入
  onImportBill() {
    // 让用户从聊天记录里选（微信支付小程序发的账单文件在「微信支付」聊天里）
    wx.chooseMessageFile({
      count: 1,
      type: 'file',
      extension: ['xlsx', 'csv', 'xls'],
      success: (res) => {
        const f = res.tempFiles && res.tempFiles[0]
        if (!f) return
        this.runDryRunPreview(f.path, f.name || '账单文件')
      },
      fail: (err) => {
        // 用户取消选择是常见操作，不弹错
        if (err && err.errMsg && err.errMsg.indexOf('cancel') === -1) {
          wx.showToast({ title: '打开文件失败', icon: 'none' })
        }
      }
    })
  },

  async runDryRunPreview(filePath, fileName) {
    // 打开弹窗并显示 loading
    this.setData({
      'importPreview.visible': true,
      'importPreview.loading': true,
      'importPreview.loadingText': `正在解析 ${fileName}...`,
      'importPreview.done': false,
      'importPreview.error': '',
      'importPreview.filePath': filePath,
      'importPreview.preview': [],
      'importPreview.total': 0,
      'importPreview.duplicate': 0,
      'importPreview.errors': []
    })
    try {
      const res = await api.importFile(filePath, true)
      // 后端 dry_run 成功返回 { preview, total, duplicate }
      if (!res || res.code !== undefined && res.code !== 0) {
        const msg = (res && res.message) || '解析失败'
        this.setData({
          'importPreview.loading': false,
          'importPreview.error': msg
        })
        return
      }
      // 兼容两种返回：直接 {preview,total,duplicate} 或 {data:{...}}
      const data = res.preview !== undefined ? res : (res.data || {})
      const preview = data.preview || []
      // dry_run 的 preview 是 tuple 数组 [date, amount, type, category, note]
      // 转成对象数组方便 wxml 用
      const items = preview.map(p => ({
        date: p[0],
        amount: parseFloat(p[1]).toFixed(2),
        type: p[2],
        category: p[3],
        note: p[4] || ''
      }))
      this.setData({
        'importPreview.loading': false,
        'importPreview.done': true,
        'importPreview.preview': items,
        'importPreview.total': data.total || 0,
        'importPreview.duplicate': data.duplicate || 0,
        'importPreview.errors': (res.errors) || []
      })
    } catch (e) {
      // 错误是对象时（api.js 会 reject(res.data)）取 message
      const msg = (e && e.message) || (e && e.code ? `错误 ${e.code}` : '解析失败，请确认文件格式')
      this.setData({
        'importPreview.loading': false,
        'importPreview.error': msg
      })
    }
  },

  async onConfirmImport() {
    const { filePath, total } = this.data.importPreview
    if (!filePath || total === 0) return
    this.setData({ 'importPreview.submitting': true })
    try {
      const res = await api.importFile(filePath, false)
      // 后端真导入返回 {imported, duplicate, errors}
      const data = res.imported !== undefined ? res : (res.data || {})
      const imported = data.imported || 0
      const dup = data.duplicate || 0
      const errs = data.errors || []
      this.setData({
        'importPreview.submitting': false,
        'importPreview.visible': false
      })
      // 反馈给用户
      let msg = `已导入 ${imported} 笔`
      if (dup > 0) msg += `，跳过重复 ${dup} 笔`
      wx.showToast({ title: msg, icon: 'success', duration: 2000 })
      // 刷新首页数据
      this.loadData()
      // 如果有解析错误，弹个 modal 让用户知道
      if (errs.length > 0) {
        setTimeout(() => {
          wx.showModal({
            title: '部分行未导入',
            content: errs.slice(0, 5).join('\n') + (errs.length > 5 ? `\n...还有 ${errs.length - 5} 条` : ''),
            showCancel: false,
            confirmText: '知道了'
          })
        }, 500)
      }
    } catch (e) {
      const msg = (e && e.message) || (e && e.code ? `错误 ${e.code}` : '导入失败')
      wx.showToast({ title: msg, icon: 'none', duration: 2500 })
      this.setData({ 'importPreview.submitting': false })
    }
  },

  onClosePreview() {
    if (this.data.importPreview.submitting) return // 导入中别关
    this.setData({
      'importPreview.visible': false,
      'importPreview.done': false,
      'importPreview.error': '',
      'importPreview.preview': []
    })
  }
})