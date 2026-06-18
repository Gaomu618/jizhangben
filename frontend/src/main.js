import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import './style.css'

// 国际化：通过 useI18n() 拿到 t / setLanguage / lang（模块只 export 了 useI18n + t + SUPPORTED_LANGUAGES）
import { useI18n } from './i18n'
const { t, setLanguage, lang } = useI18n()

// ECharts 按需引入（替代整个 echarts 包，体积从 ~900KB 降到 ~400KB）
import * as echarts from 'echarts/core'
import { BarChart, LineChart, PieChart } from 'echarts/charts'
import {
  GridComponent,
  TooltipComponent,
  LegendComponent,
  TitleComponent,
  GraphicComponent
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

echarts.use([
  BarChart, LineChart, PieChart,
  GridComponent, TooltipComponent, LegendComponent, TitleComponent, GraphicComponent,
  CanvasRenderer
])

// 暴露到 window，让 .vue 里的 window.echarts.init() 继续工作（不破坏现有代码）
window.echarts = echarts

const app = createApp(App)

// 全局属性：模板里直接用 {{ t('xxx') }} / {{ $t('xxx') }} 都可以
app.config.globalProperties.$t = t
app.config.globalProperties.$setLanguage = setLanguage
app.config.globalProperties.$lang = lang

app.use(router)
app.mount('#app')

// 创建背景粒子效果
function createBubble() {
  const bubble = document.createElement('div')
  bubble.className = 'bubble'
  const size = Math.random() * 60 + 20
  bubble.style.width = size + 'px'
  bubble.style.height = size + 'px'
  bubble.style.left = Math.random() * 100 + 'vw'
  bubble.style.animationDuration = Math.random() * 10 + 10 + 's'
  bubble.style.animationDelay = Math.random() * 5 + 's'
  document.body.appendChild(bubble)
  setTimeout(() => bubble.remove(), 20000)
}

// 每 800ms 创建一个气泡
setInterval(createBubble, 800)
// 初始化几个气泡
for (let i = 0; i < 8; i++) {
  setTimeout(createBubble, i * 500)
}