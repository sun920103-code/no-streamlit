<template>
  <div class="three-way-matrix fade-in" v-if="hasData">
    <div class="card-title" style="margin-bottom:16px;">
       📊 AI 决策三维透明验证表 (The 3-Way Reference)
    </div>
    <p class="desc">
       透视各大模型子模块在原持仓基础上叠加的具体战略/战术偏离，追踪每一分配置权重的演化路径。
    </p>

    <div class="table-container">
      <table class="holdings-table matrix-table">
        <thead>
          <tr>
            <th style="width:140px;">核心大类资产标签</th>
            <th class="col-raw">当前原始持仓</th>
            <th class="col-hrp">HRP 平价最优解</th>
            <th class="col-news">资讯战术附加偏离</th>
            <th class="col-final">AI 最终复合配置</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="cat in allCategories" :key="cat">
            <td class="cat-label">{{ cat }}</td>
            <td class="col-raw">{{ formatP(rawMap[cat]) }}</td>
            <td class="col-hrp">
               {{ formatP(hrpMap[cat]) }}
               <span class="diff-tag" :class="getDiffClass(hrpMap[cat], rawMap[cat])" v-if="rawMap[cat]">
                  {{ getDiffText(hrpMap[cat], rawMap[cat]) }}
               </span>
            </td>
            <td class="col-news">
               {{ formatP(newsMap[cat]) }}
               <span class="diff-tag" :class="getDiffClass(newsMap[cat], hrpMap[cat])" v-if="hrpMap[cat]">
                  {{ getDiffText(newsMap[cat], hrpMap[cat]) }}
               </span>
            </td>
            <td class="col-final final-val">
               {{ formatP(finalMap[cat]) }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useDiagnoseStore } from '../store/diagnose'

const store = useDiagnoseStore()

const hasData = computed(() => {
   return Object.keys(store.rawWeights).length > 0 || Object.keys(store.hrpWeights).length > 0;
})

function formatP(val) {
   if (!val && val !== 0) return '—';
   return (val * 100).toFixed(2) + '%';
}

function getDiffText(newVal, oldVal) {
   if (!newVal || !oldVal) return '';
   const diff = newVal - oldVal;
   if(Math.abs(diff) < 0.0001) return '-';
   return (diff > 0 ? '+' : '') + (diff * 100).toFixed(1) + '%';
}

function getDiffClass(newVal, oldVal) {
   if (!newVal || !oldVal) return '';
   const diff = newVal - oldVal;
   if(Math.abs(diff) < 0.0001) return 'diff-neutral';
   return diff > 0 ? 'diff-up' : 'diff-down';
}

// 提取当前在任何一部运算中出现过的资产大类
const allCategories = computed(() => {
   const set = new Set([
      ...Object.keys(store.rawWeights),
      ...Object.keys(store.hrpWeights),
      ...Object.keys(store.newsWeights),
      ...Object.keys(store.finalWeights)
   ])
   return Array.from(set).sort()
})

const rawMap = computed(() => store.rawWeights)
const hrpMap = computed(() => store.hrpWeights)
const newsMap = computed(() => store.newsWeights)
const finalMap = computed(() => Object.keys(store.finalWeights).length > 0 ? store.finalWeights : store.hrpWeights)

</script>

<style scoped>
.three-way-matrix {
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
  padding: 24px;
  border: 1px solid #E2E8F0;
  margin-bottom: 24px;
}
.desc {
  font-size: 13px;
  color: #64748B;
  margin-bottom: 20px;
}
.table-container {
  overflow-x: auto;
}
.matrix-table {
  width: 100%;
  border-collapse: collapse;
}
.matrix-table th {
  background: #F8FAFC;
  color: #334155;
  font-weight: 600;
  font-size: 13px;
  padding: 12px;
  border-bottom: 2px solid #E2E8F0;
  text-align: right;
  white-space: nowrap;
}
.matrix-table th:first-child { text-align: left; }

.matrix-table td {
  padding: 14px 12px;
  border-bottom: 1px solid #F1F5F9;
  font-size: 14px;
  font-family: 'JetBrains Mono', monospace;
  text-align: right;
  color: #1E293B;
}
.matrix-table td.cat-label {
  text-align: left;
  font-family: -apple-system, BlinkMacSystemFont, sans-serif;
  font-weight: 600;
  color: #0F172A;
}

.col-raw { background: rgba(241,245,249,0.3); }
.col-hrp { background: rgba(59,130,246,0.03); border-left: 1px dashed #E2E8F0; }
.col-news { background: rgba(245,158,11,0.03); border-left: 1px dashed #E2E8F0; }
.col-final { background: rgba(16,185,129,0.05); border-left: 2px solid #E2E8F0; }

.final-val {
  font-weight: 700;
  color: #059669;
}

.diff-tag {
  display: inline-block;
  margin-left: 8px;
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: 600;
}
.diff-up { color: #EF4444; background: #FEE2E2; }
.diff-down { color: #10B981; background: #D1FAE5; }
.diff-neutral { color: #94A3B8; }
</style>
