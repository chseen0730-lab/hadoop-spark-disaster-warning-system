<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Icon } from '@iconify/vue'
import GlassChart from '../components/GlassChart.vue'
import { useDisasterData } from '../composables/useDisasterData'
import { areaGradient, axisCommon, barGradient, chartPalette, tooltipCommon } from '../utils/chartPreset'
import { fetchRegions } from '../api'

const { state, loading, error } = useDisasterData()
const router = useRouter()
const regionQuery = ref('')
const regionOptions = ref([])

onMounted(async () => {
  try {
    const regions = await fetchRegions()
    regionOptions.value = regions.regions || []
  } catch {
    regionOptions.value = []
  }
})

const kpi = computed(() => state.value?.kpi || {})
const donutData = computed(() => state.value?.charts?.eventClassify || [])
const yearTrend = computed(() => state.value?.charts?.yearTrend || [])
const lossTop10 = computed(() => state.value?.charts?.lossTop10 || [])

const donutOption = computed(() => ({
  backgroundColor: 'transparent',
  tooltip: tooltipCommon('item'),
  color: chartPalette,
  series: [
    {
      type: 'pie',
      radius: ['44%', '70%'],
      center: ['50%', '52%'],
      itemStyle: { borderRadius: 6, borderColor: 'rgba(185, 206, 232, 0.32)', borderWidth: 1.5 },
      label: { color: '#c7d6e8', formatter: '{b|{b}}\n{c|{c}}', rich: { b: { color: '#dce8f7' }, c: { color: '#8ea0b8' } } },
      data: donutData.value
    }
  ]
}))

const trendOption = computed(() => ({
  tooltip: tooltipCommon('axis'),
  color: ['#29c4d6', '#f97316', '#fbbf24'],
  legend: { top: 4, textStyle: { color: '#b8c8dd' } },
  grid: { left: 44, right: 24, top: 42, bottom: 34 },
  xAxis: { type: 'category', data: yearTrend.value.map((i) => i.year), ...axisCommon() },
  yAxis: [{ type: 'value', ...axisCommon() }],
  series: [
    { name: '死亡人数', type: 'line', smooth: true, symbolSize: 7, data: yearTrend.value.map((i) => i.deaths) },
    { name: '受灾人口', type: 'line', smooth: true, symbolSize: 7, areaStyle: { color: areaGradient() }, data: yearTrend.value.map((i) => i.affected) },
    { name: '经济损失(万元)', type: 'line', smooth: true, symbolSize: 7, data: yearTrend.value.map((i) => i.loss) }
  ]
}))

const lossOption = computed(() => ({
  tooltip: tooltipCommon('axis'),
  grid: { left: 96, right: 24, top: 16, bottom: 20 },
  xAxis: { type: 'value', ...axisCommon('万元') },
  yAxis: { type: 'category', data: lossTop10.value.map((i) => i.name), axisLabel: { color: '#c7d6e8', fontSize: 11 } },
  series: [
    {
      type: 'bar',
      data: lossTop10.value.map((i) => i.value),
      itemStyle: {
        borderRadius: [0, 8, 8, 0],
        color: barGradient()
      }
    }
  ]
}))

async function onSearchRegion() {
  if (!regionQuery.value.trim()) return
  await router.push({ name: 'insight', query: { region: regionQuery.value.trim() } })
}
</script>

<template>
  <section class="view-wrap">
    <header class="view-header">
      <h2>综合总览</h2>
      <p>全国自然灾害事件态势、损失强度与年度变化</p>
    </header>

    <section class="glass-card search-panel">
      <div class="search-row">
        <label for="region-search">地区搜索与风险预测</label>
        <div class="search-ctrl">
          <input id="region-search" v-model="regionQuery" list="region-list" placeholder="输入省份，如：四川省、广东省" />
          <button type="button" @click="onSearchRegion">进入地区研判</button>
        </div>
        <datalist id="region-list">
          <option v-for="r in regionOptions" :key="r" :value="r" />
        </datalist>
      </div>
      <div class="search-result">输入地区后将跳转到“地区研判”模块，查看该地区完整图表、灾害类型概率预测与分群建议。</div>
    </section>

    <div v-if="loading" class="glass-card state-tip">正在加载数据...</div>
    <div v-else-if="error" class="glass-card state-tip error">{{ error }}</div>

    <div class="kpi-grid">
      <article class="glass-card kpi-item">
        <Icon icon="ph:warning-duotone" />
        <div>
          <h3>灾害事件总数</h3>
          <strong>{{ kpi.totalEvents || 0 }}</strong>
        </div>
      </article>
      <article class="glass-card kpi-item">
        <Icon icon="ph:heartbeat-duotone" />
        <div>
          <h3>死亡人数</h3>
          <strong>{{ kpi.totalDeaths || 0 }}</strong>
        </div>
      </article>
      <article class="glass-card kpi-item">
        <Icon icon="ph:coins-duotone" />
        <div>
          <h3>经济损失(万元)</h3>
          <strong>{{ Number(kpi.totalLossWanYuan || 0).toLocaleString() }}</strong>
        </div>
      </article>
      <article class="glass-card kpi-item">
        <Icon icon="ph:users-three-duotone" />
        <div>
          <h3>受灾人口</h3>
          <strong>{{ Number(kpi.totalAffected || 0).toLocaleString() }}</strong>
        </div>
      </article>
    </div>

    <div class="chart-grid two">
      <GlassChart title="灾害类型分布" icon="ph:donut-duotone" :option="donutOption" :height="360" />
      <GlassChart title="历年灾情趋势" icon="ph:chart-line-up-duotone" :option="trendOption" :height="360" />
    </div>
    <div class="chart-grid one">
      <GlassChart title="经济损失 TOP10 省份" icon="ph:trophy-duotone" :option="lossOption" :height="420" />
    </div>
  </section>
</template>
