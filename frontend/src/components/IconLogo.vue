<template>
  <svg :width="size" :height="size" viewBox="0 0 24 24" fill="none" :aria-label="name" role="img">
    <path d="M4 19V6.5A2.5 2.5 0 0 1 6.5 4h11A2.5 2.5 0 0 1 20 6.5V18a3 3 0 0 1-3 3H5"
          stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
    <path d="M4 19a3 3 0 0 1 3-3h10" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
    <circle cx="9" cy="9.5" r="1.2" fill="currentColor"/>
    <path d="M9 13h6" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
    <path d="M9 15.5h4" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" opacity="0.6"/>
  </svg>
</template>

<script setup>
defineProps({
  size: { type: [Number, String], default: 20 },
  name: { type: String, default: '账本' },
})
</script>
