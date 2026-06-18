<template>
  <svg :width="size" :height="size" viewBox="0 0 24 24" fill="none" :aria-label="name" role="img">
    <path d="M4 7h16" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
    <path d="M9.5 7V5.5A1.5 1.5 0 0 1 11 4h2a1.5 1.5 0 0 1 1.5 1.5V7" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
    <path d="M6 7.5 7 19a2 2 0 0 0 2 1.8h6a2 2 0 0 0 2-1.8l1-11.5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
    <path d="M10 11v6M14 11v6" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" opacity="0.6"/>
  </svg>
</template>

<script setup>
defineProps({
  size: { type: [Number, String], default: 20 },
  name: { type: String, default: '回收站' },
})
</script>
