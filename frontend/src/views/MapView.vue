<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import VChart from 'vue-echarts'
import { Icon } from '@iconify/vue'
import GlassChart from '../components/GlassChart.vue'
import { useDisasterData } from '../composables/useDisasterData'
import { axisCommon, chartPalette, tooltipCommon } from '../utils/chartPreset'
import { fetchRegionInsight, fetchRegions } from '../api'

const { state } = useDisasterData()
const mapReady = ref(false)
const regionOptions = ref(['全国'])
const selectedRegion = ref('全国')
const regionInsight = ref(null)
const insightLoading = ref(false)

const mapData = computed(() => (state.value?.charts?.provinceHeat || []).map((item) => ({ name: item.name, value: item.value })))
const allLoss = computed(() => [...mapData.value].sort((a, b) => b.value - a.value))
const shouldScrollRank = computed(() => allLoss.value.length > 8)
const rankTrackDuration = computed(() => `${Math.max(20, allLoss.value.length * 1.6)}s`)
const rankCarousel = computed(() => {
  if (!allLoss.value.length) return []
  return shouldScrollRank.value ? [...allLoss.value, ...allLoss.value] : allLoss.value
})

onMounted(async () => {
  try {
    const rr = await fetchRegions()
    regionOptions.value = rr.regions || ['全国']
  } catch {
    regionOptions.value = ['全国']
  }
})

onMounted(async () => {
  try {
    const res = await fetch('https://geo.datav.aliyun.com/areas_v3/bound/100000_full.json')
    const geoJson = await res.json()
    echarts.registerMap('china', geoJson)
    mapReady.value = true
  } catch {
    mapReady.value = false
  }
})

watch(
  selectedRegion,
  async (val) => {
    if (val === '全国') {
      regionInsight.value = null
      return
    }
    insightLoading.value = true
    try {
      regionInsight.value = await fetchRegionInsight(val)
    } catch {
      regionInsight.value = null
    } finally {
      insightLoading.value = false
    }
  },
  { immediate: true }
)

const mapOption = computed(() => ({
  tooltip: tooltipCommon('item'),
  visualMap: {
    min: 0,
    max: Math.max(...mapData.value.map((i) => i.value), 1000),
    text: ['高', '低'],
    textStyle: { color: '#c7d6e8' },
    calculable: true,
    inRange: { color: ['#1f3448', '#29c4d6', '#f97316'] }
  },
  series: [
    {
      name: '经济损失',
      type: 'map',
      map: 'china',
      roam: true,
      label: { color: '#b7c6d8', fontSize: 10 },
      itemStyle: { borderColor: '#35506d', areaColor: '#182434' },
      emphasis: {
        label: { color: '#fff' },
        itemStyle: { areaColor: '#f97316' }
      },
      data: mapData.value
    }
  ]
}))

const typeProbOption = computed(() => ({
  tooltip: tooltipCommon('axis'),
  grid: { left: 92, right: 20, top: 18, bottom: 20 },
  xAxis: { type: 'value', ...axisCommon('%') },
  yAxis: {
    type: 'category',
    data: (regionInsight.value?.charts?.typeProbability || []).slice(0, 8).map((i) => i.type),
    axisLabel: { color: '#c7d6e8' }
  },
  series: [
    {
      type: 'bar',
      data: (regionInsight.value?.charts?.typeProbability || []).slice(0, 8).map((i) => i.probability),
      itemStyle: { borderRadius: [0, 6, 6, 0] }
    }
  ]
}))

const yearTrendOption = computed(() => ({
  tooltip: tooltipCommon('axis'),
  color: chartPalette,
  grid: { left: 42, right: 24, top: 24, bottom: 30 },
  xAxis: {
    type: 'category',
    data: (regionInsight.value?.charts?.yearTrend || []).map((i) => i.year),
    ...axisCommon()
  },
  yAxis: { type: 'value', ...axisCommon() },
  series: [
    { name: '死亡', type: 'line', smooth: true, data: (regionInsight.value?.charts?.yearTrend || []).map((i) => i.deaths) },
    { name: '受灾', type: 'line', smooth: true, data: (regionInsight.value?.charts?.yearTrend || []).map((i) => i.affected) },
    { name: '损失', type: 'line', smooth: true, data: (regionInsight.value?.charts?.yearTrend || []).map((i) => i.loss) }
  ]
}))
</script>

<template>
  <section class="view-wrap">
    <header class="view-header">
      <h2>灾害地图</h2>
      <p>全国省域经济损失热力分布</p>
    </header>

    <div class="map-layout">
      <section class="glass-card map-main">
        <header class="map-title">
          <div>
            <h3>全国省级灾害热力图</h3>
            <p>色阶越高表示历史经济损失越高</p>
          </div>
          <Icon icon="ph:map-trifold-duotone" />
        </header>
        <div v-if="!mapReady" class="state-tip">正在加载中国地图底图...</div>
        <v-chart v-else autoresize :option="mapOption" :style="{ height: '620px' }" />
      </section>

      <aside class="glass-card map-side">
        <header class="map-title compact">
          <div>
            <h3>重点省份风险榜</h3>
            <p>按累计损失排序</p>
          </div>
          <Icon icon="ph:trophy-duotone" />
        </header>
        <div class="rank-viewport">
          <ol class="rank-list" :class="{ scrolling: shouldScrollRank }" :style="{ '--rank-scroll-duration': rankTrackDuration }">
            <li v-for="(item, idx) in rankCarousel" :key="`${item.name}-${idx}`">
              <span class="rank-no">{{ (idx % allLoss.length) + 1 }}</span>
              <span class="rank-name">{{ item.name }}</span>
              <span class="rank-val">{{ Number(item.value).toLocaleString() }}</span>
            </li>
          </ol>
        </div>

        <div class="region-card">
          <label>地区精细研判</label>
          <select v-model="selectedRegion">
            <option v-for="r in regionOptions" :key="r" :value="r">{{ r }}</option>
          </select>
          <p v-if="insightLoading">正在分析地区数据...</p>
          <template v-else-if="regionInsight">
            <p>下一年受灾概率：<strong>{{ regionInsight.prediction.nextYearRiskProbability }}%</strong></p>
            <p>高发类型：<strong>{{ regionInsight.prediction.nextYearLikelyType }}</strong></p>
            <p class="advice">{{ (regionInsight.recommendations?.government || [])[0] }}</p>
          </template>
          <p v-else>选择地区后查看详细风险评估</p>
        </div>
      </aside>
    </div>

    <div class="chart-grid two">
      <GlassChart
        title="地区灾害类型概率分布"
        icon="ph:chart-bar-duotone"
        :option="typeProbOption"
        :height="320"
        :region-options="regionOptions"
        v-model="selectedRegion"
      />
      <GlassChart
        title="地区年度灾情趋势"
        icon="ph:chart-line-up-duotone"
        :option="yearTrendOption"
        :height="320"
        :region-options="regionOptions"
        v-model="selectedRegion"
      />
    </div>
  </section>
</template>

<style scoped>
.map-layout {
  display: grid;
  grid-template-columns: 1.8fr 1fr;
  gap: 10px;
}

.map-main,
.map-side {
  min-height: 320px;
}

.map-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.map-title h3 {
  margin: 0;
  font-size: 1rem;
}

.map-title p {
  margin-top: 3px;
  color: #8ea0b8;
  font-size: 0.8rem;
}

.map-title svg {
  font-size: 1.4rem;
  color: #29c4d6;
}

.rank-list {
  margin: 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 7px;
}

.rank-viewport {
  max-height: 468px;
  overflow: hidden;
  mask-image: linear-gradient(180deg, transparent 0%, #000 6%, #000 94%, transparent 100%);
  -webkit-mask-image: linear-gradient(180deg, transparent 0%, #000 6%, #000 94%, transparent 100%);
}

.rank-list.scrolling {
  animation: rankScroll var(--rank-scroll-duration) linear infinite;
}

.rank-list.scrolling:hover {
  animation-play-state: paused;
}

.rank-list li {
  display: grid;
  grid-template-columns: 24px 1fr auto;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  border-radius: 8px;
  background: rgba(18, 28, 41, 0.44);
  backdrop-filter: blur(8px);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.08);
}

.rank-no {
  color: #8ec6d7;
}

.rank-name {
  color: #dce8f7;
}

.rank-val {
  color: #f7c37b;
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
}

.region-card {
  margin-top: 12px;
  padding-top: 10px;
  border-top: 1px solid rgba(71, 103, 133, 0.35);
}

.region-card label {
  font-size: 0.82rem;
  color: #8ea0b8;
}

.region-card select {
  width: 100%;
  margin-top: 6px;
  border: 1px solid rgba(71, 103, 133, 0.65);
  border-radius: 8px;
  background: rgba(11, 20, 31, 0.5);
  backdrop-filter: blur(8px);
  color: #d4e3f7;
  padding: 7px 9px;
}

.region-card p {
  font-size: 0.84rem;
  color: #b8cde6;
  margin-top: 8px;
  line-height: 1.6;
}

.region-card .advice {
  color: #dce8f7;
}

@keyframes rankScroll {
  0% {
    transform: translateY(0);
  }
  100% {
    transform: translateY(-50%);
  }
}

@media (max-width: 1180px) {
  .map-layout {
    grid-template-columns: 1fr;
  }
}
</style>
