Component({
  options: { multipleSlots: true },
  properties: {
    title:   { type: String, value: '' },
    message: { type: String, value: '' },
    cta:     { type: Boolean, value: false }
  }
})
