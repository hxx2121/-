<script setup lang="ts">
import { computed, h, onMounted, reactive, ref } from "vue"
import { useRouter } from "vue-router"
import { 
  ArrowUpTrayIcon, 
  DocumentTextIcon, 
  DocumentIcon, 
  ArrowPathIcon, 
  ArrowDownTrayIcon, 
  TrashIcon, 
  ArrowTopRightOnSquareIcon,
  PlusIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
  ClockIcon,
  MagnifyingGlassIcon,
  BoltIcon
} from "@heroicons/vue/24/outline"
import { 
  NButton, 
  NCard, 
  NDataTable, 
  NForm, 
  NFormItem, 
  NInput, 
  NPopconfirm, 
  NTabPane, 
  NTabs, 
  NTag, 
  useMessage,
  NUpload,
  NUploadDragger,
  NIcon,
  NP
} from "naive-ui"

import type { DataTableColumns } from "naive-ui"
import type { KnowledgeDocumentItem } from "@/types/rag"
import { downloadDocument, ingestText, listDocuments, uploadDocument, deleteDocument } from "@/api/rag"
import { useAuthStore } from "@/stores/auth-store"
import gsap from "gsap"

const message = useMessage()
const router = useRouter()
const authStore = useAuthStore()

const collectionId = 1
const docs = ref<KnowledgeDocumentItem[]>([])
const isLoading = ref(false)
const searchQuery = ref("")

const textForm = reactive({ title: "", content: "" })
const isIngestingText = ref(false)
const isUploadingFile = ref(false)

const isAdmin = computed(() => authStore.isAdmin)

const filteredDocs = computed(() => {
  if (!searchQuery.value) return docs.value
  const q = searchQuery.value.toLowerCase()
  return docs.value.filter(d => 
    d.original_name?.toLowerCase().includes(q) || 
    d.id.toString().includes(q)
  )
})

const statusConfig = {
  ready: { type: 'success', label: '已就绪', icon: CheckCircleIcon, color: 'text-green-500' },
  failed: { type: 'error', label: '解析失败', icon: ExclamationCircleIcon, color: 'text-red-500' },
  ingesting: { type: 'warning', label: '正在入库', icon: ClockIcon, color: 'text-orange-500' },
  default: { type: 'default', label: '未知状态', icon: DocumentIcon, color: 'text-gray-400' }
}

async function refresh() {
  isLoading.value = true
  try {
    docs.value = await listDocuments(collectionId)
  } catch {
    message.error("获取记录失败")
  } finally {
    isLoading.value = false
  }
}

async function handleUploadChange(data: { fileList: any }) {
  const file = data.fileList[0]?.file
  if (!file) return
  
  isUploadingFile.value = true
  try {
    await uploadDocument(collectionId, file)
    message.success("上传成功，系统正在后台进行语义解析")
    await refresh()
  } catch {
    message.error("上传失败")
  } finally {
    isUploadingFile.value = false
  }
}

async function handleIngestText() {
  if (!textForm.content.trim()) {
    message.warning("请输入要入库的文本内容")
    return
  }
  isIngestingText.value = true
  try {
    await ingestText(collectionId, { title: textForm.title || "手动输入文本", content: textForm.content })
    message.success("文本入库成功")
    textForm.title = ""
    textForm.content = ""
    await refresh()
  } catch {
    message.error("入库失败")
  } finally {
    isIngestingText.value = false
  }
}

async function handleDownload(row: KnowledgeDocumentItem) {
  try {
    const { blob, filename } = await downloadDocument(row.id)
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = filename || row.original_name || "download"
    document.body.appendChild(a)
    a.click()
    a.remove()
    URL.revokeObjectURL(url)
    message.success("下载已开始")
  } catch {
    message.error("文件下载失败")
  }
}

async function handleDelete(row: KnowledgeDocumentItem) {
  try {
    await deleteDocument(row.id)
    message.success("文档已从知识库移除")
    await refresh()
  } catch {
    message.error("删除失败")
  }
}

onMounted(() => {
  refresh()
  gsap.from(".upload-zone", {
    y: 20,
    opacity: 0,
    duration: 0.6,
    ease: "power3.out"
  })
})
</script>

<template>
  <div class="max-w-6xl mx-auto space-y-10 pb-16">
    <!-- Page Header -->
    <div class="flex flex-col md:flex-row md:items-end justify-between gap-4">
      <div>
        <h1 class="text-3xl font-bold text-gray-900 tracking-tight">文件中心</h1>
        <p class="mt-1 text-gray-500 font-medium">将非结构化数据转化为 AI 可理解的语义向量</p>
      </div>
      <div class="flex items-center gap-3">
        <div class="relative">
          <MagnifyingGlassIcon class="w-[18px] h-[18px] absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input 
            v-model="searchQuery"
            type="text" 
            placeholder="搜索文档记录..." 
            class="pl-10 pr-4 py-2 bg-white border border-gray-200 rounded-figma text-sm w-64 focus:border-brand/30 outline-none transition-all shadow-sm"
          />
        </div>
        <button 
          @click="refresh"
          :class="['p-2 rounded-figma border border-gray-200 bg-white text-gray-500 hover:text-brand hover:border-brand/20 transition-all shadow-sm', isLoading && 'animate-spin text-brand']"
        >
          <ArrowPathIcon class="w-[18px] h-[18px]" />
        </button>
      </div>
    </div>

    <!-- Upload/Ingest Section -->
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-8">
      <!-- Left: Ingest Controls -->
      <div class="lg:col-span-8 space-y-6 upload-zone">
        <div class="bg-white rounded-figma-lg shadow-figma border border-gray-100 overflow-hidden">
          <n-tabs type="line" animated content-style="padding: 24px;">
            <n-tab-pane name="docx">
              <template #tab>
                <div class="flex items-center gap-2 px-2">
                  <ArrowUpTrayIcon class="w-4 h-4" />
                  <span class="font-bold">上传 Word 文档</span>
                </div>
              </template>
              
              <div class="space-y-6">
                <n-upload
                  multiple
                  directory-dnd
                  :show-file-list="false"
                  @change="handleUploadChange"
                >
                  <n-upload-dragger class="!border-dashed !border-2 !border-gray-100 !bg-gray-50/50 hover:!border-brand/30 hover:!bg-white transition-all group py-12">
                    <div class="flex flex-col items-center space-y-4">
                      <div class="w-16 h-16 bg-white rounded-full flex items-center justify-center shadow-figma group-hover:scale-110 transition-transform duration-300">
                        <ArrowUpTrayIcon class="w-8 h-8 text-brand" />
                      </div>
                      <div class="text-center">
                        <p class="text-lg font-bold text-gray-900">点击或拖拽文件到这里上传</p>
                        <p class="text-sm text-gray-400 font-medium mt-1">支持 .docx 格式文档，最大支持 20MB</p>
                      </div>
                    </div>
                  </n-upload-dragger>
                </n-upload>
                
                <div class="flex items-start gap-4 p-4 bg-brand/5 rounded-figma border border-brand/10">
                  <div class="w-8 h-8 rounded-full bg-white flex items-center justify-center shrink-0 text-brand">
                    <BoltIcon class="w-4 h-4" />
                  </div>
                  <div class="text-sm">
                    <p class="font-bold text-brand">自动分块与向量化</p>
                    <p class="text-brand/70 font-medium leading-relaxed">系统将自动识别文档结构，将其分割为适合 AI 检索的小块，并利用高性能 Embedding 模型进行向量化存储。</p>
                  </div>
                </div>
              </div>
            </n-tab-pane>

            <n-tab-pane name="text">
              <template #tab>
                <div class="flex items-center gap-2 px-2">
                  <DocumentTextIcon class="w-4 h-4" />
                  <span class="font-bold">导入纯文本</span>
                </div>
              </template>
              
              <n-form label-placement="top" class="space-y-4">
                <n-form-item label="文档标题 (可选)">
                  <n-input 
                    v-model:value="textForm.title" 
                    placeholder="输入该内容的描述性标题..." 
                    class="!rounded-figma"
                  />
                </n-form-item>
                <n-form-item label="详细内容">
                  <n-input 
                    v-model:value="textForm.content" 
                    type="textarea" 
                    :rows="6" 
                    placeholder="在此粘贴或输入需要入库的文本内容..." 
                    class="!rounded-figma"
                  />
                </n-form-item>
                <div class="flex justify-end">
                  <button 
                    @click="handleIngestText"
                    :disabled="isIngestingText || !textForm.content"
                    class="flex items-center gap-2 px-6 py-2.5 bg-brand text-white rounded-figma font-bold text-sm hover:bg-gray-900 active:scale-95 transition-all shadow-figma disabled:opacity-50"
                  >
                    <CheckCircleIcon class="w-[18px] h-[18px]" />
                    {{ isIngestingText ? '正在入库...' : '立即入库' }}
                  </button>
                </div>
              </n-form>
            </n-tab-pane>
          </n-tabs>
        </div>
      </div>

      <!-- Right: Tips/Status Summary -->
      <div class="lg:col-span-4 space-y-6">
        <div class="bg-gray-900 rounded-figma-lg p-8 text-white shadow-2xl relative overflow-hidden h-full">
          <div class="relative z-10 space-y-6">
            <h2 class="text-xl font-bold flex items-center gap-2">
              <ArrowTopRightOnSquareIcon class="w-5 h-5" />
              入库指南
            </h2>
            <div class="space-y-4">
              <div class="flex items-start gap-3">
                <div class="w-6 h-6 bg-white/10 rounded-full flex items-center justify-center shrink-0 text-xs font-bold">1</div>
                <p class="text-sm text-white/70 leading-relaxed font-medium">确保文档排版清晰，目录和标题有助于提高解析精度。</p>
              </div>
              <div class="flex items-start gap-3">
                <div class="w-6 h-6 bg-white/10 rounded-full flex items-center justify-center shrink-0 text-xs font-bold">2</div>
                <p class="text-sm text-white/70 leading-relaxed font-medium">Word 文档中的表格会被尽可能保留其语义关联性。</p>
              </div>
              <div class="flex items-start gap-3">
                <div class="w-6 h-6 bg-white/10 rounded-full flex items-center justify-center shrink-0 text-xs font-bold">3</div>
                <p class="text-sm text-white/70 leading-relaxed font-medium">入库后的内容将立即在“问答系统”中生效。</p>
              </div>
            </div>
            
            <div class="pt-6 border-t border-white/10">
              <div class="flex items-center justify-between mb-4">
                <span class="text-sm font-bold text-white/50 uppercase tracking-widest">知识库统计</span>
              </div>
              <div class="grid grid-cols-2 gap-4">
                <div>
                  <p class="text-2xl font-bold">{{ docs.length }}</p>
                  <p class="text-xs text-white/40 font-bold uppercase">已存文档</p>
                </div>
                <div>
                  <p class="text-2xl font-bold">2.4k</p>
                  <p class="text-xs text-white/40 font-bold uppercase">向量节点</p>
                </div>
              </div>
            </div>
          </div>
          <!-- Decoration -->
          <div class="absolute -bottom-10 -right-10 w-40 h-40 bg-brand rounded-full blur-3xl opacity-30" />
        </div>
      </div>
    </div>

    <!-- Documents List -->
    <div class="space-y-6">
      <div class="flex items-center gap-2">
        <DocumentTextIcon class="w-5 h-5 text-brand" />
        <h2 class="text-xl font-bold text-gray-900 tracking-tight">入库记录列表</h2>
      </div>

      <div class="bg-white rounded-figma-lg shadow-figma border border-gray-100 overflow-hidden">
        <div class="overflow-x-auto">
          <table class="w-full text-left border-collapse">
            <thead>
              <tr class="bg-gray-50 border-b border-gray-100">
                <th class="px-6 py-4 text-[11px] font-bold text-gray-400 uppercase tracking-widest">文档 ID</th>
                <th class="px-6 py-4 text-[11px] font-bold text-gray-400 uppercase tracking-widest">文件名 / 标题</th>
                <th class="px-6 py-4 text-[11px] font-bold text-gray-400 uppercase tracking-widest">状态</th>
                <th class="px-6 py-4 text-[11px] font-bold text-gray-400 uppercase tracking-widest">创建时间</th>
                <th class="px-6 py-4 text-[11px] font-bold text-gray-400 uppercase tracking-widest text-right">操作</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-50">
              <tr 
                v-for="row in filteredDocs" 
                :key="row.id"
                class="hover:bg-gray-50/80 transition-colors group"
              >
                <td class="px-6 py-4 text-xs font-mono text-gray-400">#{{ row.id }}</td>
                <td class="px-6 py-4">
                  <div class="flex items-center gap-3">
                    <div class="w-8 h-8 rounded-figma bg-gray-100 flex items-center justify-center text-gray-500 group-hover:bg-brand/10 group-hover:text-brand transition-all">
                      <DocumentTextIcon class="w-4 h-4" />
                    </div>
                    <span class="text-sm font-bold text-gray-900 truncate max-w-[200px]">{{ row.original_name }}</span>
                  </div>
                </td>
                <td class="px-6 py-4">
                  <div class="flex items-center gap-2">
                    <component 
                      :is="statusConfig[row.status as keyof typeof statusConfig]?.icon || statusConfig.default.icon" 
                      class="w-3.5 h-3.5"
                      :class="statusConfig[row.status as keyof typeof statusConfig]?.color || statusConfig.default.color"
                    />
                    <span :class="['text-xs font-bold', statusConfig[row.status as keyof typeof statusConfig]?.color || statusConfig.default.color]">
                      {{ statusConfig[row.status as keyof typeof statusConfig]?.label || statusConfig.default.label }}
                    </span>
                  </div>
                </td>
                <td class="px-6 py-4 text-xs text-gray-500 font-medium">{{ row.created_at }}</td>
                <td class="px-6 py-4">
                  <div class="flex items-center justify-end gap-2">
                    <button 
                      @click="router.push({ name: 'rag-document-detail', params: { collectionId, docId: row.id } })"
                      class="p-2 text-gray-400 hover:text-brand hover:bg-brand/5 rounded-figma transition-all"
                    >
                      <ArrowTopRightOnSquareIcon class="w-4 h-4" />
                    </button>
                    <button 
                      @click="handleDownload(row)"
                      class="p-2 text-gray-400 hover:text-gray-900 hover:bg-gray-100 rounded-figma transition-all"
                    >
                      <ArrowDownTrayIcon class="w-4 h-4" />
                    </button>
                    <n-popconfirm v-if="isAdmin" @positive-click="handleDelete(row)">
                      <template #trigger>
                        <button class="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-figma transition-all">
                          <TrashIcon class="w-4 h-4" />
                        </button>
                      </template>
                      确认从知识库永久删除该文档吗？
                    </n-popconfirm>
                  </div>
                </td>
              </tr>
              <tr v-if="filteredDocs.length === 0">
                <td colspan="5" class="px-6 py-20 text-center text-gray-400 font-medium">
                  暂无匹配的文档记录
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
:deep(.n-tabs-tab) {
  padding: 12px 0 !important;
}

:deep(.n-tabs-bar) {
  background-color: #000 !important;
}

:deep(.n-tabs-tab--active .n-tabs-tab__label) {
  color: #000 !important;
}

:deep(.n-upload-dragger) {
  border-radius: 12px !important;
}
</style>
