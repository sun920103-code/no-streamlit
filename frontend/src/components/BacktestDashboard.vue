<template>
  <div class="fade-in relative font-body text-slate-900 antialiased">

    <!-- Action Bar Container -->
    <div class="w-full mb-6">
      <div class="bg-white rounded-xl shadow-sm border border-[#c4c6cd]/20 overflow-hidden">
        <div class="flex flex-row items-center gap-6 p-4 md:px-8 md:py-4 justify-center">
          <div class="shrink-0">
            <button
              :disabled="btnLoading"
              @click="handleBacktestClick"
              class="px-8 h-10 bg-[#001529] rounded-lg shadow-md transition-all active:scale-[0.98] hover:shadow-lg hover:brightness-110 flex items-center justify-center disabled:opacity-60 disabled:cursor-not-allowed"
            >
              <span v-if="btnLoading" class="inline-block w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin mr-2"></span>
              <span class="text-white text-sm font-bold tracking-widest">一键历史业绩回测</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Results Container -->
    <div class="bg-white rounded-xl shadow-sm border border-[#c4c6cd]/20 overflow-hidden p-6 mb-6" v-if="kpiList && kpiList.length > 0 || (timeseries && timeseries.dates)">
      
      <!-- KPI Table with new HTML UI -->
      <div v-if="kpiList && kpiList.length > 0" class="bg-[#ffffff] rounded-xl shadow-sm overflow-hidden border border-[#c4c6cf]/10 mb-8 flex flex-col">
        <div class="px-6 py-4 bg-[#dfe3e7] flex justify-between items-center">
          <h3 class="text-sm font-bold text-[#001d53] uppercase tracking-widest">策略绩效对比矩阵</h3>
          <div class="flex items-center gap-2">
            <span class="text-[10px] font-bold text-slate-500 uppercase">Auto-refresh in 12s</span>
            <div class="w-2 h-2 rounded-full bg-[#00b47d] animate-pulse"></div>
          </div>
        </div>
        <div class="overflow-auto">
          <table class="w-full text-left border-collapse min-w-[1000px]">
            <thead class="sticky top-0 z-10">
              <tr class="bg-[#f0f4f8]/90 backdrop-blur-sm border-b border-[#c4c6cf]/20">
                <th class="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-wider">对比策略</th>
                <th class="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-wider text-right">年化收益</th>
                <th class="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-wider text-right">年化波动</th>
                <th class="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-wider text-right">夏普比率</th>
                <th class="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-wider text-right">最大回撤</th>
                <th class="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-wider text-right">卡玛比率</th>
                <th class="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-wider text-right">胜率</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-[#c4c6cf]/10 font-body">
              <tr v-for="(row, i) in kpiList" :key="i"
                class="transition-colors group"
                :class="[
                  row.strategy_label.includes('客户持仓') 
                    ? 'bg-[#ffdad6]/10 hover:bg-[#ffdad6]/20' 
                    : (i % 2 === 1 ? 'bg-[#f0f4f8]/20 hover:bg-[#e4e9ed]/30' : 'hover:bg-[#e4e9ed]/30')
                ]"
              >
                <td class="px-6 py-4" 
                  :class="[row.strategy_label.includes('客户持仓') ? 'font-bold text-[#001d53]' : (row.strategy_label.includes('调仓') || row.strategy_label.includes('配置') ? 'font-semibold text-[#001d53]' : '')]"
                >
                  <span class="flex items-center gap-2">
                    <span class="material-symbols-outlined text-[#001d53] text-[18px]">
                      {{
                        row.strategy_label.includes('基准') ? 'show_chart' :
                        row.strategy_label.includes('客户持仓') ? 'account_balance_wallet' :
                        row.strategy_label.includes('宏观') ? 'public' :
                        row.strategy_label.includes('资讯') || row.strategy_label.includes('新闻') ? 'analytics' :
                        row.strategy_label.includes('研报') ? 'description' : 'show_chart'
                      }}
                    </span>
                    {{ row.strategy_label }}
                  </span>
                </td>
                <td class="px-6 py-4 text-right font-medium" :class="getReturnTextClass(row.ann_return)">
                  {{ (row.ann_return * 100).toFixed(2) }}%
                </td>
                <td class="px-6 py-4 text-right">{{ (row.ann_volatility * 100).toFixed(2) }}%</td>
                <td class="px-6 py-4 text-right">{{ row.sharpe_ratio.toFixed(2) }}</td>
                <td class="px-6 py-4 text-right text-[#00b47d]">{{ (row.max_drawdown * 100).toFixed(2) }}%</td>
                <td class="px-6 py-4 text-right">{{ row.calmar_ratio.toFixed(2) }}</td>
                <td class="px-6 py-4 text-right">{{ (row.win_rate * 100).toFixed(1) }}%</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- ECharts Backtest Bar Chart -->
      <div v-show="timeseries && timeseries.dates" style="width: 100%; height: 450px;" ref="chartContainer"></div>
    </div>

    <!-- ── 全屏加载态 (Wind 终端直连) ── -->
    <div v-if="isLoading" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-sm transition-all duration-300">
      <div class="bg-white rounded-3xl p-10 max-w-sm w-full shadow-2xl relative overflow-hidden flex flex-col items-center">
        <!-- 炫彩背景光弧 -->
        <div class="absolute top-0 left-0 w-full h-2 bg-gradient-to-r from-blue-500 via-indigo-500 to-emerald-500 wind-progress-bar"></div>
        <div class="absolute -top-24 -left-24 w-48 h-48 bg-blue-500/10 rounded-full blur-3xl"></div>
        <div class="absolute -bottom-24 -right-24 w-48 h-48 bg-emerald-500/10 rounded-full blur-3xl"></div>
        
        <!-- 中央雷达/终端扫描动画 -->
        <div class="relative w-24 h-24 mb-8 flex items-center justify-center">
          <div class="absolute inset-0 border-4 border-slate-100 rounded-full"></div>
          <div class="absolute inset-0 border-4 border-blue-500 rounded-full border-t-transparent animate-spin"></div>
          <div class="absolute inset-2 border-4 border-emerald-400 rounded-full border-b-transparent wind-sync-spin blur-[2px]" style="animation-direction: reverse; animation-duration: 1.5s;"></div>
          <span class="material-symbols-outlined text-4xl text-[#001529] z-10">satellite_alt</span>
        </div>

        <h3 class="text-xl font-bold text-[#001529] mb-3 tracking-wide">直连 Wind 金融终端</h3>
        <p class="text-slate-500 text-sm font-medium text-center leading-relaxed">
          正在触发同步过去 5 年的历史行情数据<br/>
          <span class="text-blue-600 font-semibold animate-pulse block mt-2">请稍候，系统正在通过子进程调取数据...</span>
        </p>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import * as echarts from 'echarts'
import { calculateKpis } from '../api'

const props = defineProps({
  strategiesPayload: { type: Function, required: true },
  pdfStatePayload: { type: Function, required: true }
})

const kpiList = ref([])
const timeseries = ref(null)
const chartContainer = ref(null)
const isLoading = ref(false)
const btnLoading = ref(false)
let chartInstance = null

// 暴露 refreshChart 供父组件在 v-show 切换后调用
function refreshChart() {
  if (chartInstance) {
    nextTick(() => chartInstance.resize())
  }
}
defineExpose({ refreshChart })

function getRowBg(label) {
  if (label.includes('客户持仓')) return 'rgba(239, 68, 68, 0.05)'
  if (label.includes('基准')) return 'rgba(107, 114, 128, 0.05)'
  return 'transparent'
}

function getAmountColor(val) {
  if (val > 0) return '#EF4444';
  if (val < 0) return '#10B981';
  return '#43474d';
}

function getReturnTextClass(val) {
  if (val > 0) return 'text-[#ba1a1a]';
  if (val < 0) return 'text-[#00b47d]';
  return 'text-[#43474d]';
}

function stripEmoji(str) {
  if (!str) return str;
  return str.replace(/^[^a-zA-Z\u4e00-\u9fa5\d]+/, '').trim();
}

async function handleBacktestClick() {
  if (btnLoading.value) return;
  
  const req = props.strategiesPayload();
  if (!req || !req.strategies || req.strategies.length === 0) {
    alert('尚未生成任何算子策略，请先回到上方生成策略');
    return;
  }
  
  btnLoading.value = true;
  isLoading.value = true;
  
  try {
    const res = await calculateKpis(req);
    
    // Sanitize emojis from labels
    const sanitizedKpis = res.data.kpi_list.map(k => ({
       ...k,
       strategy_label: stripEmoji(k.strategy_label)
    }));
    
    // Also sanitize timeseries keys
    const newSeries = {};
    if (res.data.timeseries && res.data.timeseries.series) {
      for (const [key, val] of Object.entries(res.data.timeseries.series)) {
        newSeries[stripEmoji(key)] = val;
      }
      res.data.timeseries.series = newSeries;
    }

    kpiList.value = sanitizedKpis;
    timeseries.value = res.data.timeseries;
    
    await nextTick();
    renderChart();
  } catch (error) {
    console.error('Backtest error:', error);
    let errorMsg = error.response?.data?.detail || error.response?.data?.message || error.message || '未知错误';
    if (typeof errorMsg === 'object') errorMsg = JSON.stringify(errorMsg, null, 2);
    alert(`请求失败:\n${errorMsg}`);
  } finally {
    isLoading.value = false;
    btnLoading.value = false;
  }
}

function renderChart() {
  if (!chartContainer.value || !timeseries.value) return;
  if (!chartInstance) chartInstance = echarts.init(chartContainer.value);
  
  const ts = timeseries.value;
  const seriesData = Object.keys(ts.series).map(name => {
    let itemColor = undefined;
    if (name.includes('基准')) itemColor = '#94A3B8';
    if (name.includes('基准 [沪深300]')) itemColor = '#475569';
    if (name.includes('客户持仓')) itemColor = '#3B82F6';
    if (name.includes('宏观')) itemColor = '#EF4444';
    if (name.includes('资讯')) itemColor = '#8B5CF6';
    if (name.includes('研报')) itemColor = '#F59E0B';
    
    return {
      name,
      type: 'bar',
      barGap: '10%',
      barCategoryGap: '20%',
      itemStyle: { 
        borderRadius: [4, 4, 0, 0],
        color: itemColor
      },
      label: { 
        show: true, 
        position: 'top', 
        formatter: (params) => {
          const val = params.value;
          if (Math.abs(val) < 0.01) return '';
          return (val > 0 ? '+' : '') + val.toFixed(2) + '%'
        },
        color: (params) => {
          return params.value > 0 ? '#EF4444' : (params.value < 0 ? '#10B981' : '#64748B');
        },
        fontSize: 11,
        fontWeight: 'bold',
        fontFamily: "'JetBrains Mono', monospace"
      },
      data: ts.series[name].map(v => Number.isNaN(v) ? 0 : v * 100)
    };
  });

  const option = {
    title: {
      text: '历年配置策略年化回报表现',
      textStyle: { fontSize: 14, color: '#475569', fontWeight: 600 }
    },
    tooltip: { 
      trigger: 'axis', 
      axisPointer: { type: 'shadow' },
      valueFormatter: (val) => val.toFixed(2) + '%' 
    },
    legend: { top: 30, type: 'scroll' },
    grid: { left: '3%', right: '4%', bottom: '3%', top: 80, containLabel: true },
    xAxis: { 
      type: 'category', 
      data: ts.dates,
      axisLabel: { fontWeight: 'bold' }
    },
    yAxis: { 
      type: 'value', 
      axisLabel: { formatter: '{value}%' },
      splitLine: { lineStyle: { type: 'dashed', color: '#E2E8F0' } }
    },
    series: seriesData,
    color: ['#6B7280', '#EF4444', '#3B82F6', '#F59E0B', '#10B981']
  };
  
  chartInstance.setOption(option, true);
}
</script>

<style scoped>
.holdings-table th {
  background: #F8FAFC;
  color: #001529;
  font-weight: 600;
  padding: 12px;
  border-bottom: 2px solid #E2E8F0;
  white-space: nowrap;
}
.holdings-table td {
  padding: 12px;
  border-bottom: 1px solid #E2E8F0;
}
.wind-progress-bar {
  animation: wind-progress 2s ease-in-out infinite;
}
.wind-sync-spin {
  animation: wind-spin 2s linear infinite;
}
@keyframes wind-progress {
  0% { transform: translateX(-100%); }
  50% { transform: translateX(100%); }
  100% { transform: translateX(-100%); }
}
@keyframes wind-spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
