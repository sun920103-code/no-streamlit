/**
 * 智选平台专属 API 模块
 * ======================
 * 命名空间: /api/v1/smart/
 * 严禁引用 api/index.js 中的任何诊断平台 API。
 */
import axios from 'axios'

const smartApi = axios.create({
  baseURL: '',
  timeout: 60000,
  headers: { 'Content-Type': 'application/json' },
})

// ── 基金池 ──
export const zxGetFundPool = () => smartApi.get('/api/v1/smart/fund_pool')
export const zxGetFundProfiles = () => smartApi.get('/api/v1/smart/fund_profiles')

// ── 宏观底仓引擎 ──
export const zxMacroAllocation = (payload) => smartApi.post('/api/v1/smart/macro_allocation', payload, {
  timeout: 120000,
})

// ── 战术调仓引擎 ──
export const zxTacticalAdjustment = (payload) => smartApi.post('/api/v1/smart/tactical_adjustment', payload, {
  timeout: 120000,
})

// ── 研报上传调仓 (multipart) ──
export const zxTacticalWithReport = (formData) => smartApi.post('/api/v1/smart/tactical_with_report', formData, {
  headers: { 'Content-Type': 'multipart/form-data' },
  timeout: 180000,
})

// ── 一键战术配置 (multipart: 新闻调仓 + 研报调仓) ──
export const zxTacticalOneClick = (formData) => smartApi.post('/api/v1/smart/tactical_oneclick', formData, {
  headers: { 'Content-Type': undefined },
  timeout: 300000,
})

// ── 历史回测引擎 ──
export const zxBacktest = (payload) => smartApi.post('/api/v1/smart/backtest', payload, {
  timeout: 120000,
})

export default smartApi
