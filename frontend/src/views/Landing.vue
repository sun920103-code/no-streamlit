<template>
  <div class="landing-page">
    <!-- Logo -->
    <div class="landing-logo">
      <img src="../assets/yc_logo.jpg" alt="粤财信托" />
    </div>

    <main class="landing-main">
      <!-- Main Cards -->
      <section class="cards-grid">
        <!-- Left Card — 粤财智选资产配置 -->
        <div class="hero-card card-navy" @click="enterSmartSelection">
          <div class="hero-card-content">
            <h2 class="hero-title">粤财智选资产配置</h2>
            <p class="hero-desc">粤财信托精选资产池+宏观周期视角+CVaR风控，为高净值客户提供多资产组合策略。深度优化资产配置权重。</p>
          </div>
          <div class="hero-card-action">
            <button class="hero-btn hero-btn-navy">
              进入配置中心
              <span class="material-symbols-outlined hero-btn-icon">arrow_forward</span>
            </button>
          </div>
          <div class="hero-glow"></div>
        </div>

        <!-- Right Card — 资产配置智能分析 -->
        <div class="hero-card card-crimson" @click="enterDiag">
          <div class="hero-card-content">
            <h2 class="hero-title">资产配置智能分析</h2>
            <p class="hero-desc hero-desc-light">系统自动化穿透式诊断，多维度分析现有组合风险。提供基于宏观因子和主观研报研判的资产配置建议。</p>
          </div>
          <div class="hero-card-action">
            <button class="hero-btn hero-btn-crimson">
              开始智能分析
              <span class="material-symbols-outlined hero-btn-icon">analytics</span>
            </button>
          </div>
          <div class="hero-glow hero-glow-dark"></div>
        </div>
      </section>

      <!-- Functional Buttons Section -->
      <section class="func-btns-row">
        <!-- Upload CSV Button -->
        <button class="func-btn func-btn-outline" @click="$refs.csvInput.click()">
          <span class="material-symbols-outlined func-btn-icon">upload_file</span>
          <div class="func-btn-text">
            <div class="func-btn-label">上传 CSV 文件</div>
            <div class="func-btn-sub">支持宽基指数因子报告</div>
          </div>
        </button>
        <input type="file" ref="csvInput" style="display:none" accept=".csv,.xls,.xlsx" multiple @change="onCsvSelected" />

        <!-- Generate Review Button -->
        <button class="func-btn func-btn-dark" @click="triggerReview" :disabled="isGeneratingReview">
          <span class="material-symbols-outlined func-btn-icon">auto_awesome</span>
          <div class="func-btn-text">
            <div class="func-btn-label">{{ isGeneratingReview ? '正在生成...' : '生成一周市场回顾' }}</div>
            <div class="func-btn-sub-light">基于最新宏观数据复盘</div>
          </div>
        </button>
      </section>

      <!-- Uploaded Files Table -->
      <section v-if="selectedFiles.length > 0" class="file-section fade-in">
        <div class="file-section-header">
          <h3>已选文件</h3>
          <span class="file-count">{{ selectedFiles.length }} 个文件</span>
        </div>
        <table class="file-table">
          <thead>
            <tr>
              <th>文件名</th>
              <th>大小</th>
              <th>状态</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(file, idx) in selectedFiles" :key="idx">
              <td class="ft-name">{{ file.name }}</td>
              <td class="ft-size">{{ formatFileSize(file.size) }}</td>
              <td><span class="status-badge badge-ready">就绪</span></td>
              <td class="ft-actions">
                <button class="icon-btn icon-btn-danger" @click.stop="removeFile(idx)" title="移除">
                  <span class="material-symbols-outlined" style="font-size:16px;">delete</span>
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </section>

      <!-- AI Review Canvas (SSE Stream) -->
      <section v-if="isReviewExpanded" class="review-canvas fade-in">
        <div class="review-decor"></div>
        <div class="review-inner">
          <div v-if="reviewStatus" class="review-status">
            <div class="pulse-dot"></div>
            <span>{{ reviewStatus }}</span>
          </div>
          <div class="markdown-preview market-review-text" v-html="renderedReview"></div>
          <div v-if="isGeneratingReview && reviewText.length > 0" class="cursor-blink">▍</div>
        </div>
      </section>
    </main>

    <!-- 全局 Toast -->
    <div v-if="toastMessage" class="global-toast fade-in">
       {{ toastMessage }}
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { marked } from 'marked'
import DOMPurify from 'dompurify'

const router = useRouter()

// Router paths
const enterSmartSelection = () => router.push('/smart')
const enterDiag = () => router.push('/diag')

// AI Review State
const selectedFiles = ref([])
const isReviewExpanded = ref(false)
const isGeneratingReview = ref(false)
const reviewStatus = ref('')
const reviewText = ref('')
const toastMessage = ref('')

function showToast(msg) {
  toastMessage.value = msg
  setTimeout(() => { toastMessage.value = '' }, 3000)
}

function formatFileSize(bytes) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(0) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

function onCsvSelected(event) {
  const files = Array.from(event.target.files)
  if (files.length > 0) {
    selectedFiles.value.push(...files)
    showToast(`已添加 ${files.length} 个文件`)
    event.target.value = ''  // 重置input，允许重复选择同名文件
  }
}

function removeFile(idx) {
  selectedFiles.value.splice(idx, 1)
}

async function triggerReview() {
  isReviewExpanded.value = true
  isGeneratingReview.value = true
  reviewStatus.value = '粤财信托，您的专业财富顾问，正在搜集全球市场资讯...'
  reviewText.value = ''
  
  try {
    // 构建 FormData，将上传的因子报告文件一并发送
    const formData = new FormData()
    if (selectedFiles.value.length > 0) {
      for (const file of selectedFiles.value) {
        formData.append('files', file)
      }
    }

    const response = await fetch('/api/v1/ai/generate_market_review', {
      method: 'POST',
      body: formData
    })

    if (!response.ok) {
       throw new Error(`请求失败: ${response.statusText}`)
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder('utf-8')
    reviewStatus.value = '粤财信托，您的专业财富顾问，正在搜集全球市场资讯，为您生成过去一周市场回顾中...'

    while (true) {
      const { value, done } = await reader.read()
      if (done) break
      
      const chunk = decoder.decode(value, { stream: true })
      const lines = chunk.split('\n')
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const dataStr = line.replace('data: ', '').trim()
          if (!dataStr) continue
          try {
            const parsed = JSON.parse(dataStr)
            if (parsed.type === 'log') {
              // 进度日志 — 更新状态栏
              reviewStatus.value = parsed.content
            } else if (parsed.type === 'stream_chunk') {
              // 打字机流式内容
              reviewText.value += parsed.content
            } else if (parsed.type === 'finish_stream') {
              reviewStatus.value = '✅ 一周市场回顾生成完毕'
              isGeneratingReview.value = false
              return
            } else if (parsed.type === 'error') {
              reviewStatus.value = `❌ 生成失败: ${parsed.content}`
              isGeneratingReview.value = false
              return
            }
          } catch(e) { /* ignore partial JSON */ }
        }
      }
    }
    // 流结束但未收到 finish_stream
    if (isGeneratingReview.value) {
      reviewStatus.value = '✅ 一周市场回顾生成完毕'
      isGeneratingReview.value = false
    }
    
  } catch (error) {
    console.error("SSE Error:", error)
    reviewStatus.value = '生成出错，请重试'
    isGeneratingReview.value = false
  }
}

const renderedReview = computed(() => {
  return DOMPurify.sanitize(marked.parse(reviewText.value))
})
</script>

<style scoped>
/* ═══════════════════════════════════════════════════
   Landing Page — Material Design 3 Palette
   ═══════════════════════════════════════════════════ */
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;600;700;800&family=Inter:wght@300;400;500;600&display=swap');

.landing-page {
  min-height: 100vh;
  background: #f8f9fa;
  font-family: 'Manrope', sans-serif;
  color: #191c1d;
  display: flex;
  flex-direction: column;
  justify-content: center;
  -webkit-font-smoothing: antialiased;
  position: relative;
}

.landing-logo {
  position: absolute;
  top: 24px;
  left: 32px;
  z-index: 10;
}
.landing-logo img {
  height: 40px;
  width: auto;
  object-fit: contain;
}

/* ─── Main Container ─── */
.landing-main {
  max-width: 1200px;
  margin: 0 auto;
  padding: 48px 32px;
  width: 100%;
}

/* ─── Hero Cards Grid ─── */
.cards-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 32px;
  margin-bottom: 48px;
}

.hero-card {
  color: #FFFFFF;
  padding: 40px;
  border-radius: 16px;
  position: relative;
  overflow: hidden;
  cursor: pointer;
  min-height: 300px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}
.hero-card:hover {
  transform: translateY(-4px);
}

.card-navy {
  background: #001529;
  box-shadow: 0 20px 40px -12px rgba(0, 21, 41, 0.4);
}
.card-navy:hover {
  box-shadow: 0 25px 50px -12px rgba(0, 21, 41, 0.5);
}
.card-crimson {
  background: #8B1A1A;
  box-shadow: 0 20px 40px -12px rgba(139, 26, 26, 0.4);
}
.card-crimson:hover {
  box-shadow: 0 25px 50px -12px rgba(139, 26, 26, 0.5);
}

.hero-card-content {
  position: relative;
  z-index: 1;
}
.hero-title {
  font-size: 30px;
  font-weight: 700;
  letter-spacing: -0.5px;
  margin: 0 0 16px 0;
  line-height: 1.2;
}
.hero-desc {
  color: #94a3b8;
  line-height: 1.7;
  font-size: 15px;
  max-width: 420px;
  margin: 0;
}
.hero-desc-light {
  color: rgba(255, 255, 255, 0.8);
}

.hero-card-action {
  position: relative;
  z-index: 1;
  margin-top: 32px;
}

.hero-btn {
  padding: 12px 32px;
  font-weight: 700;
  font-size: 15px;
  border-radius: 10px;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.3s;
  font-family: 'Manrope', sans-serif;
}
.hero-btn-navy {
  background: #FFFFFF;
  color: #001529;
}
.hero-btn-navy:hover {
  background: #f1f5f9;
  transform: scale(1.03);
}
.hero-btn-crimson {
  background: #FFFFFF;
  color: #8B1A1A;
}
.hero-btn-crimson:hover {
  background: #f1f5f9;
  transform: scale(1.03);
}
.hero-btn-icon {
  font-size: 18px;
}

/* Glow effect */
.hero-glow {
  position: absolute;
  right: -48px;
  bottom: -48px;
  width: 256px;
  height: 256px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 50%;
  filter: blur(48px);
  transition: background 0.3s;
}
.hero-card:hover .hero-glow {
  background: rgba(255, 255, 255, 0.1);
}
.hero-glow-dark {
  background: rgba(0, 0, 0, 0.1);
}
.hero-card:hover .hero-glow-dark {
  background: rgba(0, 0, 0, 0.2);
}

/* ─── Functional Buttons Row ─── */
.func-btns-row {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: center;
  gap: 24px;
  margin-bottom: 32px;
  flex-wrap: wrap;
}

.func-btn {
  min-width: 280px;
  padding: 20px 40px;
  border-radius: 16px;
  font-weight: 700;
  font-size: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
  font-family: 'Manrope', sans-serif;
  border: none;
}

.func-btn-outline {
  background: #FFFFFF;
  border: 1px solid #c4c6cd;
  color: #191c1d;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}
.func-btn-outline:hover {
  background: #f3f4f5;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
}

.func-btn-dark {
  background: #001529;
  color: #FFFFFF;
  box-shadow: 0 8px 24px rgba(0, 21, 41, 0.2);
}
.func-btn-dark:hover:not(:disabled) {
  background: #1e293b;
  box-shadow: 0 12px 32px rgba(0, 21, 41, 0.25);
}
.func-btn-dark:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.func-btn-icon {
  font-size: 24px;
  color: #001529;
}
.func-btn-dark .func-btn-icon {
  color: #FFFFFF;
}

.func-btn-text {
  text-align: left;
}
.func-btn-label {
  font-size: 16px;
  font-weight: 700;
}
.func-btn-sub {
  font-size: 12px;
  font-weight: 400;
  color: #43474d;
  margin-top: 2px;
}
.func-btn-sub-light {
  font-size: 12px;
  font-weight: 400;
  color: rgba(255, 255, 255, 0.6);
  margin-top: 2px;
}

/* ─── File Section ─── */
.file-section {
  background: #FFFFFF;
  border-radius: 16px;
  border: 1px solid #e1e3e4;
  padding: 24px 32px;
  margin-bottom: 32px;
}
.file-section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.file-section-header h3 {
  font-size: 16px;
  font-weight: 700;
  color: #191c1d;
  margin: 0;
}
.file-count {
  font-size: 12px;
  color: #74777d;
  background: #edeeef;
  padding: 4px 12px;
  border-radius: 20px;
  font-weight: 600;
}

.file-table {
  width: 100%;
  text-align: left;
  font-size: 13px;
  border-collapse: collapse;
}
.file-table thead th {
  color: #74777d;
  font-weight: 500;
  font-size: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid #edeeef;
}
.file-table tbody td {
  padding: 12px 0;
  border-bottom: 1px solid #f3f4f5;
}
.ft-name { font-weight: 600; color: #191c1d; }
.ft-size { color: #74777d; }
.ft-actions { text-align: right; }
.status-badge {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 9999px;
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.badge-ready { background: #acf4a4; color: #002203; }
.icon-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px;
  border-radius: 6px;
  transition: all 0.15s;
}
.icon-btn-danger { color: #74777d; }
.icon-btn-danger:hover { color: #ba1a1a; background: #ffdad6; }

/* ─── Review Canvas ─── */
.review-canvas {
  background: #f3f4f5;
  border-radius: 16px;
  border: 1px solid #e1e3e4;
  position: relative;
  overflow: hidden;
  margin-bottom: 32px;
}
.review-decor {
  position: absolute;
  right: 0; top: 0;
  width: 50%; height: 100%;
  background: radial-gradient(circle at right, rgba(196, 198, 205, 0.3), transparent);
  pointer-events: none;
}
.review-inner {
  position: relative;
  z-index: 1;
  padding: 28px 32px;
}
.review-status {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  background: rgba(77, 96, 119, 0.08);
  border: 1px solid rgba(77, 96, 119, 0.15);
  padding: 6px 14px;
  border-radius: 20px;
  color: #4d6077;
  font-size: 12px;
  font-weight: 500;
  margin-bottom: 20px;
}
.pulse-dot {
  width: 7px; height: 7px;
  background: #4d6077;
  border-radius: 50%;
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

/* 市场回顾正文 */
.market-review-text {
  font-family: 'Microsoft YaHei', '微软雅黑', 'PingFang SC', sans-serif;
  font-size: 20px;
  color: #191c1d;
  line-height: 2.0;
  text-align: justify;
}
.market-review-text :deep(p) { margin-bottom: 16px; text-indent: 2em; }
.market-review-text :deep(strong) { color: #ba1a1a; font-weight: 700; }

.cursor-blink {
  display: inline;
  animation: blink 1s step-end infinite;
  color: #4d6077;
  font-size: 16px;
}

/* ─── Global Toast ─── */
.global-toast {
  position: fixed;
  bottom: 24px; right: 24px;
  background: #001529;
  color: #FFFFFF;
  padding: 10px 22px;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 500;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
  z-index: 9999;
}

/* ─── Animations ─── */
.fade-in { animation: fadeIn 0.5s ease-out forwards; }
@keyframes fadeIn { from { opacity:0; transform:translateY(8px); } to { opacity:1; transform:translateY(0); } }
@keyframes pulse { 0%,100%{opacity:1;} 50%{opacity:.4;} }
@keyframes blink { 50%{opacity:0;} }

/* ─── Responsive ─── */
@media (max-width: 768px) {
  .cards-grid { grid-template-columns: 1fr; }
  .func-btns-row { flex-direction: column; }
  .landing-main { padding: 24px 16px; }
  .hero-card { min-height: auto; padding: 28px; }
  .func-btn { min-width: auto; width: 100%; }
}
</style>
