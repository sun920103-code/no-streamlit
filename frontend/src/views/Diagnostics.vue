<template>
  <div style="min-height:100vh;background:var(--bg-page);">
    <!-- Top Nav -->
    <div class="hud-bar" style="margin:0;">
      <div style="display:flex;align-items:center;gap:12px;">
        <button class="btn btn-outline" @click="$router.push('/')" style="padding:6px 14px;font-size:13px;">
          🔙 返回大厅
        </button>
        <h3 style="font-size:18px;font-weight:700;color:var(--navy);margin:0;">🩺 既有组合持仓诊断与结构优化</h3>
      </div>
      <div class="status-badge">
        <span class="status-dot"></span>
        诊断引擎就绪
      </div>
    </div>

    <div style="display:flex;">
      <!-- Left Nav -->
      <aside style="width:220px;background:#FFFFFF;border-right:1px solid #E2E8F0;padding:20px 12px;min-height:calc(100vh - 52px);">
        <div style="color:var(--text-secondary);font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:12px;padding:0 8px;">
          📊 智能分析导航
        </div>
        <div
          v-for="(page, i) in subPages" :key="i"
          @click="activePage = i"
          style="padding:10px 12px;border-radius:6px;cursor:pointer;margin-bottom:4px;font-size:13px;transition:all 0.2s;"
          :style="{
            background: activePage === i ? 'var(--sovereign-accent)' : 'transparent',
            color: activePage === i ? '#FFF' : 'var(--text-secondary)',
            fontWeight: activePage === i ? 600 : 400,
          }"
        >{{ page }}</div>
      </aside>

      <!-- Main Area -->
      <main style="flex:1;padding:24px 32px;">
        <!-- 5-Step Pipeline -->
        <div class="step-pipeline">
          <template v-for="(step, i) in pipelineSteps" :key="i">
            <div class="step-circle" :class="i < currentStep ? 'done' : i === currentStep ? 'active' : 'pending'">
              {{ step.icon }}
            </div>
            <div v-if="i < pipelineSteps.length - 1" class="step-line" :class="i < currentStep ? 'done' : ''"></div>
          </template>
        </div>
        <div style="text-align:center;margin-bottom:24px;">
          <div style="display:flex;justify-content:center;gap:32px;">
            <span v-for="(step, i) in pipelineSteps" :key="'l'+i" style="font-size:11px;width:70px;text-align:center;"
              :style="{ color: i <= currentStep ? 'var(--navy)' : 'var(--text-muted)', fontWeight: i === currentStep ? 600 : 400 }">
              {{ step.label }}
            </span>
          </div>
        </div>

        <!-- Page 1: 持仓分析 -->
        <div v-if="activePage === 0" class="fade-in">
          <div class="section-title">📂 持仓分析</div>

          <div class="card" style="margin-bottom:24px;">
            <div class="card-title">上传持仓明细 (CSV)</div>
            <div style="display:flex;gap:16px;align-items:flex-start;">
              <!-- Upload area -->
              <div style="flex:1;">
                <div
                  style="border:2px dashed #E2E8F0;border-radius:8px;padding:24px;text-align:center;transition:all 0.2s;cursor:pointer;position:relative;"
                  @dragover.prevent="dragActive=true"
                  @dragleave="dragActive=false"
                  @drop.prevent="onDrop"
                  :style="{ borderColor: dragActive ? '#2E86C1' : '#E2E8F0', background: dragActive ? '#EBF5FB' : 'transparent' }"
                  @click="$refs.fileInput.click()"
                >
                  <p style="color:var(--text-muted);margin-bottom:8px;">📎 拖拽上传 CSV 文件或点击选择</p>
                  <div style="display:flex;align-items:center;justify-content:center;gap:8px;">
                    <button class="btn btn-outline" style="padding:6px 16px;font-size:13px;pointer-events:none;">选择文件</button>
                    <span v-if="selectedFileName" style="font-size:13px;color:var(--navy);font-weight:500;">{{ selectedFileName }}</span>
                  </div>
                  <input ref="fileInput" type="file" accept=".csv" @change="onFileChange" style="display:none;" />
                </div>
                <!-- Loading State -->
                <div v-if="uploading" style="text-align:center;padding:16px;color:var(--text-secondary);font-size:13px;">
                  ⏳ 正在解析持仓数据...
                </div>
                <!-- Error State -->
                <div v-if="uploadError" style="margin-top:12px;padding:10px 14px;background:#FDEDEC;border-radius:6px;color:#C0392B;font-size:13px;">
                  ❌ {{ uploadError }}
                </div>
              </div>
              <!-- Download template -->
              <div style="min-width:140px;text-align:center;">
                <button class="btn btn-outline" style="padding:8px 16px;font-size:12px;" @click="downloadTemplate">
                  📥 下载标准模板
                </button>
                <div style="font-size:11px;color:var(--text-muted);margin-top:8px;text-align:left;line-height:1.6;">
                  <div><b>格式要求</b></div>
                  <div>• 基金代码 (必填)</div>
                  <div>• 基金名称 (选填)</div>
                  <div>• 金额 (必填)</div>
                </div>
              </div>
            </div>
          </div>

          <!-- Holdings Table -->
          <div v-if="holdings.length > 0" class="card fade-in" style="margin-bottom:24px;">
            <div class="card-title" style="display:flex;justify-content:space-between;align-items:center;">
              <span>✅ 解析完成：{{ holdings.length }} 只基金 · 总资产 ¥{{ formatNumber(holdingsTotal) }}</span>
              <button class="btn btn-outline" style="padding:4px 12px;font-size:12px;" @click="clearHoldings">🗑️ 清除</button>
            </div>
            <div style="overflow-x:auto;">
              <table class="holdings-table">
                <thead>
                  <tr>
                    <th style="width:50px;">#</th>
                    <th style="width:110px;">基金代码</th>
                    <th>基金名称</th>
                    <th style="width:160px;text-align:right;">持有金额 (元)</th>
                    <th style="width:100px;text-align:right;">占比</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(h, i) in holdings" :key="h.code">
                    <td style="color:var(--text-muted);">{{ i + 1 }}</td>
                    <td style="font-family:'JetBrains Mono',monospace;font-weight:600;color:var(--navy);">{{ h.code }}</td>
                    <td>{{ h.name || '—' }}</td>
                    <td style="text-align:right;font-family:'JetBrains Mono',monospace;">{{ formatNumber(h.amount) }}</td>
                    <td style="text-align:right;">
                      <span class="proportion-badge">{{ (h.proportion * 100).toFixed(2) }}%</span>
                    </td>
                  </tr>
                </tbody>
                <tfoot>
                  <tr>
                    <td colspan="3" style="font-weight:700;color:var(--navy);">合计</td>
                    <td style="text-align:right;font-weight:700;font-family:'JetBrains Mono',monospace;color:var(--navy);">
                      ¥{{ formatNumber(holdingsTotal) }}
                    </td>
                    <td style="text-align:right;font-weight:700;color:var(--navy);">100.00%</td>
                  </tr>
                </tfoot>
              </table>
            </div>
            <!-- Skipped warnings -->
            <div v-if="skippedItems.length > 0" style="margin-top:12px;padding:10px 14px;background:#FEF9E7;border-radius:6px;font-size:12px;color:#7D6608;">
              ⚠️ 以下 {{ skippedItems.length }} 行被跳过：<span v-for="(s, i) in skippedItems" :key="i">{{ s }}<span v-if="i < skippedItems.length-1">、</span></span>
            </div>
          </div>

          <WindDashboard :holdings="holdings" @success="handleWindSuccess" />

          <div class="card">
            <div class="card-title">🔬 因子映射 & RP 体检</div>
            <p style="color:var(--text-secondary);font-size:13px;">
              将持仓基金映射到 8 大资产类别，计算 HRP 均衡权重，对比当前持仓与最优配置的偏离度。
            </p>
            <AsyncButton 
              :action="runHrpOptimization"
              type="primary"
              text="⚖️ 执行 HRP 风险平价配置"
              style="margin-top:12px;"
            />

            <!-- HRP Rebalance Table (Interface 2 mapped) -->
            <RebalanceTable :result="hrpResultTable" />
          </div>
        </div>

        <!-- Page 2: AI 研判调仓 -->
        <div v-if="activePage === 1" class="fade-in">
          <div class="section-title">🧠 AI 研判调仓</div>

          <div class="card" style="margin-bottom:24px;">
            <div class="card-title">📡 资讯调仓</div>
            <p style="color:var(--text-secondary);font-size:13px;margin-bottom:12px;">
              自动搜索最新市场新闻，AI 投委会分析后生成 BL 调仓建议。
            </p>
            <AsyncButton
              :action="runAiNewsRebalance"
              type="primary"
              text="📡 执行资讯战术调仓"
            />
            <RebalanceTable :result="aiNewsResultTable" />
          </div>

          <div class="card" style="margin-bottom:24px;">
            <div class="card-title">📄 研报调仓 (Interface 2)</div>
            <div style="border:2px dashed #E2E8F0;border-radius:8px;padding:20px;text-align:center;margin-bottom:12px;">
              <p style="color:var(--text-muted);">📎 上传宏观研报 (PDF/TXT)</p>
              <input type="file" ref="reportFileInput" accept=".pdf,.txt" style="margin-top:8px;" />
            </div>
            <AsyncButton
              :action="runAiReportRebalance"
              type="primary"
              text="📄 上传研报并执行战术调仓"
            />
            
            <RebalanceTable :result="aiReportResultTable" />

          </div>

          <div class="card">
            <div class="card-title">⚖️ 核心 KPI 业绩比较面板 (Interface 3)</div>
            <p style="color:var(--text-secondary);font-size:13px;margin-bottom:16px;">
              调用回测引擎，横向对比调仓前后策略的各项指标，确保收益和风险达标。
            </p>
            <AsyncButton
              :action="generatedApi.runStressTestApiV1AnalysisStressTestGet"
              type="primary"
              text="📈 执行回测对比 (可能需要几秒)"
              @success="handleKpiSuccess"
            />

            <!-- Interface 3: KPI Table -->
            <div v-if="kpiResult" class="fade-in" style="margin-top:20px;overflow-x:auto;">
              <table class="holdings-table">
                <thead>
                  <tr>
                    <th>策略</th>
                    <th style="text-align:right;">年化收益</th>
                    <th style="text-align:right;">年化波动</th>
                    <th style="text-align:right;">夏普比率</th>
                    <th style="text-align:right;">最大回撤</th>
                    <th style="text-align:right;">Calmar</th>
                    <th style="text-align:right;">胜率</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(kpi, i) in kpiResult.kpi_list" :key="i">
                    <td style="font-weight:600;color:var(--navy);">{{ kpi.strategy_label }}</td>
                    <td style="text-align:right;font-family:'JetBrains Mono',monospace;color:#EF4444;">{{ kpi.ann_return >= 0 ? '+' : '' }}{{ (kpi.ann_return * 100).toFixed(2) }}%</td>
                    <td style="text-align:right;font-family:'JetBrains Mono',monospace;">{{ (kpi.ann_volatility * 100).toFixed(2) }}%</td>
                    <td style="text-align:right;font-family:'JetBrains Mono',monospace;">{{ kpi.sharpe_ratio.toFixed(2) }}</td>
                    <td style="text-align:right;font-family:'JetBrains Mono',monospace;color:#10B981;">{{ (kpi.max_drawdown * 100).toFixed(2) }}%</td>
                    <td style="text-align:right;font-family:'JetBrains Mono',monospace;">{{ kpi.calmar_ratio.toFixed(2) }}</td>
                    <td style="text-align:right;font-family:'JetBrains Mono',monospace;">{{ (kpi.win_rate * 100).toFixed(1) }}%</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <!-- Page 3: 业绩回测 (Now fully dynamic) -->
        <div v-if="activePage === 2 && holdings.length > 0" class="fade-in">
           <!-- Campaign 13: The 3-Way Grid Component -->
           <ThreeWayMatrix />
           <BacktestDashboard 
             :strategiesPayload="getStrategiesPayload" 
             :pdfStatePayload="getPdfStatePayload" 
           />
        </div>
        <div v-if="activePage === 2 && holdings.length === 0" class="fade-in">
          <div class="card" style="text-align:center;color:var(--text-muted);padding:40px;">
            请先在左侧「📂 持仓分析」界面上传您的当前持仓
          </div>
        </div>
      </main>
      <!-- Campaign 11: 左侧或者右侧全局控制参数侧边栏 -->
      <aside style="width: 300px; padding-left: 20px;">
         <ConfigSidebar />
      </aside>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { uploadHoldings, optimizeHrp, getRebalanceInstructions, extractNewsViews, extractReportViews, optimizeBl } from '../api'
import AsyncButton from '../components/common/AsyncButton.vue'
import WindDashboard from '../components/WindDashboard.vue'
import RebalanceTable from '../components/RebalanceTable.vue'
import BacktestDashboard from '../components/BacktestDashboard.vue'
import ThreeWayMatrix from '../components/ThreeWayMatrix.vue'
import ConfigSidebar from '../components/ConfigSidebar.vue'

const activePage = ref(0)
const currentStep = ref(0) // 0: upload, 1: mapping, 2: hrp
const hrpResultTable = ref(null)

async function runHrpOptimization() {
  if (holdings.value.length === 0) {
    throw new Error("无持仓数据，无法进行 HRP 配置");
  }
  
  // 1. Prepare inputs
  const assetNames = holdings.value.map(h => h.code);
  const n = assetNames.length;
  // Mock standard diagonal matrix as frontend doesn't strictly hold the C++ Wind result array yet
  const mockCov = Array(n).fill(0).map((_, i) => Array(n).fill(0).map((_, j) => i === j ? 0.04 : 0.01));
  
  // 2. Call optimize_hrp
  const hrpRes = await optimizeHrp({
    asset_names: assetNames,
    cov_matrix_2d: mockCov,
    max_weight: 0.35,
    min_weight: 0.02
  });
  
  if (hrpRes.data.status === "error") {
    throw new Error(hrpRes.data.message || "HRP模型失败");
  }
  
  const targetWeights = hrpRes.data.target_weights;
  
  // 3. Prepare for rebalance_instructions
  const currentWeights = {};
  const assetClassMap = {};
  const fundNameMap = {};
  
  holdings.value.forEach(h => {
    currentWeights[h.code] = h.proportion;
    assetClassMap[h.code] = h.asset_class || "主动股票"; 
    fundNameMap[h.code] = h.name;
    // ensure missing assets in target are 0
    if (!(h.code in targetWeights)) {
      targetWeights[h.code] = 0.0;
    }
  });
  
  // 4. Call rebalance_instructions
  const rebalRes = await getRebalanceInstructions({
    current_weights: currentWeights,
    target_weights: targetWeights,
    total_aum: holdingsTotal.value,
    asset_class_map: assetClassMap,
    fund_name_map: fundNameMap
  });
  
  // 5. Render
  hrpResultTable.value = rebalRes.data;
  
  if (currentStep.value < 3) {
    currentStep.value = 3;
  }
}

function handleKpiSuccess(res) {
  kpiResult.value = res.data || res
}

// === AI BL Rebalance Methods ===

const aiNewsResultTable = ref(null)
const aiReportResultTable = ref(null)
const reportFileInput = ref(null)

async function executeBlOptimization(nlpScores) {
  const assetNames = holdings.value.map(h => h.code);
  const n = assetNames.length;
  const mockCov = Array(n).fill(0).map((_, i) => Array(n).fill(0).map((_, j) => i === j ? 0.04 : 0.01));
  
  const currentWeights = {};
  const assetClassMap = {};
  holdings.value.forEach(h => {
    currentWeights[h.code] = h.proportion;
    assetClassMap[h.code] = h.asset_class || "主动股票"; 
  });
  
  const res = await optimizeBl({
    nlp_scores: nlpScores,
    current_weights: currentWeights,
    total_aum: holdingsTotal.value,
    asset_class_map: assetClassMap,
    cov_matrix_2d: mockCov,
    asset_names: assetNames
  });
  return res.data;
}

async function runAiNewsRebalance() {
  if (holdings.value.length === 0) throw new Error("请先根据步骤一上传持仓");
  
  // 1. Extract Views
  const viewsRes = await extractNewsViews({ query: "最新宏观经济焦点" });
  if (viewsRes.data.status !== "success") throw new Error("新闻推演计算异常");
  
  // 2. BL Optimization
  const blRes = await executeBlOptimization(viewsRes.data.nlp_scores);
  aiNewsResultTable.value = blRes;
}

async function runAiReportRebalance() {
  if (holdings.value.length === 0) throw new Error("请先上传持仓组合");
  
  const file = reportFileInput.value?.files?.[0];
  if (!file) throw new Error("请您先选择至少一份本地宏观研报");
  
  // 1. Upload & Extract Views
  const formData = new FormData();
  formData.append('file', file);
  
  const viewsRes = await extractReportViews(formData);
  if (viewsRes.data.status !== "success") throw new Error("研报解析失利");
  
  // 2. BL Optimization
  const blRes = await executeBlOptimization(viewsRes.data.nlp_scores);
  aiReportResultTable.value = blRes;
}

// === Payload Generators for KPI Backtest & PDF Export ===

function getStrategiesPayload() {
  const assetNames = holdings.value.map(h => h.code);
  const n = assetNames.length;
  // Simple mock cov matrix for stateless calculation visualization
  const mockCov = Array(n).fill(0).map((_, i) => Array(n).fill(0).map((_, j) => i === j ? 0.04 : 0.01));

  const clientWeights = {};
  holdings.value.forEach(h => clientWeights[h.code] = h.proportion);
  
  const strats = [{ label: '📋 客户持仓', weights: clientWeights }];
  
  if (hrpResultTable.value) {
    const w = { ...clientWeights };
    hrpResultTable.value.instructions.forEach(ins => w[ins.code] += ins.delta_w);
    strats.push({ label: '⚖️ HRP 配置 [沪深300基准]', weights: w });
  }
  if (aiNewsResultTable.value) {
    const w = { ...clientWeights };
    aiNewsResultTable.value.instructions.forEach(ins => w[ins.code] += ins.delta_w);
    strats.push({ label: '📡 资讯调仓', weights: w });
  }
  if (aiReportResultTable.value) {
    const w = { ...clientWeights };
    aiReportResultTable.value.instructions.forEach(ins => w[ins.code] += ins.delta_w);
    strats.push({ label: '📄 研报调仓', weights: w });
  }
  
  return {
    strategies: strats,
    benchmark_code: "000300.SH",
    cov_matrix_2d: mockCov,
    asset_names: assetNames
  }
}

function getPdfStatePayload() {
  return {
    diagnose_state: {
      client_holdings: holdings.value,
      client_total_aum: holdingsTotal.value,
      hrp_instructions: hrpResultTable.value?.instructions || [],
      ai_news_instructions: aiNewsResultTable.value?.instructions || [],
      ai_report_instructions: aiReportResultTable.value?.instructions || []
    }
  }
}

const showAlert = (msg) => alert(msg)

const subPages = ['📂 持仓分析', '🧠 AI 研判调仓', '📈 业绩回测']

const pipelineSteps = [
  { icon: '📂', label: '上传 CSV' },
  { icon: '📡', label: 'Wind 拉取' },
  { icon: '🔬', label: '因子映射' },
  { icon: '⚖️', label: 'RP 体检' },
  { icon: '🧠', label: 'AI 增强' },
]

// Holdings state
const holdings = ref([])
const holdingsTotal = ref(0)
const skippedItems = ref([])
const selectedFileName = ref('')
const uploading = ref(false)
const uploadError = ref('')
const dragActive = ref(false)

function formatNumber(n) {
  return Number(n).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

async function processFile(file) {
  if (!file) return
  selectedFileName.value = file.name
  uploading.value = true
  uploadError.value = ''

  try {
    const res = await uploadHoldings(file)
    const data = res.data
    if (data.status === 'ok') {
      holdings.value = data.holdings
      holdingsTotal.value = data.total
      skippedItems.value = data.skipped || []
      currentStep.value = 1
    } else {
      uploadError.value = data.message || '解析失败'
    }
  } catch (e) {
    uploadError.value = e.response?.data?.detail || e.message || '上传失败'
  } finally {
    uploading.value = false
  }
}

function onFileChange(e) {
  const file = e.target.files[0]
  processFile(file)
}

function onDrop(e) {
  dragActive.value = false
  const file = e.dataTransfer.files[0]
  if (file && file.name.endsWith('.csv')) {
    processFile(file)
  }
}

function clearHoldings() {
  holdings.value = []
  holdingsTotal.value = 0
  skippedItems.value = []
  selectedFileName.value = ''
  currentStep.value = 0
}

function downloadTemplate() {
  const csv = '\ufeff基金代码,基金名称,持有金额(元)\n000979,,1997602.88\n001203,,2997003.00\n002657,,999400.36\n005014,,2949300.07\n006965,,2900389.02\n'
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = '客户持仓模板.csv'
  a.click()
  URL.revokeObjectURL(url)
}
</script>

<style scoped>
.holdings-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.holdings-table th {
  background: #F8FAFC;
  color: var(--text-secondary);
  font-weight: 600;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding: 10px 12px;
  border-bottom: 2px solid #E2E8F0;
  text-align: left;
}
.holdings-table td {
  padding: 10px 12px;
  border-bottom: 1px solid #F1F5F9;
  color: var(--text-primary);
}
.holdings-table tbody tr:hover {
  background: #F8FAFC;
}
.holdings-table tfoot td {
  border-top: 2px solid #E2E8F0;
  border-bottom: none;
  padding: 12px;
  background: #F8FAFC;
}
.proportion-badge {
  display: inline-block;
  background: #EBF5FB;
  color: #2E86C1;
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 600;
  font-size: 12px;
}
</style>
