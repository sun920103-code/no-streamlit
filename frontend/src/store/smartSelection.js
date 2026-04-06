/**
 * 智选平台专属 Pinia Store
 * ========================
 * 严格与 diagnose.js / config.js 物理隔离。
 * 所有字段带 zx_ 语义前缀。
 */
import { defineStore } from 'pinia'

export const useSmartStore = defineStore('zx_smartSelection', {
  state: () => ({
    // ── 全局配置参数 (智选平台独立) ──
    zx_capital: 1000,            // 万元
    zx_targetReturn: 8.0,        // %
    zx_maxVol: 15.0,             // %
    zx_period: '1年',            // 半年/1年/3年

    // ── 基金池 ──
    zx_fundPool: [],             // 114只核心基金
    zx_fundPoolGrouped: {},      // 按类别分组
    zx_fundProfiles: [],         // 基金深度资料

    // ── Step 1: 宏观底仓结果 ──
    zx_macroResult: null,        // macro_allocation 完整返回
    zx_currentScenarioIdx: 1,    // 当前选中方案 (0=进取, 1=稳健, 2=防守)

    // ── Step 2: 战术配置结果 ──
    zx_tacticalResult: null,
    zx_tacticalOneclickResult: null,   // 一键战术配置完整返回
    zx_uploadedReports: [],            // 已上传研报文件列表

    // ── Step 3: 回测结果 ──
    zx_backtestResult: null,

    // ── 流水线状态 ──
    zx_loading: false,
    zx_error: null,
  }),

  getters: {
    /** 当前选中方案 (供战术配置使用) */
    zx_selectedScenario(state) {
      if (!state.zx_macroResult?.scenarios) return null
      const idx = state.zx_currentScenarioIdx !== undefined ? state.zx_currentScenarioIdx : 1
      return state.zx_macroResult.scenarios[idx] || state.zx_macroResult.scenarios[0]
    },

    /** 选中方案的权重字典 {code: weight_pct} */
    zx_selectedWeights(state) {
      const scenario = this.zx_selectedScenario
      if (!scenario?.allocations) return {}
      const weights = {}
      for (const alloc of scenario.allocations) {
        weights[alloc.code] = alloc.weight_pct
      }
      return weights
    },
  },

  actions: {
    // ── 配置参数更新 ──
    updateConfig({ capital, targetReturn, maxVol, period }) {
      if (capital !== undefined) this.zx_capital = capital
      if (targetReturn !== undefined) this.zx_targetReturn = targetReturn
      if (maxVol !== undefined) this.zx_maxVol = maxVol
      if (period !== undefined) this.zx_period = period
    },

    // ── 结果存储 ──
    setMacroResult(result) { this.zx_macroResult = result },
    setTacticalResult(result) { this.zx_tacticalResult = result },
    setTacticalOneclickResult(result) { this.zx_tacticalOneclickResult = result },
    setBacktestResult(result) { this.zx_backtestResult = result },
    setFundPool(pool, grouped) {
      this.zx_fundPool = pool
      this.zx_fundPoolGrouped = grouped || {}
    },
    setFundProfiles(profiles) { this.zx_fundProfiles = profiles },

    // ── 完全清空 (切换平台时调用) ──
    clearAll() {
      this.zx_macroResult = null
      this.zx_tacticalResult = null
      this.zx_tacticalOneclickResult = null
      this.zx_uploadedReports = []
      this.zx_backtestResult = null
      this.zx_loading = false
      this.zx_error = null
    },
  },
})
