import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// ── 组合管理 ──
export const getPortfolioConfig = () => api.get('/portfolio/config')
export const triggerRebalance = (params) => api.post('/portfolio/rebalance', params)
export const getRebalanceStatus = (taskId) => api.get(`/portfolio/status/${taskId}`)

// ── 分析 ──
export const getMacroRegime = () => api.get('/analysis/macro/regime')
export const getBLViews = () => api.get('/analysis/whitebox/bl-views')
export const getStressTest = () => api.get('/analysis/stress-test')

// ── 报告 ──
export const generateMarketReview = (params) => api.post('/report/market-review', params)
export const generateReport = (params) => api.post('/report/generate', params)
export const getReportTemplates = () => api.get('/report/templates')

export default api
