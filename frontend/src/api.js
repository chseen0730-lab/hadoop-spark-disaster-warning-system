import axios from 'axios'

const http = axios.create({
  baseURL: 'http://localhost:8000/api',
  timeout: 20000
})

export async function fetchDashboardData() {
  const { data } = await http.get('/all')
  return data
}

export async function fetchRegions() {
  const { data } = await http.get('/regions')
  return data
}

export async function fetchRegionInsight(region) {
  const { data } = await http.get('/region-insight', { params: { region } })
  return data
}
