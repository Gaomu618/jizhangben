const api = require('../../utils/api.js')
const app = getApp()

const CATEGORY_EMOJIS = {
  '餐饮': '🍜', '交通': '🚗', '购物': '🛒', '娱乐': '🎮',
  '医疗': '💊', '居住': '🏠', '教育': '📚', '其他': '📝',
  '工资': '💰', '奖金': '🎁', '投资': '📈', '兼职': '💼', '红包': '🧧'
}

Page({
  data: {
    trashList: [],
    expandedId: null,
    categoryEmojis: CATEGORY_EMOJIS,
    categoryList: ['全部分类', '餐饮', '交通', '购物', '居住', '娱乐', '医疗', '教育', '其他', '工资', '奖金', '投资', '兼职', '红包'],
    categoryIndex: 0,
    filters: { start: '', end: '', category: '' }
  },

  onShow() {
    this.loadList()
    this.refreshCount()
  },

  get hasActiveFilter() {
    return !!(this.data.filters.start || this.data.filters.end || this.data.filters.category)
  },

  async loadList() {
    try {
      const params = { page_size: 50 }
      if (this.data.filters.start) params.start = this.data.filters.start
      if (this.data.filters.end) params.end = this.data.filters.end
      if (this.data.filters.category) params.category = this.data.filters.category
      const res = await api.getTrash(params)
      this.setData({ trashList: res.list || [] })
    } catch (e) {
      console.error('[trash loadList]', e)
    }
  },

  async refreshCount() {
    try {
      const res = await api.getTrashCount()
      app.globalData.trashCount = res.count
    } catch (e) {
      // 静默
    }
  },

  onStartChange(e) {
    this.setData({ 'filters.start': e.detail.value }, () => this.loadList())
  },
  onEndChange(e) {
    this.setData({ 'filters.end': e.detail.value }, () => this.loadList())
  },
  onCategoryChange(e) {
    const idx = e.detail.value
    const cat = idx === 0 ? '' : this.data.categoryList[idx]
    this.setData({ categoryIndex: idx, 'filters.category': cat }, () => this.loadList())
  },
  clearFilter() {
    this.setData({
      filters: { start: '', end: '', category: '' },
      categoryIndex: 0
    }, () => this.loadList())
  },

  toggleDetail(e) {
    const id = e.currentTarget.dataset.id
    this.setData({ expandedId: this.data.expandedId === id ? null : id })
  },

  async onRestore(e) {
    const id = e.currentTarget.dataset.id
    try {
      await api.restore(id)
      wx.showToast({ title: '已还原', icon: 'success' })
      this.setData({
        trashList: this.data.trashList.filter(item => item.id !== id),
        expandedId: this.data.expandedId === id ? null : this.data.expandedId
      })
      this.refreshCount()
    } catch (e) {
      console.error(e)
    }
  },

  onPurge(e) {
    const id = e.currentTarget.dataset.id
    wx.showModal({
      title: '永久删除',
      content: '删除后无法恢复，确定要永久删除吗？',
      confirmText: '永久删除',
      confirmColor: '#d94f1e',
      success: async (res) => {
        if (!res.confirm) return
        try {
          await api.purge(id)
          wx.showToast({ title: '已永久删除', icon: 'success' })
          this.setData({
            trashList: this.data.trashList.filter(item => item.id !== id),
            expandedId: this.data.expandedId === id ? null : this.data.expandedId
          })
          this.refreshCount()
        } catch (e) {
          console.error(e)
        }
      }
    })
  },

  onRestoreAll() {
    if (this.data.trashList.length === 0) return
    wx.showModal({
      title: '还原全部',
      content: `将还原当前列表中的 ${this.data.trashList.length} 条记录`,
      success: async (res) => {
        if (!res.confirm) return
        try {
          const ids = this.data.trashList.map(item => item.id)
          await api.restoreBatchTrash(ids)
          wx.showToast({ title: '已全部还原', icon: 'success' })
          this.loadList()
          this.refreshCount()
        } catch (e) {
          console.error(e)
        }
      }
    })
  },

  onEmpty() {
    if (this.data.trashList.length === 0) return
    wx.showModal({
      title: '清空回收站',
      content: `将永久删除当前列表中的 ${this.data.trashList.length} 条记录，无法恢复`,
      confirmText: '永久清空',
      confirmColor: '#d94f1e',
      success: async (res) => {
        if (!res.confirm) return
        try {
          await api.emptyTrash()
          wx.showToast({ title: '已清空回收站', icon: 'success' })
          this.loadList()
          this.refreshCount()
        } catch (e) {
          console.error(e)
        }
      }
    })
  }
})
