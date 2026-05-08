<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Icon } from '@iconify/vue'
import projectLogo from '../../image/logo.svg'
import projectBg from '../../image/background.jpg'

const navItems = [
  { to: '/', label: '总览', icon: 'ph:gauge-duotone' },
  { to: '/map', label: '地图', icon: 'ph:map-pin-area-duotone' },
  { to: '/trend', label: '趋势', icon: 'ph:chart-line-up-duotone' },
  { to: '/loss', label: '损失', icon: 'ph:chart-bar-horizontal-duotone' },
  { to: '/monitor', label: '监控', icon: 'ph:desktop-tower-duotone' }
]

const route = useRoute()
const router = useRouter()
const navRef = ref(null)
const brandLogoEl = ref(null)
const linkRefs = ref([])
const indicatorStyle = ref({ left: '0px', width: '0px', opacity: 0 })
const routeTransitionName = ref('module-slide-left')
let lastNavIndex = navItems.findIndex((i) => i.to === route.path)
const isLoginRoute = computed(() => route.name === 'login')
const isLogoutAnimating = ref(false)
const logoutPhase = ref('move')
const logoutProgress = ref(0)
const logoutStartStyle = ref({ '--from-x': '0px', '--from-y': '0px' })
let logoutTimer = null

function handleLogout() {
  if (isLogoutAnimating.value) return
  const logoRect = brandLogoEl.value?.getBoundingClientRect?.()
  if (logoRect) {
    const fromX = logoRect.left + logoRect.width / 2 - window.innerWidth / 2
    const fromY = logoRect.top + logoRect.height / 2 - window.innerHeight / 2
    logoutStartStyle.value = {
      '--from-x': `${fromX}px`,
      '--from-y': `${fromY}px`
    }
  }
  logoutPhase.value = 'move'
  logoutProgress.value = 0
  isLogoutAnimating.value = true
  window.setTimeout(() => {
    logoutPhase.value = 'loading'
    const duration = 2000
    const step = 20
    const totalSteps = duration / step
    let current = 0
    logoutTimer = window.setInterval(() => {
      current += 1
      logoutProgress.value = Math.min(100, (current / totalSteps) * 100)
      if (current >= totalSteps) {
        window.clearInterval(logoutTimer)
        logoutTimer = null
        sessionStorage.removeItem('disaster_auth_ok')
        sessionStorage.setItem('disaster_logout_transition', '1')
        router.push('/login')
        window.setTimeout(() => {
          isLogoutAnimating.value = false
        }, 120)
      }
    }, step)
  }, 520)
}

function setLinkRef(el, idx) {
  if (!el) return
  const normalized = el?.$el ?? el
  if (normalized && typeof normalized.getBoundingClientRect === 'function') {
    linkRefs.value[idx] = normalized
  }
}

function updateIndicator() {
  const navEl = navRef.value
  if (!navEl) return
  const idx = navItems.findIndex((i) => i.to === route.path)
  const activeEl = linkRefs.value[idx]
  if (!activeEl) return
  const navRect = navEl.getBoundingClientRect()
  const activeRect = activeEl.getBoundingClientRect()
  indicatorStyle.value = {
    left: `${activeRect.left - navRect.left}px`,
    width: `${activeRect.width}px`,
    opacity: 1
  }
}

watch(
  () => route.path,
  async (newPath) => {
    const nextIndex = navItems.findIndex((i) => i.to === newPath)
    if (nextIndex !== -1 && lastNavIndex !== -1) {
      routeTransitionName.value = nextIndex >= lastNavIndex ? 'module-slide-left' : 'module-slide-right'
    } else {
      routeTransitionName.value = 'module-slide-left'
    }
    if (nextIndex !== -1) lastNavIndex = nextIndex
    await nextTick()
    updateIndicator()
  },
  { immediate: true }
)

onMounted(() => {
  window.addEventListener('resize', updateIndicator)
  nextTick(updateIndicator)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', updateIndicator)
  if (logoutTimer) {
    window.clearInterval(logoutTimer)
    logoutTimer = null
  }
})
</script>

<template>
  <div class="app-shell" :class="{ 'login-mode': isLoginRoute }" :style="{ '--app-bg-image': `url(${projectBg})` }">
    <header v-if="!isLoginRoute" class="top-nav glass-card">
      <div class="brand">
        <img ref="brandLogoEl" :src="projectLogo" alt="项目logo" class="brand-logo" />
        <div class="brand-text">
          <h1>自然灾害可视化预警平台</h1>
          <p>风雨未至数先知</p>
        </div>
      </div>
      <nav ref="navRef" class="nav">
        <span class="nav-indicator" :style="indicatorStyle" />
        <RouterLink
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          :ref="(el) => setLinkRef(el, navItems.findIndex((n) => n.to === item.to))"
          class="nav-link"
          active-class="is-active"
        >
          <Icon :icon="item.icon" />
          <span>{{ item.label }}</span>
        </RouterLink>
      </nav>
      <div class="meta">
        <Icon icon="ph:warning-circle-duotone" />
        <span>数据来源：国家减灾网（2016-2020）</span>
        <button type="button" class="logout-btn" @click="handleLogout">
          <Icon icon="ph:sign-out-duotone" />
          <span>退出</span>
        </button>
      </div>
    </header>
    <main class="content-shell">
      <RouterView v-slot="{ Component, route: currentRoute }">
        <Transition :name="isLoginRoute ? 'login-view-fade' : routeTransitionName" mode="out-in">
          <component :is="Component" :key="currentRoute.fullPath" />
        </Transition>
      </RouterView>
    </main>

    <Transition name="logout-fade">
      <div v-if="isLogoutAnimating" class="logout-overlay" :class="logoutPhase" :style="logoutStartStyle">
        <img :src="projectLogo" alt="退出过渡logo" class="logout-logo" />
        <div v-if="logoutPhase === 'loading'" class="logout-progress">
          <div class="bar"><span :style="{ width: `${Math.round(logoutProgress)}%` }" /></div>
          <em>{{ Math.round(logoutProgress) }}%</em>
        </div>
      </div>
    </Transition>
  </div>
</template>
