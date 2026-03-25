import { defineStore } from 'pinia'

export const useDiagnoseStore = defineStore('diagnose', {
  state: () => ({
    rawWeights: {},
    hrpWeights: {},
    newsWeights: {},
    finalWeights: {},
    assetPrices: {},
    covMatrix: [],
    portfolioVolatility: 0,
    kpiResults: null
  }),
  actions: {
    setRawWeights(weights) { this.rawWeights = weights },
    setHrpWeights(weights) { this.hrpWeights = weights },
    setNewsWeights(weights) { this.newsWeights = weights },
    setFinalWeights(weights) { this.finalWeights = weights },
    setAssetData(prices, cov) {
      this.assetPrices = prices;
      this.covMatrix = cov;
    },
    setPortfolioVol(vol) { this.portfolioVolatility = vol },
    setKpis(kpis) { this.kpiResults = kpis },
    clear() {
      this.rawWeights = {}
      this.hrpWeights = {}
      this.newsWeights = {}
      this.finalWeights = {}
      this.assetPrices = {}
      this.covMatrix = []
      this.portfolioVolatility = 0
      this.kpiResults = null
    }
  }
})
