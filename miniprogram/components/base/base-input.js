Component({
  options: { multipleSlots: true },
  properties: {
    value:       { type: String, value: '' },
    label:       { type: String, value: '' },
    type:        { type: String, value: 'text' },   // text | number | digit | password | textarea | nickname
    variant:     { type: String, value: 'default' },// default | filled | flushed
    size:        { type: String, value: 'md' },     // sm | md | lg
    placeholder: { type: String, value: '' },
    hint:        { type: String, value: '' },
    error:       { type: String, value: '' },
    disabled:    { type: Boolean, value: false },
    multiline:   { type: Boolean, value: false },
    rows:        { type: Number, value: 3 },
    maxlength:   { type: Number, value: 140 },
    prefix:      { type: Boolean, value: false },
    suffix:      { type: Boolean, value: false },
    focus:       { type: Boolean, value: false }    // 自动聚焦（用于 type=nickname 唤起微信昵称建议条）
  },
  methods: {
    // 透传原生 input 事件的完整 detail（含 value / cursor / keyCode），
    // 这样消费方写 e.detail.value 跟用原生 <input> 一致。
    // 历史 bug：之前传的是 e.detail.value（裸字符串），消费方拿到的 e.detail 就是字符串，
    // 再取 .value 永远 undefined → 整个 app 凡是用 base-input 的输入框都打不上字。
    onInput(e) {
      this.triggerEvent('input', e.detail)
    },
    onBlur(e) {
      this.triggerEvent('blur', e.detail)
    },
    onFocus(e) {
      this.triggerEvent('focus', e.detail)
    }
  }
})
