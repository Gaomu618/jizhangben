<template>
  <svg
    :viewBox="`0 0 ${width} ${height}`"
    preserveAspectRatio="none"
    :class="['sparkline', `tone-${tone}`]"
    role="img"
    :aria-label="alt || '趋势图'"
  >
    <defs v-if="fill">
      <linearGradient :id="gradientId" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" :stop-color="strokeColor" stop-opacity="0.22" />
        <stop offset="100%" :stop-color="strokeColor" stop-opacity="0" />
      </linearGradient>
    </defs>

    <path v-if="fill" :d="fillPath" :fill="`url(#${gradientId})`" />
    <path :d="linePath" fill="none" :stroke="strokeColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" />

    <!-- 视觉锚点：最新点 -->
    <circle v-if="data.length" :cx="lastX" :cy="lastY" r="3" :fill="strokeColor" />
  </svg>
</template>

<script setup>
import { computed, useId } from 'vue'

const props = defineProps({
  data:     { type: Array, required: true },         // numbers
  width:    { type: Number, default: 220 },
  height:   { type: Number, default: 60 },
  tone:     { type: String, default: 'accent' },     // accent | positive | ink | gold
  fill:     { type: Boolean, default: true },
  alt:      { type: String, default: '' },
})

const id = useId()
const gradientId = `spark-grad-${id.replace(/[^a-z0-9]/gi, '')}`

const strokeColor = computed(() => {
  switch (props.tone) {
    case 'positive': return 'var(--color-feedback-positive)'
    case 'ink':      return 'var(--color-text-primary)'
    case 'gold':     return 'var(--color-feedback-warning)'
    default:         return 'var(--color-action-accent)'
  }
})

const linePath = computed(() => {
  if (!props.data.length) return ''
  const max = Math.max(...props.data)
  const min = Math.min(...props.data)
  const range = max - min || 1
  const stepX = props.width / Math.max(props.data.length - 1, 1)
  return props.data
    .map((v, i) => {
      const x = i * stepX
      const y = props.height - ((v - min) / range) * (props.height - 8) - 4
      return `${i === 0 ? 'M' : 'L'} ${x.toFixed(2)} ${y.toFixed(2)}`
    })
    .join(' ')
})

const fillPath = computed(() => {
  if (!linePath.value) return ''
  return `${linePath.value} L ${props.width} ${props.height} L 0 ${props.height} Z`
})

const lastX = computed(() => {
  if (!props.data.length) return 0
  return ((props.data.length - 1) * props.width) / Math.max(props.data.length - 1, 1)
})
const lastY = computed(() => {
  if (!props.data.length) return 0
  const max = Math.max(...props.data)
  const min = Math.min(...props.data)
  const range = max - min || 1
  return props.height - ((props.data[props.data.length - 1] - min) / range) * (props.height - 8) - 4
})
</script>

<style scoped>
.sparkline {
  display: block;
  width: 100%;
  height: 60px;
  overflow: visible;
}
</style>
