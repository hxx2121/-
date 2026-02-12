<script setup lang="ts">
import { computed, h, onMounted, reactive, ref } from "vue"
import { datasetSummary, getDatasetPairDetail, listDatasetPairs } from "@/api/qa"
import type { DatasetPairDetailData, DatasetPairItem, DatasetPairsPageData, DatasetSummaryData } from "@/types/qa"
import { useMessage, NButton, NCard, NDataTable, NInput, NModal, NScrollbar, NSelect, NTag } from "naive-ui"
import type { DataTableColumns } from "naive-ui"

const message = useMessage()

const summary = ref<DatasetSummaryData | null>(null)
const pageData = ref<DatasetPairsPageData | null>(null)
const isLoadingSummary = ref(false)
const isLoadingPairs = ref(false)

const filter = reactive({
  q: "",
  tag: "",
  sort: "answer_score" as "answer_score" | "question_score" | "recent",
  page: 1,
  pageSize: 20,
})

const tagOptions = computed(() => {
  const rows = summary.value?.top_tags || []
  return rows.map((r) => ({ label: `${r.tag} (${r.count})`, value: r.tag }))
})

const sortOptions = [
  { label: "按回答分", value: "answer_score" },
  { label: "按问题分", value: "question_score" },
  { label: "按入库时间", value: "recent" },
]

const pageSizeOptions = [
  { label: "20 / 页", value: 20 },
  { label: "50 / 页", value: 50 },
  { label: "100 / 页", value: 100 },
]

const totalPages = computed(() => {
  const t = pageData.value?.total || 0
  return Math.max(1, Math.ceil(t / filter.pageSize))
})

async function loadSummary() {
  isLoadingSummary.value = true
  try {
    summary.value = await datasetSummary()
  } catch {
    summary.value = null
    message.error("加载数据集概览失败")
  } finally {
    isLoadingSummary.value = false
  }
}

async function loadPairs(resetPage = false) {
  if (resetPage) filter.page = 1
  isLoadingPairs.value = true
  try {
    pageData.value = await listDatasetPairs({
      q: filter.q || undefined,
      tag: filter.tag || undefined,
      sort: filter.sort,
      page: filter.page,
      page_size: filter.pageSize,
    })
  } catch {
    pageData.value = null
    message.error("加载数据列表失败")
  } finally {
    isLoadingPairs.value = false
  }
}

const rows = computed<DatasetPairItem[]>(() => pageData.value?.items || [])

const isDetailOpen = ref(false)
const detailId = ref<number | null>(null)
const detail = ref<DatasetPairDetailData | null>(null)
const isLoadingDetail = ref(false)

async function openDetail(row: DatasetPairItem) {
  isDetailOpen.value = true
  detailId.value = row.id
  detail.value = null
  isLoadingDetail.value = true
  try {
    detail.value = await getDatasetPairDetail(row.id)
  } catch {
    detail.value = null
    message.error("加载详情失败")
  } finally {
    isLoadingDetail.value = false
  }
}

function closeDetail() {
  isDetailOpen.value = false
  detailId.value = null
  detail.value = null
}

function renderTags(tags: string[]) {
  const out = (tags || []).slice(0, 4)
  return h(
    "div",
    { class: "flex flex-wrap gap-1" },
    out.map((t) =>
      h(
        NTag,
        { size: "small", bordered: false, type: "info" },
        { default: () => t }
      )
    )
  )
}

const columns = computed<DataTableColumns<DatasetPairItem>>(() => {
  const cols: DataTableColumns<DatasetPairItem> = [
    {
      title: "标题",
      key: "title",
      width: 420,
      render: (row) =>
        h(
          "button",
          { class: "text-left text-brand font-semibold hover:underline", onClick: () => openDetail(row) },
          row.title || "(无标题)"
        ),
    },
    {
      title: "标签",
      key: "tags",
      width: 240,
      render: (row) => renderTags(row.tags),
    },
    {
      title: "得分",
      key: "scores",
      width: 160,
      render: (row) =>
        h("div", { class: "text-xs text-gray-600 space-y-1" }, [
          h("div", {}, `Q: ${row.question_score}`),
          h("div", {}, `A: ${row.answer_score}`),
        ]),
    },
    {
      title: "摘要",
      key: "excerpt",
      minWidth: 520,
      render: (row) =>
        h("div", { class: "text-xs text-gray-600 space-y-2" }, [
          h("div", { class: "line-clamp-2" }, row.question_excerpt || ""),
          h("div", { class: "line-clamp-2 text-gray-500" }, row.answer_excerpt || ""),
        ]),
    },
  ]
  return cols
})

function applyTag(tag: string) {
  filter.tag = tag
  loadPairs(true)
}

function prevPage() {
  if (filter.page <= 1) return
  filter.page -= 1
  loadPairs(false)
}

function nextPage() {
  if (filter.page >= totalPages.value) return
  filter.page += 1
  loadPairs(false)
}

onMounted(async () => {
  await loadSummary()
  await loadPairs(true)
})
</script>

<template>
  <div class="max-w-7xl mx-auto space-y-6 pb-12">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-3xl font-bold text-gray-900 tracking-tight">数据集浏览</h1>
        <p class="mt-1 text-gray-500 font-medium">查看清洗入库后的问答数据、标签分布与样例</p>
      </div>
      <div class="flex items-center gap-3">
        <n-button :loading="isLoadingSummary" @click="loadSummary" class="!font-bold">刷新概览</n-button>
        <n-button :loading="isLoadingPairs" type="primary" @click="loadPairs(true)" class="!bg-brand !font-bold">
          查询
        </n-button>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <n-card :bordered="false" class="!shadow-figma !border !border-gray-100 !rounded-figma-lg lg:col-span-1">
        <template #header>
          <div class="flex items-center justify-between">
            <span class="font-bold text-gray-900">概览</span>
            <span class="text-xs text-gray-400 font-mono">total: {{ summary?.total ?? 0 }}</span>
          </div>
        </template>

        <div v-if="summary" class="space-y-4">
          <div class="bg-gray-50 rounded-figma p-4 border border-gray-100">
            <div class="text-xs text-gray-400 font-bold uppercase tracking-widest">入库问答对</div>
            <div class="text-3xl font-bold text-gray-900 mt-2">{{ summary.total }}</div>
          </div>

          <div>
            <div class="text-[11px] font-bold text-gray-400 uppercase tracking-widest mb-2">热门标签 Top 20</div>
            <div class="flex flex-wrap gap-2">
              <button
                v-for="t in summary.top_tags"
                :key="t.tag"
                @click="applyTag(t.tag)"
                class="px-2.5 py-1 rounded-full bg-gray-100 text-gray-700 text-xs font-semibold hover:bg-brand/10 hover:text-brand transition-colors"
                :class="filter.tag === t.tag ? 'bg-brand/10 text-brand' : ''"
              >
                {{ t.tag }} ({{ t.count }})
              </button>
            </div>
          </div>
        </div>
        <div v-else class="text-sm text-gray-400">暂无概览数据</div>
      </n-card>

      <n-card :bordered="false" class="!shadow-figma !border !border-gray-100 !rounded-figma-lg lg:col-span-2">
        <template #header>
          <div class="flex items-center justify-between w-full">
            <span class="font-bold text-gray-900">数据列表</span>
            <span class="text-xs text-gray-400 font-mono">
              page {{ pageData?.page ?? 1 }} / {{ totalPages }}
            </span>
          </div>
        </template>

        <div class="space-y-4">
          <div class="grid grid-cols-1 md:grid-cols-4 gap-3">
            <n-input
              v-model:value="filter.q"
              placeholder="关键词：标题/正文/答案..."
              class="!rounded-figma md:col-span-2"
              @keyup.enter="loadPairs(true)"
            />
            <n-select
              v-model:value="filter.tag"
              :options="[{ label: '全部标签', value: '' }, ...tagOptions]"
              class="!rounded-figma"
              @update:value="() => loadPairs(true)"
            />
            <n-select
              v-model:value="filter.sort"
              :options="sortOptions"
              class="!rounded-figma"
              @update:value="() => loadPairs(true)"
            />
          </div>

          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <n-button size="small" :disabled="filter.page <= 1" @click="prevPage">上一页</n-button>
              <n-button size="small" :disabled="filter.page >= totalPages" @click="nextPage">下一页</n-button>
              <span class="text-xs text-gray-400 ml-2">共 {{ pageData?.total ?? 0 }} 条</span>
            </div>
            <div class="flex items-center gap-2">
              <span class="text-xs text-gray-400">每页</span>
              <n-select
                v-model:value="filter.pageSize"
                :options="pageSizeOptions"
                class="!rounded-figma w-28"
                @update:value="() => loadPairs(true)"
              />
            </div>
          </div>

          <n-data-table
            :columns="columns"
            :data="rows"
            :loading="isLoadingPairs"
            :bordered="false"
            size="small"
            class="!rounded-figma"
          />
        </div>
      </n-card>
    </div>

    <n-modal v-model:show="isDetailOpen" preset="card" title="问答详情" style="width: 980px" @after-leave="closeDetail">
      <n-scrollbar style="max-height: 70vh">
        <div class="space-y-6">
          <div v-if="isLoadingDetail" class="text-sm text-gray-400">加载中...</div>
          <div v-else-if="detail" class="space-y-6">
            <div class="flex items-start justify-between gap-4">
              <div>
                <div class="text-xl font-bold text-gray-900">{{ detail.title || '(无标题)' }}</div>
                <div class="mt-2 flex flex-wrap gap-2">
                  <n-tag v-for="t in detail.tags" :key="t" size="small" :bordered="false" type="info">{{ t }}</n-tag>
                </div>
              </div>
              <div class="text-right text-xs text-gray-500 font-mono shrink-0">
                <div>#{{ detail.id }}</div>
                <div>qid={{ detail.question_id }}</div>
                <div>aid={{ detail.answer_id }}</div>
              </div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div class="bg-gray-50 rounded-figma p-4 border border-gray-100">
                <div class="text-[10px] font-bold text-gray-400 uppercase tracking-widest">问题分</div>
                <div class="text-2xl font-bold text-gray-900 mt-2">{{ detail.question_score }}</div>
              </div>
              <div class="bg-gray-50 rounded-figma p-4 border border-gray-100">
                <div class="text-[10px] font-bold text-gray-400 uppercase tracking-widest">回答分</div>
                <div class="text-2xl font-bold text-gray-900 mt-2">{{ detail.answer_score }}</div>
              </div>
              <div class="bg-gray-50 rounded-figma p-4 border border-gray-100">
                <div class="text-[10px] font-bold text-gray-400 uppercase tracking-widest">浏览量</div>
                <div class="text-2xl font-bold text-gray-900 mt-2">{{ detail.view_count ?? 0 }}</div>
              </div>
            </div>

            <div class="space-y-2">
              <div class="text-sm font-bold text-gray-900">问题正文</div>
              <pre class="whitespace-pre-wrap text-xs bg-gray-50 border border-gray-100 rounded-figma p-4">{{ detail.question_body }}</pre>
            </div>

            <div class="space-y-2">
              <div class="text-sm font-bold text-gray-900">回答正文</div>
              <pre class="whitespace-pre-wrap text-xs bg-gray-50 border border-gray-100 rounded-figma p-4">{{ detail.answer_body }}</pre>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div class="space-y-2">
                <div class="text-sm font-bold text-gray-900">问题代码块</div>
                <div v-if="(detail.question_code_snippets_json || []).length === 0" class="text-xs text-gray-400">无</div>
                <pre
                  v-for="(c, idx) in detail.question_code_snippets_json"
                  :key="`q-${idx}`"
                  class="whitespace-pre-wrap text-xs bg-black text-white rounded-figma p-4 overflow-auto"
                >{{ c }}</pre>
              </div>
              <div class="space-y-2">
                <div class="text-sm font-bold text-gray-900">回答代码块</div>
                <div v-if="(detail.answer_code_snippets_json || []).length === 0" class="text-xs text-gray-400">无</div>
                <pre
                  v-for="(c, idx) in detail.answer_code_snippets_json"
                  :key="`a-${idx}`"
                  class="whitespace-pre-wrap text-xs bg-black text-white rounded-figma p-4 overflow-auto"
                >{{ c }}</pre>
              </div>
            </div>
          </div>
          <div v-else class="text-sm text-gray-400">暂无数据</div>
        </div>
      </n-scrollbar>
    </n-modal>
  </div>
</template>

