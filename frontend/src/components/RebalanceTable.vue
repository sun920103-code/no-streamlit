<template>
  <div v-if="result" class="fade-in" style="margin-top:24px;">
    <!-- Abstract conclusions from backend summary_text -->
    <div style="padding:16px;background:#F8FAFC;border:1px solid #E2E8F0;border-radius:8px;margin-bottom:16px;">
      <div style="color:var(--navy);font-weight:600;font-size:14px;margin-bottom:8px;">💡 配置结论摘要</div>
      <div style="font-size:13px;color:var(--text-primary);line-height:1.6;white-space:pre-wrap;">{{ result.summary_text }}</div>
    </div>
    
    <!-- Render strict API Contract 6-column instruction table -->
    <div style="overflow-x:auto;">
      <table class="holdings-table">
        <thead>
          <tr>
            <th style="width:110px;">基金代码</th>
            <th>基金名称</th>
            <th>宏观因子</th>
            <th style="text-align:center;">执行操作</th>
            <th style="text-align:right;">资金调整(元)</th>
            <th style="text-align:right;">权重变化</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in result.instructions" :key="row.code">
            <td style="font-family:'JetBrains Mono',monospace;font-weight:600;color:var(--navy);">{{ row.code }}</td>
            <td>{{ row.name }}</td>
            <td><span style="background:#EBF5FB;color:#2E86C1;padding:2px 6px;border-radius:4px;font-size:11px;">{{ row.asset_class }}</span></td>
            <td style="text-align:center;font-weight:600;" :style="{ color: getActionColor(row.action_tag) }">
              {{ getActionIcon(row.action_tag) }} {{ row.action_tag }}
            </td>
            <td style="text-align:right;font-family:'JetBrains Mono',monospace;" :style="{ color: getAmountColor(row.delta_amount) }">
              {{ row.delta_amount > 0 ? '+' : '' }}{{ Math.round(row.delta_amount).toLocaleString('zh-CN') }}
            </td>
            <td style="text-align:right;font-family:'JetBrains Mono',monospace;" :style="{ color: getAmountColor(row.delta_w) }">
              {{ row.delta_w > 0 ? '+' : '' }}{{ (row.delta_w * 100).toFixed(2) }}%
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
defineProps({
  result: {
    type: Object,
    default: null
  }
})

function getActionColor(actionTag) {
  if (actionTag.includes('减') || actionTag.includes('清')) return '#10B981'; // Green for sell
  if (actionTag.includes('加') || actionTag.includes('建')) return '#EF4444'; // Red for buy
  return '#6B7280'; // Gray for hold
}

function getActionIcon(actionTag) {
  if (actionTag.includes('减') || actionTag.includes('清')) return '🔴';
  if (actionTag.includes('加') || actionTag.includes('建')) return '🟢';
  return '⚪';
}

function getAmountColor(val) {
  if (val > 0) return '#EF4444';
  if (val < 0) return '#10B981';
  return 'var(--text-primary)';
}
</script>

<style scoped>
/* Scoped styles inherit from generic if class overrides not needed */
</style>
