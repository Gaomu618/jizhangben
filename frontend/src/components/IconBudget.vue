<template>
  <svg :width="size" :height="size" viewBox="0 0 24 24" fill="none" :aria-label="name" role="img">
    <circle cx="12" cy="12" r="8.5" stroke="currentColor" stroke-width="1.6"/>
    <circle cx="12" cy="12" r="5.5" stroke="currentColor" stroke-width="1.6"/>
    <circle cx="12" cy="12" r="2.5" fill="currentColor"/>
  </svg>
</template>

<script setup>
defineProps({
  size: { type: [Number, String], default: 20 },
  name: { type: String, default: '预算' },
})
</script>
