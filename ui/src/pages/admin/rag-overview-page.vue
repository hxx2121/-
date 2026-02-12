<script setup lang="ts">
import { onMounted, ref, computed } from "vue"
import { 
  Squares2X2Icon, 
  ArrowPathIcon, 
  CircleStackIcon, 
  CheckCircleIcon, 
  ExclamationCircleIcon, 
  DocumentTextIcon, 
  ChartBarIcon,
  ChevronRightIcon,
  ChartPieIcon,
  ChartBarSquareIcon
} from "@heroicons/vue/24/outline"
import type { AdminCollectionOverviewItem } from "@/types/rag"
import { adminCollectionOverview } from "@/api/rag"
import { useMessage, NTag, NProgress, NScrollbar } from "naive-ui"
import gsap from "gsap"

const message = useMessage()
const rows = ref<AdminCollectionOverviewItem[]>([])
const isLoading = ref(false)

async function refresh() {
  isLoading.value = true
  try {
    rows.value = await adminCollectionOverview()
  } catch {
    message.error("获取概览数据失败")
  } finally {
    isLoading.value = false
  }
}

const totalDocs = computed(() => rows.value.reduce((acc, r) => acc + r.doc_total, 0))
const totalReady = computed(() => rows.value.reduce((acc, r) => acc + r.doc_ready, 0))
const totalFailed = computed(() => rows.value.reduce((acc, r) => acc + r.doc_failed, 0))

onMounted(() => {
  refresh()
  gsap.from(".page-header", { opacity: 0, y: -20, duration: 0.5, ease: "power2.out" })
})
</script>

<template>
  <div class="max-w-7xl mx-auto space-y-8 pb-12">
    <!-- Header -->
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 page-header">
      <div>
        <h1 class="text-3xl font-bold text-gray-900 tracking-tight flex items-center gap-3">
          <ChartBarIcon class="w-7 h-7 text-brand" />
          RAG 运行概览
        </h1>
        <p class="mt-1 text-gray-500 font-medium">全站知识库合集状态监控与数据分布审计</p>
      </div>
      <button 
        @click="refresh"
        :class="['p-2 rounded-figma border border-gray-200 bg-white text-gray-500 hover:text-brand hover:border-brand/20 transition-all shadow-sm', isLoading && 'animate-spin text-brand']"
      >
        <ArrowPathIcon class="w-5 h-5" />
      </button>
    </div>

    <!-- Top Level Metrics -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <div class="bg-white p-6 rounded-figma-lg border border-gray-100 shadow-figma flex items-center gap-4 relative overflow-hidden">
        <div class="w-12 h-12 bg-brand/5 rounded-figma flex items-center justify-center text-brand">
          <DocumentTextIcon class="w-6 h-6" />
        </div>
        <div>
          <p class="text-2xl font-bold text-gray-900 leading-none">{{ totalDocs }}</p>
          <p class="text-xs text-gray-400 font-bold uppercase tracking-widest mt-1">全站文档总数</p>
        </div>
        <div class="absolute -right-2 -bottom-2 opacity-[0.03] rotate-12">
          <DocumentTextIcon class="w-20 h-20" />
        </div>
      </div>
      <div class="bg-white p-6 rounded-figma-lg border border-gray-100 shadow-figma flex items-center gap-4 relative overflow-hidden">
        <div class="w-12 h-12 bg-emerald-50 rounded-figma flex items-center justify-center text-emerald-600">
          <CheckCircleIcon class="w-6 h-6" />
        </div>
        <div>
          <p class="text-2xl font-bold text-gray-900 leading-none">{{ totalReady }}</p>
          <p class="text-xs text-gray-400 font-bold uppercase tracking-widest mt-1">可用向量切片</p>
        </div>
        <div class="absolute -right-2 -bottom-2 opacity-[0.03] rotate-12">
          <CheckCircleIcon class="w-20 h-20" />
        </div>
      </div>
      <div class="bg-white p-6 rounded-figma-lg border border-gray-100 shadow-figma flex items-center gap-4 relative overflow-hidden">
        <div class="w-12 h-12 bg-red-50 rounded-figma flex items-center justify-center text-red-500">
          <ExclamationCircleIcon class="w-6 h-6" />
        </div>
        <div>
          <p class="text-2xl font-bold text-gray-900 leading-none">{{ totalFailed }}</p>
          <p class="text-xs text-gray-400 font-bold uppercase tracking-widest mt-1">解析异常记录</p>
        </div>
        <div class="absolute -right-2 -bottom-2 opacity-[0.03] rotate-12">
          <ExclamationCircleIcon class="w-20 h-20" />
        </div>
      </div>
    </div>

    <!-- Main List -->
    <div class="bg-white rounded-figma-lg shadow-figma border border-gray-100 overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-left border-collapse">
          <thead>
            <tr class="bg-gray-50 border-b border-gray-100">
              <th class="px-6 py-4 text-[10px] font-bold text-gray-400 uppercase tracking-widest">合集 ID</th>
              <th class="px-6 py-4 text-[10px] font-bold text-gray-400 uppercase tracking-widest">合集名称</th>
              <th class="px-6 py-4 text-[10px] font-bold text-gray-400 uppercase tracking-widest text-center">处理进度 (可用率)</th>
              <th class="px-6 py-4 text-[10px] font-bold text-gray-400 uppercase tracking-widest text-center">文档总数</th>
              <th class="px-6 py-4 text-[10px] font-bold text-gray-400 uppercase tracking-widest text-right">状态分布</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-50">
            <tr 
              v-for="(row, idx) in rows" 
              :key="row.id"
              v-motion
              :initial="{ opacity: 0, x: -10 }"
              :enter="{ opacity: 1, x: 0, transition: { delay: idx * 30 } }"
              class="hover:bg-gray-50/30 transition-colors group"
            >
              <td class="px-6 py-4 text-xs font-mono text-gray-400">#{{ row.id }}</td>
              <td class="px-6 py-4">
                <div class="flex items-center gap-3">
                  <div class="w-9 h-9 bg-gray-100 rounded-figma flex items-center justify-center text-gray-500 group-hover:bg-brand/10 group-hover:text-brand transition-all">
                    <CircleStackIcon class="w-5 h-5" />
                  </div>
                  <span class="text-sm font-bold text-gray-900">{{ row.name }}</span>
                </div>
              </td>
              <td class="px-6 py-4">
                <div class="flex flex-col items-center gap-1 min-w-[120px]">
                  <n-progress 
                    type="line" 
                    :percentage="row.doc_total > 0 ? Math.round((row.doc_ready / row.doc_total) * 100) : 0" 
                    :show-indicator="false" 
                    :height="6" 
                    processing
                    class="!w-24"
                    color="#000"
                  />
                  <span class="text-[10px] font-bold text-gray-400">
                    {{ row.doc_total > 0 ? Math.round((row.doc_ready / row.doc_total) * 100) : 0 }}% READY
                  </span>
                </div>
              </td>
              <td class="px-6 py-4 text-center">
                <span class="text-sm font-bold text-gray-900">{{ row.doc_total }}</span>
              </td>
              <td class="px-6 py-4">
                <div class="flex items-center justify-end gap-3">
                  <div class="flex items-center gap-1.5">
                    <div class="w-2 h-2 rounded-full bg-emerald-500"></div>
                    <span class="text-[10px] font-bold text-gray-500">{{ row.doc_ready }}</span>
                  </div>
                  <div class="flex items-center gap-1.5" v-if="row.doc_failed > 0">
                    <div class="w-2 h-2 rounded-full bg-red-500"></div>
                    <span class="text-[10px] font-bold text-gray-500">{{ row.doc_failed }}</span>
                  </div>
                </div>
              </td>
            </tr>
            <tr v-if="rows.length === 0 && !isLoading">
              <td colspan="5" class="px-6 py-20 text-center text-gray-400 font-medium italic">
                没有找到任何知识库合集数据
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<style scoped>
:deep(.n-progress-graph-line-rail) {
  background-color: #f3f4f6 !important;
}
</style>

