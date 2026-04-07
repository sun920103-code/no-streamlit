<template>
  <div class="min-h-screen flex flex-col bg-white text-[#1a1c1e]" style="font-family: 'Noto Serif SC', serif;">
    
    <!-- 顶部导航 -->
    <header class="sticky top-0 z-50 backdrop-blur-[20px] bg-white/90 border-b border-[#eee]">
      <div class="flex justify-between items-center px-16 py-8 w-full max-w-[1920px] mx-auto">
        <div class="flex flex-col">
          <h1 class="text-3xl font-bold tracking-tight text-[#1a1c1e] m-0">业绩回测</h1>
          <p class="text-xs tracking-widest font-medium text-[#737c7f] mt-1 mb-0">配置方案对比 7 大宽基指数 · 5 年绝对回报分析</p>
        </div>
        <button 
          v-if="hasAllocation"
          class="bg-[#001529] text-white px-8 py-3 rounded-sm flex items-center gap-2 transition-all hover:bg-opacity-90 active:scale-95 disabled:opacity-50 shadow-md"
          :disabled="loading" 
          @click="runBacktest"
        >
          <span class="material-symbols-outlined text-[18px] transition-transform" :class="{ 'animate-spin': loading }">refresh</span>
          <span class="text-sm font-semibold tracking-wide" style="font-family: 'Inter', sans-serif;">{{ loading ? '计算中...' : '重新计算' }}</span>
        </button>
      </div>
    </header>

    <main class="max-w-[1920px] mx-auto px-16 py-12 flex-grow w-full">
      <!-- 提示先完成底仓 -->
      <div v-if="!hasAllocation" class="bg-[#f1f4f6] rounded-sm p-12 border border-[#abb3b7]/20 flex flex-col items-center justify-center min-h-[400px]">
        <span class="material-symbols-outlined text-4xl text-[#C0392B] mb-4">warning</span>
        <h2 class="text-xl font-bold mb-2">请先完成宏观配置底仓</h2>
        <p class="text-[#737c7f] mb-6">获取配置方案后再进行业绩回测</p>
        <button class="px-6 py-2 bg-[#1a1c1e] text-white rounded-sm hover:-translate-y-0.5 transition-transform" @click="$router.push('/smart/macro')">
          前往配置底仓
        </button>
      </div>

      <!-- 空白占位状态 -->
      <div v-else-if="!result && !loading" class="bg-[#f8f9fa] rounded-sm p-12 border border-[#abb3b7]/20 flex flex-col items-center justify-center min-h-[400px]">
        <span class="material-symbols-outlined text-[#4f6174] mb-4 opacity-50" style="font-size: 48px;">insights</span>
        <h2 class="text-xl font-bold mb-2">模型已就绪</h2>
        <p class="text-[#737c7f]">点击右上角「重新计算」按钮启动 5 年回测引擎</p>
      </div>

      <!-- 仪表盘区域：年度收益表现 -->
      <section v-show="result" class="mb-8 fade-in">
        <div class="flex items-baseline justify-between mb-8">
          <h2 class="text-xl font-bold tracking-tight text-[#1a1c1e] border-l-4 border-[#C0392B] pl-4">过去 5 年年度绝对收益率对比 · 红涨绿跌</h2>
        </div>

        <!-- 组合图表容器 -->
        <div class="bg-[#f8f9fa] rounded-sm p-12 border border-[#abb3b7]/20 shadow-sm overflow-hidden text-[#1a1c1e]">
          
          <!-- ECharts 容器 -->
          <div ref="chartRef" class="w-full h-[460px] border-b border-[#abb3b7]/30 pb-8"></div>

          <!-- 数据图例 -->
          <div class="grid grid-cols-2 lg:grid-cols-4 xl:grid-cols-5 gap-x-6 gap-y-8 mt-12 pt-8">
            <div class="flex flex-col gap-1">
              <div class="flex items-center gap-2 mb-1">
                <div class="w-2.5 h-2.5 bg-[#C0392B]"></div>
                <span class="text-[11px] font-bold text-[#1a1c1e]">智选稳健配置</span>
              </div>
              <p class="text-[10px] text-[#737c7f] leading-relaxed">基于量化多因子模型的动态平衡策略</p>
            </div>
            <div class="flex flex-col gap-1">
              <div class="flex items-center gap-2 mb-1">
                <div class="w-2.5 h-2.5 bg-[#C0392B]"></div>
                <span class="text-[11px] font-bold text-[#1a1c1e]">新闻资讯调仓</span>
              </div>
              <p class="text-[10px] text-[#737c7f] leading-relaxed">金融时报与财联社事件驱动分析</p>
            </div>
            <div class="flex flex-col gap-1">
              <div class="flex items-center gap-2 mb-1">
                <div class="w-2.5 h-2.5 bg-[#C0392B]"></div>
                <span class="text-[11px] font-bold text-[#1a1c1e]">研报调仓</span>
              </div>
              <p class="text-[10px] text-[#737c7f] leading-relaxed">券商深度研报归纳及共识调仓</p>
            </div>
            <div class="flex flex-col gap-1">
              <div class="flex items-center gap-2 mb-1">
                <div class="w-2.5 h-2.5 bg-[#E6B0AA]"></div>
                <span class="text-[11px] font-bold text-[#1a1c1e]">上证指数</span>
              </div>
              <p class="text-[10px] text-[#737c7f] leading-relaxed">代表 A 股核心市场整体表现</p>
            </div>
            <div class="flex flex-col gap-1">
              <div class="flex items-center gap-2 mb-1">
                <div class="w-2.5 h-2.5 bg-[#E6B0AA]"></div>
                <span class="text-[11px] font-bold text-[#1a1c1e]">沪深 300</span>
              </div>
              <p class="text-[10px] text-[#737c7f] leading-relaxed">蓝筹股代表，反映大盘股走势</p>
            </div>
            <div class="flex flex-col gap-1">
              <div class="flex items-center gap-2 mb-1">
                <div class="w-2.5 h-2.5 bg-[#E6B0AA]"></div>
                <span class="text-[11px] font-bold text-[#1a1c1e]">深证成指</span>
              </div>
              <p class="text-[10px] text-[#737c7f] leading-relaxed">深市核心资产与科技制造业风向</p>
            </div>
            <div class="flex flex-col gap-1">
              <div class="flex items-center gap-2 mb-1">
                <div class="w-2.5 h-2.5 bg-[#E6B0AA]"></div>
                <span class="text-[11px] font-bold text-[#1a1c1e]">中证 500</span>
              </div>
              <p class="text-[10px] text-[#737c7f] leading-relaxed">中小盘成长性企业的核心指标</p>
            </div>
            <div class="flex flex-col gap-1">
              <div class="flex items-center gap-2 mb-1">
                <div class="w-2.5 h-2.5 bg-[#E6B0AA]"></div>
                <span class="text-[11px] font-bold text-[#1a1c1e]">中证 1000</span>
              </div>
              <p class="text-[10px] text-[#737c7f] leading-relaxed">反映微盘及小市值风格波动</p>
            </div>
            <div class="flex flex-col gap-1">
              <div class="flex items-center gap-2 mb-1">
                <div class="w-2.5 h-2.5 bg-[#E6B0AA]"></div>
                <span class="text-[11px] font-bold text-[#1a1c1e]">创业板指</span>
              </div>
              <p class="text-[10px] text-[#737c7f] leading-relaxed">科技创新与成长风格风向标</p>
            </div>
            <div class="flex flex-col gap-1">
              <div class="flex items-center gap-2 mb-1">
                <div class="w-2.5 h-2.5 bg-[#E6B0AA]"></div>
                <span class="text-[11px] font-bold text-[#1a1c1e]">恒生指数</span>
              </div>
              <p class="text-[10px] text-[#737c7f] leading-relaxed">离岸中国资产与全球流动性参考</p>
            </div>
          </div>
        </div>

        <!-- 年度收益率明细表格 -->
        <div class="mt-16">
          <div class="flex items-center justify-between mb-8">
            <div class="flex items-center gap-4">
              <div class="w-10 h-10 flex items-center justify-center bg-[#C0392B] rounded-sm shadow-sm" style="border: 1px solid rgba(255,255,255,0.2);">
                <svg class="w-6 h-6 fill-none stroke-white" stroke-linecap="square" stroke-width="1.5" viewBox="0 0 24 24">
                  <path d="M4 20h16M4 16h16M4 12h8M4 8h4" opacity="0.5"></path>
                  <path d="M12 12l3-3 5 5" stroke-linejoin="bevel"></path>
                  <rect height="18" rx="0.5" stroke-opacity="0.3" width="18" x="3" y="3"></rect>
                </svg>
              </div>
              <h1 class="text-2xl font-bold tracking-tight text-[#111d27]" style="font-family: 'Noto Serif', 'Noto Serif SC', serif;">年度收益率明细 (%)</h1>
            </div>
          </div>
          <!-- Table Container -->
          <div class="border border-[#e1bfb9]/30 overflow-hidden bg-white shadow-[0_2px_12px_rgba(225,191,185,0.15)] rounded-sm">
            <table class="w-full text-left border-collapse">
              <thead>
                <tr class="border-b border-[#e1bfb9]/50 hover:bg-gray-50 bg-[#f7f9ff]">
                  <th class="py-5 px-6 font-bold text-[#59413d] uppercase tracking-wider text-[13px]" style="font-family: 'Noto Serif', 'Noto Serif SC', serif;">指数/方案</th>
                  <th v-for="year in result?.years || []" :key="year" class="py-5 px-6 font-semibold text-[#59413d] text-center text-[13px]" style="font-family: 'Work Sans', sans-serif;">{{ year }}</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-[#e1bfb9]/20" v-if="result">
                <!-- 配置方案 -->
                <tr v-for="(rets, label) in result.portfolios_returns" :key="label" class="transition-colors group hover:bg-gray-50">
                  <td class="py-5 px-6 flex items-center gap-3">
                    <span class="material-symbols-outlined filled-icon text-lg" style="font-variation-settings: 'FILL' 1; color: #735c00;">star</span>
                    <span class="font-semibold text-[#111d27]">{{ label }}</span>
                  </td>
                  <td v-for="year in result.years" :key="year" class="py-5 px-6 text-center font-bold" :class="fmtRetClass(rets[year])" style="font-family: 'Work Sans', sans-serif;">
                    {{ fmtRet(rets[year]) }}
                  </td>
                </tr>
                <!-- 各个宽基指数 -->
                <tr v-for="(rets, bmName) in result.benchmark_returns" :key="bmName" class="transition-colors hover:bg-gray-50">
                  <td class="py-5 px-6 text-[#59413d] font-medium pl-14">{{ bmName }}</td>
                  <td v-for="year in result.years" :key="year" class="py-5 px-6 text-center" :class="fmtRetClass(rets[year])" style="font-family: 'Work Sans', sans-serif;">
                    {{ fmtRet(rets[year]) }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <!-- Footnote / Legend -->
          <div class="mt-8 flex items-center justify-between text-[#59413d] text-sm border-t border-[#e1bfb9]/20 pt-6">
            <div class="flex gap-6">
              <div class="flex items-center gap-2">
                <span class="w-2.5 h-2.5 rounded-full bg-[#c0392b]"></span>
                <span class="text-[12px] font-bold" style="font-family: 'Noto Serif', 'Noto Serif SC', serif;">正收益 (Gain)</span>
              </div>
              <div class="flex items-center gap-2">
                <span class="w-2.5 h-2.5 rounded-full bg-[#2e7d32]"></span>
                <span class="text-[12px] font-bold" style="font-family: 'Noto Serif', 'Noto Serif SC', serif;">负收益 (Loss)</span>
              </div>
            </div>
            <p class="italic text-[12px] opacity-70" style="font-family: 'Noto Serif', 'Noto Serif SC', serif;">* 数据来源: Wind。过往业绩不代表未来收益。</p>
          </div>
        </div>

      </section>

    </main>

    <!-- 页脚 -->
    <footer class="max-w-[1920px] mx-auto px-16 py-12 border-t border-[#abb3b7]/10 w-full mt-auto bg-white">
      <div class="flex justify-end items-center opacity-70">
        <div class="text-[11px] text-[#737c7f] font-medium tracking-widest uppercase" style="font-family: 'Inter', sans-serif;">
            仅供参考 · 投资有风险 · 入市需谨慎
        </div>
      </div>
    </footer>
    
    <!-- Error Floating -->
    <div v-if="error" class="fixed bottom-6 right-6 z-50 bg-[#FEF2F2] border border-[#FECACA] text-[#C0392B] px-6 py-4 rounded-sm shadow-2xl flex items-center gap-3">
      <span class="material-symbols-outlined">error</span>
      {{ error }}
    </div>

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
    const baseWeights = store.zx_selectedWeights
    const tacRes = store.zx_tacticalOneclickResult
    
    const ports = {}
    if (baseWeights && Object.keys(baseWeights).length > 0) {
      const scenarioName = store.zx_selectedScenario?.name || '量化配置底仓'
      ports[scenarioName] = baseWeights
    }
    if (tacRes?.news_result?.weights) {
      ports['新闻资讯调仓'] = tacRes.news_result.weights
    }
    if (tacRes?.report_result?.weights) {
      ports['研报调仓'] = tacRes.report_result.weights
    }

    const res = await zxBacktest({
      portfolios: ports,
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

// ── 格式化收益率 (严格 null 检查, 防止 0% 被渲染为 N/A) ──
function fmtRet(val) {
  if (val === null || val === undefined) return 'N/A'
  const n = Number(val)
  if (isNaN(n)) return 'N/A'
  return (n > 0 ? '+' : '') + n.toFixed(2)
}
function fmtRetClass(val) {
  if (val === null || val === undefined) return 'text-[#737c7f]'
  return Number(val) >= 0 ? 'text-[#c0392b]' : 'text-[#2e7d32]'
}

function renderChart() {
  if (!chartRef.value || !result.value) return

  import('echarts').then((echarts) => {
    if (chartInstance) chartInstance.dispose()
    chartInstance = echarts.init(chartRef.value, null, { renderer: 'canvas' })

    const data = result.value
    const years = data.years
    const allSeries = []

    // 组合方案 (支持多个)
    const portfolios = data.portfolios_returns || {}
    for (const [label, rets] of Object.entries(portfolios)) {
      allSeries.push({
        name: label,
        type: 'bar',
        data: years.map(y => rets[y] || 0),
        itemStyle: {
          color: function(params) {
            // 红涨绿跌 (主组合颜色较深)
            return params.data >= 0 ? '#C0392B' : '#27ae60'
          },
          borderRadius: 2,
        },
        label: {
          show: true,
          position: 'top',
          formatter: '{c}%',
          fontSize: 10,
          fontWeight: 700,
          color: '#1a1c1e',
          fontFamily: "'Inter', sans-serif"
        },
        barMaxWidth: 30,
        barGap: '10%'
      })
    }

    // 宽基指数
    for (const [bmName, rets] of Object.entries(data.benchmark_returns || {})) {
      allSeries.push({
        name: bmName,
        type: 'bar',
        data: years.map(y => rets[y] || 0),
        itemStyle: {
          color: function(params) {
            // 红涨绿跌 (宽基指数使用较浅静音颜色)
            return params.data >= 0 ? '#E6B0AA' : '#A9DFBF'
          },
          borderRadius: 2,
        },
        label: {
          show: false // 隐藏指数标签，避免图表过于拥挤，如HTML示例中那样
        },
        barMaxWidth: 16,
      })
    }

    const option = {
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow', shadowStyle: { color: 'rgba(0,21,41,0.03)' } },
        backgroundColor: '#ffffff',
        borderColor: '#abb3b7',
        borderWidth: 1,
        padding: [12, 16],
        textStyle: { fontSize: 13, fontFamily: "'Inter', sans-serif", color: '#1a1c1e' },
        formatter: function(params) {
          let html = `<div style="font-weight:700;margin-bottom:12px;color:#1a1c1e;">${params[0].axisValue}</div>`
          params.forEach(p => {
            let color = p.value >= 0 ? '#C0392B' : '#27ae60'
            // 如果是指数，tooltip使用同样对应的muted浅红色/浅绿色
            if (p.seriesName.includes('指数') || p.seriesName.includes('300') || p.seriesName.includes('500') || p.seriesName.includes('1000') || p.seriesName.includes('50') || p.seriesName.includes('板')) {
                color = p.value >= 0 ? '#e68f84' : '#69cf93' // 略深一点以便阅读
            }
            html += `<div style="display:flex;justify-content:space-between;gap:24px;margin-bottom:6px;align-items:center;">
                       <span><span style="display:inline-block;width:6px;height:6px;border-radius:50%;background-color:${color};margin-right:8px;vertical-align:middle;"></span><span style="color:#4f6174;font-size:12px;vertical-align:middle;">${p.seriesName}</span></span>
                       <span style="font-family:'Inter',sans-serif;font-weight:600;color:${color}">${p.value >= 0 ? '+' : ''}${p.value}%</span>
                     </div>`
          })
          return html
        },
      },
      legend: { show: false }, // 图例已经用 HTML 写在了下面，这里隐藏 ECharts 的图例
      grid: {
        left: 20, right: 20, top: 40, bottom: 20, containLabel: true
      },
      xAxis: {
        type: 'category',
        data: years,
        axisLabel: { fontWeight: 700, fontSize: 13, color: '#4f6174', fontFamily: "'Inter', sans-serif", margin: 16 },
        axisLine: { lineStyle: { color: '#eaeff1' }, show: true },
        axisTick: { show: false }
      },
      yAxis: {
        type: 'value',
        axisLabel: {
          formatter: '{value}%',
          color: '#737c7f',
          fontSize: 11,
          fontFamily: "'Inter', sans-serif",
          margin: 16
        },
        splitLine: { lineStyle: { type: 'dashed', color: '#eaeff1' } },
      },
      series: allSeries,
    }

    chartInstance.setOption(option)

    const resizeObserver = new ResizeObserver(() => chartInstance?.resize())
    resizeObserver.observe(chartRef.value)
  }).catch(e => {
    console.error('ECharts config failed:', e)
    error.value = 'ECharts load failed.'
  })
}

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
@import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@300;400;500;600;700;900&family=Inter:wght@400;700&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Noto+Serif:wght@400;700;900&family=Work+Sans:wght@300;400;500;600;700&display=swap');

.fade-in { animation: fadeIn 0.4s ease-out; }
@keyframes fadeIn { from { opacity:0; transform:translateY(10px); } to { opacity:1; transform:translateY(0); } }
</style>
