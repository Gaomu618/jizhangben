import { ref, computed, readonly } from 'vue'

// 支持的语言
export const SUPPORTED_LANGUAGES = [
  { code: 'zh-CN', label: '简体中文' },
  { code: 'en-US', label: 'English' }
]

// 翻译字典（key 路径用点号分隔）
const messages = {
  'zh-CN': {
    app: {
      title: '记账本',
      welcome: '欢迎回来',
      greetingMorning: '早上好',
      greetingAfternoon: '下午好',
      greetingEvening: '晚上好',
    },
    nav: {
      stats: '统计分析',
      budget: '预算',
      trash: '回收站',
    },
    balance: {
      monthlyBalance: '本月结余',
      monthlyIncome: '本月收入',
      monthlyExpense: '本月支出',
      remainingDays: '剩 ¥{amount}（{percent}%）',
      overBudget: '已超支 ¥{amount}',
      remainingWarn: '还剩 ¥{amount}，快用完了',
      setBudget: '前往设置 →',
    },
    transaction: {
      title: '本月记录',
      search: '筛选',
      clearFilter: '清除',
      noRecords: '本月暂无记录',
      noMatch: '没有符合条件的记录',
      addHint: '点击下方"记一笔"开始记账',
      selected: '已选 {n} 条',
      delete: '删除选中',
      cancel: '取消',
      category: '分类',
      type: '类型',
      allTypes: '全部',
      income: '收入',
      expense: '支出',
      dateFrom: '日期起',
      dateTo: '日期止',
      amountFrom: '金额起',
      amountTo: '金额止',
      deleteConfirm: '删除后无法恢复，确定要删除吗？',
      batchDeleteConfirm: '确认要删除选中的 {n} 条记录吗？删除后无法恢复。',
    },
    modal: {
      newRecord: '新增记录',
      editRecord: '修改记录',
      amount: '金额',
      note: '备注（选填）',
      save: '保存',
      submit: '确认',
      delete: '删除',
    },
    trash: {
      title: '回收站',
      hint: '已删除的记录会在此保留 30 天',
      empty: '回收站是空的',
      restoreAll: '全部还原',
      emptyTrash: '清空回收站',
      emptyConfirm: '这将<strong>永久删除</strong>回收站里所有 {n} 条记录，无法恢复。确定吗？',
      purgeForever: '永久清空',
      date: '日期',
      type: '类型',
      amount: '金额',
      note: '备注',
      deletedAt: '删除时间',
      filterDate: '日期范围',
      filterCategory: '全部分类',
      detail: '详情',
      allCategory: '全部分类',
      restore: '还原',
      purge: '永久删除',
    },
    stats: {
      title: '统计分析',
      back: '← 返回主页',
      range: '区间',
      thisMonth: '本月',
      lastMonth: '上月',
      last7d: '近7天',
      last30d: '近30天',
      last90d: '近90天',
      thisYear: '今年',
      custom: '自定义',
      apply: '应用',
      exportPNG: '导出图片',
      avgDailyExpense: '日均支出',
      maxSingle: '最大单笔',
      topCategory: '最高频分类',
      recordsCount: '收支笔数',
      firstPeriod: '首期无对比',
      vsLast: 'vs 上期',
      vsLastUp: '↑ {n}% vs 上期',
      vsLastDown: '↓ {n}% vs 上期',
      heatmap: '每日支出热力图',
      incomeExpense: '收支对比',
      trend: '近6个月趋势',
      ratio: '收支占比',
      incomeCategory: '收入分类',
      expenseCategory: '支出分类',
      expenseRanking: '支出分类排行',
      budgetOverview: '本月预算概览',
      topExpenses: '最高支出 TOP {n}',
      noExpense: '本区间暂无支出',
      noRecord: '本区间暂无支出记录',
      noBudget: '本月还没有设置预算，',
      goSetBudget: '前往设置 →',
      records: '条',
      remaining: '结余',
    },
    common: {
      confirm: '确认',
      cancel: '取消',
      loading: '加载中...',
      addRecord: '记一笔',
      yes: '是',
      no: '否',
      income: '收入',
      expense: '支出',
    },
    language: {
      switchTo: '切换语言',
    },
  },
  'en-US': {
    app: {
      title: 'Ledger',
      welcome: 'Welcome back',
      greetingMorning: 'Good morning',
      greetingAfternoon: 'Good afternoon',
      greetingEvening: 'Good evening',
    },
    nav: {
      stats: 'Statistics',
      budget: 'Budget',
      trash: 'Recycle Bin',
    },
    balance: {
      monthlyBalance: 'This Month',
      monthlyIncome: 'Income',
      monthlyExpense: 'Expense',
      remainingDays: '¥{amount} left ({percent}%)',
      overBudget: 'Over budget by ¥{amount}',
      remainingWarn: 'Only ¥{amount} left',
      setBudget: 'Set budget →',
    },
    transaction: {
      title: 'Records',
      search: 'Filter',
      clearFilter: 'Clear',
      noRecords: 'No records this month',
      noMatch: 'No matching records',
      addHint: 'Tap "+" below to add your first record',
      selected: '{n} selected',
      delete: 'Delete',
      cancel: 'Cancel',
      category: 'Category',
      type: 'Type',
      allTypes: 'All',
      income: 'Income',
      expense: 'Expense',
      dateFrom: 'From',
      dateTo: 'To',
      amountFrom: 'Min',
      amountTo: 'Max',
      deleteConfirm: 'This cannot be undone. Delete?',
      batchDeleteConfirm: 'Delete {n} selected records? This cannot be undone.',
    },
    modal: {
      newRecord: 'New Record',
      editRecord: 'Edit Record',
      amount: 'Amount',
      note: 'Note (optional)',
      save: 'Save',
      submit: 'Submit',
      delete: 'Delete',
    },
    trash: {
      title: 'Recycle Bin',
      hint: 'Deleted records are kept for 30 days',
      empty: 'Recycle bin is empty',
      restoreAll: 'Restore All',
      emptyTrash: 'Empty Bin',
      emptyConfirm: 'This will <strong>permanently delete</strong> all {n} records. Continue?',
      purgeForever: 'Empty Forever',
      date: 'Date',
      type: 'Type',
      amount: 'Amount',
      note: 'Note',
      deletedAt: 'Deleted At',
      filterDate: 'Date Range',
      filterCategory: 'All Categories',
      detail: 'Detail',
      allCategory: 'All Categories',
      restore: 'Restore',
      purge: 'Delete Forever',
    },
    stats: {
      title: 'Statistics',
      back: '← Back',
      range: 'Range',
      thisMonth: 'Month',
      lastMonth: 'Last Month',
      last7d: '7 Days',
      last30d: '30 Days',
      last90d: '90 Days',
      thisYear: 'Year',
      custom: 'Custom',
      apply: 'Apply',
      exportPNG: 'Export',
      avgDailyExpense: 'Daily Avg',
      maxSingle: 'Max Single',
      topCategory: 'Top Category',
      recordsCount: 'Records',
      firstPeriod: 'No comparison',
      vsLast: 'vs prev',
      vsLastUp: '↑ {n}% vs prev',
      vsLastDown: '↓ {n}% vs prev',
      heatmap: 'Daily Heatmap',
      incomeExpense: 'Income vs Expense',
      trend: '6-Month Trend',
      ratio: 'Income/Expense Ratio',
      incomeCategory: 'Income by Category',
      expenseCategory: 'Expense by Category',
      expenseRanking: 'Expense Ranking',
      budgetOverview: 'Budget Overview',
      topExpenses: 'Top {n} Expenses',
      noExpense: 'No expenses in range',
      noRecord: 'No records in range',
      noBudget: 'No budget set, ',
      goSetBudget: 'Go set up →',
      records: 'records',
      remaining: 'Balance',
    },
    common: {
      confirm: 'Confirm',
      cancel: 'Cancel',
      loading: 'Loading...',
      addRecord: 'Add Record',
      yes: 'Yes',
      no: 'No',
      income: 'Income',
      expense: 'Expense',
    },
    language: {
      switchTo: 'Switch Language',
    },
  },
}

// 当前语言（localStorage 持久化）
const STORAGE_KEY = 'app_language'
const stored = localStorage.getItem(STORAGE_KEY)
const currentLang = ref(stored && messages[stored] ? stored : 'zh-CN')

// 切换语言
function setLanguage(code) {
  if (messages[code]) {
    currentLang.value = code
    localStorage.setItem(STORAGE_KEY, code)
  }
}

// 翻译函数：t('balance.monthlyBalance') 或 t('common.confirm', { name: 'X' })
export function t(key, params = {}) {
  const dict = messages[currentLang.value] || messages['zh-CN']
  const parts = key.split('.')
  let val = dict
  for (const p of parts) {
    val = val?.[p]
  }
  if (val === undefined) {
    // 回退到中文
    let fallback = messages['zh-CN']
    for (const p of parts) fallback = fallback?.[p]
    val = fallback
  }
  if (typeof val !== 'string') return key
  // 替换占位符 {name}
  return val.replace(/\{(\w+)\}/g, (_, k) => params[k] !== undefined ? params[k] : `{${k}}`)
}

export function useI18n() {
  return {
    lang: readonly(currentLang),
    setLanguage,
    t,
  }
}
