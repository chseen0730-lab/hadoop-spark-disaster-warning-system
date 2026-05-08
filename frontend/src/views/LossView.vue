<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import GlassChart from '../components/GlassChart.vue'
import { useDisasterData } from '../composables/useDisasterData'
import { areaGradient, axisCommon, chartPalette, tooltipCommon } from '../utils/chartPreset'
import { fetchRegionInsight, fetchRegions } from '../api'

const { state } = useDisasterData()
const selectedRegion = ref('全国')
const regionOptions = ref(['全国'])
const regionalCharts = ref(null)

onMounted(async () => {
  try {
    const regionResp = await fetchRegions()
    regionOptions.value = regionResp.regions || ['全国']
  } catch {
    regionOptions.value = ['全国']
  }
})

watch(selectedRegion, async (val) => {
  if (val === '全国') {
    regionalCharts.value = null
    return
  }
  try {
    const data = await fetchRegionInsight(val)
    regionalCharts.value = data.charts
  } catch {
    regionalCharts.value = null
  }
})

const cropTrend = computed(() => regionalCharts.value?.cropTrend || state.value?.charts?.cropTrend || [])
const houseDamage = computed(() => regionalCharts.value?.houseDamageStack || state.value?.charts?.houseDamageStack || [])
const casualtyRose = computed(() => regionalCharts.value?.casualtyRose || state.value?.charts?.casualtyRose || [])

const areaOption = computed(() => ({
  tooltip: tooltipCommon('axis'),
  grid: { left: 42, right: 24, top: 22, bottom: 30 },
  xAxis: { type: 'category', data: cropTrend.value.map((i) => i.year), ...axisCommon() },
  yAxis: { type: 'value', ...axisCommon('千公顷') },
  series: [
    {
      name: '受灾面积',
      type: 'line',
      smooth: true,
      data: cropTrend.value.map((i) => i.value),
      areaStyle: { color: areaGradient() },
      itemStyle: { color: '#29c4d6' }
    }
  ]
}))

const stackOption = computed(() => ({
  tooltip: tooltipCommon('axis'),
  legend: { bottom: 6, left: 'center', textStyle: { color: '#b8c8dd' } },
  color: chartPalette,
  grid: { left: 42, right: 24, top: 34, bottom: 58 },
  xAxis: { type: 'category', data: houseDamage.value.map((i) => i.year), ...axisCommon() },
  yAxis: { type: 'value', ...axisCommon('户') },
  series: [
    { name: '倒塌', type: 'bar', stack: 'house', data: houseDamage.value.map((i) => i.collapse), itemStyle: { color: '#ef4444' } },
    { name: '严重', type: 'bar', stack: 'house', data: houseDamage.value.map((i) => i.serious), itemStyle: { color: '#f97316' } },
    { name: '中等', type: 'bar', stack: 'house', data: houseDamage.value.map((i) => i.secondary), itemStyle: { color: '#f59e0b' } },
    { name: '轻微', type: 'bar', stack: 'house', data: houseDamage.value.map((i) => i.minor), itemStyle: { color: '#fde68a' } }
  ]
}))

const roseOption = computed(() => ({
  tooltip: tooltipCommon('item'),
  legend: { type: 'scroll', orient: 'vertical', right: 8, top: 'middle', textStyle: { color: '#b8c8dd', fontSize: 11 } },
  color: chartPalette,
  series: [
    {
      type: 'pie',
      roseType: 'area',
      radius: [20, 120],
      center: ['38%', '52%'],
      itemStyle: { borderRadius: 6 },
      data: casualtyRose.value
    }
  ]
}))
</script>

<template>
  <section class="view-wrap">
    <header class="view-header">
      <h2>损失统计</h2>
      <p>聚焦经济损失、房屋损伤与伤亡结构</p>
    </header>

    <div class="chart-grid two">
      <GlassChart title="受灾趋势面积" icon="ph:plant-duotone" :option="areaOption" :height="360" :region-options="regionOptions" v-model="selectedRegion" />
      <GlassChart title="房屋损失" icon="ph:house-line-duotone" :option="stackOption" :height="360" :region-options="regionOptions" v-model="selectedRegion" />
    </div>
    <div class="chart-grid one">
      <GlassChart title="损失惨重占比" icon="ph:flower-lotus-duotone" :option="roseOption" :height="420" :region-options="regionOptions" v-model="selectedRegion" />
    </div>
  </section>
</template>
