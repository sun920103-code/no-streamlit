<template>
  <div class="fade-in">
    <div class="page-header">
      <h2>报告中心</h2>
      <p class="subtitle">市场回顾 · 投资报告 · 导出下载</p>
    </div>

    <div class="grid-3" style="margin-bottom: 28px;">
      <div class="card" v-for="t in templates" :key="t.id" style="cursor:pointer;">
        <div class="card-title">{{ t.name }}</div>
        <p style="color:var(--text-secondary);font-size:13px;margin-bottom:16px;">{{ t.description }}</p>
        <button class="btn btn-outline" style="width:100%;">
          📄 生成报告
        </button>
      </div>
    </div>

    <div class="card">
      <div class="card-title">市场回顾预览</div>
      <div style="padding:16px 0;color:var(--text-secondary);font-size:14px;line-height:1.8;">
        <p>本周市场整体呈现震荡格局，A股主要指数涨跌互现。上证指数收于 3,280 点附近，
        周涨幅 0.3%。债券市场方面，10Y 国债收益率小幅下行 2bp 至 2.28%，
        信用利差保持稳定。大宗商品中，黄金受避险情绪推动上涨 1.2%。</p>
        <p style="margin-top:12px;">宏观层面，3月 PMI 数据重返荣枯线上方，显示制造业景气度边际改善。
        信贷数据超预期，社融存量同比增长 8.7%，反映实体融资需求回暖。</p>
        <p style="margin-top:12px;color:var(--text-muted);font-style:italic;">
          ⚠️ 以上为示例文本。Phase 2 将对接 AI 大模型实时生成。
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const templates = ref([
  { id: 'full', name: '完整投资报告', description: '包含市场回顾、配置建议、风险分析' },
  { id: 'summary', name: '简要概览', description: '一页纸投资概览' },
  { id: 'risk', name: '风险报告', description: '压力测试 + 回撤分析' },
])
</script>
