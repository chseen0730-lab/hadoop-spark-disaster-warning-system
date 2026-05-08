<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import GlassChart from '../components/GlassChart.vue'
import { useDisasterData } from '../composables/useDisasterData'
import { axisCommon, chartPalette, tooltipCommon } from '../utils/chartPreset'
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

const yearTrend = computed(() => regionalCharts.value?.yearTrend || state.value?.charts?.yearTrend || [])
const monthHeat = computed(() => regionalCharts.value?.monthHeat || state.value?.charts?.monthHeat || [])
const populationVsLoss = computed(() => regionalCharts.value?.populationVsLoss || state.value?.charts?.populationVsLoss || [])

const trendOption = computed(() => ({
  tooltip: tooltipCommon('axis'),
  legend: { bottom: 8, left: 'center', textStyle: { color: '#b8c8dd' } },
  color: chartPalette,
  grid: { left: 44, right: 24, top: 32, bottom: 64 },
  xAxis: { type: 'category', data: yearTrend.value.map((i) => i.year), ...axisCommon() },
  yAxis: { type: 'value', ...axisCommon() },
  series: [
    { name: '死亡', type: 'line', smooth: true, symbolSize: 6, data: yearTrend.value.map((i) => i.deaths) },
    { name: '受灾', type: 'line', smooth: true, symbolSize: 6, data: yearTrend.value.map((i) => i.affected) },
    { name: '损失', type: 'line', smooth: true, symbolSize: 6, data: yearTrend.value.map((i) => i.loss) }
  ]
}))

const monthHeatOption = computed(() => ({
  tooltip: tooltipCommon(),
  grid: { left: 20, right: 20, top: 20, bottom: 24 },
  xAxis: { type: 'category', data: monthHeat.value.map((i) => `${i.month}月`), axisLabel: { color: '#c7d6e8' } },
  yAxis: { type: 'category', data: ['事件频次'], axisLabel: { color: '#c7d6e8' } },
  visualMap: { min: 0, max: Math.max(...monthHeat.value.map((i) => i.count), 1), show: false, inRange: { color: ['#22364d', '#29c4d6', '#f97316'] } },
  series: [
    {
      type: 'heatmap',
      data: monthHeat.value.map((i, idx) => [idx, 0, i.count]),
      label: { show: true, color: '#eaf2ff', fontWeight: 600 }
    }
  ]
}))

const bubbleOption = computed(() => ({
  tooltip: tooltipCommon('item'),
  grid: { left: 56, right: 26, top: 26, bottom: 40 },
  xAxis: { type: 'value', ...axisCommon('受灾人口') },
  yAxis: { type: 'value', ...axisCommon('经济损失(万元)') },
  series: [
    {
      type: 'scatter',
      symbolSize: (val) => Math.max(18, Math.sqrt((val[2] || 0) + 1) * 4.4),
      itemStyle: { color: '#29c4d6', opacity: 0.8, shadowColor: 'rgba(41,196,214,0.45)', shadowBlur: 12 },
      data: populationVsLoss.value.map((i) => [i.affected, i.loss, 1, i.name])
    }
  ]
}))
</script>

<template>
  <section class="view-wrap">
    <header class="view-header">
      <h2>趋势分析</h2>
      <p>按年、按月识别灾情周期规律与损失联动</p>
    </header>
    <div class="chart-grid two">
      <GlassChart title="历年灾情趋势折线" icon="ph:chart-line-up-duotone" :option="trendOption" :height="360" :region-options="regionOptions" v-model="selectedRegion" />
      <GlassChart title="月度灾害频次热力" icon="ph:calendar-blank-duotone" :option="monthHeatOption" :height="360" :region-options="regionOptions" v-model="selectedRegion" />
    </div>
    <div class="chart-grid one">
      <GlassChart title="受灾人口 vs 经济损失 气泡图" icon="ph:bubbles-duotone" :option="bubbleOption" :height="360" :region-options="regionOptions" v-model="selectedRegion" />
    </div>
  </section>
</template>
