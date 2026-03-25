import { defineStore } from 'pinia'

export const useConfigStore = defineStore('config', {
  state: () => ({
    // 全局默认配置参数
    totalAmount: 10000000,
    targetReturn: 0.08,
    maxVolatility: 0.15,
    benchmarkCode: '000300.SH' // Campaign 13: 全局比较基准
  }),
  actions: {
    updateConfig({ amount, returnRate, volatility, benchmark }) {
      if (amount !== undefined) this.totalAmount = amount;
      if (returnRate !== undefined) this.targetReturn = returnRate;
      if (volatility !== undefined) this.maxVolatility = volatility;
      if (benchmark !== undefined) this.benchmarkCode = benchmark;
    }
  }
})
