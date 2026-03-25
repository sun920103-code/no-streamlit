<template>
  <div class="fade-in">
    <div class="section-title" style="margin-top: 40px; border-top: 1px solid #E2E8F0; padding-top: 24px;">📊 最终诊断与回测概览</div>
    
    <div class="card" style="margin-bottom:24px;">
      <div style="display:flex; gap: 16px; margin-bottom: 24px;">
         <AsyncButton
            :action="runBacktest"
            type="primary"
            text="📈 执行回测对比计算"
         />
         <AsyncButton
            :action="exportPdf"
            style="background:#10B981;border-color:#10B981;"
            text="📥 导出全套诊断分析报告 (PDF)"
         />
         <!-- Campaign 13: 被遗忘的 DOCX 双轨导出 -->
         <AsyncButton
            :action="exportDocx"
            style="background:#3B82F6;border-color:#3B82F6;"
            text="📝 提取动态 Word (DOCX) 底稿"
         />
      </div>

      <!-- KPI Table -->
      <div v-if="kpiList && kpiList.length > 0" style="overflow-x:auto; margin-bottom: 24px;">
        <table class="holdings-table">
          <thead>
            <tr>
              <th style="width: 180px;">对比策略</th>
              <th style="text-align:right;">年化收益</th>
              <th style="text-align:right;">年化波动</th>
              <th style="text-align:right;">夏普比率</th>
              <th style="text-align:right;">最大回撤</th>
              <th style="text-align:right;">卡玛比率</th>
              <th style="text-align:right;">胜率</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, i) in kpiList" :key="i" :style="{ backgroundColor: getRowBg(row.strategy_label) }">
              <td style="font-weight:600;color:var(--navy);">{{ row.strategy_label }}</td>
              <td style="text-align:right;font-family:'JetBrains Mono',monospace;" :style="{ color: getAmountColor(row.ann_return) }">{{ (row.ann_return * 100).toFixed(2) }}%</td>
              <td style="text-align:right;font-family:'JetBrains Mono',monospace;">{{ (row.ann_volatility * 100).toFixed(2) }}%</td>
              <td style="text-align:right;font-family:'JetBrains Mono',monospace;">{{ row.sharpe_ratio.toFixed(2) }}</td>
              <td style="text-align:right;font-family:'JetBrains Mono',monospace;color:#10B981;">{{ (row.max_drawdown * 100).toFixed(2) }}%</td>
              <td style="text-align:right;font-family:'JetBrains Mono',monospace;">{{ row.calmar_ratio.toFixed(2) }}</td>
              <td style="text-align:right;font-family:'JetBrains Mono',monospace;">{{ (row.win_rate * 100).toFixed(1) }}%</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- ECharts Cumulative Returns -->
      <div v-show="timeseries && timeseries.dates" style="width: 100%; height: 400px;" ref="chartContainer"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import * as echarts from 'echarts'
import { calculateKpis, exportDiagnosePdf, exportDiagnoseDocx } from '../api'
import AsyncButton from './common/AsyncButton.vue'

const props = defineProps({
  strategiesPayload: { type: Function, required: true },
  pdfStatePayload: { type: Function, required: true }
})

const kpiList = ref([])
const timeseries = ref(null)
const chartContainer = ref(null)
let chartInstance = null

function getRowBg(label) {
  if (label.includes('客户持仓')) return 'rgba(239, 68, 68, 0.05)'
  if (label.includes('基准')) return 'rgba(107, 114, 128, 0.05)'
  return 'transparent'
}

function getAmountColor(val) {
  if (val > 0) return '#EF4444';
  if (val < 0) return '#10B981';
  return 'var(--text-primary)';
}

async function runBacktest() {
  const req = props.strategiesPayload();
  if (req.strategies.length === 0) throw new Error("尚未生成任何算子策略，请先回到上方生成策略");
  
  const res = await calculateKpis(req);
  kpiList.value = res.data.kpi_list;
  timeseries.value = res.data.timeseries;
  
  await nextTick();
  renderChart();
}

async function exportPdf() {
  const req = props.pdfStatePayload();
  const res = await exportDiagnosePdf(req);
  // Download blob
  const url = window.URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', '智能分析诊断战报.pdf');
  document.body.appendChild(link);
  link.click();
  link.remove();
}

async function exportDocx() {
  const req = props.pdfStatePayload(); // state payload is shared intentionally
  const res = await exportDiagnoseDocx(req);
  const url = window.URL.createObjectURL(new Blob([res.data], { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' }));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', '智能诊断底稿.docx');
  document.body.appendChild(link);
  link.click();
  link.remove();
}

function renderChart() {
  if (!chartContainer.value || !timeseries.value) return;
  if (!chartInstance) chartInstance = echarts.init(chartContainer.value);
  
  const ts = timeseries.value;
  const seriesData = Object.keys(ts.series).map(name => ({
    name,
    type: 'line',
    showSymbol: false,
    smooth: true,
    data: ts.series[name].map(v => Number.isNaN(v) ? 0 : v * 100) // 健壮性容错处理 (NaN)
  }));

  const option = {
    tooltip: { trigger: 'axis', valueFormatter: (val) => val.toFixed(2) + '%' },
    legend: { top: 0, type: 'scroll' },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', boundaryGap: false, data: ts.dates },
    yAxis: { type: 'value', axisLabel: { formatter: '{value}%' } },
    series: seriesData,
    color: ['#EF4444', '#3B82F6', '#10B981', '#F59E0B', '#6366F1', '#6B7280']
  };
  
  chartInstance.setOption(option, true);
}
</script>

<style scoped>
.holdings-table th {
  background: #F8FAFC;
  color: var(--navy);
  font-weight: 600;
  padding: 12px;
  border-bottom: 2px solid #E2E8F0;
  white-space: nowrap;
}
.holdings-table td {
  padding: 12px;
  border-bottom: 1px solid #E2E8F0;
}
</style>
