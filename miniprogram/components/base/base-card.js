Component({
  properties: {
    variant:  { type: String, value: 'default' },  // default | dark | bordered | gradient
    padding:  { type: String, value: 'md' },       // sm | md | lg
    hoverable:{ type: Boolean, value: false },
    selected: { type: Boolean, value: false },
    disabled: { type: Boolean, value: false }
  },
  methods: {
    onTap() {
      if (this.data.disabled) return
      this.triggerEvent('click')
    }
  }
})
