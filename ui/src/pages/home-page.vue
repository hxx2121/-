<script setup lang="ts">
import { computed, onMounted, ref } from "vue"
import { useRouter } from "vue-router"
import { useAuthStore } from "@/stores/auth-store"
import { adminAnswerMetrics } from "@/api/qa"
import type { AnswerMetricsData } from "@/types/qa"
import { 
  DocumentTextIcon, 
  CircleStackIcon, 
  ChatBubbleLeftRightIcon, 
  ShieldCheckIcon, 
  ArrowUpRightIcon,
  PlusIcon,
  BoltIcon,
  ClockIcon,
  Squares2X2Icon,
  BookOpenIcon
} from "@heroicons/vue/24/outline"

const authStore = useAuthStore()
const router = useRouter()

const username = computed(() => authStore.me?.username || "访客")
const role = computed(() => authStore.me?.role || "标准用户")

const metrics = ref<AnswerMetricsData | null>(null)
const isLoadingMetrics = ref(false)

const totalEvaluations = computed(() => {
  const q = metrics.value?.quality_distribution
  if (!q) return 0
  return q.low + q.medium + q.good + q.excellent
})

const yesterdayEvaluations = computed(() => {
  const items = metrics.value?.daily_activity ?? []
  if (!items.length) return 0
  const d = new Date()
  d.setDate(d.getDate() - 1)
  const target = d.toISOString().slice(0, 10)
  const found = items.find((it) => it.date === target)
  return found ? found.count : 0
})

const last7Total = computed(() => {
  const items = metrics.value?.daily_activity ?? []
  return items.reduce((sum, it) => sum + it.count, 0)
})

const last7Avg = computed(() => {
  const items = metrics.value?.daily_activity ?? []
  if (!items.length) return 0
  return Number((last7Total.value / items.length).toFixed(1))
})

const avgTotalScore = computed(() => {
  const total = metrics.value?.avg_scores.total ?? 0
  if (!total) return 0
  return Number(total.toFixed(1))
})

const hasMetrics = computed(() => Boolean(metrics.value && totalEvaluations.value > 0))

const backendHealthy = computed(() => {
  if (!authStore.isAuthenticated) return false
  if (!authStore.isAdmin) return true
  return hasMetrics.value
})

function formatNumber(n: number): string {
  return n.toLocaleString()
}

async function loadMetrics() {
  if (!authStore.isAdmin) return
  isLoadingMetrics.value = true
  try {
    metrics.value = await adminAnswerMetrics()
  } catch {
    metrics.value = null
  } finally {
    isLoadingMetrics.value = false
  }
}

onMounted(() => {
  loadMetrics()
})

const quickActions = [
  { 
    title: "编程问答", 
    desc: "基于代码大模型的智能问答与分析", 
    icon: ChatBubbleLeftRightIcon, 
    route: "qa-chat",
    color: "bg-purple-500" 
  },
  { 
    title: "推荐仪表盘", 
    desc: "查看回答质量与系统运营数据总览", 
    icon: Squares2X2Icon, 
    route: "qa-dashboard",
    color: "bg-indigo-500" 
  },
  { 
    title: "提示词模板", 
    desc: "配置与管理业务场景提示词模板", 
    icon: DocumentTextIcon, 
    route: "admin-prompts",
    color: "bg-amber-500" 
  },
]
</script>

<template>
  <div class="max-w-7xl mx-auto space-y-10 pb-12">
    <!-- Welcome Section -->
    <div 
      class="relative overflow-hidden rounded-figma-lg bg-brand p-10 text-white shadow-2xl"
    >
      <div class="relative z-10 max-w-2xl">
        <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/10 backdrop-blur-md border border-white/20 text-xs font-bold uppercase tracking-wider mb-6">
          <BoltIcon class="w-4 h-4" />
          <span>欢迎回来，{{ role }}</span>
        </div>
        <h1 class="text-4xl md:text-5xl font-bold tracking-tight mb-4 leading-tight">
          你好, {{ username }} 👋
        </h1>
        <p class="text-lg text-white/80 font-medium leading-relaxed mb-8">
          今天想处理什么任务？您可以快速开始 编程问答 ，或者继续之前的智能对话。
        
        </p>
        <div class="flex flex-wrap gap-4">
          <button 
            @click="router.push({ name: 'rag-chat' })"
            class="px-6 py-3 bg-white text-brand rounded-figma font-bold hover:bg-gray-100 transition-all flex items-center gap-2 shadow-lg"
          >
            开始新对话
            <ChatBubbleLeftRightIcon class="w-5 h-5" />
          </button>
          <button 
            @click="router.push({ name: 'file-center' })"
            class="px-6 py-3 bg-white/10 hover:bg-white/20 text-white border border-white/20 rounded-figma font-bold transition-all flex items-center gap-2"
          >
            导入数据
            <PlusIcon class="w-5 h-5" />
          </button>
        </div>
      </div>
      
      <!-- Abstract decorative elements -->
      <div class="absolute top-[-20%] right-[-10%] w-[500px] h-[500px] bg-white/5 rounded-full blur-3xl pointer-events-none" />
      <div class="absolute bottom-[-20%] left-[40%] w-[300px] h-[300px] bg-accent/20 rounded-full blur-3xl pointer-events-none" />
    </div>

    <!-- Quick Actions Grid -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <div 
        v-for="(action, idx) in quickActions" 
        :key="idx"
        @click="router.push({ name: action.route })"
        class="stat-card group cursor-pointer bg-white p-6 rounded-figma-lg shadow-figma hover:shadow-figma-hover border border-gray-100 transition-all relative overflow-hidden"
      >
        <div class="flex justify-between items-start mb-4">
          <div :class="[action.color, 'w-12 h-12 rounded-figma flex items-center justify-center text-white shadow-lg group-hover:scale-110 transition-transform duration-300']">
            <component :is="action.icon" class="w-6 h-6" />
          </div>
          <ArrowUpRightIcon class="w-5 h-5 text-gray-300 group-hover:text-brand transition-colors" />
        </div>
        <h3 class="text-lg font-bold text-gray-900 mb-2">{{ action.title }}</h3>
        <p class="text-sm text-gray-500 font-medium leading-relaxed">{{ action.desc }}</p>
        
        <div class="absolute bottom-0 left-0 w-full h-1 bg-gray-50 group-hover:bg-brand/10 transition-colors" />
      </div>
    </div>

    <!-- Stats & Insights Section -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
      <!-- Activity Feed -->
      <div class="lg:col-span-2 bg-white rounded-figma-lg shadow-figma border border-gray-100 overflow-hidden">
        <div class="p-6 border-b border-gray-50 flex items-center justify-between">
          <h2 class="text-xl font-bold text-gray-900 flex items-center gap-2">
            <Squares2X2Icon class="w-5 h-5 text-brand" />
            系统概览
          </h2>
          <button 
            class="text-sm font-bold text-brand hover:underline"
            @click="router.push({ name: 'dashboard' })"
          >
            查看全部
          </button>
        </div>
        <div class="p-8 grid grid-cols-1 sm:grid-cols-2 gap-8">
          <div class="space-y-2">
            <p class="text-sm font-bold text-gray-400 uppercase tracking-widest">累计回答评估数</p>
            <div class="flex items-end gap-3">
              <span class="text-4xl font-bold text-gray-900 leading-none">
                {{ hasMetrics ? formatNumber(totalEvaluations) : "—" }}
              </span>
              <span class="text-green-500 text-sm font-bold pb-1 flex items-center">
                <span v-if="hasMetrics">已完成质量评估</span>
                <span v-else>等待评估数据</span>
                <ArrowUpRightIcon class="w-4 h-4 ml-1" />
              </span>
            </div>
          </div>
          <div class="space-y-2">
            <p class="text-sm font-bold text-gray-400 uppercase tracking-widest">昨日已评估回答数</p>
            <div class="flex items-end gap-3">
              <span class="text-4xl font-bold text-gray-900 leading-none">
                {{ hasMetrics ? formatNumber(yesterdayEvaluations) : "—" }}
              </span>
              <span class="text-brand text-sm font-bold pb-1 flex items-center">
                <span v-if="hasMetrics">近7日平均 {{ last7Avg }} 条/天</span>
                <span v-else>等待首条评估</span>
                <ClockIcon class="w-4 h-4 ml-1" />
              </span>
            </div>
          </div>
        </div>
        <div class="px-8 pb-8">
          <div class="bg-gray-50 rounded-figma p-6 border border-dashed border-gray-200 flex flex-col items-center justify-center text-center space-y-4">
            <div class="w-12 h-12 bg-white rounded-full flex items-center justify-center shadow-sm">
              <BookOpenIcon class="w-5 h-5 text-gray-400" />
            </div>
            <div>
              <p class="font-bold text-gray-900">
                <span v-if="hasMetrics">推荐仪表盘已接入真实评估数据</span>
                <span v-else>推荐仪表盘暂无真实数据</span>
              </p>
              <p class="text-sm text-gray-500 font-medium mt-1">
                <span v-if="hasMetrics">点击右上角「推荐仪表盘」查看质量趋势与多维分析。</span>
                <span v-else>多进行几次代码对话，系统会自动生成质量趋势与统计。</span>
              </p>
            </div>
          </div>
        </div>
      </div>

      <!-- System Health -->
      <div class="bg-white rounded-figma-lg shadow-figma border border-gray-100 overflow-hidden flex flex-col">
        <div class="p-6 border-b border-gray-50">
          <h2 class="text-xl font-bold text-gray-900 flex items-center gap-2">
            <ShieldCheckIcon class="w-5 h-5 text-green-500" />
            运行状态
          </h2>
        </div>
        <div class="flex-1 p-6 space-y-6">
          <div class="space-y-4">
            <div class="flex justify-between items-center text-sm">
              <span class="font-medium text-gray-600">代码知识检索服务</span>
              <span
                :class="[
                  'font-bold px-2 py-0.5 rounded-full text-xs uppercase',
                  backendHealthy ? 'text-green-500 bg-green-50' : 'text-red-500 bg-red-50',
                ]"
              >
                {{ backendHealthy ? "正常运行" : "需检查" }}
              </span>
            </div>
            <div class="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
              <div class="h-full bg-green-500" :style="{ width: backendHealthy ? '96%' : '40%' }" />
            </div>
          </div>

          <div class="space-y-4">
            <div class="flex justify-between items-center text-sm">
              <span class="font-medium text-gray-600">模型推理服务</span>
              <span
                :class="[
                  'font-bold px-2 py-0.5 rounded-full text-xs uppercase',
                  backendHealthy ? 'text-green-500 bg-green-50' : 'text-yellow-600 bg-yellow-50',
                ]"
              >
                {{ backendHealthy ? "响应顺畅" : "可能存在延迟" }}
              </span>
            </div>
            <div class="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
              <div class="h-full bg-green-500" :style="{ width: backendHealthy ? '92%' : '40%' }" />
            </div>
          </div>

          <div class="mt-8 p-4 bg-gray-50 rounded-figma border border-gray-100">
            <div class="flex items-center gap-3 text-brand">
              <BoltIcon class="w-5 h-5" />
              <span class="font-bold text-sm">系统运行提示</span>
            </div>
            <p class="text-xs text-gray-500 font-medium mt-2 leading-relaxed">
              当前为内部使用环境，建议定期前往「API 自检」页面做全链路健康检查。
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.stat-card {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.stat-card:hover {
  transform: translateY(-4px);
}
</style>
