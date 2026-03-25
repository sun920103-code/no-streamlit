<template>
  <div class="advanced-metrics fade-in">
    <div class="header">
      <h3><span class="icon">🔬</span> 智选平台·高级量化动力学分析</h3>
      <p>EGARCH 条件波动预测 | 主成分特征提取 | 年度收益切片</p>
    </div>

    <!-- loading 窗 -->
    <div v-if="loading" class="metrics-loading">
      <div class="spinner"></div>
      <span>正在启动量化算子集群计算中...</span>
    </div>

    <div v-else class="metrics-grid">
      <!-- EGARCH 波动率 -->
      <div class="metric-card">
         <div class="card-title">EGARCH(1,1) 动态条件波动率</div>
         <v-chart class="chart-container" :option="egarchOption" autoresize />
      </div>
      
      <!-- PCA 因子载荷 -->
      <div class="metric-card">
         <div class="card-title">PCA 核心主成分特征载荷</div>
         <v-chart class="chart-container" :option="pcaOption" autoresize />
      </div>
      
      <!-- Annual Returns -->
      <div class="metric-card full-width">
         <div class="card-title">配置组合历年收益追踪</div>
         <v-chart class="chart-container" :option="annualOption" autoresize style="height: 250px" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, BarChart, RadarChart } from 'echarts/charts'
import { TooltipComponent, GridComponent, LegendComponent, VisualMapComponent, MarkAreaComponent, MarkLineComponent } from 'echarts/components'
import { forecastEgarch, analyzePca, annualReturns } from '../api'

use([CanvasRenderer, LineChart, BarChart, RadarChart, TooltipComponent, GridComponent, LegendComponent, VisualMapComponent, MarkAreaComponent, MarkLineComponent])

const props = defineProps({
  funds: {
    type: Array,
    default: () => []
  }
})

const loading = ref(true)

const egarchOption = ref({})
const pcaOption = ref({})
const annualOption = ref({})

// 生成伪回测序列 (近3年)
function generateSyntheticReturns(funds) {
   const dates = [];
   const returns = []; // 组合级收益
   const assetsReturns = {}; // 个券级收益
   
   funds.forEach(f => {
      assetsReturns[f.name] = [];
   });
   
   const today = new Date();
   let currentNav = 1.0;
   
   for(let i=750; i>=0; i--) {
      const d = new Date(today.getTime() - i * 24 * 3600 * 1000);
      // 跳过周末
      if(d.getDay() === 0 || d.getDay() === 6) continue;
      dates.push(d.toISOString().split('T')[0]);
      
      let dayRet = 0;
      funds.forEach(f => {
         // 根据类别制造点不同的分布
         const vol = f.category.includes('股票') ? 0.012 : (f.category.includes('债') ? 0.002 : 0.008);
         // 加入一些共同的系统性冲击
         const sysShock = Math.sin(i / 20) * 0.005;
         const r = sysShock + (Math.random() - 0.5) * vol * 2.5; 
         assetsReturns[f.name].push(r);
         dayRet += r * f.weight;
      });
      returns.push(dayRet);
   }
   
   return { dates, returns, assetsReturns };
}

async function fetchMetrics() {
  if (!props.funds || props.funds.length === 0) return;
  loading.value = true;
  
  try {
    const { dates, returns, assetsReturns } = generateSyntheticReturns(props.funds);
    
    // 1. EGARCH
    const egRes = await forecastEgarch({ dates, returns });
    if(egRes.status === 'success') {
       const egData = egRes.data;
       egarchOption.value = {
         tooltip: { trigger: 'axis', formatter: '{b}<br/>波动率: {c}' },
         grid: { left: '10%', right: '5%', bottom: '15%', top: '15%' },
         xAxis: { type: 'category', data: egData.dates, axisLabel: { color: '#6B7B8D' } },
         yAxis: { type: 'value', axisLabel: { formatter: (v) => (v * 100).toFixed(1) + '%' } },
         series: [{
            data: egData.cond_vol, 
            type: 'line', 
            smooth: true,
            lineStyle: { width: 2, color: '#F59E0B' },
            areaStyle: { color: 'rgba(245,158,11,0.1)' },
            markLine: {
               data: [{ type: 'average', name: 'Avg' }],
               lineStyle: { type: 'dashed', color: '#EF4444' }
            }
         }]
       }
    }
    
    // 2. PCA
    const pcaRes = await analyzePca({ assets_returns: assetsReturns });
    if(pcaRes.status === 'success') {
       const pcaData = pcaRes.data; // [{pc_name, explained_variance_ratio, loadings}]
       const pc1 = pcaData[0];
       const pc2 = pcaData[1] || pcaData[0];
       
       const indicator = props.funds.map(f => ({ name: f.name.substring(0,6), max: 1, min: -1 }));
       const v1 = props.funds.map(f => pc1.loadings[f.name] || 0);
       const v2 = props.funds.map(f => pc2.loadings[f.name] || 0);
       
       pcaOption.value = {
          tooltip: {},
          legend: { data: [`PC1 (${(pc1.explained_variance_ratio*100).toFixed(1)}%)`, `PC2 (${(pc2.explained_variance_ratio*100).toFixed(1)}%)`], bottom: 0 },
          radar: {
             indicator,
             radius: '60%',
             splitArea: { areaStyle: { color: ['#F9FAFB', '#F3F4F6'] } }
          },
          series: [{
             type: 'radar',
             data: [
               { value: v1, name: `PC1 (${(pc1.explained_variance_ratio*100).toFixed(1)}%)`, lineStyle: { color: '#3B82F6' }, areaStyle: { color: 'rgba(59,130,246,0.3)' } },
               { value: v2, name: `PC2 (${(pc2.explained_variance_ratio*100).toFixed(1)}%)`, lineStyle: { color: '#10B981' } }
             ]
          }]
       };
    }
    
    // 3. Annual Returns
    const annRes = await annualReturns({ dates, returns });
    if(annRes.status === 'success') {
       const annData = annRes.data;
       const years = annData.map(d => d.year);
       const rets = annData.map(d => d.return);
       
       annualOption.value = {
          tooltip: { formatter: (p) => `${p.name}年: ${(p.value*100).toFixed(2)}%` },
          grid: { left: '5%', right: '5%', bottom: '15%', top: '15%' },
          xAxis: { type: 'category', data: years },
          yAxis: { type: 'value', axisLabel: { formatter: (v) => (v * 100).toFixed(0) + '%' } },
          visualMap: {
             show: false,
             pieces: [{ gt: 0, color: '#10B981' }, { lte: 0, color: '#EF4444' }]
          },
          series: [{
             type: 'bar',
             data: rets,
             barWidth: '40%',
             itemStyle: { borderRadius: [4, 4, 0, 0] }
          }]
       }
    }
    
  } catch(e) {
    console.error("Failed to load metrics", e);
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
   fetchMetrics()
})

watch(() => props.funds, () => {
   fetchMetrics()
}, { deep: true })
</script>

<style scoped>
.advanced-metrics {
  margin-top: 40px;
  background: white;
  border-radius: 16px;
  padding: 30px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.05);
}
.header {
  margin-bottom: 24px;
}
.header h3 {
  font-size: 20px;
  color: #1E293B;
  display: flex;
  align-items: center;
  gap: 8px;
}
.header p {
  color: #64748B;
  font-size: 14px;
  margin-top: 6px;
}

.metrics-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px;
  color: #8B5CF6;
  font-weight: 500;
}
.spinner {
  width: 36px;
  height: 36px;
  border: 3px solid rgba(139,92,246,0.2);
  border-top-color: #8B5CF6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}
@keyframes spin { to { transform: rotate(360deg); } }

.metrics-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}
.metric-card {
  background: #F8FAFC;
  border-radius: 12px;
  padding: 20px;
  border: 1px solid #E2E8F0;
}
.full-width {
  grid-column: span 2;
}
.card-title {
  font-size: 14px;
  font-weight: 600;
  color: #334155;
  margin-bottom: 16px;
}
.chart-container {
  height: 280px;
  width: 100%;
}
</style>
