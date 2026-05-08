<script setup>
import VChart from 'vue-echarts'
import { Icon } from '@iconify/vue'

const props = defineProps({
  title: { type: String, default: '' },
  option: { type: Object, required: true },
  height: { type: Number, default: 320 },
  icon: { type: String, default: 'ph:chart-line-up-duotone' },
  subtitle: { type: String, default: '' },
  regionOptions: { type: Array, default: () => [] },
  modelValue: { type: String, default: '' }
})

const emit = defineEmits(['update:modelValue'])
</script>

<template>
  <section class="glass-card chart-card">
    <header class="card-title">
      <Icon :icon="icon" />
      <div>
        <h3>{{ title }}</h3>
        <p v-if="subtitle" class="card-subtitle">{{ subtitle }}</p>
      </div>
      <select
        v-if="props.regionOptions.length"
        class="region-select"
        :value="props.modelValue"
        @change="emit('update:modelValue', $event.target.value)"
      >
        <option v-for="item in props.regionOptions" :key="item" :value="item">{{ item }}</option>
      </select>
    </header>
    <v-chart autoresize :option="option" :style="{ height: `${height}px` }" />
  </section>
</template>

<style scoped>
.chart-card {
  min-height: 240px;
  transition: transform 0.24s ease, border-color 0.24s ease;
}

.chart-card:hover {
  transform: translateY(-2px);
  border-color: rgba(41, 196, 214, 0.35);
}

.card-title {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.card-title h3 {
  margin: 0;
  font-size: 0.98rem;
}

.card-subtitle {
  margin-top: 2px;
  color: #8ea0b8;
  font-size: 0.76rem;
}

.region-select {
  margin-left: auto;
  background: rgba(15, 26, 39, 0.52);
  backdrop-filter: blur(8px);
  color: #d4e3f7;
  border: 1px solid rgba(71, 103, 133, 0.65);
  border-radius: 8px;
  padding: 5px 10px;
  font-size: 12px;
}
</style>
