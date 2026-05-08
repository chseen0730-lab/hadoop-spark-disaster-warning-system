<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { fetchRegionInsight, fetchRegions } from '../api'
import GlassChart from '../components/GlassChart.vue'
import { axisCommon, chartPalette, tooltipCommon } from '../utils/chartPreset'

const route = useRoute()
const router = useRouter()
const queryRegion = ref((route.query.region || '全国').toString())
const regionOptions = ref(['全国'])
const loading = ref(false)
const error = ref('')
const insight = ref(null)

onMounted(async () => {
  try {
    const r = await fetchRegions()
    regionOptions.value = r.regions || ['全国']
  } catch {
    regionOptions.value = ['全国']
  }
  await load()
})

watch(
  () => route.query.region,
  async (v) => {
    if (typeof v === 'string' && v) {
      queryRegion.value = v
      await load()
    }
  }
)

watch(queryRegion, async (v) => {
  await router.replace({ name: 'insight', query: { region: v } })
})

async function load() {
  loading.value = true
  error.value = ''
  try {
    insight.value = await fetchRegionInsight(queryRegion.value)
  } catch (err) {
    error.value = err?.response?.data?.detail || '地区研判失败'
    insight.value = null
  } finally {
    loading.value = false
  }
}

const k = computed(() => insight.value?.overview || {})
const p = computed(() => insight.value?.prediction || {})
const c = computed(() => insight.value?.charts || {})
const rec = computed(() => insight.value?.recommendations || {})

const trendOption = computed(() => ({
  tooltip: tooltipCommon('axis'),
  color: ['#29c4d6', '#f97316', '#fbbf24'],
  legend: { bottom: 8, left: 'center', textStyle: { color: '#b8c8dd' } },
  grid: { left: 40, right: 20, top: 30, bottom: 62 },
  xAxis: { type: 'category', data: (c.value.yearTrend || []).map((i) => i.year), ...axisCommon() },
  yAxis: { type: 'value', ...axisCommon() },
  series: [
    { name: '死亡', type: 'line', smooth: true, data: (c.value.yearTrend || []).map((i) => i.deaths) },
    { name: '受灾', type: 'line', smooth: true, data: (c.value.yearTrend || []).map((i) => i.affected) },
    { name: '损失', type: 'line', smooth: true, data: (c.value.yearTrend || []).map((i) => i.loss) }
  ]
}))

const monthHeatOption = computed(() => ({
  tooltip: tooltipCommon(),
  xAxis: { type: 'category', data: (c.value.monthHeat || []).map((i) => `${i.month}月`), axisLabel: { color: '#c7d6e8' } },
  yAxis: { type: 'category', data: ['频次'], axisLabel: { color: '#c7d6e8' } },
  visualMap: { min: 0, max: Math.max(...(c.value.monthHeat || []).map((i) => i.count), 1), show: false, inRange: { color: ['#22364d', '#29c4d6', '#f97316'] } },
  series: [{ type: 'heatmap', data: (c.value.monthHeat || []).map((i, idx) => [idx, 0, i.count]), label: { show: true, color: '#eaf2ff' } }]
}))

const typeProbOption = computed(() => ({
  tooltip: tooltipCommon('axis'),
  grid: { left: 90, right: 20, top: 20, bottom: 20 },
  xAxis: { type: 'value', ...axisCommon('%') },
  yAxis: { type: 'category', data: (c.value.typeProbability || []).slice(0, 8).map((i) => i.type), axisLabel: { color: '#c7d6e8' } },
  series: [{ type: 'bar', data: (c.value.typeProbability || []).slice(0, 8).map((i) => i.probability), itemStyle: { borderRadius: [0, 6, 6, 0] } }]
}))

const lossScatterOption = computed(() => ({
  tooltip: tooltipCommon('item'),
  xAxis: { type: 'value', ...axisCommon('受灾人口') },
  yAxis: { type: 'value', ...axisCommon('经济损失(万元)') },
  series: [
    {
      type: 'scatter',
      symbolSize: 28,
      itemStyle: { color: '#29c4d6', opacity: 0.8 },
      data: (c.value.populationVsLoss || []).map((i) => [i.affected, i.loss, i.name])
    }
  ]
}))

const roseOption = computed(() => ({
  tooltip: tooltipCommon('item'),
  legend: { type: 'scroll', bottom: 4, left: 'center', textStyle: { color: '#b8c8dd', fontSize: 11 } },
  color: chartPalette,
  series: [{ type: 'pie', roseType: 'area', radius: [18, 95], center: ['50%', '42%'], data: (c.value.casualtyRose || []).slice(0, 12) }]
}))
</script>

<template>
  <section class="view-wrap">
    <header class="view-header">
      <h2>地区研判中心</h2>
      <p>基于历史灾情数据的地区级可视化分析、概率预测与分群预警建议</p>
    </header>

    <section class="glass-card search-panel">
      <div class="search-row">
        <label>地区模糊搜索</label>
        <div class="search-ctrl">
          <input v-model="queryRegion" list="region-list-2" placeholder="输入任意地区关键词，如 四川 / 广东 / 重庆市" />
          <button type="button" @click="load">更新研判</button>
        </div>
        <datalist id="region-list-2">
          <option v-for="r in regionOptions" :key="r" :value="r" />
        </datalist>
      </div>
      <div v-if="loading" class="search-result">正在生成地区研判结果...</div>
      <div v-else-if="error" class="search-result error">{{ error }}</div>
      <div v-else-if="insight" class="search-result">
        <p>
          <strong>{{ k.region }}</strong> 历史事件 {{ k.totalEvents }} 起，死亡 {{ k.totalDeaths }}，受灾人口
          {{ Number(k.totalAffected).toLocaleString() }}，经济损失 {{ Number(k.totalLossWanYuan).toLocaleString() }} 万元。
        </p>
        <p>
          下一年受灾概率预测：<strong>{{ p.nextYearRiskProbability }}%</strong>，最可能灾害类型：
          <strong>{{ p.nextYearLikelyType }}</strong>。
        </p>
      </div>
    </section>

    <div class="kpi-grid">
      <article class="glass-card kpi-item"><div><h3>灾害事件</h3><strong>{{ k.totalEvents || 0 }}</strong></div></article>
      <article class="glass-card kpi-item"><div><h3>死亡人数</h3><strong>{{ k.totalDeaths || 0 }}</strong></div></article>
      <article class="glass-card kpi-item"><div><h3>经济损失(万元)</h3><strong>{{ Number(k.totalLossWanYuan || 0).toLocaleString() }}</strong></div></article>
      <article class="glass-card kpi-item"><div><h3>受灾人口</h3><strong>{{ Number(k.totalAffected || 0).toLocaleString() }}</strong></div></article>
    </div>

    <div class="chart-grid two">
      <GlassChart title="年度灾情趋势" :option="trendOption" icon="ph:chart-line-up-duotone" :height="330" />
      <GlassChart title="月度灾害频次热力" :option="monthHeatOption" icon="ph:calendar-blank-duotone" :height="330" />
    </div>
    <div class="chart-grid two">
      <GlassChart title="下一年灾害类型概率" :option="typeProbOption" icon="ph:chart-bar-duotone" :height="330" />
      <GlassChart title="类型受灾与损失散点" :option="lossScatterOption" icon="ph:bubbles-duotone" :height="330" />
    </div>
    <div class="chart-grid one">
      <GlassChart title="重点区域伤亡玫瑰图" :option="roseOption" icon="ph:flower-lotus-duotone" :height="360" />
    </div>

    <div class="chart-grid three">
      <article class="glass-card advice-card">
        <h3>面向农民</h3>
        <ul><li v-for="(a, i) in rec.farmers || []" :key="`f-${i}`">{{ a }}</li></ul>
      </article>
      <article class="glass-card advice-card">
        <h3>面向企业</h3>
        <ul><li v-for="(a, i) in rec.enterprise || []" :key="`e-${i}`">{{ a }}</li></ul>
      </article>
      <article class="glass-card advice-card">
        <h3>面向政府</h3>
        <ul><li v-for="(a, i) in rec.government || []" :key="`g-${i}`">{{ a }}</li></ul>
      </article>
    </div>
  </section>
</template>
