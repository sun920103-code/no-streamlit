<template>
  <button :class="computedClass" :disabled="isPending || disabled" @click="handleClick">
    <span v-if="isPending" class="spinner"></span>
    <slot>{{ text }}</slot>
  </button>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  /** The async function to execute when clicked (e.g. an API call from generated.js) */
  action: {
    type: Function,
    required: true,
  },
  /** Parameters to pass to the action function */
  params: {
    type: [Object, Array, String, Number, Boolean],
    default: null,
  },
  /** Default button text if no slot content is provided */
  text: {
    type: String,
    default: 'Submit',
  },
  /** Disabled state override */
  disabled: {
    type: Boolean,
    default: false,
  },
  /** Button style variant: primary, default, danger */
  type: {
    type: String,
    default: 'primary', 
  }
})

// Loading state
const isPending = ref(false)

const computedClass = computed(() => {
  return [
    'async-button',
    `btn-${props.type}`,
    { 'is-loading': isPending.value }
  ]
})

const emit = defineEmits(['success', 'error', 'click'])

const handleClick = async (event) => {
  if (isPending.value || props.disabled) return
  
  emit('click', event)
  isPending.value = true
  
  try {
    // If params is explicitly provided as an object, pass it. 
    // Otherwise call the action without args.
    const res = await (props.params !== null ? props.action(props.params) : props.action())
    emit('success', res)
    
    // You can integrate global toast notifications here
    // e.g., ElMessage.success('操作成功') 
  } catch (error) {
    console.error('Action Failed:', error)
    emit('error', error)
    
    let errorMsg = error.response?.data?.detail || error.response?.data?.message || error.message || '未知错误'
    
    // If FastAPI returns a 422 validation array or an object, convert it to string
    if (typeof errorMsg === 'object') {
      errorMsg = JSON.stringify(errorMsg, null, 2)
    }
    
    alert(`请求失败:\n${errorMsg}`)
  } finally {
    isPending.value = false
  }
}
</script>

<style scoped>
.async-button {
  padding: 8px 16px;
  border-radius: 4px;
  border: 1px solid transparent;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-weight: 500;
  transition: all 0.2s ease;
  font-size: 14px;
  line-height: 1.5;
}

.async-button:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

/* Primary Button */
.btn-primary {
  background-color: #3b82f6; /* Tailwind blue-500 */
  color: white;
}
.btn-primary:hover:not(:disabled) {
  background-color: #2563eb;
}

/* Default/Ghost Button */
.btn-default {
  background-color: #f3f4f6;
  color: #1f2937;
  border-color: #d1d5db;
}
.btn-default:hover:not(:disabled) {
  background-color: #e5e7eb;
}

/* Danger Button */
.btn-danger {
  background-color: #ef4444; /* Tailwind red-500 */
  color: white;
}
.btn-danger:hover:not(:disabled) {
  background-color: #dc2626;
}

/* Simple CSS Spinner */
.spinner {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255, 255, 255, 0.4);
  border-top-color: currentColor; /* Matches text color */
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  flex-shrink: 0;
}

.btn-default .spinner {
  border: 2px solid rgba(0, 0, 0, 0.2);
  border-top-color: currentColor;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
