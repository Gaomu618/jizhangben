// Component：渲染空状态 UI
// 数据生成函数在 utils/empty-state.js

Component({
  properties: {
    state: {
      type: Object,
      value: null
    }
  },
  methods: {
    onCta() {
      if (this.data.state && this.data.state.cta && typeof this.data.state.cta.handler === 'function') {
        this.data.state.cta.handler()
      }
    }
  }
})
