import axios from 'axios'

// baseURL 留空 — 因为每个方法路径里都自带 /api/... 前缀
// 开发期：vite 代理会把 /api/* → http://localhost:5002/api/*
// 生产期：Nginx 反代同样处理 /api/*
const api = axios.create({
  baseURL: '',
  timeout: 10000,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器：添加 token
api.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => Promise.reject(error)
)

// 响应拦截器：处理错误
api.interceptors.response.use(
  response => {
    const res = response.data
    if (res.code !== 0 && res.code !== undefined) {
      alert(res.message || '请求失败')
      return Promise.reject(new Error(res.message || '请求失败'))
    }
    return res
  },
  error => {
    if (error.response) {
      if (error.response.status === 401) {
        localStorage.removeItem('token')
        window.location.href = '/login'
      }
      alert(error.response.data?.message || '网络错误')
    }
    return Promise.reject(error)
  }
)

// Auth API
export const authAPI = {
  login: (data) => api.post('/api/auth/login', data),
  register: (data) => api.post('/api/auth/register', data),
  logout: () => api.post('/api/auth/logout'),
  getUserInfo: () => api.get('/api/auth/userinfo'),
  updateProfile: (data) => api.post('/api/auth/profile', data),
  uploadAvatar: (formData) => api.post('/api/auth/avatar', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  wechatLogin: (data) => api.post('/api/auth/wechat/login', data)
}

// Bill API
export const billAPI = {
  getList: (params) => api.get('/api/bill/list', { params }),
  getDetail: (id) => api.get(`/api/bill/${id}`),
  add: (data) => api.post('/api/bill/add', data),
  edit: (id, data) => api.post(`/api/bill/edit/${id}`, data),
  delete: (id) => api.post(`/api/bill/delete/${id}`),
  batchDelete: (data) => api.post('/api/bill/batch-delete', data),
  // 导入/导出（用 FormData，所以单独走 fetch 路径，不走 axios 包装）
  importFile: async (file, dryRun = false) => {
    const fd = new FormData()
    fd.append('file', file)
    fd.append('dry_run', dryRun ? 'true' : 'false')
    const res = await fetch('/api/bill/import', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${localStorage.getItem('token') || ''}` },
      body: fd,
    })
    return { data: await res.json(), status: res.status }
  },
  exportFile: async (format = 'csv') => {
    const res = await fetch(`/api/bill/export?format=${format}`, {
      method: 'GET',
      headers: { 'Authorization': `Bearer ${localStorage.getItem('token') || ''}` },
    })
    if (!res.ok) throw new Error(`导出失败: ${res.status}`)
    const blob = await res.blob()
    return { blob, filename: `账单记录.${format}` }
  },
  // 回收站
  getTrash: (params) => api.get('/api/bill/trash', { params }),
  getTrashCount: () => api.get('/api/bill/trash/count'),
  restore: (id) => api.post(`/api/bill/restore/${id}`),
  purge: (id) => api.post(`/api/bill/purge/${id}`),
  emptyTrash: () => api.post('/api/bill/trash/empty'),
  restoreBatchTrash: (data) => api.post('/api/bill/trash/restore-batch', data),
  // 智能分类
  classify: (text) => api.post('/api/bill/classify', { text }),
  getClassifyMemory: () => api.get('/api/bill/classify/memory'),
  deleteClassifyMemory: (id) => api.delete(`/api/bill/classify/memory/${id}`),
  clearClassifyMemory: () => api.post('/api/bill/classify/memory/clear'),
  getBudget: (params) => api.get('/api/bill/budget', { params }),
  setBudget: (data) => api.post('/api/bill/budget', data),
  deleteBudget: (data) => api.post('/api/bill/delete-budget', data),
}

// Stats API
export const statsAPI = {
  getSummary: (params) => api.get('/api/stats/summary', { params }),
  getDaily: (params) => api.get('/api/stats/daily', { params }),
  getMonthly: (params) => api.get('/api/stats/monthly', { params }),
  getCategory: (params) => api.get('/api/stats/category', { params }),
  getTrend: (params) => api.get('/api/stats/trend', { params }),
  getTop: (params) => api.get('/api/stats/top', { params }),
}

// 分类管理 API
export const categoryAPI = {
  list: () => api.get('/api/category'),
  create: (data) => api.post('/api/category', data),
  remove: (id) => api.delete(`/api/category/${id}`),
  listKeywords: (id) => api.get(`/api/category/${id}/keywords`),
  addKeyword: (id, data) => api.post(`/api/category/${id}/keywords`, data),
  removeKeyword: (kwId) => api.delete(`/api/category/keywords/${kwId}`),
}

export default api