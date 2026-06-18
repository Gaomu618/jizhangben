<template>
  <div class="app app-bg">
    <!-- 顶部导航栏 -->
    <header class="nav">
      <div class="nav-left">
        <span class="nav-title"><IconLogo :size="22" /> {{ t('app.title') }}</span>
      </div>
      <div class="nav-right">
        <select v-model="selectedMonth" class="month-picker" @change="onMonthChange" :aria-label="t('nav.month')">
          <option v-for="m in monthOptions" :key="m.value" :value="m.value">{{ m.label }}</option>
        </select>
        <button class="icon-btn" @click="goStats" :title="t('nav.stats')" :aria-label="t('nav.stats')"><IconStats :size="20" /></button>
        <button class="icon-btn" @click="goBudget" :title="t('nav.budget')" :aria-label="t('nav.budget')"><IconBudget :size="20" /></button>
        <button class="icon-btn" @click="openMemoryModal" :title="t('nav.memory', '智能分类记忆')" :aria-label="t('nav.memory', '智能分类记忆')"><IconBrain :size="20" /></button>
        <button class="icon-btn icon-btn-trash" @click="openTrash" :title="t('nav.trash')" :aria-label="t('nav.trash')">
          <IconTrash :size="20" />
          <span v-if="trashCount > 0" class="trash-badge">{{ trashCount }}</span>
        </button>
        <button class="icon-btn" @click="goProfile" :title="'个人中心'" :aria-label="'个人中心'">
          <BaseAvatar :src="userAvatar" :name="userDisplayName" :size="28" />
        </button>
        <select :value="lang" @change="setLanguage($event.target.value)" class="lang-select" :title="t('language.switchTo')">
          <option v-for="l in SUPPORTED_LANGUAGES" :key="l.code" :value="l.code">{{ l.label }}</option>
        </select>
      </div>
    </header>

    <main class="main">
      <!-- ==================== Hero 余额区：1+3 布局（左大字 + 右深色引导卡） ==================== -->
      <section class="balance-row">
        <!-- 左侧：本月结余大字 -->
        <BaseCard padding="lg" class="balance-card">
          <BaseEyebrow tone="accent">No.01 · Monthly Balance · 本月</BaseEyebrow>
          <h2 class="balance-title display">本月结余</h2>
          <p class="balance-amount numeric"
             :class="totalBalance >= 0 ? 'text-positive' : 'text-expense'">
            <span class="num-sign">{{ totalBalance >= 0 ? '+' : '-' }}</span>¥{{ Math.abs(totalBalance).toLocaleString('zh-CN', {minimumFractionDigits: 2}) }}
          </p>
          <p class="balance-foot">
            <span class="muted">较上月</span>
            <span class="num-delta numeric" :class="totalBalance >= 0 ? 'text-positive' : 'text-expense'">
              {{ totalBalance >= 0 ? '↑' : '↓' }} 12.4%
            </span>
            <span class="muted">· 收支差</span>
          </p>

          <!-- 预算进度条 -->
          <div v-if="budgetList.length" class="budget-list">
            <div v-for="b in budgetList" :key="b.category" class="budget-row">
              <span class="budget-cat">{{ b.category }}</span>
              <BaseProgress
                :value="b.percent"
                :variant="b.percent >= 80 ? 'warning' : 'accent'"
                :label="''"
                :show-label="false"
              />
              <span class="budget-amount numeric" :class="b.percent >= 80 ? 'text-expense' : ''">
                ¥{{ b.spent.toFixed(0) }}<span class="muted-sm">/¥{{ b.budget.toFixed(0) }}</span>
              </span>
            </div>
          </div>
          <!-- 还没设预算的分类（轻量提示） -->
          <p v-if="unbudgetedCategories.length" class="budget-hint" @click="showBudgetModal = true">
            还有 <b>{{ unbudgetedCategories.length }}</b> 个分类未设预算：
            <span class="hint-cat">{{ unbudgetedCategories.slice(0, 3).join(' / ') }}<span v-if="unbudgetedCategories.length > 3">…</span></span>
            <span class="text-accent">前往设置 →</span>
          </p>
        </BaseCard>

        <!-- 右侧：深色引导卡（合并收支汇总 + sparkline） -->
        <BaseCard variant="dark" padding="lg" class="balance-summary-card">
          <BaseEyebrow tone="ink">Cash Flow · 收支</BaseEyebrow>

          <!-- 收入：主指标 -->
          <div class="summary-main">
            <p class="summary-eyebrow">本月收入</p>
            <p class="summary-value numeric text-positive">
              +¥{{ totalIncome.toLocaleString('zh-CN', {minimumFractionDigits: 2}) }}
            </p>
          </div>

          <hr class="deco-divider" style="margin: 16px 0; opacity: 0.15;" />

          <!-- 支出：副指标 + sparkline -->
          <div class="summary-sub">
            <div>
              <p class="summary-eyebrow">本月支出</p>
              <p class="summary-value-sm numeric text-expense">
                -¥{{ totalExpense.toLocaleString('zh-CN', {minimumFractionDigits: 2}) }}
              </p>
            </div>
            <BaseSparkline
              v-if="monthlyTrend.length"
              :data="monthlyTrend"
              tone="accent"
              :height="40"
              :width="180"
            />
          </div>
        </BaseCard>
      </section>

      <!-- ==================== 图表速览：1+2 不对称布局 ==================== -->
      <section class="charts-row">
        <!-- 左侧大卡：近 6 个月趋势（视觉锚点） -->
        <BaseCard padding="md" class="charts-trend-card">
          <BaseSectionHeader
            eyebrow="Trend · 6M"
            eyebrow-tone="accent"
            title="近 6 个月趋势"
            subtitle="收入 · 支出 · 结余"
          >
            <template #aside>
              <BaseButton variant="ghost" size="sm" @click="goStats">查看完整统计 →</BaseButton>
            </template>
          </BaseSectionHeader>
          <div ref="previewTrendRef" class="chart-trend-canvas"></div>
        </BaseCard>

        <!-- 右侧 2 张并排（不对称：1 大 + 2 小） -->
        <div class="charts-side-col">
          <BaseCard padding="md" class="charts-side-card">
            <div class="chart-preview-label">
              <span class="deco-mark" style="background: var(--color-feedback-negative);"></span>
              <span class="eyebrow">Categories · 分类</span>
            </div>
            <div ref="previewExpensePieRef" class="chart-mini-canvas"></div>
          </BaseCard>

          <BaseCard padding="md" class="charts-side-card">
            <div class="chart-preview-label">
              <span class="deco-mark" style="background: linear-gradient(90deg, var(--color-feedback-positive), var(--color-feedback-negative));"></span>
              <span class="eyebrow">Income vs Expense · 对比</span>
            </div>
            <div ref="previewBarRef" class="chart-mini-canvas"></div>
          </BaseCard>
        </div>
      </section>
    </main>

    <!-- 筛选栏 -->
    <section class="filter-section">
      <BaseCard padding="md" class="filter-card">
        <div class="filter-header">
          <BaseEyebrow tone="default">Filters · 筛选</BaseEyebrow>
          <div class="filter-header-aside">
            <BaseTag v-if="hasActiveFilter" variant="accent" toneStyle="soft">{{ filteredTransactions.length }} 条匹配</BaseTag>
            <BaseButton v-if="hasActiveFilter" variant="ghost" size="sm" @click="clearFilters">清除</BaseButton>
          </div>
        </div>
        <div class="filter-grid">
          <div class="filter-cell">
            <label class="filter-label">日期起</label>
            <input v-model="filterDateStart" type="date" class="input" />
          </div>
          <div class="filter-cell">
            <label class="filter-label">日期止</label>
            <input v-model="filterDateEnd" type="date" class="input" />
          </div>
          <div class="filter-cell">
            <label class="filter-label">类型</label>
            <select v-model="filterType" class="input">
              <option value="all">全部</option>
              <option value="income">收入</option>
              <option value="expense">支出</option>
            </select>
          </div>
          <div class="filter-cell">
            <label class="filter-label">分类</label>
            <select v-model="filterCategory" class="input">
              <option value="all">全部</option>
              <option v-for="cat in allFilterCategories" :key="cat" :value="cat">{{ cat }}</option>
            </select>
          </div>
        </div>
        <div class="filter-amount">
          <input v-model.number="filterAmountMin" type="number" placeholder="金额起" class="input" />
          <span class="filter-dash">~</span>
          <input v-model.number="filterAmountMax" type="number" placeholder="金额止" class="input" />
        </div>
      </BaseCard>
    </section>

    <!-- 交易列表 -->
    <section class="transaction-section">
      <BaseSectionHeader
        eyebrow="Records · 流水"
        eyebrow-tone="default"
        title="本月记录"
        :subtitle="`共 ${filteredTransactions.length} 条 · ${selectedIds.size > 0 ? `已选 ${selectedIds.size}` : '点击记录可编辑'}`"
      >
        <template #aside>
          <div class="header-actions">
            <BaseButton variant="soft" size="sm" @click="showImportModal = true">导入</BaseButton>
            <div class="export-wrapper">
              <BaseButton variant="ghost" size="sm" @click="showExportMenu = !showExportMenu">导出</BaseButton>
              <BaseModal v-model="showExportMenu" title="导出格式" size="sm" :show-close="true">
                <div class="export-list">
                  <button class="export-option" @click="doExport('xlsx')">
                    <span class="opt-name">Excel</span>
                    <span class="opt-hint">.xlsx 格式</span>
                  </button>
                  <button class="export-option" @click="doExport('csv')">
                    <span class="opt-name">CSV</span>
                    <span class="opt-hint">通用表格</span>
                  </button>
                  <button class="export-option" @click="doExport('pdf')">
                    <span class="opt-name">PDF 财报</span>
                    <span class="opt-hint">含图表 + 数据表</span>
                  </button>
                </div>
              </BaseModal>
            </div>
          </div>
        </template>
      </BaseSectionHeader>

      <!-- 批量操作工具栏 -->
      <div v-if="filteredTransactions.length" class="batch-bar" :class="{ active: selectedIds.size > 0 }">
        <label class="batch-check">
          <input
            type="checkbox"
            :checked="isAllSelected"
            :indeterminate.prop="isPartialSelected"
            @change="toggleSelectAll"
            class="batch-checkbox"
          />
          <span class="batch-label">
            <template v-if="selectedIds.size > 0">已选 {{ selectedIds.size }} 条</template>
            <template v-else>全选</template>
          </span>
        </label>
        <BaseButton v-if="selectedIds.size > 0" variant="ghost" size="sm" @click="clearSelection">取消</BaseButton>
        <BaseButton v-if="selectedIds.size > 0" variant="accent" size="sm" @click="confirmBatchDelete">删除选中</BaseButton>
      </div>

      <div class="transaction-list">
        <BaseEmpty
          v-if="!loading && filteredTransactions.length === 0"
          :title="hasActiveFilter ? t('transaction.noMatch') : t('transaction.noRecords')"
          :message="hasActiveFilter ? '' : t('transaction.addHint')"
        >
          <template #icon>
            <svg width="56" height="56" viewBox="0 0 64 64" fill="none" aria-hidden="true">
              <rect x="14" y="10" width="36" height="44" rx="4" stroke="currentColor" stroke-width="1.5" opacity="0.4"/>
              <path d="M22 22h20M22 30h20M22 38h12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" opacity="0.5"/>
            </svg>
          </template>
          <template #cta>
            <BaseButton v-if="!hasActiveFilter" variant="primary" @click="openModal">记一笔</BaseButton>
          </template>
        </BaseEmpty>

        <BaseCard
          v-for="item in filteredTransactions"
          :key="item.id"
          padding="sm"
          :hoverable="true"
          :selected="selectedIds.has(item.id)"
          class="transaction-row"
          @click="handleRowClick(item, $event)"
        >
          <div class="tx-content">
            <input
              type="checkbox"
              :checked="selectedIds.has(item.id)"
              @click.stop
              @change="toggleSelect(item.id)"
              class="row-checkbox"
              :aria-label="`选择 ${item.category}`"
            />
            <BaseAvatar :name="item.category" shape="square" size="sm" />
            <div class="tx-info">
              <p class="tx-category">{{ item.note || item.category }}</p>
              <p class="tx-meta">
                <BaseTag :variant="item.type === 'income' ? 'positive' : 'neutral'" toneStyle="soft" size="sm">{{ item.category }}</BaseTag>
                <span class="muted-sm">·</span>
                <span class="muted-sm">{{ item.date }}</span>
              </p>
            </div>
            <div class="tx-amount numeric" :class="item.type === 'income' ? 'text-positive' : 'text-expense'">
              <span class="num-sign">{{ item.type === 'income' ? '+' : '-' }}</span>¥{{ item.amount.toFixed(2) }}
            </div>
          </div>
        </BaseCard>
      </div>

      <!-- 加载更多 -->
      <div v-if="hasMore && !loading" class="load-more" @click="loadMore">
        加载更多
      </div>
      <div v-if="loading && hasMore" class="loading-more">加载中...</div>
    </section>

    <!-- 底部固定按钮 -->
    <button class="add-btn" @click="openModal" :aria-label="t('common.addRecord')">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <path d="M12 5v14M5 12h14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
      </svg>
      <span class="add-label">{{ t('common.addRecord') }}</span>
    </button>

    <!-- 底部弹出模态框 -->
    <BaseModal v-model="showModal" :title="editingId ? '修改记录' : '新增记录'" size="md" @close="closeModal">
      <div class="bill-form">
        <!-- 金额输入 -->
        <div class="amount-input-wrap">
          <span class="amount-yen">¥</span>
          <input
            v-model="form.amount"
            type="number"
            step="0.01"
            min="0"
            placeholder="0.00"
            class="amount-input"
          />
        </div>

        <!-- 类型切换 -->
        <div class="type-toggle">
          <button
            :class="['type-btn', { active: form.type === 'expense' }]"
            @click="form.type = 'expense'"
          >支出</button>
          <button
            :class="['type-btn', { active: form.type === 'income' }]"
            @click="form.type = 'income'"
          >收入</button>
        </div>

        <!-- 4宫格分类选择 -->
        <div class="category-grid">
          <button
            v-for="cat in currentCategories"
            :key="cat.name"
            :class="['cat-btn', { selected: form.category === cat.name }]"
            @click="form.category = cat.name"
          >
            <span class="cat-emoji">{{ cat.emoji }}</span>
            <span class="cat-name">{{ cat.name }}</span>
          </button>
        </div>

        <!-- 备注输入（带智能分类提示） -->
        <div class="input-wrap">
          <input
            v-model="form.note"
            @input="onNoteInput"
            type="text"
            placeholder="备注（选填）输入试试「美团 28.5」"
            class="form-input-bare"
          />
          <BaseTag v-if="classifyHint" variant="accent" toneStyle="soft" class="classify-tag" @click="applyClassifyHint">
            {{ classifyHint.category }}
          </BaseTag>
        </div>
        <p v-if="classifyHint" class="classify-hint">智能识别建议「{{ classifyHint.category }}」分类，点右侧应用</p>

        <!-- 日期输入 -->
        <input
          v-model="form.date"
          type="date"
          class="input"
        />
      </div>

      <template #footer>
        <BaseButton v-if="editingId" variant="danger" @click="showConfirmDelete = true">删除</BaseButton>
        <BaseButton variant="primary" @click="submitRecord" :disabled="!form.amount || submitting" :loading="submitting">
          {{ editingId ? '保存' : '确认' }}
        </BaseButton>
      </template>
    </BaseModal>

    <!-- 删除确认弹窗 -->
    <BaseModal v-model="showConfirmDelete" size="sm" :show-close="false">
      <div class="confirm-content">
        <p class="confirm-title display">确认删除</p>
        <p class="confirm-msg">删除后无法恢复，确定要删除吗？</p>
      </div>
      <template #footer>
        <BaseButton variant="ghost" @click="showConfirmDelete = false">取消</BaseButton>
        <BaseButton variant="danger" @click="confirmDelete">确认删除</BaseButton>
      </template>
    </BaseModal>

    <!-- 批量删除确认弹窗 -->
    <BaseModal v-model="showBatchConfirm" size="sm" :show-close="false">
      <div class="confirm-content">
        <p class="confirm-title display">批量删除</p>
        <p class="confirm-msg" v-html="t('transaction.batchDeleteConfirm', { n: selectedIds.size })"></p>
      </div>
      <template #footer>
        <BaseButton variant="ghost" @click="showBatchConfirm = false">{{ t('common.cancel') }}</BaseButton>
        <BaseButton variant="danger" @click="doBatchDelete">{{ t('common.confirm') }}删除</BaseButton>
      </template>
    </BaseModal>

    <!-- 回收站弹窗 -->
    <BaseModal v-model="showTrashModal" size="md" :title="t('trash.title')">
      <template #header>
        <div>
          <h2 :id="trashTitleId" class="modal-title">{{ t('trash.title') }}</h2>
          <p class="modal-subtitle">{{ t('trash.hint') }}</p>
        </div>
      </template>

      <div v-if="trashList.length" class="trash-actions">
        <BaseButton variant="ghost" size="sm" @click="showRestoreAllConfirm = true">{{ t('trash.restoreAll') }}</BaseButton>
        <BaseButton variant="danger" size="sm" @click="confirmEmptyTrash">{{ t('trash.emptyTrash') }}</BaseButton>
      </div>

      <!-- 回收站搜索/过滤 -->
      <div v-if="trashList.length || trashHasFilter" class="trash-filters">
        <div class="trash-filter-row">
          <input v-model="trashFilter.start" type="date" class="input" placeholder="开始日期" />
          <span class="muted text-xs">~</span>
          <input v-model="trashFilter.end" type="date" class="input" placeholder="结束日期" />
        </div>
        <div class="trash-filter-row">
          <select v-model="trashFilter.category" class="input">
            <option value="">全部分类</option>
            <option v-for="c in trashCategories" :key="c" :value="c">{{ c }}</option>
          </select>
          <BaseButton v-if="trashHasFilter" variant="ghost" size="sm" @click="clearTrashFilter">清除</BaseButton>
        </div>
      </div>

      <div v-if="trashLoading" class="text-center py-8 muted">加载中...</div>
      <BaseEmpty
        v-else-if="!trashList.length"
        title="回收站是空的"
        message="删除的记录会保留 30 天，到期自动清理"
      />
      <div v-else class="trash-list">
        <div v-for="item in trashList" :key="item.id" class="trash-item-wrap">
          <div class="trash-item" @click="toggleTrashDetail(item.id)">
            <BaseAvatar :name="item.category" shape="square" size="sm" />
            <div class="trash-info">
              <p class="trash-title">{{ item.note || item.category }}</p>
              <p class="trash-meta">
                <span :class="item.type === 'income' ? 'text-positive' : 'text-expense'">
                  {{ item.type === 'income' ? '+' : '-' }}¥{{ Number(item.amount).toFixed(2) }}
                </span>
                <span class="muted"> · {{ item.date }} · 删除于 {{ item.deleted_at?.slice(5, 16) }}</span>
              </p>
            </div>
            <div class="trash-buttons">
              <BaseButton variant="ghost" size="sm" @click.stop="restoreTrashItem(item.id)">还原</BaseButton>
              <BaseButton variant="danger" size="sm" @click.stop="askPurge(item.id)">删除</BaseButton>
            </div>
          </div>
          <!-- 详情展开 -->
          <div v-if="expandedTrashId === item.id" class="trash-detail">
            <div class="trash-detail-row">
              <span class="muted">类型</span>
              <span :class="item.type === 'income' ? 'text-positive' : 'text-expense'">
                {{ item.type === 'income' ? '收入' : '支出' }}
              </span>
            </div>
            <div class="trash-detail-row">
              <span class="muted">分类</span>
              <span>{{ item.category }}</span>
            </div>
            <div class="trash-detail-row">
              <span class="muted">金额</span>
              <span class="numeric" :class="item.type === 'income' ? 'text-positive' : 'text-expense'" style="font-weight: 600;">
                ¥{{ Number(item.amount).toFixed(2) }}
              </span>
            </div>
            <div class="trash-detail-row">
              <span class="muted">日期</span>
              <span class="numeric">{{ item.date }}</span>
            </div>
            <div v-if="item.note" class="trash-detail-row">
              <span class="muted">备注</span>
              <span>{{ item.note }}</span>
            </div>
            <div class="trash-detail-row">
              <span class="muted">删除时间</span>
              <span class="numeric">{{ item.deleted_at }}</span>
            </div>
          </div>
        </div>
      </div>
    </BaseModal>

    <!-- 清空回收站确认 -->
    <BaseModal v-model="showEmptyTrashConfirm" size="sm" :show-close="false">
      <div class="confirm-content">
        <p class="confirm-title display">清空回收站</p>
        <p class="confirm-msg">这将<strong>永久删除</strong>回收站里所有 <b>{{ trashList.length }}</b> 条记录，无法恢复。确定吗？</p>
      </div>
      <template #footer>
        <BaseButton variant="ghost" @click="showEmptyTrashConfirm = false">取消</BaseButton>
        <BaseButton variant="danger" @click="doEmptyTrash">永久清空</BaseButton>
      </template>
    </BaseModal>

    <!-- 永久删除单条 确认弹窗 -->
    <BaseModal v-model="showPurgeConfirm" size="sm" :show-close="false">
      <div class="confirm-content">
        <p class="confirm-title display">永久删除</p>
        <p class="confirm-msg">删除后无法恢复。确定要删除这条记录吗？</p>
      </div>
      <template #footer>
        <BaseButton variant="ghost" @click="showPurgeConfirm = false">取消</BaseButton>
        <BaseButton variant="danger" @click="confirmPurge">永久删除</BaseButton>
      </template>
    </BaseModal>

    <!-- 全部还原 确认弹窗 -->
    <BaseModal v-model="showRestoreAllConfirm" size="sm" :show-close="false">
      <div class="confirm-content">
        <p class="confirm-title display">还原全部</p>
        <p class="confirm-msg">将还原回收站里 <b>{{ trashList.length }}</b> 条记录到主列表，确定吗？</p>
      </div>
      <template #footer>
        <BaseButton variant="ghost" @click="showRestoreAllConfirm = false">取消</BaseButton>
        <BaseButton variant="primary" @click="confirmRestoreAll">全部还原</BaseButton>
      </template>
    </BaseModal>

    <!-- 清空分类记忆 确认弹窗 -->
    <BaseModal v-model="showClearMemoryConfirm" size="sm" :show-close="false">
      <div class="confirm-content">
        <p class="confirm-title display">清空分类记忆</p>
        <p class="confirm-msg">这将<strong>永久删除</strong>所有 <b>{{ memoryList.length }}</b> 条记忆，无法恢复。确定吗？</p>
      </div>
      <template #footer>
        <BaseButton variant="ghost" @click="showClearMemoryConfirm = false">取消</BaseButton>
        <BaseButton variant="danger" @click="doClearMemory">永久清空</BaseButton>
      </template>
    </BaseModal>

    <!-- 智能分类记忆管理弹窗 -->
    <BaseModal v-model="showMemoryModal" title="智能分类记忆" size="md">
      <template #header>
        <div>
          <h2 class="modal-title">智能分类记忆</h2>
          <p class="modal-subtitle">智能分类会优先用你学过的映射（删除错误的不会影响别人）</p>
        </div>
      </template>

      <!-- 测试输入 -->
      <div class="memory-test">
        <input
          v-model="memoryTestText"
          @keyup.enter="testMemoryMatch"
          type="text"
          placeholder="输入文字测试会按什么分类（回车测试）"
          class="input"
        />
        <BaseButton variant="primary" @click="testMemoryMatch">测试</BaseButton>
      </div>
      <div v-if="memoryTestResult" class="memory-test-result"
           :class="memoryTestResult.category ? 'hit' : 'miss'">
        <span v-if="memoryTestResult.category">
          命中：<b>{{ memoryTestResult.category }}</b>（{{ memoryTestResult.source === 'user_memory' ? '用户记忆' : '关键词字典' }}，置信度 {{ memoryTestResult.confidence }}）
        </span>
        <span v-else>没识别出来（建议选分类后自动记忆）</span>
      </div>

      <div v-if="memoryList.length" class="memory-toolbar">
        <span class="memory-count">共 {{ memoryList.length }} 条记忆</span>
        <BaseButton variant="danger" size="sm" @click="showClearMemoryConfirm = true">清空所有</BaseButton>
      </div>

      <div v-if="memoryLoading" class="text-center py-8 muted">加载中...</div>
      <BaseEmpty
        v-else-if="!memoryList.length"
        title="还没有分类记忆"
        message="编辑账单的分类后，会自动学习"
      >
        <template #icon><IconBrain :size="56" /></template>
      </BaseEmpty>
      <div v-else class="memory-list">
        <div v-for="m in memoryList" :key="m.id" class="memory-item">
          <div class="memory-keyword">{{ m.keyword }}</div>
          <span class="memory-arrow">→</span>
          <BaseTag variant="accent" toneStyle="soft">{{ m.category }}</BaseTag>
          <div class="memory-meta">
            <span class="memory-use-count" :title="`被引用 ${m.use_count} 次`">{{ m.use_count }}×</span>
          </div>
          <BaseButton variant="ghost" size="sm" @click="deleteMemory(m.id)">删除</BaseButton>
        </div>
      </div>
    </BaseModal>

    <!-- 导入账单弹窗 -->
    <BaseModal v-model="showImportModal" title="导入微信/支付宝账单" size="md">
      <p class="modal-subtitle">请上传微信/支付宝/通用格式的 CSV 或 XLSX 文件</p>
      <label class="import-label">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M17 8l-5-5-5 5M12 3v12" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <span>选择文件</span>
        <input type="file" accept=".csv,.xlsx" @change="handleFileSelect" class="hidden" />
      </label>
      <p v-if="selectedFile" class="import-filename">{{ selectedFile.name }}</p>
      <div v-if="importPreview.length" class="import-preview">
        <p class="preview-title">预览 (前{{ importPreview.length }}条，共{{ importTotal }}条)</p>
        <div v-for="(r, i) in importPreview" :key="i" class="preview-row">
          <span class="numeric">{{ r[0] }} {{ r[2] === 'income' ? '↑' : '↓' }} ¥{{ r[1] }}</span>
          <span class="muted">{{ r[3] }} - {{ r[4] }}</span>
        </div>
      </div>
      <p v-if="importError" class="import-error">{{ importError }}</p>
      <template #footer>
        <BaseButton variant="ghost" @click="showImportModal = false">取消</BaseButton>
        <BaseButton variant="primary" @click="doImport" :disabled="!selectedFile || importing" :loading="importing">确认导入</BaseButton>
      </template>
    </BaseModal>

    <!-- 预算设置弹窗 -->
    <BaseModal v-model="showBudgetModal" title="预算设置" size="md">
      <!-- Feature #1: 总月预算汇总 -->
      <div v-if="budgetList.length" class="budget-summary">
        <div class="summary-cell">
          <p class="summary-eyebrow">总月预算</p>
          <p class="summary-num numeric">¥{{ totalBudget.toFixed(0) }}</p>
        </div>
        <div class="summary-cell">
          <p class="summary-eyebrow">已支出</p>
          <p class="summary-num numeric" :class="totalSpent > totalBudget ? 'text-expense' : 'text-positive'">¥{{ totalSpent.toFixed(0) }}</p>
        </div>
        <div class="summary-cell">
          <p class="summary-eyebrow">剩余</p>
          <p class="summary-num numeric" :class="totalRemaining < 0 ? 'text-expense' : 'text-positive'">¥{{ totalRemaining.toFixed(0) }}</p>
        </div>
        <div class="summary-cell summary-usage">
          <p class="summary-eyebrow">整体使用率</p>
          <BaseProgress :value="totalPercent" :variant="totalPercent >= 100 ? 'warning' : 'accent'" :show-label="false" />
          <p class="summary-percent numeric">{{ totalPercent.toFixed(0) }}%</p>
        </div>
      </div>
      <div v-if="budgetList.length" class="budget-list">
        <div v-for="b in budgetList" :key="b.category" class="budget-item">
          <div class="budget-item-header">
            <span class="budget-cat">{{ b.category }}</span>
            <span class="budget-amounts numeric" :class="b.percent >= 80 ? 'text-expense' : ''">¥{{ b.spent }}/¥{{ b.budget }}</span>
          </div>
          <BaseProgress
            :value="b.percent"
            :variant="b.percent >= 80 ? 'warning' : 'accent'"
            :show-label="false"
          />
          <div class="budget-item-actions">
            <input v-model.number="budgetInputs[b.category]" type="number" :placeholder="b.budget" class="input" />
            <BaseButton variant="primary" size="sm" @click="saveBudget(b.category)">保存</BaseButton>
            <BaseButton variant="ghost" size="sm" @click="askDeleteBudget(b.category)">删除</BaseButton>
          </div>
        </div>
      </div>
      <p v-if="!budgetList.length" class="budget-empty">还没有设置任何预算</p>
      <div v-if="showAddBudget" class="budget-add-form">
        <select v-model="newBudgetCategory" class="input">
          <option value="">选择分类</option>
          <option v-for="cat in allExpenseCategories.filter(c => !budgetList.some(b => b.category === c))" :key="cat">{{ cat }}</option>
        </select>
        <input v-model.number="newBudgetAmount" type="number" placeholder="预算金额" class="input" />
        <!-- Feature #3: 快速预算模板 -->
        <div class="quick-amounts">
          <button v-for="amt in quickAmounts" :key="amt" type="button"
                  class="quick-amt-btn" @click="newBudgetAmount = amt">¥{{ amt }}</button>
        </div>
        <BaseButton variant="primary" @click="confirmAddBudget">添加</BaseButton>
      </div>
      <BaseButton v-else variant="ghost" @click="showAddBudget = true">+ 添加预算分类</BaseButton>
      <template #footer>
        <BaseButton variant="primary" @click="showBudgetModal = false">关闭</BaseButton>
      </template>
    </BaseModal>

    <!-- 删除预算 确认弹窗 -->
    <BaseModal v-model="showDeleteBudgetConfirm" size="sm" :show-close="false">
      <div class="confirm-content">
        <p class="confirm-title display">删除预算</p>
        <p class="confirm-msg">将删除 <b>{{ deleteBudgetTarget }}</b> 在 <b>{{ selectedMonth }}</b> 月的预算（仅当月，下月可重新设置）。确定吗？</p>
      </div>
      <template #footer>
        <BaseButton variant="ghost" @click="showDeleteBudgetConfirm = false">取消</BaseButton>
        <BaseButton variant="danger" @click="confirmDeleteBudget">删除</BaseButton>
      </template>
    </BaseModal>

    <!-- 全局 toast（替代浏览器原生 alert） -->
    <BaseToast v-model="toast.show" :message="toast.message" :tone="toast.tone" position="top" />
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { billAPI } from '../api'
import { formatDate } from '../utils/date'
import { t, useI18n, SUPPORTED_LANGUAGES } from '../i18n'
import IconLogo from '../components/IconLogo.vue'
import IconStats from '../components/IconStats.vue'
import IconBudget from '../components/IconBudget.vue'
import IconBrain from '../components/IconBrain.vue'
import IconTrash from '../components/IconTrash.vue'
import {
  BaseButton, BaseCard, BaseInput, BaseSelect, BaseTag,
  BaseModal, BaseProgress, BaseSparkline, BaseEyebrow,
  BaseEmpty, BaseSectionHeader, BaseToggle, BaseAvatar,
  BaseToast
} from '../components/base'

const { lang, setLanguage } = useI18n()

// 用户头像（从 auth store 拿）
import { useAuth } from '../stores/auth'
const { state: authState } = useAuth()
const userAvatar = computed(() => authState.userinfo?.avatar_url || '')
const userDisplayName = computed(() => authState.userinfo?.nickname || authState.userinfo?.username || '')

const trashTitleId = `trash-title-${Math.random().toString(36).slice(2, 8)}`

// Toast 状态（全局单例，多个 toast 会按队列显示）
const toast = reactive({ show: false, message: '', tone: 'info', timer: null })

function showToast(msg, tone = 'info') {
  // 清除上一个 timer 避免堆叠
  if (toast.timer) clearTimeout(toast.timer)
  toast.message = msg
  toast.tone = tone
  toast.show = true
  toast.timer = setTimeout(() => { toast.show = false }, 2800)
}

const router = useRouter()
function goStats() { router.push('/stats') }
function goBudget() { router.push('/budget') }
function goProfile() { router.push('/profile') }

// 筛选状态
const filterDateStart = ref('')
const filterDateEnd = ref('')
const filterCategory = ref('all')
const filterType = ref('all')
const filterAmountMin = ref('')
const filterAmountMax = ref('')

// 多选状态
const selectedIds = ref(new Set())
const showBatchConfirm = ref(false)

// 回收站状态
const showTrashModal = ref(false)
const trashList = ref([])
const trashCount = ref(0)
const trashLoading = ref(false)
const showEmptyTrashConfirm = ref(false)
const showPurgeConfirm = ref(false)
const purgeTargetId = ref(null)
const showRestoreAllConfirm = ref(false)
const showClearMemoryConfirm = ref(false)
const showDeleteBudgetConfirm = ref(false)
const deleteBudgetTarget = ref('')

// 智能分类记忆状态
const showMemoryModal = ref(false)
const memoryList = ref([])
const memoryLoading = ref(false)
const memoryTestText = ref('')
const memoryTestResult = ref(null)
const trashFilter = reactive({ start: '', end: '', category: '' })
const trashCategories = computed(() => [...new Set(trashList.value.map(t => t.category))].sort())
const trashHasFilter = computed(() => trashFilter.start || trashFilter.end || trashFilter.category)
const expandedTrashId = ref(null)  // 当前展开详情的记录 ID

function toggleTrashDetail(id) {
  expandedTrashId.value = expandedTrashId.value === id ? null : id
}

// 智能分类：备注输入时实时推荐
const classifyHint = ref(null)  // {category, type, matched, confidence}
let classifyTimer = null

function onNoteInput() {
  // 防抖：500ms 后才调 API
  if (classifyTimer) clearTimeout(classifyTimer)
  classifyTimer = setTimeout(async () => {
    const text = form.note?.trim()
    if (!text || text.length < 2) {
      classifyHint.value = null
      return
    }
    try {
      const res = await billAPI.classify(text)
      const data = res.data
      if (data?.category && data.confidence >= 0.4) {
        classifyHint.value = data
      } else {
        classifyHint.value = null
      }
    } catch (e) {
      // 静默失败
    }
  }, 500)
}

function applyClassifyHint() {
  if (!classifyHint.value) return
  form.category = classifyHint.value.category
  // 如果是收入类型，自动切到收入
  if (classifyHint.value.type === 'income' && form.type === 'expense') {
    form.type = 'income'
  }
  classifyHint.value = null
}

const allFilterCategories = computed(() => {
  const cats = new Set()
  transactions.value.forEach(t => cats.add(t.category))
  return [...cats].sort()
})

// 还没设预算的分类（用 allExpenseCategories ∩ transactions，排除 budgetList）
const unbudgetedCategories = computed(() => {
  const set = new Set(budgetList.value.map(b => b.category))
  // 用"这个月实际花过钱"的分类（说明用户有在用），但还没设预算
  const used = new Set(transactions.value.filter(t => t.type === 'expense').map(t => t.category))
  return [...used].filter(c => !set.has(c) && allExpenseCategories.includes(c)).sort()
})

// Feature #1: 总月预算汇总
const totalBudget = computed(() => budgetList.value.reduce((s, b) => s + (b.budget || 0), 0))
const totalSpent = computed(() => budgetList.value.reduce((s, b) => s + (b.spent || 0), 0))
const totalRemaining = computed(() => totalBudget.value - totalSpent.value)
const totalPercent = computed(() => totalBudget.value > 0 ? (totalSpent.value / totalBudget.value) * 100 : 0)

// Feature #3: 快速预算模板（常用金额档位）
const quickAmounts = [300, 500, 1000, 2000]

// Feature #4: 预算 80% / 100% 提醒
// 用 Set 追踪"已提醒过的 (category, month, threshold)" 防止重复弹
const budgetAlertsNotified = ref(new Set())
function budgetAlertKey(cat, month, threshold) {
  return `${cat}|${month}|${threshold}`
}
function checkBudgetAlerts() {
  if (!budgetList.value.length) return
  const month = selectedMonth.value
  for (const b of budgetList.value) {
    if (!b.budget || b.budget <= 0) continue
    const p = b.percent || 0
    if (p >= 100) {
      const k = budgetAlertKey(b.category, month, 100)
      if (!budgetAlertsNotified.value.has(k)) {
        budgetAlertsNotified.value.add(k)
        showToast(`🚨 ${b.category} 已超预算！已花 ¥${b.spent.toFixed(0)} / 预算 ¥${b.budget.toFixed(0)}`, 'error')
      }
    } else if (p >= 80) {
      const k = budgetAlertKey(b.category, month, 80)
      if (!budgetAlertsNotified.value.has(k)) {
        budgetAlertsNotified.value.add(k)
        showToast(`⚠️ ${b.category} 已用 ${p.toFixed(0)}% 预算（¥${b.spent.toFixed(0)} / ¥${b.budget.toFixed(0)}）`, 'info')
      }
    }
  }
}

const hasActiveFilter = computed(() => {
  return filterDateStart.value || filterDateEnd.value ||
         filterCategory.value !== 'all' || filterType.value !== 'all' ||
         filterAmountMin.value !== '' || filterAmountMax.value !== ''
})

function clearFilters() {
  filterDateStart.value = ''
  filterDateEnd.value = ''
  filterCategory.value = 'all'
  filterType.value = 'all'
  filterAmountMin.value = ''
  filterAmountMax.value = ''
}

// 多选逻辑
const isAllSelected = computed(() => {
  const list = filteredTransactions.value
  if (!list.length) return false
  return list.every(t => selectedIds.value.has(t.id))
})

const isPartialSelected = computed(() => {
  const list = filteredTransactions.value
  if (!list.length) return false
  const selected = list.filter(t => selectedIds.value.has(t.id)).length
  return selected > 0 && selected < list.length
})

function toggleSelect(id) {
  const s = new Set(selectedIds.value)
  if (s.has(id)) s.delete(id)
  else s.add(id)
  selectedIds.value = s
}

function toggleSelectAll() {
  const list = filteredTransactions.value
  if (isAllSelected.value) {
    // 全取消
    const s = new Set(selectedIds.value)
    list.forEach(t => s.delete(t.id))
    selectedIds.value = s
  } else {
    // 全选当前筛选结果
    const s = new Set(selectedIds.value)
    list.forEach(t => s.add(t.id))
    selectedIds.value = s
  }
}

function clearSelection() {
  selectedIds.value = new Set()
}

// 行点击：勾选时只切换选中，不打开编辑
function handleRowClick(item, event) {
  // 如果点击的是 checkbox，不处理
  if (event.target.type === 'checkbox') return
  // 如果已选中超过 0 条，再次点击切换选中
  if (selectedIds.value.size > 0) {
    toggleSelect(item.id)
  } else {
    startEdit(item)
  }
}

function confirmBatchDelete() {
  if (selectedIds.value.size === 0) return
  showBatchConfirm.value = true
}

async function doBatchDelete() {
  const ids = Array.from(selectedIds.value)
  showBatchConfirm.value = false
  if (!ids.length) return
  const idSet = new Set(ids)

  // ✅ 秒刷：备份 → 主列表过滤 → trash 计数 +=N → (modal 开着) 加到 trash 头部
  const removed = transactions.value.filter(t => idSet.has(t.id))
  transactions.value = transactions.value.filter(t => !idSet.has(t.id))
  selectedIds.value = new Set()
  trashCount.value += removed.length
  if (removed.length && showTrashModal.value) {
    const now = new Date().toISOString().slice(0, 19)
    trashList.value = [
      ...removed.map(r => ({ ...r, deleted_at: now })),
      ...trashList.value,
    ]
  }

  // 后台同步服务器
  try {
    const res = await billAPI.batchDelete({ ids })
    const deleted = res.data?.deleted || ids.length
    showToast(`成功删除 ${deleted} 条记录`, 'success')
  } catch (e) {
    // 失败时回滚：恢复本地状态
    transactions.value = [...removed, ...transactions.value]
    trashCount.value = Math.max(0, trashCount.value - removed.length)
    if (removed.length && showTrashModal.value) {
      trashList.value = trashList.value.filter(t => !idSet.has(t.id))
    }
    showToast(e.message || '批量删除失败')
    await loadRecords()
  }
}

// 多选状态
const expenseCategories = [
  { name: '餐饮', emoji: '🍜' },
  { name: '出行', emoji: '🚗' },
  { name: '购物', emoji: '🛒' },
  { name: '娱乐', emoji: '🎮' },
]

const incomeCategories = [
  { name: '工资', emoji: '💰' },
  { name: '奖金', emoji: '🎁' },
  { name: '理财', emoji: '📈' },
  { name: '其他', emoji: '💵' },
]

const currentCategories = computed(() =>
  form.type === 'expense' ? expenseCategories : incomeCategories
)

const form = reactive({
  type: 'expense',
  amount: '',
  category: '餐饮',
  note: '',
  date: new Date().toISOString().slice(0, 10),
})

const transactions = ref([])

// 图表速览实例
const previewExpensePieRef = ref(null)
const previewBarRef = ref(null)
const previewTrendRef = ref(null)
let previewExpensePie = null
let previewBar = null
let previewTrend = null

const selectedMonth = ref(formatDate(new Date()).slice(0, 7))

// 切换月份时清除选择 + 重新加载预算（预算按月存储）
watch(selectedMonth, () => {
  selectedIds.value = new Set()
  loadBudget()
})
const showModal = ref(false)
const editingId = ref(null)
const submitting = ref(false)
const showConfirmDelete = ref(false)
const loading = ref(false)
const currentPage = ref(1)
const pageSize = 20
const hasMore = ref(false)
const showImportModal = ref(false)
const selectedFile = ref(null)
const importPreview = ref([])
const importTotal = ref(0)
const importError = ref('')
const importing = ref(false)
const showBudgetModal = ref(false)
const showExportMenu = ref(false)
const exporting = ref(false)
const budgetList = ref([])
const budgetInputs = ref({})
const newBudgetCategory = ref('')
const newBudgetAmount = ref('')
const showAddBudget = ref(false)
const allExpenseCategories = ['餐饮', '交通', '购物', '娱乐', '医疗', '居住', '教育', '其他']

const monthOptions = computed(() => {
  const options = []
  const now = new Date()
  for (let i = 0; i < 12; i++) {
    const d = new Date(now.getFullYear(), now.getMonth() - i, 1)
    options.push({
      value: formatDate(d).slice(0, 7),
      label: `${d.getFullYear()}年${d.getMonth() + 1}月`
    })
  }
  return options
})

const filteredTransactions = computed(() => {
  return transactions.value.filter(t => {
    if (filterDateStart.value && t.date < filterDateStart.value) return false
    if (filterDateEnd.value && t.date > filterDateEnd.value) return false
    if (filterCategory.value !== 'all' && t.category !== filterCategory.value) return false
    if (filterType.value !== 'all' && t.type !== filterType.value) return false
    if (filterAmountMin.value !== '' && parseFloat(t.amount) < parseFloat(filterAmountMin.value)) return false
    if (filterAmountMax.value !== '' && parseFloat(t.amount) > parseFloat(filterAmountMax.value)) return false
    return true
  })
})

const totalIncome = computed(() =>
  transactions.value
    .filter(t => t.type === 'income')
    .reduce((sum, t) => sum + parseFloat(t.amount), 0)
)

const totalExpense = computed(() =>
  transactions.value
    .filter(t => t.type === 'expense')
    .reduce((sum, t) => sum + parseFloat(t.amount), 0)
)

const totalBalance = computed(() => totalIncome.value - totalExpense.value)

// Sparkline 数据：基于现有 transactions 聚合每日支出（最多 14 天）
const monthlyTrend = computed(() => {
  const byDate = new Map()
  for (const t of transactions.value) {
    if (t.type !== 'expense') continue
    byDate.set(t.date, (byDate.get(t.date) || 0) + parseFloat(t.amount))
  }
  return [...byDate.values()].slice(-14)
})

function getCategoryEmoji(category) {
  const all = [...expenseCategories, ...incomeCategories]
  return all.find(c => c.name === category)?.emoji || '📝'
}

async function loadRecords(append = false) {
  if (loading.value) return
  loading.value = true
  try {
    const [year, month] = selectedMonth.value.split('-')
    const res = await billAPI.getList({ year: parseInt(year), month: parseInt(month), page: currentPage.value, page_size: pageSize })
    const list = res.data.list || []
    if (append) {
      transactions.value = [...transactions.value, ...list]
    } else {
      transactions.value = list
    }
    hasMore.value = res.data.page < res.data.total_pages
  } catch (e) {
    console.error('loadRecords error:', e)
  } finally {
    loading.value = false
  }
}

function loadMore() {
  currentPage.value++
  loadRecords(true)
}

function onMonthChange() {
  currentPage.value = 1
  transactions.value = []
  loadRecords()
}

function openModal() {
  showModal.value = true
  form.type = 'expense'
  form.amount = ''
  form.note = ''
  form.category = '餐饮'
  form.date = new Date().toISOString().slice(0, 10)
  editingId.value = null
  classifyHint.value = null  // 清除智能分类提示
}

function startEdit(item) {
  editingId.value = item.id
  form.type = item.type
  form.amount = parseFloat(item.amount)
  form.category = item.category
  form.note = item.note || ''
  form.date = item.date
  showModal.value = true
}

function closeModal() {
  showModal.value = false
  editingId.value = null
  submitting.value = false
  showConfirmDelete.value = false
}

async function submitRecord() {
  if (!form.amount || submitting.value) return
  submitting.value = true
  try {
    const payload = {
      type: form.type,
      amount: parseFloat(form.amount),
      category: form.category,
      note: form.note,
      date: form.date,
    }
    if (form.type === 'expense') {
      const b = budgetList.value.find(b => b.category === form.category)
      if (b && b.budget > 0) {
        const newSpent = b.spent + parseFloat(form.amount)
        if (newSpent > b.budget) {
          const over = newSpent - b.budget
          alert(`「${form.category}」已超预算 ¥${over.toFixed(2)}（¥${newSpent.toFixed(2)} / ¥${b.budget.toFixed(2)}）`)
        }
      }
    }
    if (editingId.value) {
      await billAPI.edit(editingId.value, payload)
    } else {
      await billAPI.add(payload)
    }
    closeModal()
    currentPage.value = 1
    await loadRecords()
    await loadBudget()
  } catch (e) {
    console.error('submitRecord error:', e)
  } finally {
    submitting.value = false
  }
}

async function deleteRecord() {
  if (!editingId.value || submitting.value) return
  submitting.value = true
  const idToDelete = editingId.value

  // ✅ 秒刷：先关弹窗 + 从本地列表移除 + trash 计数 +1 + (modal 开着) 加到 trash 头部
  const removed = transactions.value.find(t => t.id === idToDelete)
  showConfirmDelete.value = false
  closeModal()
  const idx = transactions.value.findIndex(t => t.id === idToDelete)
  if (idx >= 0) transactions.value.splice(idx, 1)
  trashCount.value++
  if (removed && showTrashModal.value) {
    trashList.value = [{
      ...removed,
      deleted_at: new Date().toISOString().slice(0, 19),
    }, ...trashList.value]
  }

  // 后台同步服务器
  try {
    await billAPI.delete(idToDelete)
  } catch (e) {
    console.error('deleteRecord error:', e)
    // 失败时回滚：本地状态全恢复 + 重新拉取
    if (removed) {
      transactions.value.unshift(removed)
      trashCount.value = Math.max(0, trashCount.value - 1)
      if (showTrashModal.value) {
        trashList.value = trashList.value.filter(t => t.id !== idToDelete)
      }
    }
    showToast('删除失败，已恢复数据')
    await loadRecords()
  } finally {
    submitting.value = false
  }
}

async function confirmDelete() {
  await deleteRecord()
}

onMounted(() => {
  loadRecords()
  loadTrashCount()
  // 等账单加载完再画图
  setTimeout(renderPreviewCharts, 500)
})

// 加载回收站数量（用于角标）
async function loadTrashCount() {
  try {
    const res = await billAPI.getTrashCount()
    trashCount.value = res.data?.count || 0
  } catch (e) {
    console.error('loadTrashCount error:', e)
  }
}

// 打开回收站
async function openTrash() {
  showTrashModal.value = true
  await loadTrashList()
}

// 加载回收站列表（带过滤）
async function loadTrashList() {
  trashLoading.value = true
  try {
    const params = { page_size: 100 }
    if (trashFilter.start) params.start = trashFilter.start
    if (trashFilter.end) params.end = trashFilter.end
    if (trashFilter.category) params.category = trashFilter.category
    const res = await billAPI.getTrash(params)
    trashList.value = res.data?.list || []
  } catch (e) {
    console.error('loadTrashList error:', e)
    showToast('加载回收站失败')
  } finally {
    trashLoading.value = false
  }
}

function clearTrashFilter() {
  trashFilter.start = ''
  trashFilter.end = ''
  trashFilter.category = ''
}

// 过滤变化时自动重载
watch([() => trashFilter.start, () => trashFilter.end, () => trashFilter.category], () => {
  if (showTrashModal.value) loadTrashList()
})

// 还原单条
async function restoreTrashItem(id) {
  // ✅ 秒刷：备份 → 从 trash 移除 → 角标-- → 加回主列表头部
  const restored = trashList.value.find(t => t.id === id)
  if (!restored) {
    // 本地没记录（外部操作导致），直接走 API
    try { await billAPI.restore(id) } catch (e) { showToast(e.message || '还原失败') }
    return
  }
  const { deleted_at, ...recordForMain } = restored  // 剥掉 deleted_at
  trashList.value = trashList.value.filter(t => t.id !== id)
  trashCount.value = Math.max(0, trashCount.value - 1)
  transactions.value = [recordForMain, ...transactions.value]
  showToast('已还原', 'success')

  // 后台同步服务器
  try {
    await billAPI.restore(id)
  } catch (e) {
    // 失败回滚
    trashList.value = [restored, ...trashList.value]
    trashCount.value++
    transactions.value = transactions.value.filter(t => t.id !== id)
    showToast(e.message || '还原失败')
  }
}

// 永久删除单条（BaseModal 确认版，不再用 confirm()）
function askPurge(id) {
  purgeTargetId.value = id
  showPurgeConfirm.value = true
}
async function confirmPurge() {
  const id = purgeTargetId.value
  if (!id) return
  showPurgeConfirm.value = false
  purgeTargetId.value = null
  // ✅ 秒刷
  const backup = trashList.value.find(t => t.id === id)
  trashList.value = trashList.value.filter(t => t.id !== id)
  trashCount.value = Math.max(0, trashCount.value - 1)
  showToast('已永久删除', 'success')
  try {
    await billAPI.purge(id)
  } catch (e) {
    // 回滚
    if (backup) {
      trashList.value = [backup, ...trashList.value]
      trashCount.value++
    }
    showToast(e.message || '删除失败', 'error')
  }
}

// 还原全部（BaseModal 确认版）
async function confirmRestoreAll() {
  showRestoreAllConfirm.value = false
  const ids = trashList.value.map(t => t.id)
  if (!ids.length) return
  // ✅ 秒刷：把 trash 全部移到主列表头部
  const backup = [...trashList.value]
  const restored = trashList.value.map(({ deleted_at, ...r }) => r)
  trashList.value = []
  trashCount.value = 0
  transactions.value = [...restored, ...transactions.value]
  showToast(`已还原 ${ids.length} 条`, 'success')
  try {
    await billAPI.restoreBatchTrash({ ids })
  } catch (e) {
    // 回滚
    trashList.value = backup
    trashCount.value = backup.length
    transactions.value = transactions.value.filter(t => !ids.includes(t.id))
    showToast(e.message || '还原失败', 'error')
  }
}

// 弹出清空确认
function confirmEmptyTrash() {
  showEmptyTrashConfirm.value = true
}

// 清空回收站
async function doEmptyTrash() {
  showEmptyTrashConfirm.value = false
  // ✅ 秒刷
  const backup = [...trashList.value]
  const count = backup.length
  trashList.value = []
  trashCount.value = 0
  showToast(`已清空 ${count} 条`, 'success')
  try {
    await billAPI.emptyTrash()
  } catch (e) {
    // 回滚
    trashList.value = backup
    trashCount.value = backup.length
    showToast(e.message || '清空失败')
  }
}

// ==================== 智能分类记忆管理 ====================
async function openMemoryModal() {
  showMemoryModal.value = true
  await loadMemoryList()
}

async function loadMemoryList() {
  memoryLoading.value = true
  try {
    const res = await billAPI.getClassifyMemory()
    memoryList.value = res.data || []
  } catch (e) {
    console.error('loadMemoryList error:', e)
    showToast('加载记忆失败')
  } finally {
    memoryLoading.value = false
  }
}

async function testMemoryMatch() {
  const text = memoryTestText.value.trim()
  if (!text) {
    memoryTestResult.value = null
    return
  }
  try {
    const res = await billAPI.classify(text)
    memoryTestResult.value = res.data || null
  } catch (e) {
    showToast(e.message || '测试失败')
  }
}

async function deleteMemory(id) {
  try {
    await billAPI.deleteClassifyMemory(id)
    // 乐观更新
    memoryList.value = memoryList.value.filter(m => m.id !== id)
    showToast('已删除', 'success')
  } catch (e) {
    showToast(e.message || '删除失败')
  }
}

async function doClearMemory() {
  showClearMemoryConfirm.value = false
  try {
    const res = await billAPI.clearClassifyMemory()
    const count = res.data?.deleted || memoryList.value.length
    memoryList.value = []
    showToast(`已清空 ${count} 条`, 'success')
  } catch (e) {
    showToast(e.message || '清空失败', 'error')
  }
}

onUnmounted(() => {
  if (previewExpensePie) previewExpensePie.dispose()
  if (previewBar) previewBar.dispose()
  if (previewTrend) previewTrend.dispose()
})

async function renderPreviewCharts() {
  // 等 DOM 准备好
  await new Promise(r => setTimeout(r, 100))
  const [year, month] = selectedMonth.value.split('-')

  try {
    // 1) 支出分类饼图
    const catRes = await fetch(`/api/stats/category?year=${year}&month=${month}`, {
      headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
    }).then(r => r.json())

    const expenseData = (catRes.data || []).filter(d => d.type === 'expense')
    if (previewExpensePieRef.value) {
      if (!previewExpensePie) previewExpensePie = window.echarts.init(previewExpensePieRef.value)
      previewExpensePie.setOption({
        tooltip: { trigger: 'item', formatter: '{b}: ¥{c} ({d}%)', backgroundColor: '#FFFFFF', borderColor: '#E5E7EB', textStyle: { color: '#1F2937', fontSize: 12 } },
        legend: { bottom: 0, textStyle: { color: '#6B7280', fontSize: 10 } },
        series: [{
          type: 'pie', radius: ['38%', '62%'], center: ['50%', '45%'],
          itemStyle: { borderColor: '#FFFFFF', borderWidth: 2 },
          label: { show: false },
          data: expenseData.length
            ? expenseData.map(d => ({ name: d.category, value: d.amount }))
            : [{ name: '暂无', value: 1, itemStyle: { color: '#F3F4F6' } }]
        }]
      })
    }

    // 2) 收支对比柱图
    const monthlyRes = await fetch(`/api/stats/monthly?year=${year}&month=${month}`, {
      headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
    }).then(r => r.json())

    if (previewBarRef.value && monthlyRes.data) {
      if (!previewBar) previewBar = window.echarts.init(previewBarRef.value)
      const m = monthlyRes.data
      previewBar.setOption({
        tooltip: { trigger: 'axis', backgroundColor: '#FFFFFF', borderColor: '#E5E7EB', textStyle: { color: '#1F2937', fontSize: 12 } },
        grid: { left: '3%', right: '4%', bottom: '3%', top: '8%', containLabel: true },
        xAxis: { type: 'category', data: ['收入', '支出'], axisLine: { lineStyle: { color: '#E5E7EB' } }, axisLabel: { color: '#6B7280' } },
        yAxis: { type: 'value', axisLine: { show: false }, axisTick: { show: false }, axisLabel: { color: '#9CA3AF' }, splitLine: { lineStyle: { color: '#F3F4F6' } } },
        series: [{
          type: 'bar', data: [m.income, m.expense], barWidth: 32,
          itemStyle: { borderRadius: [6, 6, 0, 0], color: (p) => p.dataIndex === 0 ? '#10B981' : '#EF4444' },
          label: { show: true, position: 'top', color: '#1F2937', fontSize: 11, fontWeight: 600, formatter: (p) => '¥' + p.value.toFixed(0) }
        }]
      })
    }

    // 3) 近 6 个月趋势柱图
    const trendRes = await fetch(`/api/stats/trend?months=6`, {
      headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
    }).then(r => r.json())

    if (previewTrendRef.value && trendRes.data) {
      if (!previewTrend) previewTrend = window.echarts.init(previewTrendRef.value)
      const t = trendRes.data
      const balance = t.income.map((inc, i) => (inc - (t.expense[i] || 0)).toFixed(2))
      previewTrend.setOption({
        tooltip: { trigger: 'axis', backgroundColor: '#FFFFFF', borderColor: '#E5E7EB', textStyle: { color: '#1F2937', fontSize: 12 } },
        legend: { data: ['收入', '支出', '结余'], textStyle: { color: '#6B7280' }, top: 0 },
        grid: { left: '3%', right: '4%', bottom: '3%', top: '15%', containLabel: true },
        xAxis: { type: 'category', data: t.months, axisLine: { lineStyle: { color: '#E5E7EB' } }, axisLabel: { color: '#6B7280' } },
        yAxis: { type: 'value', axisLine: { show: false }, axisTick: { show: false }, axisLabel: { color: '#9CA3AF' }, splitLine: { lineStyle: { color: '#F3F4F6' } } },
        series: [
          { name: '收入', type: 'bar', data: t.income, barWidth: 8, itemStyle: { color: '#10B981', borderRadius: [3, 3, 0, 0] } },
          { name: '支出', type: 'bar', data: t.expense, barWidth: 8, itemStyle: { color: '#EF4444', borderRadius: [3, 3, 0, 0] } },
          { name: '结余', type: 'line', data: balance, smooth: true, itemStyle: { color: '#4F46E5' }, lineStyle: { width: 2, type: 'dashed' } }
        ]
      })
    }
  } catch (e) {
    console.error('renderPreviewCharts error:', e)
  }
}

function handleFileSelect(e) {
  const file = e.target.files[0]
  if (!file) return
  selectedFile.value = file
  importError.value = ''
  billAPI.importFile(file, true).then((res) => {
    if (res.data.code === 0) {
      importPreview.value = res.data.data.preview || []
      importTotal.value = res.data.data.total || 0
    } else {
      importError.value = res.data.message || '预览失败'
    }
  }).catch((e) => { importError.value = e.message || '预览失败' })
}

async function doImport() {
  if (!selectedFile.value) return
  importing.value = true
  importError.value = ''
  try {
    const res = await billAPI.importFile(selectedFile.value, false)
    if (res.data.code === 0) {
      showImportModal.value = false
      selectedFile.value = null
      importPreview.value = []
      importTotal.value = 0
      await loadRecords()
    } else {
      importError.value = res.data.message || '导入失败'
    }
  } catch (e) { importError.value = e.message }
  finally { importing.value = false }
}

async function doExport(fmt) {
  showExportMenu.value = false
  exporting.value = true
  try {
    const { blob, filename } = await billAPI.exportFile(fmt)
    const url = window.URL.createObjectURL(blob)
    const a = window.document.createElement('a')
    a.href = url; a.download = filename; a.style.display = 'none'
    window.document.body.appendChild(a)
    a.click()
    window.document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
    showToast(`已导出 ${filename}`, 'success')
  } catch (e) {
    console.error('Export error:', e)
    showToast(e.message || '导出失败', 'error')
  }
  finally { exporting.value = false }
}

async function loadBudget() {
  try {
    // 关键修复：传当前 selectedMonth 的 year/month，否则后端默认返回"当前月"
    // 导致用户切到 5 月时看到的是 6 月的预算
    const [year, month] = selectedMonth.value.split('-')
    const res = await billAPI.getBudget({ year: parseInt(year), month: parseInt(month) })
    budgetList.value = res.data || []
    for (const b of budgetList.value) {
      budgetInputs.value[b.category] = b.budget > 0 ? b.budget : null
    }
    // Feature #4: 加载完预算后检查 80% / 100% 提醒
    checkBudgetAlerts()
  } catch (e) { console.error('loadBudget error:', e) }
}

async function saveBudget(category) {
  const amount = budgetInputs.value[category]
  if (!amount || amount <= 0) return
  const month = selectedMonth.value
  try {
    await billAPI.setBudget({ category, amount: parseFloat(amount), type: 'expense', month })
    const idx = budgetList.value.findIndex(b => b.category === category)
    if (idx >= 0) {
      budgetList.value[idx].budget = parseFloat(amount)
    }
  } catch (e) { console.error('saveBudget error:', e) }
}

function askDeleteBudget(category) {
  deleteBudgetTarget.value = category
  showDeleteBudgetConfirm.value = true
}
async function confirmDeleteBudget() {
  const category = deleteBudgetTarget.value
  if (!category) return
  showDeleteBudgetConfirm.value = false
  deleteBudgetTarget.value = ''
  try {
    await billAPI.deleteBudget({ category, month: selectedMonth.value })
    budgetList.value = budgetList.value.filter(b => b.category !== category)
    delete budgetInputs.value[category]
    showToast(`已删除 ${category} 预算`, 'success')
  } catch (e) {
    showToast(e.message || '删除预算失败', 'error')
  }
}

function openAddBudget() {
  newBudgetCategory.value = ''
  newBudgetAmount.value = ''
  showAddBudget.value = true
}

async function confirmAddBudget() {
  const cat = newBudgetCategory.value.trim()
  const amount = parseFloat(newBudgetAmount.value)
  if (!cat || !amount) return
  try {
    await billAPI.setBudget({ category: cat, amount, type: 'expense', month: selectedMonth.value })
    if (!budgetList.value.some(b => b.category === cat)) {
      budgetList.value.push({ category: cat, budget: amount, spent: 0, percent: 0 })
    }
    showAddBudget.value = false
  } catch (e) { console.error('confirmAddBudget error:', e) }
}

watch(showBudgetModal, (val) => {
  if (val) loadBudget()
})
</script>

<style scoped>
/* ==================== App shell ==================== */
.app {
  min-height: 100vh;
  padding-bottom: 100px;
}
.main {
  max-width: 720px;
  margin: 0 auto;
  padding: 0 16px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* ==================== Nav ==================== */
.nav {
  position: sticky;
  top: 0;
  z-index: 50;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 20px;
  background: rgba(250, 247, 242, 0.85);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--color-border-soft);
}
.nav-left { display: flex; align-items: center; gap: 8px; }
.nav-title { font-family: var(--font-display); font-size: 18px; font-weight: 500; color: var(--color-text-primary); display: inline-flex; align-items: center; gap: 8px; }
.nav-right { display: flex; align-items: center; gap: 6px; }

.month-picker, .lang-select {
  appearance: none;
  background: var(--card-bg);
  border: 1px solid var(--color-border);
  color: var(--color-text-primary);
  border-radius: var(--input-radius);
  padding: 6px 10px;
  font-size: 12px;
  font-family: inherit;
  cursor: pointer;
  outline: none;
  transition: all var(--t-fast) var(--ease-out);
}
.month-picker:hover, .lang-select:hover { border-color: var(--muted-2); background: var(--paper-50); }

.icon-btn {
  position: relative;
  width: 36px;
  height: 36px;
  background: transparent;
  border: 1px solid var(--color-border);
  border-radius: 9px;
  color: var(--color-text-secondary);
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: all var(--t-fast) var(--ease-out);
}
.icon-btn:hover { background: var(--paper-200); color: var(--color-text-primary); border-color: var(--muted-2); }

.trash-badge {
  position: absolute;
  top: -4px;
  right: -4px;
  background: var(--color-feedback-negative);
  color: var(--color-text-inverse);
  font-size: 10px;
  font-weight: 700;
  border-radius: 10px;
  min-width: 16px;
  height: 16px;
  padding: 0 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
}

/* ==================== Hero 1+3 布局 ==================== */
.balance-row {
  display: grid;
  grid-template-columns: 1.6fr 1fr;
  gap: 16px;
  align-items: stretch;
}
.balance-card { display: flex; flex-direction: column; gap: 12px; }

.balance-title {
  font-size: 22px;
  font-weight: 500;
  color: var(--color-text-primary);
  margin: 4px 0 8px;
  letter-spacing: -0.01em;
}
.balance-amount {
  font-size: 44px;
  font-weight: 600;
  letter-spacing: -0.03em;
  line-height: 1;
  margin-bottom: 8px;
}
.balance-foot {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--color-text-secondary);
  margin-bottom: 4px;
}
.num-delta { font-weight: 600; }

.budget-list { display: flex; flex-direction: column; gap: 10px; margin-top: 12px; padding-top: 12px; border-top: 1px solid var(--color-border-soft); }
.budget-row {
  display: grid;
  grid-template-columns: 56px 1fr auto;
  gap: 10px;
  align-items: center;
  font-size: 12px;
}
.budget-cat { color: var(--color-text-secondary); font-weight: 500; }
.budget-amount { color: var(--color-text-primary); font-weight: 600; font-size: 12.5px; }
.muted-sm { color: var(--color-text-muted); font-size: 11px; font-weight: 400; }
.budget-hint {
  font-size: 11.5px;
  color: var(--color-text-muted);
  background: var(--paper-200);
  border: 1px dashed var(--color-border);
  border-radius: 10px;
  padding: 8px 12px;
  margin-top: 8px;
  cursor: pointer;
  transition: all var(--t-fast) var(--ease-out);
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px;
}
.budget-hint:hover {
  background: var(--orange-50);
  border-color: var(--color-action-accent);
  color: var(--color-text-primary);
}
.budget-hint b { color: var(--color-text-primary); font-weight: 600; }
.budget-hint .hint-cat { color: var(--color-text-secondary); font-weight: 500; }
.budget-hint .text-accent { color: var(--color-action-accent); font-weight: 500; margin-left: 2px; }

/* ==================== 深色引导卡 ==================== */
.balance-summary-card { display: flex; flex-direction: column; gap: 4px; }
.summary-main { margin-top: 12px; }
.summary-eyebrow {
  font-family: var(--font-num);
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: rgba(253, 251, 246, 0.55);
  margin-bottom: 6px;
}
.summary-value {
  font-size: 32px;
  font-weight: 600;
  letter-spacing: -0.03em;
  line-height: 1;
  color: var(--paper-50);
}
.summary-value-sm {
  font-size: 22px;
  font-weight: 600;
  letter-spacing: -0.02em;
  color: var(--paper-50);
}
.summary-sub { display: flex; align-items: flex-end; justify-content: space-between; gap: 12px; }

/* ==================== Charts 1+2 不对称 ==================== */
.charts-row {
  display: grid;
  grid-template-columns: 1.4fr 1fr;
  gap: 16px;
  align-items: stretch;
}
.charts-trend-card { display: flex; flex-direction: column; }
.chart-trend-canvas { width: 100%; height: 180px; margin-top: 8px; }
.charts-side-col { display: flex; flex-direction: column; gap: 16px; }
.charts-side-card { display: flex; flex-direction: column; gap: 8px; }
.chart-mini-canvas { width: 100%; height: 120px; }
.chart-preview-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  color: var(--color-text-muted);
}

/* ==================== Filter ==================== */
.filter-section { padding: 0; }
.filter-card { display: flex; flex-direction: column; gap: 14px; }
.filter-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.filter-header-aside { display: flex; align-items: center; gap: 8px; }
.filter-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
}
.filter-cell { display: flex; flex-direction: column; gap: 4px; }
.filter-label {
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--color-text-muted);
}
.filter-amount {
  display: grid;
  grid-template-columns: 1fr 16px 1fr;
  align-items: center;
  gap: 8px;
}
.filter-dash { text-align: center; color: var(--color-text-muted); }

/* ==================== Transaction list ==================== */
.transaction-section { display: flex; flex-direction: column; gap: 12px; }
.header-actions { display: flex; align-items: center; gap: 6px; }

.batch-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  background: var(--paper-200);
  border-radius: 12px;
  border: 1px solid var(--color-border-soft);
  transition: all var(--t-fast) var(--ease-out);
}
.batch-bar.active { background: var(--orange-50); border-color: var(--color-action-accent); }
.batch-check {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--color-text-secondary);
  cursor: pointer;
  user-select: none;
}
.batch-checkbox, .row-checkbox {
  width: 18px;
  height: 18px;
  cursor: pointer;
  accent-color: var(--color-action-accent);
  flex-shrink: 0;
}
.batch-label { font-weight: 500; }

.transaction-list { display: flex; flex-direction: column; gap: 8px; }
.transaction-row { margin: 0; }
.tx-content {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
}
.tx-info { flex: 1; min-width: 0; }
.tx-category { font-size: 14px; font-weight: 500; color: var(--color-text-primary); margin: 0; }
.tx-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  margin-top: 4px;
  color: var(--color-text-muted);
}
.tx-amount {
  font-size: 16px;
  font-weight: 600;
  letter-spacing: -0.02em;
  flex-shrink: 0;
}

.load-more {
  text-align: center;
  padding: 14px;
  color: var(--color-text-secondary);
  font-size: 13px;
  cursor: pointer;
  border-radius: 12px;
  transition: all var(--t-fast) var(--ease-out);
}
.load-more:hover { background: var(--paper-200); color: var(--color-text-primary); }
.loading-more { text-align: center; padding: 14px; color: var(--color-text-muted); font-size: 13px; }

/* ==================== Add button ==================== */
.add-btn {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  background: var(--ink-900);
  color: var(--color-text-inverse);
  border: none;
  border-radius: 999px;
  padding: 14px 22px;
  font-size: 14px;
  font-weight: 600;
  font-family: inherit;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  box-shadow: 0 12px 32px -8px rgba(15, 23, 42, 0.35), 0 4px 12px rgba(15, 23, 42, 0.2);
  z-index: 40;
  transition: all var(--t-base) var(--ease-out);
}
.add-btn:hover { background: var(--ink-800); transform: translateX(-50%) translateY(-2px); box-shadow: 0 16px 40px -8px rgba(15, 23, 42, 0.45); }

/* ==================== Bill form (modal body) ==================== */
.bill-form { display: flex; flex-direction: column; gap: 16px; }
.amount-input-wrap {
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: 6px;
  padding: 16px 0;
  border-bottom: 1px dashed var(--color-border);
}
.amount-yen {
  font-family: var(--font-display);
  font-size: 24px;
  color: var(--color-text-secondary);
}
.amount-input {
  background: transparent;
  border: none;
  outline: none;
  font-family: var(--font-num);
  font-size: 40px;
  font-weight: 600;
  letter-spacing: -0.03em;
  color: var(--color-text-primary);
  text-align: center;
  width: 70%;
}
.amount-input::placeholder { color: var(--color-text-muted); }

.type-toggle {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  background: var(--paper-200);
  padding: 4px;
  border-radius: var(--input-radius);
}
.type-btn {
  background: transparent;
  border: none;
  padding: 10px;
  border-radius: 7px;
  font-size: 13px;
  font-weight: 500;
  font-family: inherit;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--t-fast) var(--ease-out);
}
.type-btn.active {
  background: var(--card-bg);
  color: var(--color-text-primary);
  font-weight: 600;
  box-shadow: var(--shadow-sm);
}

.category-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
}
.cat-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  background: var(--paper-200);
  border: 1px solid transparent;
  border-radius: 12px;
  padding: 14px 4px;
  cursor: pointer;
  transition: all var(--t-fast) var(--ease-out);
}
.cat-btn:hover { background: var(--orange-50); }
.cat-btn.selected {
  background: var(--orange-50);
  border-color: var(--color-action-accent);
}
.cat-emoji { font-size: 22px; line-height: 1; }
.cat-name { font-size: 12px; color: var(--color-text-primary); font-weight: 500; }
.cat-btn.selected .cat-name { color: var(--color-action-accent); font-weight: 600; }

.form-input-bare {
  flex: 1;
  border: 1px solid var(--input-border);
  background: var(--input-bg);
  border-radius: var(--input-radius);
  padding: 10px 14px;
  font-size: 14px;
  font-family: inherit;
  color: var(--color-text-primary);
  outline: none;
  width: 100%;
}
.form-input-bare:focus { border-color: var(--color-action-accent); background: white; }
.input-wrap { display: flex; gap: 8px; align-items: center; }

.classify-hint {
  font-size: 11px;
  color: var(--color-text-muted);
  margin: -8px 0 0;
}

/* ==================== Confirm modal body ==================== */
.confirm-content { display: flex; flex-direction: column; gap: 8px; padding: 8px 0; }
.confirm-title { font-size: 18px; font-weight: 500; color: var(--color-text-primary); margin: 0; }
.confirm-msg { font-size: 14px; line-height: 1.6; color: var(--color-text-secondary); margin: 0; }

/* ==================== Trash modal body ==================== */
.trash-actions { display: flex; gap: 8px; margin-bottom: 12px; padding-bottom: 12px; border-bottom: 1px solid var(--color-border-soft); }
.trash-filters { display: flex; flex-direction: column; gap: 8px; margin-bottom: 12px; }
.trash-filter-row { display: flex; gap: 8px; align-items: center; }

.trash-list { display: flex; flex-direction: column; gap: 6px; max-height: 50vh; overflow-y: auto; }
.trash-item-wrap { border-radius: 12px; }
.trash-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: 10px;
  cursor: pointer;
  transition: background var(--t-fast) var(--ease-out);
}
.trash-item:hover { background: var(--paper-200); }
.trash-info { flex: 1; min-width: 0; }
.trash-title { font-size: 13.5px; font-weight: 500; color: var(--color-text-primary); margin: 0; }
.trash-meta { font-size: 11px; color: var(--color-text-muted); margin: 2px 0 0; }
.trash-buttons { display: flex; gap: 4px; }

.trash-detail {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 10px 12px;
  margin-top: 4px;
  background: var(--paper-200);
  border-radius: 8px;
  font-size: 12px;
}
.trash-detail-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}

/* ==================== Memory modal body ==================== */
.memory-test { display: flex; gap: 8px; }
.memory-test-btn { flex-shrink: 0; }
.memory-test-result {
  padding: 10px 14px;
  border-radius: var(--input-radius);
  font-size: 13px;
  margin-top: 8px;
}
.memory-test-result.hit {
  background: var(--green-50);
  color: var(--color-feedback-positive);
}
.memory-test-result.miss {
  background: var(--paper-200);
  color: var(--color-text-secondary);
}
.memory-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: 16px 0 8px;
  font-size: 12px;
  color: var(--color-text-secondary);
}
.memory-list { display: flex; flex-direction: column; gap: 6px; }
.memory-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: var(--paper-200);
  border-radius: 8px;
  font-size: 13px;
}
.memory-keyword { font-weight: 500; color: var(--color-text-primary); }
.memory-arrow { color: var(--color-text-muted); }
.memory-meta { margin-left: auto; display: flex; gap: 8px; align-items: center; }
.memory-use-count {
  font-family: var(--font-num);
  font-size: 11px;
  color: var(--color-text-muted);
  background: var(--card-bg);
  padding: 2px 8px;
  border-radius: 999px;
}

/* ==================== Import modal body ==================== */
.modal-subtitle {
  font-size: 13px;
  color: var(--color-text-secondary);
  margin: 0 0 12px;
}
.import-label {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: var(--card-bg);
  border: 1px dashed var(--color-border);
  border-radius: var(--input-radius);
  padding: 14px 20px;
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-primary);
  cursor: pointer;
  transition: all var(--t-fast) var(--ease-out);
}
.import-label:hover { border-color: var(--color-action-accent); background: var(--orange-50); }
.hidden { display: none; }
.import-filename {
  font-size: 12px;
  color: var(--color-text-secondary);
  margin: 8px 0 0;
}
.import-preview {
  margin-top: 16px;
  padding: 12px;
  background: var(--paper-200);
  border-radius: 8px;
  font-size: 12px;
}
.preview-title { font-weight: 500; color: var(--color-text-primary); margin: 0 0 8px; }
.preview-row {
  display: flex;
  justify-content: space-between;
  padding: 4px 0;
  border-bottom: 1px solid var(--color-border-soft);
}
.preview-row:last-child { border-bottom: none; }
.import-error {
  font-size: 12px;
  color: var(--color-feedback-negative);
  margin-top: 8px;
}

/* ==================== Budget modal body ==================== */
.budget-list { display: flex; flex-direction: column; gap: 16px; }
.budget-summary {
  display: grid;
  grid-template-columns: repeat(3, 1fr) 1.5fr;
  gap: 12px;
  padding: 14px 16px;
  background: var(--paper-200);
  border-radius: 12px;
  margin-bottom: 12px;
}
.summary-cell { display: flex; flex-direction: column; gap: 4px; }
.summary-eyebrow {
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--color-text-muted);
}
.summary-num {
  font-size: 18px;
  font-weight: 600;
  letter-spacing: -0.02em;
  line-height: 1.1;
  color: var(--color-text-primary);
}
.summary-usage { gap: 4px; }
.summary-percent {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-primary);
}
.budget-item { display: flex; flex-direction: column; gap: 8px; padding-bottom: 12px; border-bottom: 1px solid var(--color-border-soft); }
.budget-item:last-child { border-bottom: none; padding-bottom: 0; }
.budget-item-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  font-size: 13px;
}
.budget-cat { font-weight: 500; color: var(--color-text-primary); }
.budget-amounts { color: var(--color-text-secondary); font-size: 12px; }
.budget-item-actions { display: flex; gap: 6px; align-items: center; }
.budget-item-actions .input { flex: 1; }
.budget-empty {
  text-align: center;
  color: var(--color-text-muted);
  padding: 24px 0;
  font-size: 14px;
}
.budget-add-form { display: flex; gap: 8px; margin-top: 12px; }
.budget-add-form .input { flex: 1; }
.quick-amounts { display: flex; gap: 4px; }
.quick-amt-btn {
  background: var(--paper-200);
  border: 1px solid var(--color-border);
  color: var(--color-text-primary);
  padding: 4px 10px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 500;
  font-family: var(--font-num);
  cursor: pointer;
  transition: all var(--t-fast) var(--ease-out);
}
.quick-amt-btn:hover {
  background: var(--orange-50);
  border-color: var(--color-action-accent);
  color: var(--color-action-accent);
}

/* ==================== Export dropdown ==================== */
.export-wrapper { position: relative; }
.export-list { display: flex; flex-direction: column; gap: 4px; }
.export-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: transparent;
  border: none;
  padding: 12px 14px;
  border-radius: 10px;
  cursor: pointer;
  font-family: inherit;
  text-align: left;
  transition: background var(--t-fast) var(--ease-out);
}
.export-option:hover { background: var(--paper-200); }
.opt-name { font-size: 14px; font-weight: 500; color: var(--color-text-primary); }
.opt-hint { font-size: 11px; color: var(--color-text-muted); }

/* ==================== Utility ==================== */
.muted { color: var(--color-text-muted); }
.text-xs { font-size: 11px; }
.text-positive { color: var(--color-feedback-positive); }
.text-expense { color: var(--color-feedback-negative); }

/* ==================== 响应式 ==================== */
@media (max-width: 720px) {
  .main { padding: 0 12px; gap: 16px; }
  .balance-row { grid-template-columns: 1fr; }
  .balance-summary-card { order: 2; }
  .charts-row { grid-template-columns: 1fr; }
  .charts-side-col { flex-direction: row; }
  .chart-mini-canvas { height: 100px; }
  .filter-grid { grid-template-columns: 1fr 1fr; }
  .category-grid { grid-template-columns: repeat(4, 1fr); }
  .add-btn { padding: 12px 18px; }
  .add-label { display: none; }
  .add-btn { width: 52px; height: 52px; border-radius: 50%; padding: 0; justify-content: center; }
  .balance-amount { font-size: 36px; }
}
</style>

