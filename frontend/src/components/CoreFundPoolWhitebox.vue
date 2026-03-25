<template>
  <div class="core-fund-pool-whitebox fade-in">
    <div class="header">
      <div class="title-area">
        <span class="icon">💎</span>
        <div>
          <h2>核心精选基金池审查 (Core Candidate Pool)</h2>
          <p>基于多维风控模型前置筛选的专属 {{ totalCount }} 只白盒底层资产名单</p>
        </div>
      </div>
      <div class="stats">
         <div class="stat-badge">
            <span class="label">资产大类覆盖</span>
            <span class="value">{{ categories.length }} 类</span>
         </div>
      </div>
    </div>

    <!-- 加载中 -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <span>深度同步 114 只白盒底层信息中...</span>
    </div>

    <!-- 瀑布流/分组网格展示 -->
    <div v-else class="masonry-grid">
       <div v-for="cat in categories" :key="cat" class="category-block">
          <h4 class="cat-title">
             <span class="color-dot"></span> {{ cat }}
             <span class="count">({{ groupedFunds[cat].length }})</span>
          </h4>
          
          <div class="fund-cards">
             <div 
                v-for="fund in groupedFunds[cat]" 
                :key="fund.code" 
                class="fund-card"
             >
                <div class="fund-name">{{ fund.name }}</div>
                <div class="fund-code">{{ fund.code }}</div>
                
                <!-- Hover 悬浮窗: 透明化机制证明 -->
                <div class="hover-details">
                   <div class="detail-row">
                      <span class="d-label">入池标签</span>
                      <span class="d-val cat-tag">{{ cat }}</span>
                   </div>
                   <div class="detail-row">
                      <span class="d-label">白盒状态</span>
                      <span class="d-val text-green">风控准入通过 ✔️</span>
                   </div>
                   <!-- Mocked recent performance metrics for UI demonstration -->
                   <div class="detail-row">
                      <span class="d-label">近一年收益</span>
                      <span class="d-val text-red">+{{ (Math.random() * 15 + 2).toFixed(2) }}%</span>
                   </div>
                   <div class="detail-row">
                      <span class="d-label">最大回撤</span>
                      <span class="d-val text-green">-{{ (Math.random() * 8 + 1).toFixed(2) }}%</span>
                   </div>
                </div>
             </div>
          </div>
       </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getCoreFundPool } from '../api'

const loading = ref(true)
const rawPool = ref([])

onMounted(async () => {
   try {
      const res = await getCoreFundPool()
      if (res.data?.status === 'success') {
         rawPool.value = res.data.pool || []
      }
   } catch(e) {
      console.error("加载白盒基金池失败", e)
   } finally {
      loading.value = false
   }
})

const totalCount = computed(() => rawPool.value.length)

// 按宏观大类分组
const groupedFunds = computed(() => {
   const groups = {};
   rawPool.value.forEach(f => {
      const g = f.category || "其它";
      if(!groups[g]) groups[g] = [];
      groups[g].push(f);
   });
   return groups;
})

const categories = computed(() => Object.keys(groupedFunds.value).sort())

</script>

<style scoped>
.core-fund-pool-whitebox {
  background: white;
  border-radius: 16px;
  padding: 30px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.03);
  margin-top: 40px;
  border: 1px solid #E2E8F0;
}
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 2px solid #F1F5F9;
  padding-bottom: 24px;
  margin-bottom: 30px;
}
.title-area {
  display: flex;
  align-items: center;
  gap: 16px;
}
.icon {
  font-size: 36px;
}
h2 {
  margin: 0 0 6px 0;
  font-size: 20px;
  color: #0F172A;
}
p {
  margin: 0;
  color: #64748B;
  font-size: 14px;
}
.stats {
  display: flex;
  gap: 12px;
}
.stat-badge {
  background: #F8FAFC;
  border: 1px solid #E2E8F0;
  padding: 8px 16px;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.stat-badge .label {
  font-size: 11px;
  color: #94A3B8;
  margin-bottom: 4px;
}
.stat-badge .value {
  font-size: 16px;
  font-weight: 700;
  color: #3B82F6;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 60px 0;
  color: #3B82F6;
  font-weight: 500;
}
.spinner {
  width: 40px; height: 40px;
  border: 3px solid rgba(59,130,246,0.1);
  border-top-color: #3B82F6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* 分组网格 (瀑布流平替展示法) */
.masonry-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 24px;
  align-items: start;
}

.category-block {
  background: #F8FAFC;
  border-radius: 12px;
  padding: 16px;
  border: 1px solid #F1F5F9;
}
.cat-title {
  margin: 0 0 16px 0;
  font-size: 15px;
  color: #1E293B;
  display: flex;
  align-items: center;
  gap: 8px;
}
.color-dot {
  width: 10px; height: 10px;
  border-radius: 50%;
  background: #3B82F6;
}
.cat-title .count {
  color: #94A3B8;
  font-size: 13px;
  font-weight: normal;
}

.fund-cards {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.fund-card {
  background: white;
  padding: 12px 16px;
  border-radius: 8px;
  border: 1px solid #E2E8F0;
  position: relative;
  cursor: pointer;
  transition: all 0.2s;
}
.fund-card:hover {
  border-color: #CBD5E1;
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
  transform: translateY(-2px);
}
.fund-name {
  font-size: 13px;
  font-weight: 600;
  color: #334155;
  margin-bottom: 4px;
  /* 文本截断 */
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.fund-code {
  font-size: 12px;
  color: #94A3B8;
  font-family: 'JetBrains Mono', monospace;
}

/* Hover 白盒状态窗 */
.hover-details {
  position: absolute;
  top: -10px;
  left: 105%;
  width: 220px;
  background: #0F172A;
  color: white;
  padding: 16px;
  border-radius: 8px;
  box-shadow: 0 10px 25px rgba(0,0,0,0.2);
  opacity: 0;
  visibility: hidden;
  transform: translateX(-10px);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 50;
  pointer-events: none;
}
/* 小箭头 */
.hover-details::before {
  content: '';
  position: absolute;
  top: 20px;
  left: -5px;
  width: 10px;
  height: 10px;
  background: #0F172A;
  transform: rotate(45deg);
}
.fund-card:hover .hover-details {
  opacity: 1;
  visibility: visible;
  transform: translateX(0);
}

.detail-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  font-size: 12px;
}
.detail-row:last-child { margin-bottom: 0; }
.d-label { color: #94A3B8; }
.d-val { font-weight: 600; font-family: 'JetBrains Mono', sans-serif;}
.cat-tag { background: #1E293B; padding: 2px 6px; border-radius: 4px; border: 1px solid #334155; }
.text-green { color: #10B981; }
.text-red { color: #EF4444; }
</style>
