<template>
  <div class="smart-selection-layout">
    <ConfigSidebar />
    <div class="smart-selection-container">
    <div class="header-actions">
       <div class="left-actions">
         <AsyncButton :action="fetchEdb" type="primary" text="🚀 启动 EDB 数据检索提取" />
         <AsyncButton :action="runDebate" style="background:#8B5CF6;border-color:#8B5CF6;" text="🧠 运行虚拟投研分析会" />
       </div>
       <div class="right-actions" v-if="debateFinished">
         <AsyncButton :action="extractAllocation" style="background:#F59E0B;border-color:#F59E0B;" text="🎯 提取大类资产配置" />
         <AsyncButton v-if="targetAllocation" :action="runMatchFunds" style="background:#10B981;border-color:#10B981;" text="⚡ 一键智能选基配置" />
       </div>
    </div>

    <div class="content-grid">
      <!-- Left: EDB Macro & Asset Alloc Doughnut -->
      <div class="left-col">
        <div class="card edb-card">
          <div class="card-title">宏观特征引擎 (EDB)</div>
          <p v-if="!edbData" class="empty-text">等待检索...</p>
          <div v-else>
            <div class="metric-block">
               <span class="label">市场状态：</span>
               <span class="value highlight-text">{{ edbData.market_state }}</span>
            </div>
            <div class="metric-block">
               <span class="label">综合得分：</span>
               <span class="value">{{ edbData.composite_score.toFixed(3) }}</span>
            </div>
            <div class="sub-metrics">
               <div>宏观: {{ edbData.macro_total.toFixed(3) }}</div>
               <div>估值: {{ edbData.valuation_total.toFixed(3) }}</div>
               <div>风险: {{ edbData.risk_total.toFixed(3) }}</div>
            </div>
          </div>
        </div>

        <div class="card alloc-card" v-show="targetAllocation">
          <div class="card-title">自上而下大类配置占比</div>
          <div ref="doughnutChartRef" style="height: 300px; width:100%;"></div>
        </div>
      </div>

      <!-- Center: Multi-Agent Debate Timeline -->
      <div class="center-col card">
         <div class="card-title">虚拟投研辩论实况 (SSE)</div>
         <div class="debate-stream" ref="debateStreamRef">
           <div v-for="(log, idx) in debateLogs" :key="idx" class="log-item fade-in">
              <span class="log-bubble">{{ log }}</span>
           </div>
           <div v-if="isDebating" class="typing-indicator">分析师思考中<span>.</span><span>.</span><span>.</span></div>
           <p v-if="debateLogs.length === 0 && !isDebating" class="empty-text">点击上方运行投研会开始多智能体辩论...</p>
         </div>
         <div class="debate-conclusion" v-if="debateFinished && debateViews">
            <h4>🏅 投委会多空共识</h4>
            <div v-for="(val, key) in debateViews" :key="key" style="font-size: 13px;">
              {{ key }}: {{ (val.view * 100).toFixed(1) }}% (置信 {{ (val.confidence * 100).toFixed(0) }}%)
            </div>
         </div>
      </div>

      <!-- Right: Matched Funds & Heatmap -->
      <div class="right-col card" v-show="matchedFunds.length > 0">
         <div class="card-title">一键配置结果 (Top-Down Match)</div>
         <table class="holdings-table">
          <thead>
            <tr>
              <th>标的名称</th>
              <th>配置大类</th>
              <th style="text-align:right;">靶向仓位</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="cf in matchedFunds" :key="cf.code">
              <td><strong>{{ cf.name }}</strong> <span class="fund-code">{{ cf.code }}</span></td>
              <td><span class="cat-tag">{{ cf.category }}</span></td>
              <td style="text-align:right;font-family:monospace;color:#10B981;font-weight:bold;">{{ (cf.weight * 100).toFixed(1) }}%</td>
            </tr>
          </tbody>
        </table>
        
        <div style="margin-top:24px; font-weight: 600; font-size:14px; border-top: 1px dashed #E2E8F0; padding-top: 16px;">
          反脆弱相关性热力矩阵
        </div>
        <div ref="heatmapRef" style="height: 250px; width: 100%;"></div>
      </div>
    </div>

    <!-- Campaign 12: Core Fund Pool Whitebox -->
    <CoreFundPoolWhitebox />

    <!-- Campaign 10: Advanced Metrics (EGARCH, PCA, Annual) -->
    <AdvancedMetrics v-if="matchedFunds.length > 0" :funds="matchedFunds" />

    <!-- Campaign 10: Stress Testing Dashboard -->
    <StressTestDashboard v-if="matchedFunds.length > 0" :funds="matchedFunds" />

    </div>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import * as echarts from 'echarts'
import { fetchEdbData, calculateAssetAllocation, matchFunds } from '../api'
import AsyncButton from '../components/common/AsyncButton.vue'
import ConfigSidebar from '../components/ConfigSidebar.vue'
import AdvancedMetrics from '../components/AdvancedMetrics.vue'
import StressTestDashboard from '../components/StressTestDashboard.vue'
import CoreFundPoolWhitebox from '../components/CoreFundPoolWhitebox.vue'
import { useConfigStore } from '../store/config'

const configStore = useConfigStore()

const edbData = ref(null)
const debateLogs = ref([])
const isDebating = ref(false)
const debateFinished = ref(false)
const debateViews = ref(null)
const debateStreamRef = ref(null)

const targetAllocation = ref(null)
const doughnutChartRef = ref(null)
const matchedFunds = ref([])
const heatmapRef = ref(null)
let doughnutInstance = null
let heatmapInstance = null

async function fetchEdb() {
  const res = await fetchEdbData();
  edbData.value = res.data.data;
}

async function runDebate() {
  debateLogs.value = [];
  isDebating.value = true;
  debateFinished.value = false;
  debateViews.value = null;
  targetAllocation.value = null;
  matchedFunds.value = [];

  try {
    const response = await fetch('http://localhost:8000/api/v1/simulate_smart_selection_debate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: '宏观大类资产配置' })
    });
    
    if (!response.body) throw new Error("ReadableStream not supported by the browser.");

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      
      buffer += decoder.decode(value, { stream: true });
      let lines = buffer.split("\n\n");
      buffer = lines.pop(); // keep the last partial chunk

      for (const line of lines) {
        if (line.startsWith("data: ")) {
          const dataStr = line.substring(6);
          try {
            const parsed = JSON.parse(dataStr);
            if (parsed.type === 'log') {
              debateLogs.value.push(parsed.content);
              // Auto-scroll
              nextTick(() => {
                const el = debateStreamRef.value;
                if (el) el.scrollTop = el.scrollHeight;
              });
            } else if (parsed.type === 'finish') {
              debateFinished.value = true;
              debateViews.value = parsed.bl_views;
            } else if (parsed.type === 'error') {
              throw new Error(parsed.content);
            }
          } catch(e) {
             console.error("SSE parse error", e);
          }
        }
      }
    }
  } catch(e) {
    alert("辩论发生异常: " + e.message);
  } finally {
    isDebating.value = false;
  }
}

async function extractAllocation() {
  const payload = { debate_views: debateViews.value || {} };
  const res = await calculateAssetAllocation(payload);
  targetAllocation.value = res.data.target_allocation;
  
  await nextTick();
  renderDoughnut();
}

async function runMatchFunds() {
  const payload = { 
    target_allocation: targetAllocation.value,
    total_amount: configStore.totalAmount,
    target_return: configStore.targetReturn,
    max_volatility: configStore.maxVolatility   
  };
  const res = await matchFunds(payload);
  matchedFunds.value = res.data.matched_funds;
  
  await nextTick();
  renderHeatmap(res.data.matched_funds.map(f => f.name), res.data.correlation_matrix);
}

function renderDoughnut() {
  if (!doughnutChartRef.value || !targetAllocation.value) return;
  if (!doughnutInstance) doughnutInstance = echarts.init(doughnutChartRef.value);
  
  const data = Object.keys(targetAllocation.value).map(k => ({
    name: k,
    value: targetAllocation.value[k]
  })).filter(x => x.value > 0);

  const option = {
    tooltip: { trigger: 'item', formatter: '{b}: {c}%' },
    legend: { bottom: '0%', textStyle: { fontSize: 11 } },
    series: [
      {
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
        label: { show: false, position: 'center' },
        emphasis: { label: { show: true, fontSize: 14, fontWeight: 'bold' } },
        labelLine: { show: false },
        data: data
      }
    ],
    color: ['#EF4444', '#3B82F6', '#10B981', '#F59E0B', '#6366F1', '#8B5CF6']
  };
  
  doughnutInstance.setOption(option, true);
}

function renderHeatmap(fundNames, corrMatrix) {
  if (!heatmapRef.value || !corrMatrix) return;
  if (!heatmapInstance) heatmapInstance = echarts.init(heatmapRef.value);
  
  let data = [];
  for (let i = 0; i < corrMatrix.length; i++) {
    for (let j = 0; j < corrMatrix[i].length; j++) {     
      data.push([j, i, corrMatrix[i][j]]);
    }
  }

  const option = {
    tooltip: { position: 'top' },
    grid: { left: '15%', right: '5%', bottom: '15%', top: '5%' },
    xAxis: { type: 'category', data: fundNames, axisLabel: { interval: 0, rotate: 30, fontSize: 10 } },
    yAxis: { type: 'category', data: fundNames, axisLabel: { interval: 0, fontSize: 10 } },
    visualMap: {
      min: 0, max: 1,
      calculable: true,
      orient: 'horizontal', left: 'center', bottom: -10,
      inRange: { color: ['#E0F2FE', '#3B82F6', '#1E3A8A'] }
    },
    series: [{
      type: 'heatmap',
      data: data,
      label: { show: true, fontSize: 9, color: '#fff' },
      emphasis: { itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0, 0, 0, 0.5)' } }
    }]
  };
  
  heatmapInstance.setOption(option, true);
}
</script>

<style scoped>
.smart-selection-layout {
  display: flex;
  height: calc(100vh - 64px);
  background: #F8FAFC;
  overflow: hidden;
}
.smart-selection-container {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}
.header-actions {
  display: flex;
  justify-content: space-between;
  border-bottom: 1px solid #E2E8F0;
  padding-bottom: 24px;
  margin-bottom: 24px;
}
.left-actions, .right-actions {
  display: flex;
  gap: 16px;
}
.content-grid {
  display: grid;
  grid-template-columns: 320px 1fr 400px;
  gap: 24px;
  align-items: start;
}
.card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
  padding: 20px;
  border: 1px solid #E2E8F0;
}
.card-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--navy);
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #E2E8F0;
}
.empty-text {
  color: var(--text-muted);
  font-size: 13px;
  font-style: italic;
  text-align: center;
  padding: 20px 0;
}
.metric-block {
  display: flex;
  justify-content: space-between;
  margin-bottom: 12px;
  font-size: 14px;
}
.highlight-text {
  font-weight: bold;
  color: #EF4444;
}
.sub-metrics {
  background: #F8FAFC;
  padding: 12px;
  border-radius: 6px;
  font-size: 12px;
  color: var(--text-secondary);
  display: flex;
  justify-content: space-between;
}
.debate-stream {
  height: 500px;
  overflow-y: auto;
  padding-right: 8px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  color: #334155;
  background: #F8FAFC;
  border-radius: 8px;
  padding: 16px;
}
.log-item {
  margin-bottom: 12px;
}
.log-bubble {
  display: inline-block;
  background: white;
  border: 1px solid #E2E8F0;
  padding: 8px 12px;
  border-radius: 6px;
  box-shadow: 0 1px 2px rgba(0,0,0,0.02);
  line-height: 1.5;
}
.debate-conclusion {
  margin-top: 16px;
  padding: 16px;
  background: #FEF3C7;
  border-left: 4px solid #F59E0B;
  border-radius: 4px;
}
.holdings-table th {
  background: #F8FAFC; font-weight: 600; font-size: 13px; padding: 10px; border-bottom: 1px solid #E2E8F0;
}
.holdings-table td {
  font-size: 13px; padding: 10px; border-bottom: 1px solid #F1F5F9;
}
.fund-code { color: #94A3B8; font-family: monospace; font-size: 11px; margin-left: 4px; }
.cat-tag {
  background: #E0E7FF; color: #4338CA; border-radius: 12px; padding: 2px 8px; font-size: 11px; font-weight: 500;
}
.typing-indicator span {
  animation: blink 1.4s infinite both;
}
.typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
.typing-indicator span:nth-child(3) { animation-delay: 0.4s; }
@keyframes blink { 0% { opacity: 0.2; } 20% { opacity: 1; } 100% { opacity: 0.2; } }
</style>
