<template>
  <svg :width="size" :height="size" viewBox="0 0 24 24" fill="none" :aria-label="name" role="img">
    <rect x="3.5" y="13" width="3.5" height="7.5" rx="1" stroke="currentColor" stroke-width="1.6"/>
    <rect x="10.25" y="8" width="3.5" height="12.5" rx="1" stroke="currentColor" stroke-width="1.6"/>
    <rect x="17" y="3.5" width="3.5" height="17" rx="1" stroke="currentColor" stroke-width="1.6"/>
  </svg>
</template>

<script setup>
defineProps({
  size: { type: [Number, String], default: 20 },
  name: { type: String, default: '统计' },
})
</script>
