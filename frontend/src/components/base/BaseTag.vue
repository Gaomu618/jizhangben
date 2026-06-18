<template>
  <span :class="['base-tag', `tag-${variant}`, `tag-style-${toneStyle}`, `tag-size-${size}`]">
    <slot name="icon" />
    <span class="tag-label"><slot /></span>
  </span>
</template>

<script setup>
// 注意：prop 名不能叫 `style`，那是 Vue 保留的 HTML attribute 名
// （父组件写 style="soft" 时 Vue 会把 "soft" 当成 css style object 处理，
//  触发 "Invalid prop: type check failed for prop style" 警告）
// 用 `toneStyle` 避免冲突
defineProps({
  variant:  { type: String, default: 'neutral' },  // neutral | positive | warning | negative | accent | gold
  toneStyle:{ type: String, default: 'soft' },     // solid | soft | outline
  size:     { type: String, default: 'md' },        // sm | md | lg
})
</script>

<style scoped>
.base-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  border-radius: 999px;
  font-weight: 500;
  white-space: nowrap;
  font-family: inherit;
}
.tag-size-sm { padding: 2px 8px; font-size: 11px; }
.tag-size-md { padding: 4px 10px; font-size: 12px; }
.tag-size-lg { padding: 6px 14px; font-size: 13px; }

/* ============== Variants × Styles ============== */
.tag-neutral {
  --tag-color: var(--color-text-secondary);
  --tag-bg: var(--paper-200);
  --tag-border: transparent;
}
.tag-positive {
  --tag-color: var(--color-feedback-positive);
  --tag-bg: var(--green-50);
  --tag-border: transparent;
}
.tag-warning {
  --tag-color: #92590a;
  --tag-bg: var(--gold-50);
  --tag-border: transparent;
}
.tag-negative {
  --tag-color: #b53d12;
  --tag-bg: var(--orange-50);
  --tag-border: transparent;
}
.tag-accent {
  --tag-color: var(--color-action-accent);
  --tag-bg: var(--orange-50);
  --tag-border: transparent;
}
.tag-gold {
  --tag-color: var(--gold-500);
  --tag-bg: var(--gold-50);
  --tag-border: transparent;
}

.tag-style-solid { background: var(--tag-color); color: var(--color-text-inverse); border: 1px solid transparent; }
.tag-style-soft  { background: var(--tag-bg); color: var(--tag-color); border: 1px solid transparent; }
.tag-style-outline { background: transparent; color: var(--tag-color); border: 1px solid var(--tag-color); }
</style>
