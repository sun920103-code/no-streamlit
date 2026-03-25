import { defineStore } from 'pinia'

export const useSmartSelectionStore = defineStore('smartSelection', {
  state: () => ({
    edbData: null,
    targetAllocation: null,
    matchedFunds: [],
    correlationMatrix: [],
    debateViews: null
  }),
  actions: {
    setEdbData(data) { this.edbData = data },
    setTargetAllocation(allocation) { this.targetAllocation = allocation },
    setMatchedFunds(funds, corr) {
       this.matchedFunds = funds;
       this.correlationMatrix = corr;
    },
    setDebateViews(views) { this.debateViews = views },
    clear() {
       this.edbData = null
       this.targetAllocation = null
       this.matchedFunds = []
       this.correlationMatrix = []
       this.debateViews = null
    }
  }
})
