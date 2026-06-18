import { reactive } from 'vue'

const state = reactive({
  token: localStorage.getItem('token') || '',
  userinfo: (() => {
    const stored = localStorage.getItem('userinfo')
    if (!stored || stored === 'undefined') return {}
    try { return JSON.parse(stored) } catch { return {} }
  })()
})

export function useAuth() {
  const setAuth = (token, userinfo) => {
    state.token = token
    state.userinfo = userinfo
    localStorage.setItem('token', token)
    localStorage.setItem('userinfo', JSON.stringify(userinfo))
  }

  const clearAuth = () => {
    state.token = ''
    state.userinfo = {}
    localStorage.removeItem('token')
    localStorage.removeItem('userinfo')
  }

  const isAuthenticated = () => {
    return !!state.token
  }

  return {
    state,
    setAuth,
    clearAuth,
    isAuthenticated
  }
}