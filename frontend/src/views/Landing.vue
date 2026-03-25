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
    <div class="hero fade-in" :class="{ 'hero-expanded': isReviewExpanded }">
      <div class="inst-badge">
        <span class="diamond">◆</span>
        诚信，专业，创造价值
      </div>
      <h1>粤财信托·资产配置智能助手</h1>
      <p class="hero-sub">
        整合全球宏观视野与先进量化算法，为机构与高净值客户提供权威、精准、实时的资产配置决策支持。
      </p>

      <!-- AI 市场回顾核心入口 (Campaign 8) -->
      <div class="ai-review-section">
        <div class="ai-review-actions">
           <button class="mega-ai-btn" @click="triggerReview" :disabled="isGeneratingReview">
              <span class="btn-icon">✨</span>
              {{ isGeneratingReview ? 'AI 深度阅读与撰写中...' : '分析最新文档并一键生成市场回顾' }}
           </button>
           <button class="upload-btn" @click="$refs.csvInput.click()" title="[可选] 附加量化因子 CSV">
              📎
           </button>
           <input type="file" ref="csvInput" style="display:none" accept=".csv" @change="onCsvSelected" />
           <span v-if="selectedCsv" class="csv-name">{{ selectedCsv.name }}</span>
        </div>

        <div v-if="isReviewExpanded" class="review-canvas fade-in">
           <div v-if="reviewStatus" class="review-status">
              <div class="pulse-dot"></div>
              <span>{{ reviewStatus }}</span>
           </div>
           
           <div class="markdown-preview" v-html="renderedReview"></div>
           
           <div v-if="isGeneratingReview && reviewText.length > 0" class="cursor-blink">▍</div>
        </div>
      </div>
    </div>

    <!-- 两张业务入口卡片 -->
    <div class="cards-row fade-in fade-in-delay-1">
      <div class="landing-card" @click="enterYueCai">
        <div class="card-icon-wrap card-icon-yc">📊</div>
        <h3>粤财智选资产配置</h3>
        <p class="card-desc">
          深度穿透多维宏观经济因子，为您量身构建覆盖全市场维度的多元化配置方案。
          基于 Black-Litterman 模型与 HRP 风险均衡策略，实现收益最优化。
        </p>
        <div class="card-features">
          ✦ 宏观因子精选池 · 多模型集成研报增强<br/>
          ✦ Black-Litterman 主客观融合<br/>
          ✦ HRP 均衡风控 · EGARCH 波动率建模
        </div>
        <div class="landing-btn landing-btn-yc">进入智选配置平台 →</div>
      </div>

      <div class="landing-card" @click="enterDiag">
        <div class="card-icon-wrap card-icon-aa">🩺</div>
        <h3>智能分析与诊断</h3>
        <p class="card-desc">
          上传既有持仓明细，系统自动执行穿透式诊断，识别结构性风险并输出优化建议。
          AI 投委会实时研判经济周期与因子风向。
        </p>
        <div class="card-features">
          ✦ CSV 持仓穿透分析 · Wind 实时数据<br/>
          ✦ 因子归因与风险贡献<br/>
          ✦ 三方案对比 · 智能调仓指令
        </div>
        <div class="landing-btn landing-btn-aa">进入智能分析平台 →</div>
      </div>
    </div>

    <!-- 第三张业务入口卡片 (Smart Selection) -->
    <div class="cards-row-bottom fade-in fade-in-delay-1" style="max-width: 960px; margin: 0 auto 32px; padding: 0 32px;">
      <div class="landing-card card-full-width" @click="enterSmartSelection">
        <div class="card-icon-wrap card-icon-smart">🧠</div>
        <h3>智选平台 (Smart Selection)</h3>
        <p class="card-desc">
          基于宏观经济时钟 (EDB) 与多角色虚拟投研会 (Multi-Agent Debate) 构建的纯粹大模型复合中枢。
          自动检索宏观数据并开启多空辩论，自上而下得出靶向资产比例，一键智能完成底层公募实盘匹配。
        </p>
        <div class="card-features">
          ✦ EDB宏观特征自适应 · 虚拟长驻投研会 (SSE)<br/>
          ✦ 资产大类自上而下派发<br/>
          ✦ 海量实体基金底仓智能映射筛选
        </div>
        <div class="landing-btn landing-btn-smart">进入智选宏观决策平台 →</div>
      </div>
    </div>

    <!-- 底部版权 -->
    <div class="footer fade-in fade-in-delay-2">
      <div class="footer-links">
        <a href="#">技术规格</a>
        <a href="#">风险披露</a>
        <a href="#">合规体系</a>
        <a href="#">联系我们</a>
      </div>
      <p>© 2026 粤财信托 · Powered by Antigravity</p>
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
import MarkdownIt from 'markdown-it'

const router = useRouter()

function enterYueCai() {
  router.push('/yc')
}

function enterDiag() {
  router.push('/diag')
}

function enterSmartSelection() {
  router.push('/smart')
}

// ── Campaign 8: Market Review Logic ──
const isReviewExpanded = ref(false)
const isGeneratingReview = ref(false)
const reviewStatus = ref('')
const reviewText = ref('')
const selectedCsv = ref(null)
const csvInput = ref(null)

const toastMessage = ref('')
let toastTimer = null

const mdParser = new MarkdownIt()
const renderedReview = computed(() => {
  return reviewText.value ? mdParser.render(reviewText.value) : ''
})

function showToast(msg) {
  toastMessage.value = msg
  if (toastTimer) clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { toastMessage.value = '' }, 3000)
}

function onCsvSelected(e) {
  if (e.target.files && e.target.files.length > 0) {
    selectedCsv.value = e.target.files[0]
  }
}

async function triggerReview() {
  if (isGeneratingReview.value) return;
  
  isReviewExpanded.value = true;
  isGeneratingReview.value = true;
  reviewText.value = '';
  reviewStatus.value = '系统初始化，预热多智能体引擎...';
  
  try {
    const formData = new FormData()
    if (selectedCsv.value) {
      formData.append('file', selectedCsv.value)
    }

    const response = await fetch('http://localhost:8000/api/v1/ai/generate_market_review', {
      method: 'POST',
      body: formData // No Content-Type header needed for FormData!
    });
    
    if (!response.body) throw new Error("ReadableStream not supported by browser.");

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
               reviewStatus.value = parsed.content;
            } else if (parsed.type === 'start_stream') {
               reviewStatus.value = ''; // 隐藏状态，专心打字
            } else if (parsed.type === 'stream_chunk') {
               reviewText.value += parsed.content;
            } else if (parsed.type === 'finish_stream' || parsed.type === 'finish') {
               // 完成
            } else if (parsed.type === 'error') {
               throw new Error(parsed.content);
            }
          } catch(e) {
             console.error("SSE parse error", e);
          }
        }
      }
    }
    
    showToast("✅ 报告生成完毕！");
  } catch(e) {
    reviewText.value += "\n\n**生成过程发生异常**: " + e.message;
  } finally {
    isGeneratingReview.value = false;
    reviewStatus.value = '';
  }
}
</script>

<style scoped>
.landing-page {
  min-height: 100vh;
  background: #FAFBFC;
}

/* ── Topbar ── */
.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 32px;
  background: #FFFFFF;
  border-bottom: 1px solid #F0F0F0;
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
}

.brand-logo {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  background: linear-gradient(135deg, #1A2A40 0%, #2C3E50 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #C8A97E;
  font-weight: 800;
  font-size: 18px;
}

.brand-name {
  font-size: 18px;
  font-weight: 700;
  color: #1A2A40;
  letter-spacing: 1px;
}

.brand-sub {
  font-size: 10px;
  color: #999;
  font-weight: 400;
  letter-spacing: 2px;
  text-transform: uppercase;
  margin-top: -2px;
}

.login-btn {
  padding: 8px 20px;
  border-radius: 6px;
  background: #1A2A40;
  color: #FFF;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.login-btn:hover {
  background: #2C4A6E;
  box-shadow: 0 2px 8px rgba(26,42,64,0.2);
}

.hero {
  text-align: center;
  padding: 60px 20px 40px;
  background: linear-gradient(180deg, #FAFBFC 0%, #F5F7FA 100%);
  transition: padding 0.5s ease;
}
.hero-expanded {
  padding-bottom: 80px;
}

.inst-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 20px;
  border-radius: 20px;
  background: #F8F9FA;
  border: 1px solid #E8E8E8;
  font-size: 10px;
  font-weight: 600;
  color: #666;
  letter-spacing: 3px;
  text-transform: uppercase;
  margin-bottom: 24px;
}

.diamond {
  color: #C8A97E;
  font-size: 12px;
}

.hero h1 {
  font-size: 36px;
  font-weight: 800;
  color: #1A2A40;
  margin: 0 0 16px;
  line-height: 1.3;
  letter-spacing: 1px;
}

.hero-sub {
  font-size: 15px;
  color: #6B7B8D;
  line-height: 1.8;
  max-width: 600px;
  margin: 0 auto;
}

/* ── AI Market Review ── */
.ai-review-section {
  max-width: 800px;
  margin: 32px auto 0;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.ai-review-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
}

.mega-ai-btn {
  background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%);
  border: none;
  border-radius: 30px;
  padding: 14px 40px;
  color: white;
  font-size: 16px;
  font-weight: 700;
  letter-spacing: 1px;
  cursor: pointer;
  box-shadow: 0 8px 20px rgba(99,102,241,0.3);
  transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
  display: flex;
  align-items: center;
  gap: 10px;
}
.mega-ai-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 12px 28px rgba(99,102,241,0.4);
}
.mega-ai-btn:disabled {
  opacity: 0.8;
  cursor: wait;
}
.btn-icon { font-size: 20px; }

.upload-btn {
  background: #FFF;
  border: 1px dashed #CBD5E1;
  border-radius: 50%;
  width: 48px;
  height: 48px;
  font-size: 18px;
  cursor: pointer;
  color: #64748B;
  transition: all 0.2s;
}
.upload-btn:hover { border-color: #8B5CF6; color: #8B5CF6; background: #F5F3FF; }

.csv-name {
  font-size: 12px;
  color: #10B981;
  background: #D1FAE5;
  padding: 4px 10px;
  border-radius: 12px;
  max-width: 150px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.review-canvas {
  width: 100%;
  background: white;
  border-radius: 16px;
  padding: 32px;
  text-align: left;
  box-shadow: 0 10px 40px rgba(0,0,0,0.08);
  border: 1px solid #E2E8F0;
  position: relative;
  min-height: 200px;
}

.review-status {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: #F8FAFC;
  border-radius: 20px;
  font-size: 13px;
  color: #475569;
  border: 1px solid #E2E8F0;
  margin-bottom: 24px;
}

.pulse-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #10B981;
  box-shadow: 0 0 0 0 rgba(16,185,129,0.7);
  animation: pulse 1.5s infinite;
}
@keyframes pulse {
  0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16,185,129, 0.7); }
  70% { transform: scale(1); box-shadow: 0 0 0 6px rgba(16,185,129, 0); }
  100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16,185,129, 0); }
}

.markdown-preview {
  font-size: 15px;
  line-height: 1.8;
  color: #1E293B;
}
.markdown-preview :deep(h1) { font-size: 24px; margin-bottom: 16px; color: #0F172A; }
.markdown-preview :deep(h2) { font-size: 20px; margin: 24px 0 12px; color: #1E293B; border-bottom: 1px solid #E2E8F0; padding-bottom: 8px; }
.markdown-preview :deep(h3) { font-size: 17px; margin: 20px 0 10px; }
.markdown-preview :deep(p) { margin-bottom: 16px; }
.markdown-preview :deep(ul), .markdown-preview :deep(ol) { margin-bottom: 16px; padding-left: 20px; }
.markdown-preview :deep(li) { margin-bottom: 6px; }
.markdown-preview :deep(strong) { color: #8B5CF6; }
.markdown-preview :deep(blockquote) { border-left: 4px solid #CBD5E1; padding-left: 16px; color: #64748B; background:#F8FAFC; padding-top:8px; padding-bottom:8px;}

.cursor-blink {
  display: inline-block;
  width: 8px;
  height: 18px;
  background: #10B981;
  animation: blinky 1s step-end infinite;
  vertical-align: middle;
  margin-left: 4px;
}
@keyframes blinky { 50% { opacity: 0; } }

.global-toast {
  position: fixed;
  bottom: 40px;
  left: 50%;
  transform: translateX(-50%);
  background: #10B981;
  color: white;
  padding: 12px 24px;
  border-radius: 30px;
  font-weight: 600;
  box-shadow: 0 10px 25px rgba(16,185,129,0.3);
  z-index: 9999;
}

/* ── Cards Row ── */
.cards-row {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 24px;
  max-width: 960px;
  margin: 32px auto;
  padding: 0 32px;
}

.landing-card {
  background: #FFFFFF;
  border-radius: 12px;
  border: 1px solid #EBEBEB;
  padding: 32px 28px 24px;
  min-height: 300px;
  transition: box-shadow 0.3s ease, border-color 0.3s ease;
  display: flex;
  flex-direction: column;
  cursor: pointer;
}

.landing-card:hover {
  box-shadow: 0 4px 24px rgba(0,0,0,0.06);
  border-color: #D0D0D0;
}

.card-icon-wrap {
  width: 48px;
  height: 48px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 20px;
  font-size: 20px;
}

.card-icon-yc { background: #EEF2F7; }
.card-icon-aa { background: #FDF2F2; }
.card-icon-smart { background: #F3E8FF; }

.card-full-width {
  width: 100%;
}

.landing-card h3 {
  font-size: 20px;
  font-weight: 700;
  color: #1A2A40;
  margin: 0 0 12px;
  letter-spacing: 0.3px;
}

.card-desc {
  font-size: 14px;
  color: #6B7B8D;
  line-height: 1.8;
  margin: 0;
}

.card-features {
  font-size: 13px;
  color: #8C8C8C;
  line-height: 1.7;
  margin-top: 12px;
  flex: 1;
}

.landing-btn {
  display: block;
  width: 100%;
  padding: 14px 0;
  border-radius: 8px;
  cursor: pointer;
  font-size: 15px;
  font-weight: 600;
  margin-top: 24px;
  text-align: center;
  letter-spacing: 1px;
  transition: all 0.25s ease;
}

.landing-btn-yc {
  background: #1A2A40;
  color: #FFFFFF;
}
.landing-btn-yc:hover { background: #243B55; box-shadow: 0 4px 16px rgba(26,42,64,0.25); }

.landing-btn-aa {
  background: #C41E3A;
  color: #FFFFFF;
}
.landing-btn-aa:hover { background: #9A1033; box-shadow: 0 4px 16px rgba(196,30,58,0.3); }

.landing-btn-smart {
  background: #8B5CF6;
  color: #FFFFFF;
}
.landing-btn-smart:hover { background: #6D28D9; box-shadow: 0 4px 16px rgba(139,92,246,0.3); }

/* ── Footer ── */
.footer {
  text-align: center;
  padding: 20px 0 24px;
}

.footer-links {
  padding: 20px 0 8px;
  border-top: 1px solid #EBEBEB;
  margin-top: 8px;
}

.footer-links a {
  color: #8C8C8C;
  font-size: 12px;
  text-decoration: none;
  margin: 0 16px;
  font-weight: 400;
  transition: color 0.2s ease;
}

.footer-links a:hover { color: #1A2A40; }

.footer p {
  color: #B0B8C4;
  font-size: 11px;
  margin-top: 8px;
}

@media (max-width: 768px) {
  .cards-row { grid-template-columns: 1fr; }
  .hero h1 { font-size: 24px; }
}
</style>
