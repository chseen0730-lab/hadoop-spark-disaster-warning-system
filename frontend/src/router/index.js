import { createRouter, createWebHistory } from 'vue-router'
import LoginIntroView from '../views/LoginIntroView.vue'
import DashboardView from '../views/DashboardView.vue'
import MapView from '../views/MapView.vue'
import TrendView from '../views/TrendView.vue'
import LossView from '../views/LossView.vue'
import MonitorView from '../views/MonitorView.vue'
import RegionInsightView from '../views/RegionInsightView.vue'

const AUTH_KEY = 'disaster_auth_ok'

const routes = [
  { path: '/login', name: 'login', component: LoginIntroView },
  { path: '/', name: 'dashboard', component: DashboardView },
  { path: '/map', name: 'map', component: MapView },
  { path: '/trend', name: 'trend', component: TrendView },
  { path: '/loss', name: 'loss', component: LossView },
  { path: '/monitor', name: 'monitor', component: MonitorView },
  { path: '/insight', name: 'insight', component: RegionInsightView }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to) => {
  const authed = sessionStorage.getItem(AUTH_KEY) === '1'
  if (to.name !== 'login' && !authed) {
    return { name: 'login' }
  }
  if (to.name === 'login' && authed) {
    return { name: 'dashboard' }
  }
  return true
})

export default router
