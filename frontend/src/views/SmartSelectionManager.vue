<template>
  <div class="smart-selection-layout">
    <ConfigSidebar />
    <div class="smart-selection-container">

    <!-- ═══ Step 1: 一键启动 (EDB + 象限配置) ═══ -->
    <div class="header-actions">
       <div class="left-actions">
         <AsyncButton :action="runFullPipeline" type="primary" text="🚀 一键配置 (EDB + 宏观象限底仓)" />
       </div>
       <div class="right-actions" v-if="targetAllocation">
         <AsyncButton :action="runMatchFunds" style="background:#10B981;border-color:#10B981;" text="⚡ 一键智能选基配置" />
       </div>
    </div>

    <!-- ═══ 主面板: EDB + 象限底仓 + 选基结果 ═══ -->
    <div class="content-grid">
      <!-- Left: EDB 宏观 + 象限定位 + 配置占比 -->
      <div class="left-col">
        <div class="card edb-card">
          <div class="card-title">📡 宏观特征引擎 (EDB)</div>
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

        <!-- 🧭 宏观象限定位 (底仓来源) -->
        <div class="card" v-if="quadrantData" style="margin-top:16px;">
          <div class="card-title">🧭 宏观象限定位</div>
          <div style="display:flex;align-items:center;gap:10px;margin-bottom:12px;">
            <div :style="{width:'40px',height:'40px',borderRadius:'10px',display:'flex',alignItems:'center',justifyContent:'center',fontSize:'20px',background: qColors[quadrantData.current_quadrant]?.bg || '#EDF2F7'}">
              {{ qColors[quadrantData.current_quadrant]?.icon || '🧭' }}
            </div>
            <div>
              <div style="font-weight:700;font-size:15px;">{{ quadrantData.quadrant_label }}</div>
              <div style="color:var(--text-secondary);font-size:12px;">{{ quadrantData.quadrant_description }}</div>
            </div>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;font-size:12px;">
            <div style="padding:6px 8px;background:#F0FDF4;border-radius:6px;border-left:2px solid #10B981;">
              <div style="color:var(--text-muted);font-size:10px;">利好</div>
              <div style="color:#10B981;font-weight:600;">{{ (quadrantData.best_assets || []).join(', ') }}</div>
            </div>
            <div style="padding:6px 8px;background:#FEF2F2;border-radius:6px;border-left:2px solid #EF4444;">
              <div style="color:var(--text-muted);font-size:10px;">承压</div>
              <div style="color:#EF4444;font-weight:600;">{{ (quadrantData.worst_assets || []).join(', ') }}</div>
            </div>
          </div>
          <div style="font-size:11px;color:var(--text-muted);margin-top:8px;">
            Markov: <b>{{ quadrantData.markov_regime }}</b> ({{ ((quadrantData.markov_confidence||0)*100).toFixed(0) }}%)
          </div>
        </div>

        <!-- 底仓配置环形图 -->
        <div class="card alloc-card" v-show="targetAllocation" style="margin-top:16px;">
          <div class="card-title">🧭 宏观象限对应配置 (底仓)</div>
          <div ref="doughnutChartRef" style="height: 300px; width:100%;"></div>
        </div>
      </div>

      <!-- Center: 虚拟投研辩论实况 -->
      <div class="center-col card">
         <div class="card-title">🧠 虚拟投研辩论实况 (SSE)</div>
         <div style="margin-bottom:12px;">
           <AsyncButton :action="runDebate" style="background:#8B5CF6;border-color:#8B5CF6;width:100%;" text="🧠 运行虚拟投研分析会" />
         </div>
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

      <!-- Right: 选基结果 & 热力矩阵 -->
      <div class="right-col card" v-show="matchedFunds.length > 0">
         <div class="card-title">⚡ 选基配置结果 (Top-Down Match)</div>
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

    <!-- ═══ MBL 因子传导链 (底仓生成依据透明展示) ═══ -->
    <div v-if="mblResult" class="card" style="margin-top:24px;">
      <div class="card-title">🎯 因子传导链条 (底仓生成依据)</div>
      <div style="display:flex;gap:10px;margin-bottom:16px;flex-wrap:wrap;">
        <div v-for="item in mblResult.transmission_chain" :key="item.factor"
             style="padding:10px 14px;border-radius:8px;text-align:center;min-width:90px;"
             :style="{background: item.score>0?'#F0FDF4':'#FEF2F2',border:'1px solid '+(item.score>0?'#10B981':'#EF4444')}">
          <div style="font-weight:600;font-size:12px;">{{ item.factor }}</div>
          <div style="font-size:16px;font-weight:700;" :style="{color:item.score>0?'#10B981':'#EF4444'}">{{ item.score>0?'+':'' }}{{ item.score }}</div>
          <div style="font-size:10px;color:var(--text-muted);">×{{ item.regime_modifier }}</div>
        </div>
      </div>
      <div v-if="mblResult.defense_log && mblResult.defense_log.length"
           style="padding:10px 14px;border-radius:6px;background:#FFFBEB;border:1px solid #FDE68A;font-size:12px;">
        <div v-for="(log, idx) in mblResult.defense_log" :key="idx" style="margin-bottom:2px;color:var(--text-secondary);">{{ log }}</div>
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
import { fetchEdbData, calculateAssetAllocation, matchFunds, getMacroQuadrant, optimizeFactorRp } from '../api'
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
const quadrantData = ref(null)
const mblResult = ref(null)
const doughnutChartRef = ref(null)
const matchedFunds = ref([])
const heatmapRef = ref(null)
let doughnutInstance = null
let heatmapInstance = null

const qColors = {
  recovery: { bg: '#ECFDF5', icon: '🌱' },
  overheat: { bg: '#FEF3C7', icon: '🔥' },
  stagflation: { bg: '#FEE2E2', icon: '⚠️' },
  deflation: { bg: '#DBEAFE', icon: '❄️' },
}

// ═══════════════════════════════════════════
// 🚀 一键配置: EDB → 宏观象限 → 底仓
// ═══════════════════════════════════════════
async function runFullPipeline() {
  // Step 1: EDB 数据下载
  const edbRes = await fetchEdbData();
  edbData.value = edbRes.data.data;

  // Step 2: 宏观象限定位
  const defaultFactorScores = {
    "经济增长": 0.3, "通胀商品": -0.2, "利率环境": 0.4,
    "信用扩张": 0.1, "海外环境": 0.0, "市场情绪": 0.2,
  }
  const qRes = await getMacroQuadrant({ factor_scores: defaultFactorScores })
  quadrantData.value = qRes.data

  // Step 3: 因子风险平价 → 底仓配置
  const rpRes = await optimizeFactorRp({
    factor_scores: defaultFactorScores,
    apply_regime: true,
    max_volatility: configStore.maxVolatility || 0.15,
  })
  mblResult.value = rpRes.data
  
  // 将因子风险平价的目标权重转化为 targetAllocation 格式
  if (rpRes.data && rpRes.data.target_weights) {
    targetAllocation.value = {}
    for (const [asset, w] of Object.entries(rpRes.data.target_weights)) {
      targetAllocation.value[asset] = +(w * 100).toFixed(1)
    }
  }

  await nextTick()
  renderDoughnut()
}

// ═══ AI 虚拟投研辩论 (SSE 流式) ═══
async function runDebate() {
  debateLogs.value = [];
  isDebating.value = true;
  debateFinished.value = false;
  debateViews.value = null;

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
      buffer = lines.pop();

      for (const line of lines) {
        if (line.startsWith("data: ")) {
          const dataStr = line.substring(6);
          try {
            const parsed = JSON.parse(dataStr);
            if (parsed.type === 'log') {
              debateLogs.value.push(parsed.content);
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

// ═══ 一键智能选基 ═══
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

// ═══ ECharts ═══
function renderDoughnut() {
  if (!doughnutChartRef.value || !targetAllocation.value) return;
  if (!doughnutInstance) doughnutInstance = echarts.init(doughnutChartRef.value);
  
  const data = Object.keys(targetAllocation.value).map(k => ({
    name: k,
    value: targetAllocation.value[k]
  })).filter(x => x.value > 0);

  doughnutInstance.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c}%' },
    legend: { bottom: '0%', textStyle: { fontSize: 11 } },
    series: [{
      type: 'pie', radius: ['40%', '70%'], center: ['50%', '50%'],
      itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
      label: { show: false, position: 'center' },
      emphasis: { label: { show: true, fontSize: 14, fontWeight: 'bold' } },
      labelLine: { show: false },
      data: data
    }],
    color: ['#EF4444', '#3B82F6', '#10B981', '#F59E0B', '#6366F1', '#8B5CF6', '#EC4899', '#14B8A6']
  }, true);
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

  heatmapInstance.setOption({
    tooltip: { position: 'top' },
    grid: { left: '15%', right: '5%', bottom: '15%', top: '5%' },
    xAxis: { type: 'category', data: fundNames, axisLabel: { interval: 0, rotate: 30, fontSize: 10 } },
    yAxis: { type: 'category', data: fundNames, axisLabel: { interval: 0, fontSize: 10 } },
    visualMap: {
      min: 0, max: 1, calculable: true, orient: 'horizontal', left: 'center', bottom: -10,
      inRange: { color: ['#E0F2FE', '#3B82F6', '#1E3A8A'] }
    },
    series: [{
      type: 'heatmap', data: data,
      label: { show: true, fontSize: 9, color: '#fff' },
      emphasis: { itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0, 0, 0, 0.5)' } }
    }]
  }, true);
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
  height: 400px;
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
