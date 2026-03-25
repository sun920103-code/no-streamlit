<template>
  <div class="landing-page">
    <!-- 顶部导航栏 -->
    <div class="topbar">
      <div class="brand">
        <div class="brand-logo">粤</div>
        <div>
          <div class="brand-name">粤财信托</div>
          <div class="brand-sub">YUECAI TRUST</div>
        </div>
      </div>
      <div class="login-btn">登录账户</div>
    </div>

    <!-- Hero 区域 -->
    <div class="hero fade-in">
      <div class="inst-badge">
        <span class="diamond">◆</span>
        诚信，专业，创造价值
      </div>
      <h1>粤财信托·资产配置智能助手</h1>
      <p class="hero-sub">
        整合全球宏观视野与先进量化算法，为机构与高净值客户提供权威、精准、实时的资产配置决策支持。
      </p>
    </div>

    <!-- 两张核心业务入口卡片 (Matching Screenshot) -->
    <div class="cards-row fade-in">
      <!-- Card 1 -->
      <div class="landing-card">
        <div class="card-icon-wrap" style="background: rgba(59,130,246,0.1); color: #3B82F6;">
           <span class="icon-svg">🧭</span>
        </div>
        <h3>粤财智选资产配置</h3>
        <p class="card-desc">
          深度穿透多维宏观经济因子，为您量身构建覆盖全市场维度的多元化配置方案。基于 Black-Litterman 模型与 HRP 风控策略，实现收益最优化。
        </p>
        <button class="action-btn btn-dark" @click="enterSmartSelection">
          进入配置中心 →
        </button>
      </div>

      <!-- Card 2 -->
      <div class="landing-card">
        <div class="card-icon-wrap" style="background: rgba(225,29,72,0.1); color: #E11D48;">
           <span class="icon-svg">📈</span>
        </div>
        <h3>资产配置智能分析</h3>
        <p class="card-desc">
          上传既有持仓明细，系统自动执行穿透式诊断，反向推导您的真实风险偏好。AI 投委会实时研判经济周期与因子风向，助您运筹帷幄。
        </p>
        <button class="action-btn btn-red" @click="enterDiag">
          开始智能分析 🚀
        </button>
      </div>
    </div>

    <!-- 底部：因子特征上传与 AI 市场回顾 -->
    <div class="bottom-section fade-in">
       <!-- CSV Data Upload Block -->
       <div class="upload-card">
          <div class="upload-header">
             <div class="uh-icon">📄</div>
             <div class="uh-text">
                <h4>底层风险因子数据上传</h4>
                <p>上传最新量化因子数据，系统将提取特征做多空推演 CSV, xls, xlsx</p>
             </div>
          </div>
          
          <div class="dropzone" @click="$refs.csvInput.click()">
             <div class="dz-left">
                <span style="font-size:24px; color:#94A3B8; margin-right:16px;">☁️</span>
                <div class="dz-text">
                   <strong>Drag and drop files here</strong>
                   <span>Limit 200MB per file • CSV</span>
                </div>
             </div>
             <button class="browse-btn">Browse files</button>
             <input type="file" ref="csvInput" style="display:none" accept=".csv" @change="onCsvSelected" />
          </div>
          <div v-if="selectedCsv" style="margin-top:12px; font-size:13px; color:#10B981; font-weight:600;">
             ✓ 已选择文件: {{ selectedCsv.name }}
          </div>
       </div>

       <!-- AI Review Generation Button -->
       <div class="ai-review-actions" style="margin-top: 24px;">
         <button class="mega-ai-btn" @click="triggerReview" :disabled="isGeneratingReview">
            <span class="btn-icon">📊</span>
            {{ isGeneratingReview ? 'AI 深度阅读与撰写中...' : '开始全局文档并一键生成智能市场回顾' }}
         </button>
       </div>

       <!-- AI Review Canvas (SSE Stream) -->
       <div v-if="isReviewExpanded" class="review-canvas fade-in" style="margin-top:24px;">
          <div v-if="reviewStatus" class="review-status">
             <div class="pulse-dot"></div>
             <span>{{ reviewStatus }}</span>
          </div>
          
          <div class="markdown-preview" v-html="renderedReview"></div>
          
          <div v-if="isGeneratingReview && reviewText.length > 0" class="cursor-blink">▍</div>
       </div>
    </div>

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
const selectedCsv = ref(null)
const isReviewExpanded = ref(false)
const isGeneratingReview = ref(false)
const reviewStatus = ref('')
const reviewText = ref('')
const toastMessage = ref('')

function showToast(msg) {
  toastMessage.value = msg
  setTimeout(() => { toastMessage.value = '' }, 3000)
}

function onCsvSelected(event) {
  const file = event.target.files[0]
  if (file) {
    selectedCsv.value = file
    showToast(`文件 ${file.name} 已暂存`)
  }
}

async function triggerReview() {
  isReviewExpanded.value = true
  isGeneratingReview.value = true
  reviewStatus.value = '正在连接投委会 AI 智能体节点...'
  reviewText.value = ''
  
  try {
    const response = await fetch('http://localhost:8000/api/v1/ai/generate_market_review', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
         report_type: selectedCsv.value ? "quant_factor" : "general_macro",
         style: "professional",
         include_stock_picks: true
      })
    })

    if (!response.ok) {
       throw new Error(`请求失败: ${response.statusText}`)
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder('utf-8')
    reviewStatus.value = '大模型研报流式生成中，请不要离开页面...'

    while (true) {
      const { value, done } = await reader.read()
      if (done) break
      
      const chunk = decoder.decode(value, { stream: true })
      const lines = chunk.split('\n')
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const dataStr = line.replace('data: ', '').trim()
          if (dataStr === '[DONE]') {
            reviewStatus.value = '生成完毕！'
            isGeneratingReview.value = false
            return
          }
          if (dataStr) {
             try {
               const parsed = JSON.parse(dataStr)
               if (parsed.chunk) {
                  reviewText.value += parsed.chunk
               }
             } catch(e) { /* ignore parse errors for partial JSON */ }
          }
        }
      }
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
.landing-page {
  min-height: 100vh;
  background-color: #F8FAFC;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  padding-bottom: 60px;
}

/* 顶部导航 (Matching screenshot) */
.topbar {
  background: white;
  height: 64px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 32px;
  box-shadow: 0 1px 2px rgba(0,0,0,0.05);
  position: sticky;
  top: 0;
  z-index: 100;
}
.brand {
  display: flex;
  align-items: center;
  gap: 12px;
}
.brand-logo {
  width: 32px; height: 32px;
  background: #C81E1E;
  color: white;
  border-radius: 4px;
  display: flex;
  justify-content: center;
  align-items: center;
  font-weight: bold;
  font-size: 18px;
}
.brand-name {
  font-weight: 700;
  font-size: 16px;
  color: #111827;
  line-height: 1.2;
}
.brand-sub {
  font-size: 10px;
  color: #6B7280;
  letter-spacing: 1px;
}
.login-btn {
  background: #1F2937;
  color: white;
  padding: 8px 20px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}
.login-btn:hover { background: #111827; }

/* Hero Area */
.hero {
  text-align: center;
  padding: 60px 20px 40px;
  width: 100%;
}
.inst-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: white;
  padding: 6px 16px;
  border-radius: 20px;
  font-size: 13px;
  color: #4B5563;
  margin-bottom: 24px;
  border: 1px solid #E5E7EB;
  box-shadow: 0 2px 4px rgba(0,0,0,0.02);
}
.diamond {
  color: #F59E0B;
  font-size: 12px;
}
h1 {
  font-size: 32px;
  font-weight: 700;
  color: #111827;
  margin: 0 0 16px 0;
}
.hero-sub {
  font-size: 15px;
  color: #6B7280;
  max-width: 600px;
  margin: 0 auto;
  line-height: 1.6;
}

/* Core Cards 1:1 match with Screenshot */
.cards-row {
  max-width: 1100px;
  margin: 0 auto 32px;
  display: flex;
  gap: 24px;
  padding: 0 20px;
}
.landing-card {
  flex: 1;
  background: white;
  border-radius: 12px;
  padding: 32px;
  border: 1px solid #E5E7EB;
  box-shadow: 0 4px 6px -1px rgba(0,0,0,0.02), 0 2px 4px -1px rgba(0,0,0,0.02);
  display: flex;
  flex-direction: column;
}
.card-icon-wrap {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 24px;
  margin-bottom: 20px;
}
h3 {
  font-size: 18px;
  font-weight: 700;
  color: #111827;
  margin: 0 0 12px 0;
}
.card-desc {
  font-size: 14px;
  color: #4B5563;
  line-height: 1.6;
  margin: 0 0 24px 0;
  flex-grow: 1;
}

/* Action Buttons perfectly styled like screenshot */
.action-btn {
  width: 100%;
  padding: 14px 0;
  border-radius: 6px;
  font-size: 15px;
  font-weight: 600;
  text-align: center;
  cursor: pointer;
  border: none;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}
.btn-dark {
  background: #1E293B;
  color: white;
}
.btn-dark:hover {
  background: #0F172A;
}
.btn-red {
  background: #BE123C;
  color: white;
}
.btn-red:hover {
  background: #9F1239;
}

/* Bottom Section (Matching the file uploader) */
.bottom-section {
  max-width: 1100px;
  margin: 0 auto;
  padding: 0 20px;
}
.upload-card {
  background: white;
  border-radius: 12px;
  border: 1px solid #E5E7EB;
  box-shadow: 0 4px 6px -1px rgba(0,0,0,0.02);
  padding: 24px;
}
.upload-header {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 20px;
}
.uh-icon {
  width: 32px; height: 32px;
  background: #F1F5F9;
  border-radius: 8px;
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 16px;
}
.uh-text h4 {
  margin: 0 0 4px 0;
  font-size: 15px;
  font-weight: 700;
  color: #111827;
}
.uh-text p {
  margin: 0;
  font-size: 13px;
  color: #6B7280;
}

.dropzone {
  border: 2px dashed #E2E8F0;
  border-radius: 8px;
  padding: 20px 24px;
  background: #F8FAFC;
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  transition: all 0.2s;
}
.dropzone:hover {
  border-color: #3B82F6;
  background: #EFF6FF;
}
.dz-left {
  display: flex;
  align-items: center;
}
.dz-text strong {
  display: block;
  font-size: 14px;
  color: #1E293B;
}
.dz-text span {
  display: block;
  font-size: 12px;
  color: #94A3B8;
  margin-top: 4px;
}
.browse-btn {
  background: white;
  border: 1px solid #CBD5E1;
  border-radius: 6px;
  padding: 8px 16px;
  font-size: 13px;
  font-weight: 500;
  color: #334155;
  cursor: pointer;
}

/* AI Generate Button & Canvas */
.mega-ai-btn {
  width: 100%;
  padding: 16px;
  border-radius: 8px;
  background: linear-gradient(135deg, #1E3A8A, #3B82F6);
  color: white;
  font-size: 16px;
  font-weight: 700;
  border: none;
  cursor: pointer;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 12px;
  transition: transform 0.2s, box-shadow 0.2s;
  box-shadow: 0 10px 20px rgba(59, 130, 246, 0.2);
}
.mega-ai-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 14px 28px rgba(59, 130, 246, 0.3);
}

.review-canvas {
  background: #111827;
  border-radius: 16px;
  padding: 32px;
  color: #E5E7EB;
  text-align: left;
  line-height: 1.8;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
  margin-top: 30px;
}

.review-status {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  background: rgba(59, 130, 246, 0.1);
  border: 1px solid rgba(59, 130, 246, 0.2);
  padding: 8px 16px;
  border-radius: 20px;
  color: #60A5FA;
  font-size: 13px;
  margin-bottom: 24px;
}
.pulse-dot {
  width: 8px; height: 8px;
  background: #3B82F6;
  border-radius: 50%;
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: .5; }
}

/* Animations */
.fade-in { animation: fadeIn 0.6s ease-out forwards; }
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.global-toast {
  position: fixed;
  bottom: 24px;
  right: 24px;
  background: #1E293B;
  color: white;
  padding: 12px 24px;
  border-radius: 8px;
  box-shadow: 0 10px 25px rgba(0,0,0,0.1);
  z-index: 9999;
}
</style>
