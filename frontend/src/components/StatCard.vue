<template>
  <BaseCard padding="md" class="stat-card">
    <BaseEyebrow>{{ title }}</BaseEyebrow>
    <p class="stat-value numeric" :class="valueClass">¥{{ value.toFixed(2) }}</p>
    <p v-if="hint" class="stat-hint">{{ hint }}</p>
  </BaseCard>
</template>

<script setup>
import { computed } from 'vue'
import { BaseCard, BaseEyebrow } from './base'

const props = defineProps({
  title: { type: String, required: true },
  value: { type: [Number, String], default: 0 },
  color: { type: String, default: 'neutral' },  // positive | negative | accent | neutral
  hint:  { type: String, default: '' },
})

const valueClass = computed(() => {
  switch (props.color) {
    case 'positive': return 'text-positive'
    case 'negative': return 'text-expense'
    case 'accent':   return 'text-accent'
    default:         return ''
  }
})
</script>

<style scoped>
.stat-card { display: flex; flex-direction: column; gap: 6px; }
.stat-value {
  font-size: 28px;
  font-weight: 600;
  letter-spacing: -0.025em;
  line-height: 1.1;
  color: var(--color-text-primary);
  margin: 4px 0 0;
}
.stat-hint {
  font-size: 11px;
  color: var(--color-text-muted);
  margin: 0;
}
</style>
