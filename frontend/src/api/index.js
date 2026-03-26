import axios from 'axios'
import * as generatedApi from './generated'

const api = axios.create({
  baseURL: '', // Removed '/api/v1' as generated.js uses absolute paths
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// ── 组合管理 ──
export const getPortfolioConfig = () => api.get('/api/v1/portfolio/config')
export const triggerRebalance = (params) => api.post('/api/v1/portfolio/rebalance', params)
export const getRebalanceStatus = (taskId) => api.get(`/api/v1/portfolio/status/${taskId}`)

// ── 核心量化算子 ──
export const optimizeHrp = (payload) => api.post('/api/v1/quant/optimize_hrp', payload)
export const optimizeBl = (payload) => api.post('/api/v1/quant/optimize_bl', payload)
export const getRebalanceInstructions = (payload) => api.post('/api/v1/quant/rebalance_instructions', payload)

// ── AI 多智能体中枢 ──
export const extractNewsViews = (payload) => api.post('/api/v1/ai/extract_news_views', payload)
export const extractReportViews = (formData) => api.post('/api/v1/ai/extract_report_views', formData, {
  headers: { 'Content-Type': 'multipart/form-data' },
  timeout: 120000,
})

// ── 业绩回测与导出 ──
export const calculateKpis = (payload) => api.post('/api/v1/quant/calculate_kpis', payload)
export const exportDiagnosePdf = (payload) => api.post('/api/v1/export/generate_diagnose_pdf', payload, {
  responseType: 'blob', // 必须使用 blob 才能正确下载 PDF
  timeout: 300000,
})
export const exportDiagnoseDocx = (payload) => api.post('/api/v1/export/generate_diagnose_docx', payload, {
  responseType: 'blob', // 必须使用 blob
  timeout: 300000,
})

// ── 分析与宏观 ──
export const fetchEdbData = () => api.post('/api/v1/macro/fetch_edb_data')
export const calculateAssetAllocation = (payload) => api.post('/api/v1/macro/calculate_asset_allocation', payload)
export const matchFunds = (payload) => api.post('/api/v1/quant/match_funds', payload)

// ── Campaign 10: Advanced Quant Metrics ──
export const forecastEgarch = (payload) => api.post('/api/v1/quant/forecast_egarch', payload)
export const analyzePca = (payload) => api.post('/api/v1/quant/analyze_pca', payload)
export const annualReturns = (payload) => api.post('/api/v1/quant/annual_returns', payload)
export const simulateStressTest = (payload) => api.post('/api/v1/quant/simulate_stress_test', payload)
// ── Campaign 12: Core Fund Pool Whitebox ──
export const getCoreFundPool = () => api.get('/api/v1/data/get_core_fund_pool')

export const getMacroRegime = () => api.get('/api/v1/analysis/macro/regime')
export const getBLViews = () => api.get('/api/v1/analysis/whitebox/bl-views')
export const getStressTest = () => api.get('/api/v1/analysis/stress-test')

// ── 宏观量化引擎 (Markov + CVaR + MBL + Factor RP) ──
export const optimizeMbl = (payload) => api.post('/api/v1/quant/optimize_mbl', payload)
export const optimizeFactorRp = (payload) => api.post('/api/v1/quant/optimize_factor_rp', payload)
export const optimizeCvar = (payload) => api.post('/api/v1/quant/optimize_cvar', payload)
export const runFullRebalance = (payload) => api.post('/api/v1/portfolio/run_full_rebalance', payload)
// ── 一键配置调仓 SSE ──
// Note: This uses fetch() + ReadableStream in SmartSelectionManager.vue, not axios
export const getMacroQuadrant = (payload) => api.post('/api/v1/macro/quadrant', payload || {})
export const uploadHoldings = (file) => {
  const form = new FormData()
  form.append('file', file)
  return api.post('/api/v1/analysis/parse-holdings', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 30000,
  })
}

// ── 报告 ──
export const generateMarketReview = (params) => api.post('/api/v1/report/market-review', params)
export const generateReport = (params) => api.post('/api/v1/report/generate', params)
export const getReportTemplates = () => api.get('/api/v1/report/templates')

export { generatedApi }
export default api
