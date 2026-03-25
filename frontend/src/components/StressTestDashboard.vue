<template>
  <div class="stress-test-dashboard">
    <div class="st-header">
      <div class="title-area">
        <span class="st-icon">⚠️</span>
        <div>
          <h2>黑天鹅时空推演局 (Stress Test)</h2>
          <p>模拟当前配置在历次极端危机中的回撤深度与生存能力</p>
        </div>
      </div>
      <div class="st-controls">
         <select v-model="selectedScenario" class="st-select">
            <option v-for="scen in scenarios" :key="scen.label" :value="scen">{{ scen.label }}</option>
         </select>
         <button class="st-run-btn" @click="runTest" :disabled="loading">
            {{ loading ? '时空推演中...' : '💥 执行黑天鹅回测' }}
         </button>
      </div>
    </div>

    <div v-if="resultData" class="st-content fade-in">
       <!-- 核心 KPI 警告区 -->
       <div class="st-kpi-row">
          <div class="st-kpi-box text-red">
             <div class="kpi-label">危机区间最大回撤 (MDD)</div>
             <div class="kpi-val">{{ (resultData.max_drawdown * 100).toFixed(2) }}%</div>
          </div>
          <div class="st-kpi-box text-dark">
             <div class="kpi-label">区间累计总损益</div>
             <div class="kpi-val">{{ (resultData.portfolio_impact * 100).toFixed(2) }}%</div>
          </div>
          <div class="st-kpi-box text-alert">
             <div class="kpi-label">风险评定</div>
             <div class="kpi-val">{{ resultData.risk_level }}</div>
          </div>
       </div>

       <!-- 净值走势图 -->
       <div class="st-chart-box">
          <v-chart class="st-chart" :option="chartOption" autoresize />
       </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import { TooltipComponent, GridComponent, LegendComponent, MarkPointComponent } from 'echarts/components'
import { simulateStressTest } from '../api'

use([CanvasRenderer, LineChart, TooltipComponent, GridComponent, LegendComponent, MarkPointComponent])

const props = defineProps({
  funds: {
    type: Array,
    default: () => []
  }
})

const scenarios = [
  { label: '2008 全球金融危机', start: '2008-05-01', end: '2008-11-30' },
  { label: '2015 股灾与跌停潮', start: '2015-06-12', end: '2016-02-28' },
  { label: '2022 美联储激进加息', start: '2022-01-01', end: '2022-10-31' },
  { label: '2020 新冠疫情熔断', start: '2020-02-20', end: '2020-03-23' }
]
const selectedScenario = ref(scenarios[1])

const loading = ref(false)
const resultData = ref(null)
const chartOption = ref({})

async function runTest() {
   if(!props.funds || props.funds.length === 0) return;
   loading.value = true;
   
   try {
      // 提取配置权重映射到顶层宏观资产
      const weights = {};
      props.funds.forEach(f => {
         // 合并同类项权重
         const baseClass = f.category.split(" ")[1] || f.category;
         weights[baseClass] = (weights[baseClass] || 0) + f.weight;
      });
      
      const payload = {
         portfolio_weights: weights,
         scenario_label: selectedScenario.value.label,
         start_date: selectedScenario.value.start,
         end_date: selectedScenario.value.end,
         benchmark_name: "沪深300"
      };
      
      const res = await simulateStressTest(payload);
      if(res.status === 'success') {
         resultData.value = res.data;
         buildChart(res.data);
      }
   } catch(e) {
      alert("压力测试推演失败：" + e.message);
   } finally {
      loading.value = false;
   }
}

function buildChart(data) {
   const { nav_path, dates, benchmark_nav_path, benchmark_name } = data;
   const xAxisData = dates || nav_path.map((_, i) => `Day ${i+1}`);
   
   const series = [
      {
         name: '当前配置模拟净值',
         type: 'line',
         data: nav_path,
         showSymbol: false,
         lineStyle: { width: 3, color: '#EF4444' },
         areaStyle: { color: 'rgba(239, 68, 68, 0.15)' },
         markPoint: {
            data: [ { type: 'min', name: '最大坑' } ],
            itemStyle: { color: '#B91C1C' }
         }
      }
   ];
   
   if(benchmark_nav_path && benchmark_nav_path.length > 0) {
      series.push({
         name: benchmark_name,
         type: 'line',
         data: benchmark_nav_path,
         showSymbol: false,
         lineStyle: { width: 2, type: 'dashed', color: '#6B7280' }
      })
   }
   
   chartOption.value = {
      backgroundColor: '#111827', // 黑底
      tooltip: { trigger: 'axis' },
      legend: { textStyle: { color: '#9CA3AF' }, bottom: 0 },
      grid: { left: '8%', right: '5%', top: '10%', bottom: '15%' },
      xAxis: { type: 'category', data: xAxisData, axisLine: { lineStyle: { color: '#4B5563' } } },
      yAxis: { type: 'value', min: 'dataMin', axisLine: { lineStyle: { color: '#4B5563' } }, splitLine: { lineStyle: { color: '#374151' } } },
      series
   };
}
</script>

<style scoped>
.stress-test-dashboard {
  margin-top: 40px;
  background: #111827; /* 纯黑科幻风 */
  border: 1px solid #374151;
  border-radius: 16px;
  padding: 30px;
  color: #F9FAFB;
  box-shadow: 0 10px 40px rgba(0,0,0,0.5);
}
.st-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #374151;
  padding-bottom: 20px;
  margin-bottom: 24px;
}
.title-area {
  display: flex;
  align-items: center;
  gap: 16px;
}
.st-icon {
  font-size: 32px;
}
.title-area h2 {
  font-size: 22px;
  margin: 0 0 6px 0;
  color: #F87171;
  text-shadow: 0 0 10px rgba(248,113,113,0.3);
}
.title-area p {
  margin: 0;
  font-size: 14px;
  color: #9CA3AF;
}
.st-controls {
  display: flex;
  gap: 12px;
}
.st-select {
  background: #1F2937;
  border: 1px solid #4B5563;
  color: #F9FAFB;
  padding: 10px 16px;
  border-radius: 8px;
  outline: none;
  font-size: 14px;
}
.st-run-btn {
  background: linear-gradient(135deg, #DC2626 0%, #991B1B 100%);
  border: none;
  color: white;
  padding: 10px 24px;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.2s;
  box-shadow: 0 4px 15px rgba(220,38,38,0.4);
}
.st-run-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(220,38,38,0.6);
}
.st-run-btn:disabled {
  opacity: 0.6;
  cursor: wait;
}

.st-kpi-row {
  display: flex;
  gap: 20px;
  margin-bottom: 24px;
}
.st-kpi-box {
  flex: 1;
  background: #1F2937;
  border: 1px solid #374151;
  border-radius: 12px;
  padding: 20px;
  text-align: center;
}
.kpi-label {
  font-size: 13px;
  color: #9CA3AF;
  margin-bottom: 8px;
}
.kpi-val {
  font-size: 28px;
  font-weight: bold;
}
.text-red .kpi-val { color: #F87171; }
.text-dark .kpi-val { color: #E5E7EB; }
.text-alert .kpi-val { color: #FBBF24; }

.st-chart-box {
  background: #111827;
  border-radius: 12px;
  padding: 0;
  height: 350px;
  border: 1px solid #374151;
}
.st-chart {
  width: 100%;
  height: 100%;
}
</style>
