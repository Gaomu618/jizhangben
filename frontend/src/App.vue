<template>
  <div class="app-shell">
    <router-view />
  </div>
</template>

<script setup>
// TODO: 暗色模式已被冻结（与新 design tokens 冲突），待令牌体系稳定后再回归
// 原 darkMode 切换代码已移除
</script>

<style scoped>
.app-shell {
  min-height: 100vh;
  background: var(--color-bg-default);
}
</style>
