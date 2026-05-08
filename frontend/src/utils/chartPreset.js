import * as echarts from 'echarts'

export const chartText = '#c7d6e8'
export const chartGrid = '#2a3a4b'
export const chartPalette = ['#29c4d6', '#f97316', '#fbbf24', '#5d87ff', '#5ad8a6', '#ef4444']

export function axisCommon(name = '') {
  return {
    name,
    nameTextStyle: { color: '#8ea0b8' },
    axisLabel: { color: chartText },
    axisLine: { lineStyle: { color: '#40556d' } },
    splitLine: { lineStyle: { color: chartGrid, type: 'dashed' } }
  }
}

export function tooltipCommon(trigger = 'item') {
  return {
    trigger,
    backgroundColor: 'rgba(13, 22, 33, 0.92)',
    borderColor: '#2c4a63',
    textStyle: { color: '#e6effa' }
  }
}

export function barGradient() {
  return new echarts.graphic.LinearGradient(1, 0, 0, 0, [
    { offset: 0, color: '#f97316' },
    { offset: 1, color: '#fbbf24' }
  ])
}

export function areaGradient() {
  return new echarts.graphic.LinearGradient(0, 0, 0, 1, [
    { offset: 0, color: 'rgba(41, 196, 214, 0.45)' },
    { offset: 1, color: 'rgba(41, 196, 214, 0.03)' }
  ])
}
