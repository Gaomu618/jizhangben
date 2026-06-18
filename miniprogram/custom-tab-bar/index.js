// data:image/svg+xml;charset=utf-8, + URL 编码后的 SVG
// 颜色用 design token：muted #9a9081（未选）、accent #d94f1e（已选）
// stroke 1.6 / viewBox 24×24，跟项目"warm minimal"风格一致

const GRAY = '#9a9081'
const ORANGE = '#d94f1e'

// 账本：三行清单 + 左侧圆点
const ledger = (color) =>
  `data:image/svg+xml;charset=utf-8,${encodeURIComponent(
    `<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='${color}' stroke-width='1.6' stroke-linecap='round' stroke-linejoin='round'>` +
    `<line x1='8' y1='6' x2='20' y2='6'/>` +
    `<line x1='8' y1='12' x2='20' y2='12'/>` +
    `<line x1='8' y1='18' x2='20' y2='18'/>` +
    `<circle cx='5' cy='6' r='1.6' fill='${color}' stroke='none'/>` +
    `<circle cx='5' cy='12' r='1.6' fill='${color}' stroke='none'/>` +
    `<circle cx='5' cy='18' r='1.6' fill='${color}' stroke='none'/>` +
    `</svg>`
  )}`

// 统计：柱状图 + 基线
const chart = (color) =>
  `data:image/svg+xml;charset=utf-8,${encodeURIComponent(
    `<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='${color}' stroke-width='1.6' stroke-linecap='round' stroke-linejoin='round'>` +
    `<line x1='3' y1='20' x2='21' y2='20'/>` +
    `<rect x='5' y='12' width='3.5' height='8' rx='0.8'/>` +
    `<rect x='10.25' y='7' width='3.5' height='13' rx='0.8'/>` +
    `<rect x='15.5' y='14' width='3.5' height='6' rx='0.8'/>` +
    `</svg>`
  )}`

// 我的：圆形头 + 弧形肩
const user = (color) =>
  `data:image/svg+xml;charset=utf-8,${encodeURIComponent(
    `<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='${color}' stroke-width='1.6' stroke-linecap='round' stroke-linejoin='round'>` +
    `<circle cx='12' cy='8' r='4'/>` +
    `<path d='M4 21c0-4 4-7 8-7s8 3 8 7'/>` +
    `</svg>`
  )}`

Component({
  data: {
    selected: 0,
    tabs: [
      { text: '账本', pagePath: '/pages/index/index', normal: ledger(GRAY), active: ledger(ORANGE) },
      { text: '统计', pagePath: '/pages/stats/stats', normal: chart(GRAY), active: chart(ORANGE) },
      { text: '我的', pagePath: '/pages/mine/mine', normal: user(GRAY), active: user(ORANGE) }
    ]
  },
  methods: {
    onTap(e) {
      const { index, url } = e.currentTarget.dataset
      // 已经在当前 tab 时不重复切换
      if (index === this.data.selected) return
      wx.switchTab({ url })
    }
  }
})
