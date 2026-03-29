<template>
  <div class="zx-backtest-page">
    <!-- 页面标题 -->
    <div class="zx-page-header">
      <div class="zx-header-left">
        <span class="zx-accent-bar"></span>
        <div>
          <h1 class="zx-page-title">业绩回测</h1>
          <p class="zx-page-sub">Backtest · 配置方案 vs 7大宽基指数 5年绝对回报对比</p>
        </div>
      </div>
      <button class="zx-action-btn" :disabled="loading || !hasAllocation" @click="runBacktest">
        <span v-if="loading" class="zx-spinner"></span>
        <span v-else>📊</span>
        {{ loading ? '正在回测...' : '一键回测' }}
      </button>
    </div>

    <!-- 前置依赖检查 -->
    <div v-if="!hasAllocation" class="zx-notice">
      ⚠️ 请先完成「宏观配置底仓」获取配置方案后再进行业绩回测。
      <button class="zx-notice-btn" @click="$router.push('/smart/macro')">前往配置底仓 →</button>
    </div>

    <!-- ═══ 回测柱状图 (ECharts) ═══ -->
    <div v-if="result && !loading" class="zx-card fade-in" style="margin-bottom:24px;">
      <div class="zx-card-title">📊 过去5年年度绝对收益率对比 · 红涨绿跌</div>
      <div ref="chartRef" class="zx-chart-area"></div>
    </div>

    <!-- ═══ 数据表格 ═══ -->
    <div v-if="result" class="zx-card fade-in">
      <div class="zx-card-title">📋 年度收益率明细 (%)</div>
      <div class="zx-data-table-wrap">
        <table class="zx-data-table">
          <thead>
            <tr>
              <th>指数/方案</th>
              <th v-for="year in result.years" :key="year" style="text-align:right;">{{ year }}</th>
            </tr>
          </thead>
          <tbody>
            <!-- 配置方案 -->
            <tr class="zx-row-portfolio">
              <td>⭐ {{ result.portfolio_label }}</td>
              <td v-for="year in result.years" :key="year" style="text-align:right;">
                <span :class="(result.portfolio_returns[year] || 0) >= 0 ? 'zx-up' : 'zx-down'">
                  {{ result.portfolio_returns[year] || 'N/A' }}%
                </span>
              </td>
            </tr>
            <!-- 各个宽基指数 -->
            <tr v-for="(rets, bmName) in result.benchmark_returns" :key="bmName">
              <td>{{ bmName }}</td>
              <td v-for="year in result.years" :key="year" style="text-align:right;">
                <span :class="(rets[year] || 0) >= 0 ? 'zx-up' : 'zx-down'">
                  {{ rets[year] || 'N/A' }}%
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-if="!result && hasAllocation && !loading" class="zx-empty-state">
      <div class="zx-empty-icon">📊</div>
      <h2>等待业绩回测</h2>
      <p>点击上方按钮，系统将生成配置方案与 7 大宽基指数过去 5 年的绝对收益率对比图。</p>
    </div>

    <!-- Error -->
    <div v-if="error" class="zx-error fade-in">❌ {{ error }}</div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onUnmounted } from 'vue'
import { useSmartStore } from '../../store/smartSelection'
import { zxBacktest } from '../../api/smart'

const store = useSmartStore()
const loading = ref(false)
const error = ref(null)
const chartRef = ref(null)
let chartInstance = null

const hasAllocation = computed(() => {
  return store.zx_macroResult !== null && store.zx_macroResult.scenarios?.length > 0
})

const result = computed(() => store.zx_backtestResult)

async function runBacktest() {
  loading.value = true
  error.value = null
  try {
    const weights = store.zx_steadyWeights
    const res = await zxBacktest({
      allocation_weights: weights,
      benchmarks: ['上证指数', '沪深300', '深证成指', '中证500', '中证1000', '创业板指', '恒生指数'],
    })
    store.setBacktestResult(res.data)
    await nextTick()
    renderChart()
  } catch (e) {
    error.value = e.response?.data?.detail || e.message || '回测失败'
  } finally {
    loading.value = false
  }
}

function renderChart() {
  if (!chartRef.value || !result.value) return

  // 动态导入 ECharts (避免首屏加载)
  import('echarts').then((echarts) => {
    if (chartInstance) chartInstance.dispose()
    chartInstance = echarts.init(chartRef.value, null, { renderer: 'canvas' })

    const data = result.value
    const years = data.years
    const allSeries = []

    // 组合方案
    allSeries.push({
      name: data.portfolio_label,
      type: 'bar',
      data: years.map(y => data.portfolio_returns[y] || 0),
      itemStyle: {
        color: function(params) {
          // 红涨绿跌
          return params.data >= 0 ? '#DC2626' : '#16A34A'
        },
        borderRadius: [4, 4, 0, 0],
      },
      label: {
        show: true,
        position: 'top',
        formatter: '{c}%',
        fontSize: 11,
        fontWeight: 600,
        color: '#191c1d',
      },
      barMaxWidth: 28,
    })

    // 宽基指数
    const bmColors = ['#6366F1', '#0EA5E9', '#F59E0B', '#EC4899', '#8B5CF6', '#14B8A6', '#EF4444']
    let colorIdx = 0
    for (const [bmName, rets] of Object.entries(data.benchmark_returns)) {
      allSeries.push({
        name: bmName,
        type: 'bar',
        data: years.map(y => rets[y] || 0),
        itemStyle: {
          color: function(params) {
            // 红涨绿跌
            return params.data >= 0 ? '#DC2626' : '#16A34A'
          },
          borderRadius: [4, 4, 0, 0],
          opacity: 0.7,
        },
        label: {
          show: true,
          position: 'top',
          formatter: '{c}%',
          fontSize: 9,
          color: '#74777d',
        },
        barMaxWidth: 20,
      })
      colorIdx++
    }

    const option = {
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        backgroundColor: '#fff',
        borderColor: '#e1e3e4',
        textStyle: { fontSize: 12 },
        formatter: function(params) {
          let html = `<strong>${params[0].axisValue}</strong><br/>`
          params.forEach(p => {
            const color = p.value >= 0 ? '#DC2626' : '#16A34A'
            html += `<span style="color:${color};">● ${p.seriesName}：${p.value >= 0 ? '+' : ''}${p.value}%</span><br/>`
          })
          return html
        },
      },
      legend: {
        data: allSeries.map(s => s.name),
        bottom: 0,
        textStyle: { fontSize: 11 },
      },
      grid: {
        left: 50, right: 30, top: 30, bottom: 60,
      },
      xAxis: {
        type: 'category',
        data: years,
        axisLabel: { fontWeight: 600, fontSize: 13 },
        axisLine: { lineStyle: { color: '#c4c6cd' } },
      },
      yAxis: {
        type: 'value',
        axisLabel: {
          formatter: '{value}%',
          color: '#74777d',
          fontSize: 11,
        },
        splitLine: { lineStyle: { type: 'dashed', color: '#f3f4f5' } },
      },
      series: allSeries,
    }

    chartInstance.setOption(option)

    // 响应式
    const resizeObserver = new ResizeObserver(() => chartInstance?.resize())
    resizeObserver.observe(chartRef.value)
  }).catch(e => {
    console.error('ECharts 加载失败:', e)
    error.value = 'ECharts 图表库加载失败'
  })
}

// 当 result 变化时重新渲染
watch(result, () => {
  nextTick(() => renderChart())
})

onUnmounted(() => {
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
})
</script>

<style scoped>
.zx-backtest-page { max-width: 1400px; }

/* ─── Header ─── */
.zx-page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 28px;
  padding-bottom: 20px;
  border-bottom: 1px solid rgba(196,198,205,0.15);
}
.zx-header-left { display: flex; align-items: center; gap: 14px; }
.zx-accent-bar { width: 4px; height: 36px; background: #001529; border-radius: 9999px; }
.zx-page-title { font-size: 24px; font-weight: 800; color: #001529; margin: 0; }
.zx-page-sub { font-size: 12px; color: #74777d; margin: 2px 0 0; }

.zx-action-btn {
  padding: 12px 28px;
  background: #001529;
  color: #ffffff;
  border: none;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  box-shadow: 0 4px 14px rgba(0,21,41,0.2);
  transition: all 0.15s;
}
.zx-action-btn:hover:not(:disabled) { opacity: 0.9; }
.zx-action-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.zx-spinner {
  width: 16px; height: 16px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* Notice */
.zx-notice {
  background: #FFF7ED;
  border: 1px solid #FDBA74;
  border-radius: 10px;
  padding: 20px 24px;
  color: #92400E;
  font-size: 14px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.zx-notice-btn {
  padding: 8px 20px;
  background: #F97316;
  color: #fff;
  border: none;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
}

/* ─── Cards ─── */
.zx-card {
  background: #ffffff;
  border-radius: 12px;
  padding: 24px;
  border: 1px solid rgba(196,198,205,0.12);
  box-shadow: 0 2px 8px rgba(0,0,0,0.03);
}
.zx-card-title {
  font-size: 14px;
  font-weight: 700;
  color: #001529;
  margin-bottom: 16px;
  padding-bottom: 10px;
  border-bottom: 1px solid rgba(196,198,205,0.12);
}

/* Chart */
.zx-chart-area {
  width: 100%;
  height: 420px;
}

/* Data Table */
.zx-data-table-wrap {
  overflow-x: auto;
  border: 1px solid #f3f4f5;
  border-radius: 8px;
}
.zx-data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.zx-data-table thead th {
  position: sticky;
  top: 0;
  background: #f8f9fa;
  padding: 10px 14px;
  font-weight: 600;
  border-bottom: 1px solid #e1e3e4;
  text-align: left;
  white-space: nowrap;
}
.zx-data-table tbody td {
  padding: 10px 14px;
  border-bottom: 1px solid #f8f9fa;
  white-space: nowrap;
}
.zx-row-portfolio {
  background: rgba(0,21,41,0.02);
  font-weight: 700;
}
.zx-row-portfolio td:first-child {
  color: #001529;
  font-size: 14px;
}

/* 红涨绿跌 */
.zx-up {
  color: #DC2626;
  font-weight: 600;
}
.zx-down {
  color: #16A34A;
  font-weight: 600;
}

/* ─── Empty State ─── */
.zx-empty-state {
  text-align: center;
  padding: 80px 40px;
  color: #74777d;
}
.zx-empty-icon { font-size: 64px; margin-bottom: 16px; }
.zx-empty-state h2 { font-size: 22px; font-weight: 700; color: #191c1d; margin-bottom: 8px; }
.zx-empty-state p { font-size: 14px; max-width: 480px; margin: 0 auto; line-height: 1.6; }

.zx-error {
  padding: 16px 20px;
  background: #FEF2F2;
  border: 1px solid #FECACA;
  border-radius: 8px;
  color: #991B1B;
  font-size: 14px;
  margin-top: 16px;
}

.fade-in { animation: fadeIn 0.4s ease-out; }
@keyframes fadeIn { from { opacity:0; transform:translateY(6px); } to { opacity:1; transform:translateY(0); } }
</style>
