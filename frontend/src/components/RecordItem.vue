<template>
  <BaseCard padding="sm" :hoverable="true" class="record-item">
    <div class="record-content">
      <BaseAvatar :name="record.category" shape="square" size="sm" />
      <div class="record-info">
        <p class="record-title">{{ record.note || record.category }}</p>
        <p class="record-meta">
          <BaseTag :variant="record.type === 'income' ? 'positive' : 'neutral'" toneStyle="soft" size="sm">
            {{ record.category }}
          </BaseTag>
          <span class="muted-sm">· {{ record.date }}</span>
        </p>
      </div>
      <div class="record-amount numeric" :class="record.type === 'income' ? 'text-positive' : 'text-expense'">
        <span class="num-sign">{{ record.type === 'income' ? '+' : '-' }}</span>¥{{ Number(record.amount).toFixed(2) }}
      </div>
    </div>
  </BaseCard>
</template>

<script setup>
import { BaseCard, BaseAvatar, BaseTag } from './base'

defineProps({
  record: { type: Object, required: true },
})

defineEmits(['edit', 'delete'])
</script>

<style scoped>
.record-item { margin: 0; }
.record-content {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
}
.record-info { flex: 1; min-width: 0; }
.record-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-primary);
  margin: 0;
}
.record-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  margin-top: 4px;
  color: var(--color-text-muted);
}
.record-amount {
  font-size: 16px;
  font-weight: 600;
  letter-spacing: -0.02em;
  flex-shrink: 0;
}
.muted-sm { color: var(--color-text-muted); font-size: 11px; font-weight: 400; }
</style>
