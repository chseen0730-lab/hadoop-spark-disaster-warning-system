import { onMounted, ref } from 'vue'
import { fetchDashboardData } from '../api'

const state = ref(null)
const loading = ref(false)
const error = ref('')

export function useDisasterData() {
  async function load() {
    if (state.value) return
    loading.value = true
    error.value = ''
    try {
      state.value = await fetchDashboardData()
    } catch (err) {
      error.value = err?.message || '数据加载失败'
    } finally {
      loading.value = false
    }
  }

  onMounted(load)
  return { state, loading, error, reload: load }
}
