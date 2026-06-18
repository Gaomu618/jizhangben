Component({
  options: { multipleSlots: true },
  properties: {
    variant:    { type: String, value: 'primary' },  // primary | accent | ghost | soft | dark | danger
    size:       { type: String, value: 'md' },        // sm | md | lg | xl
    type:       { type: String, value: 'default' },   // 转发给 <button>
    loading:    { type: Boolean, value: false },
    disabled:   { type: Boolean, value: false },
    block:      { type: Boolean, value: false },
    iconOnly:   { type: Boolean, value: false },
    openType:   { type: String, value: '' },          // 微信开放能力：share / getUserInfo 等
    // 外部样式覆盖（绕过组件样式隔离）
    customStyle: { type: String, value: '' },         // 例："flex:0 0 124rpx;justify-content:center"
    customClass: { type: String, value: '' }          // 例："my-btn-override"
  },
  methods: {
    onTap(e) {
      if (this.data.disabled || this.data.loading) return
      this.triggerEvent('click', e)
    }
  }
})
