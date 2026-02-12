<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue"
import { useAuthStore } from "@/stores/auth-store"
import { adminAnswerMetrics } from "@/api/qa"
import type { AnswerMetricsData } from "@/types/qa"
import { useMessage, NCard, NTag } from "naive-ui"
import * as echarts from "echarts"

const authStore = useAuthStore()
const message = useMessage()

const metrics = ref<AnswerMetricsData | null>(null)
const isLoading = ref(false)

const radarEl = ref<HTMLDivElement | null>(null)
const lineEl = ref<HTMLDivElement | null>(null)
let radarChart: echarts.ECharts | null = null
let lineChart: echarts.ECharts | null = null

const totalEvaluations = computed(() => {
  const q = metrics.value?.quality_distribution
  if (!q) return 0
  return q.low + q.medium + q.good + q.excellent
})

async function load() {
  if (!authStore.isAdmin) return
  isLoading.value = true
  try {
    metrics.value = await adminAnswerMetrics()
  } catch {
    metrics.value = null
    message.error("加载仪表盘数据失败")
  } finally {
    isLoading.value = false
    renderCharts()
  }
}

function renderCharts() {
  if (!metrics.value) return

  if (radarEl.value) {
    radarChart?.dispose()
    radarChart = echarts.init(radarEl.value)
    const s = metrics.value.avg_scores
    radarChart.setOption({
      tooltip: {},
      radar: {
        indicator: [
          { name: "语法", max: 10 },
          { name: "逻辑", max: 10 },
          { name: "通用性", max: 10 },
          { name: "可读性", max: 10 },
          { name: "总分", max: 10 },
        ],
      },
      series: [
        {
          type: "radar",
          data: [
            {
              value: [s.syntax, s.logic, s.utility, s.readability, s.total],
              name: "平均得分",
            },
          ],
        },
      ],
    })
  }

  if (lineEl.value) {
    lineChart?.dispose()
    lineChart = echarts.init(lineEl.value)
    const items = metrics.value.daily_activity || []
    lineChart.setOption({
      tooltip: { trigger: "axis" },
      xAxis: { type: "category", data: items.map((it) => it.date) },
      yAxis: { type: "value" },
      series: [{ type: "line", smooth: true, data: items.map((it) => it.count) }],
    })
  }
}

function onResize() {
  radarChart?.resize()
  lineChart?.resize()
}

onMounted(() => {
  load()
  window.addEventListener("resize", onResize)
})

onUnmounted(() => {
  window.removeEventListener("resize", onResize)
  radarChart?.dispose()
  lineChart?.dispose()
})
</script>

<template>
  <div class="max-w-7xl mx-auto space-y-6 pb-12">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-3xl font-bold text-gray-900 tracking-tight">推荐仪表盘</h1>
        <p class="mt-1 text-gray-500 font-medium">回答质量评估统计与趋势</p>
      </div>
      <div v-if="metrics" class="flex items-center gap-2">
        <n-tag size="small" :bordered="false" type="info">累计评估 {{ totalEvaluations }}</n-tag>
      </div>
    </div>

    <div v-if="!authStore.isAdmin" class="bg-white rounded-figma-lg border border-gray-100 shadow-figma p-10 text-center text-gray-500">
      该页面仅管理员可见
    </div>

    <div v-else class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <n-card title="平均得分雷达图" :bordered="false" class="!shadow-figma !border !border-gray-100 !rounded-figma-lg">
        <div ref="radarEl" style="height: 340px" />
      </n-card>

      <n-card title="近 7 日评估活跃度" :bordered="false" class="!shadow-figma !border !border-gray-100 !rounded-figma-lg">
        <div ref="lineEl" style="height: 340px" />
      </n-card>

      <n-card title="质量分布" :bordered="false" class="!shadow-figma !border !border-gray-100 !rounded-figma-lg lg:col-span-2">
        <div v-if="metrics" class="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div class="bg-gray-50 rounded-figma p-4 border border-gray-100">
            <div class="text-xs text-gray-400 font-bold uppercase tracking-widest">低</div>
            <div class="text-2xl font-bold text-gray-900 mt-2">{{ metrics.quality_distribution.low }}</div>
          </div>
          <div class="bg-gray-50 rounded-figma p-4 border border-gray-100">
            <div class="text-xs text-gray-400 font-bold uppercase tracking-widest">中</div>
            <div class="text-2xl font-bold text-gray-900 mt-2">{{ metrics.quality_distribution.medium }}</div>
          </div>
          <div class="bg-gray-50 rounded-figma p-4 border border-gray-100">
            <div class="text-xs text-gray-400 font-bold uppercase tracking-widest">良</div>
            <div class="text-2xl font-bold text-gray-900 mt-2">{{ metrics.quality_distribution.good }}</div>
          </div>
          <div class="bg-gray-50 rounded-figma p-4 border border-gray-100">
            <div class="text-xs text-gray-400 font-bold uppercase tracking-widest">优</div>
            <div class="text-2xl font-bold text-gray-900 mt-2">{{ metrics.quality_distribution.excellent }}</div>
          </div>
        </div>
        <div v-else class="text-gray-400 text-sm">暂无数据</div>
      </n-card>
    </div>
  </div>
</template>

