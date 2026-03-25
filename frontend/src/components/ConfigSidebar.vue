<template>
  <div class="config-sidebar fade-in">
    <div class="sidebar-header">
      <span class="shield-icon">🛡️</span>
      <h3>个性化风险约束</h3>
      <p>Hard Constraints</p>
    </div>

    <div class="form-group">
      <label>入账原始资金 (元)</label>
      <div class="input-wrapper">
        <span class="currency-symbol">¥</span>
        <input 
          type="text" 
          :value="formattedAmount" 
          @input="onAmountInput" 
          @blur="formatAmountOnBlur"
        />
      </div>
      <small>决定了实盘调仓股数和总金额</small>
    </div>

    <div class="form-group">
      <label>预期年化收益率目标 (%)</label>
      <div class="input-wrapper">
        <input 
          type="number" 
          v-model.number="localTargetReturn" 
          step="0.01" 
          min="0"
          @change="syncStore"
        />
        <span class="percent-symbol">%</span>
      </div>
      <small>算法 Markowitz 最低回报约束门槛</small>
    </div>

    <div class="form-group">
      <label>最大年化波动率上限 (%)</label>
      <div class="input-wrapper">
        <input 
          type="number" 
          v-model.number="localMaxVol" 
          step="0.01" 
          min="0"
          @change="syncStore"
        />
        <span class="percent-symbol">%</span>
      </div>
      <small class="text-alert">核心防丢包防线：超越此阈值将拦截建仓</small>
    </div>

    <!-- Campaign 13: 全局比较基准 -->
    <div class="form-group">
      <label>分析比较基准 (Benchmark)</label>
      <div class="input-wrapper">
         <select v-model="localBenchmark" @change="syncStore" class="full-select">
            <option value="000300.SH">沪深300 (000300.SH)</option>
            <option value="399001.SZ">深证成指 (399001.SZ)</option>
            <option value="000905.SH">中证500 (000905.SH)</option>
            <option value="000852.SH">中证1000 (000852.SH)</option>
            <option value="CBA00301.CS">中债综合财富(总值)指数</option>
         </select>
      </div>
      <small>所有黑天鹅推演与Alpha/Beta都将基于此基准</small>
    </div>

    <div class="sidebar-footer">
       <button class="lock-btn" @click="syncStore">
          🔒 锁定当前配置约束
       </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useConfigStore } from '../store/config'

const store = useConfigStore()

// Local states for inputs (percentages stored as human-readable whole numbers, e.g. 8 for 0.08)
const rawAmount = ref(store.totalAmount)
const localTargetReturn = ref(parseFloat((store.targetReturn * 100).toFixed(2)))
const localMaxVol = ref(parseFloat((store.maxVolatility * 100).toFixed(2)))
const localBenchmark = ref(store.benchmarkCode || '000300.SH')

// Watch store changes if updated from elsewhere
watch(() => store.totalAmount, val => rawAmount.value = val)
watch(() => store.targetReturn, val => localTargetReturn.value = parseFloat((val * 100).toFixed(2)))
watch(() => store.maxVolatility, val => localMaxVol.value = parseFloat((val * 100).toFixed(2)))
watch(() => store.benchmarkCode, val => localBenchmark.value = val)

// 金额千分位处理
const formattedAmount = computed(() => {
  if (!rawAmount.value && rawAmount.value !== 0) return ''
  return Number(rawAmount.value).toLocaleString('zh-CN')
})

function onAmountInput(e) {
  // 只保留数字
  const val = e.target.value.replace(/[^\d]/g, '')
  rawAmount.value = val ? parseInt(val, 10) : 0
}

function formatAmountOnBlur(e) {
  e.target.value = formattedAmount.value
  syncStore()
}

function syncStore() {
   // Validate and sync to backend decimal formats
   const tr = localTargetReturn.value / 100.0;
   const mv = localMaxVol.value / 100.0;
   
   store.updateConfig({
     amount: rawAmount.value,
     returnRate: tr,
     volatility: mv,
     benchmark: localBenchmark.value
   })
}
</script>

<style scoped>
.config-sidebar {
  width: 280px;
  background: white;
  border-right: 1px solid #E2E8F0;
  padding: 24px;
  display: flex;
  flex-direction: column;
  box-shadow: 2px 0 15px rgba(0,0,0,0.02);
  height: 100%;
  overflow-y: auto;
}

.sidebar-header {
  text-align: center;
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 2px dashed #E2E8F0;
}
.sidebar-header .shield-icon {
  font-size: 32px;
  display: block;
  margin-bottom: 8px;
}
.sidebar-header h3 {
  margin: 0;
  font-size: 16px;
  color: #0F172A;
}
.sidebar-header p {
  margin: 4px 0 0;
  font-size: 12px;
  color: #94A3B8;
  font-family: monospace;
}

.form-group {
  margin-bottom: 24px;
}
.form-group label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: #334155;
  margin-bottom: 8px;
}
.input-wrapper {
  display: flex;
  align-items: center;
  background: #F8FAFC;
  border: 1px solid #CBD5E1;
  border-radius: 8px;
  overflow: hidden;
  transition: all 0.2s;
}
.input-wrapper:focus-within {
  border-color: #6366F1;
  box-shadow: 0 0 0 3px rgba(99,102,241,0.1);
}
.currency-symbol, .percent-symbol {
  padding: 0 12px;
  background: #F1F5F9;
  color: #64748B;
  font-weight: 500;
  border-right: 1px solid #CBD5E1;
}
.percent-symbol {
  border-right: none;
  border-left: 1px solid #CBD5E1;
}
input, .full-select {
  flex: 1;
  border: none;
  padding: 10px 12px;
  background: transparent;
  outline: none;
  font-size: 14px;
  font-weight: 500;
  color: #0F172A;
  width: 100%;
}
.full-select {
  cursor: pointer;
  appearance: none;
}
small {
  display: block;
  font-size: 11px;
  color: #94A3B8;
  margin-top: 6px;
}
small.text-alert {
  color: #EF4444;
}

.sidebar-footer {
  margin-top: auto;
  padding-top: 30px;
}
.lock-btn {
  width: 100%;
  background: #F1F5F9;
  color: #475569;
  border: 1px dashed #94A3B8;
  padding: 12px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}
.lock-btn:hover {
  background: #E2E8F0;
  color: #0F172A;
  border-color: #64748B;
}
</style>
