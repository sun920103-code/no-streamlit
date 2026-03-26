<template>
  <router-view v-slot="{ Component }">
    <keep-alive>
      <component :is="Component" />
    </keep-alive>
  </router-view>
</template>

<script setup>
// 顶层壳 — KeepAlive 缓存所有页面组件，确保页面切换时状态保留
</script>
