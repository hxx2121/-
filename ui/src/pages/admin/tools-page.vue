<script setup lang="ts">
import { onMounted, reactive, ref, computed } from "vue"
import { 
  WrenchIcon, 
  PlusIcon, 
  ArrowPathIcon, 
  TrashIcon, 
  CheckIcon, 
  ShieldExclamationIcon, 
  AdjustmentsHorizontalIcon, 
  Cog6ToothIcon,
  MagnifyingGlassIcon,
  ArrowTopRightOnSquareIcon,
  ChevronRightIcon,
  ShieldCheckIcon,
  InformationCircleIcon,
  EyeIcon
} from "@heroicons/vue/24/outline"
import type { ToolCreateRequest, ToolDefinitionItem, ToolUpdateRequest } from "@/types/rag"
import { createAdminTool, deleteAdminTool, listAdminTools, patchAdminTool } from "@/api/rag"
import { NModal, NForm, NFormItem, NInput, NSwitch, NPopconfirm, useMessage, NTag, NSelect, NButton } from "naive-ui"
import gsap from "gsap"

const message = useMessage()
const rows = ref<ToolDefinitionItem[]>([])
const isLoading = ref(false)
const searchQuery = ref("")
const isCreateOpen = ref(false)

// 描述预览弹窗
const isDescModalOpen = ref(false)
const currentDescTool = ref<ToolDefinitionItem | null>(null)
const editingDesc = ref("")

function openDescModal(row: ToolDefinitionItem) {
  currentDescTool.value = row
  editingDesc.value = row.description || ""
  isDescModalOpen.value = true
}

function saveDesc() {
  if (currentDescTool.value) {
    currentDescTool.value.description = editingDesc.value
  }
  isDescModalOpen.value = false
}

const createForm = reactive<ToolCreateRequest>({ 
  name: "", 
  title: "", 
  description: "", 
  is_enabled: true, 
  risk_level: "medium" 
})

const riskOptions = [
  { label: "低风险 (Low)", value: "low" },
  { label: "中等风险 (Medium)", value: "medium" },
  { label: "高风险 (High)", value: "high" }
]

const riskConfig: Record<string, { color: string, bg: string, label: string }> = {
  low: { color: 'text-green-600', bg: 'bg-green-50', label: '低风险' },
  medium: { color: 'text-orange-600', bg: 'bg-orange-50', label: '中等风险' },
  high: { color: 'text-red-600', bg: 'bg-red-50', label: '高风险' }
}

async function refresh() {
  isLoading.value = true
  try {
    rows.value = await listAdminTools()
  } catch {
    message.error("加载工具列表失败")
  } finally {
    isLoading.value = false
  }
}

async function handleCreate() {
  if (!createForm.name || !createForm.title) return
  try {
    await createAdminTool(createForm)
    isCreateOpen.value = false
    createForm.name = ""
    createForm.title = ""
    createForm.description = ""
    createForm.is_enabled = true
    createForm.risk_level = "medium"
    message.success("新工具已注册")
    await refresh()
  } catch {
    message.error("创建失败")
  }
}

async function handleSave(row: ToolDefinitionItem) {
  try {
    const payload: ToolUpdateRequest = {
      title: row.title,
      description: row.description,
      is_enabled: row.is_enabled,
      risk_level: row.risk_level,
    }
    await patchAdminTool(row.id, payload)
    message.success(`工具 ${row.name} 配置已更新`)
    await refresh()
  } catch {
    message.error("更新失败")
  }
}

async function handleDelete(id: number) {
  try {
    await deleteAdminTool(id)
    message.success("工具已移除")
    await refresh()
  } catch {
    message.error("删除失败")
  }
}

const filteredRows = computed(() => {
  if (!searchQuery.value) return rows.value
  const q = searchQuery.value.toLowerCase()
  return rows.value.filter(r => 
    r.name.toLowerCase().includes(q) || 
    r.title.toLowerCase().includes(q) ||
    r.description?.toLowerCase().includes(q)
  )
})

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
          <WrenchIcon class="w-7 h-7 text-brand" />
          工具能力管理
        </h1>
        <p class="mt-1 text-gray-500 font-medium">配置和启用 AI 助手可以调用的外部工具与函数接口</p>
      </div>
      <div class="flex items-center gap-3">
        <div class="relative">
          <MagnifyingGlassIcon class="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input 
            v-model="searchQuery"
            type="text" 
            placeholder="搜索工具名称..." 
            class="pl-10 pr-4 py-2 bg-white border border-gray-200 rounded-figma text-sm w-64 focus:border-brand/30 outline-none transition-all shadow-sm"
          />
        </div>
        <button 
          @click="refresh"
          :class="['p-2 rounded-figma border border-gray-200 bg-white text-gray-500 hover:text-brand hover:border-brand/20 transition-all shadow-sm', isLoading && 'animate-spin text-brand']"
        >
          <ArrowPathIcon class="w-5 h-5" />
        </button>
        <button 
          @click="isCreateOpen = true"
          class="flex items-center gap-2 px-4 py-2 bg-brand text-white rounded-figma font-bold text-sm hover:bg-gray-900 active:scale-95 transition-all shadow-figma"
        >
          <PlusIcon class="w-5 h-5" />
          注册工具
        </button>
      </div>
    </div>

    <!-- Info Banner -->
    <div class="bg-blue-50 border border-blue-100 rounded-figma-lg p-4 flex items-start gap-4">
      <div class="w-10 h-10 bg-white rounded-figma flex items-center justify-center text-blue-600 shadow-sm shrink-0">
        <InformationCircleIcon class="w-5 h-5" />
      </div>
      <div>
        <p class="text-sm font-bold text-blue-900">提示</p>
        <p class="text-xs text-blue-700/80 font-medium leading-relaxed">
          工具启用后，Agent 场景下的 AI 助手将能够根据用户的需求自动选择并调用这些接口。请务必配置正确的风险等级以确保系统安全。
        </p>
      </div>
    </div>

    <!-- Tools List -->
    <div class="bg-white rounded-figma-lg shadow-figma border border-gray-100 overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-left border-collapse">
          <thead>
            <tr class="bg-gray-50 border-b border-gray-100">
              <th class="px-6 py-4 text-[10px] font-bold text-gray-400 uppercase tracking-widest">ID / 内部标识</th>
              <th class="px-6 py-4 text-[10px] font-bold text-gray-400 uppercase tracking-widest">展示名称</th>
              <th class="px-6 py-4 text-[10px] font-bold text-gray-400 uppercase tracking-widest">风险等级</th>
              <th class="px-6 py-4 text-[10px] font-bold text-gray-400 uppercase tracking-widest">状态</th>
              <th class="px-6 py-4 text-[10px] font-bold text-gray-400 uppercase tracking-widest">详细描述</th>
              <th class="px-6 py-4 text-[10px] font-bold text-gray-400 uppercase tracking-widest text-right">操作</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-50">
            <tr 
              v-for="(row, idx) in filteredRows" 
              :key="row.id"
              class="hover:bg-gray-50/30 transition-colors group"
            >
              <td class="px-6 py-4">
                <div class="flex flex-col">
                  <span class="text-[10px] font-mono text-gray-400">#{{ row.id }}</span>
                  <span class="text-sm font-mono font-bold text-gray-900">{{ row.name }}</span>
                </div>
              </td>
              <td class="px-6 py-4">
                <input 
                  v-model="row.title" 
                  class="bg-transparent border-b border-transparent focus:border-brand/20 outline-none text-sm font-bold text-gray-800 w-full py-1 transition-all"
                />
              </td>
              <td class="px-6 py-4">
                <select 
                  v-model="row.risk_level" 
                  :class="['bg-transparent text-[10px] font-bold uppercase tracking-wider border-none outline-none cursor-pointer p-1 rounded', riskConfig[row.risk_level]?.color, riskConfig[row.risk_level]?.bg]"
                >
                  <option value="low">低风险</option>
                  <option value="medium">中风险</option>
                  <option value="high">高风险</option>
                </select>
              </td>
              <td class="px-6 py-4">
                <n-switch v-model:value="row.is_enabled" size="small" :rail-style="() => ({ background: row.is_enabled ? 'black' : '#e5e7eb' })" />
              </td>
              <td class="px-6 py-4 max-w-xs">
                <button 
                  @click="openDescModal(row)"
                  class="flex items-center gap-2 text-xs text-gray-500 hover:text-brand transition-colors group/desc"
                >
                  <span class="truncate max-w-[200px]">{{ row.description || '点击添加描述...' }}</span>
                  <EyeIcon class="w-4 h-4 opacity-0 group-hover/desc:opacity-100 transition-opacity shrink-0" />
                </button>
              </td>
              <td class="px-6 py-4">
                <div class="flex items-center justify-end gap-2">
                  <button 
                    @click="handleSave(row)"
                    class="p-2 text-brand hover:bg-brand/5 rounded-figma transition-all"
                    title="保存修改"
                  >
                    <CheckIcon class="w-5 h-5" />
                  </button>
                  <n-popconfirm @positive-click="handleDelete(row.id)">
                    <template #trigger>
                      <button class="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-figma transition-all">
                        <TrashIcon class="w-5 h-5" />
                      </button>
                    </template>
                    确认永久注销并删除该工具定义吗？
                  </n-popconfirm>
                </div>
              </td>
            </tr>
            <tr v-if="filteredRows.length === 0 && !isLoading">
              <td colspan="6" class="px-6 py-20 text-center text-gray-400 font-medium italic">
                没有找到匹配的工具能力
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Create Modal -->
    <n-modal 
      v-model:show="isCreateOpen" 
      preset="card" 
      title="注册新工具接口" 
      style="width: 560px; border-radius: 12px"
      :segmented="{ content: true, footer: true }"
    >
      <n-form label-placement="top">
        <div class="grid grid-cols-2 gap-4">
          <n-form-item label="内部唯一名称 (Name)" required>
            <n-input v-model:value="createForm.name" placeholder="例如：web_search" />
          </n-form-item>
          <n-form-item label="展示名称 (Title)" required>
            <n-input v-model:value="createForm.title" placeholder="例如：联网搜索" />
          </n-form-item>
        </div>
        
        <n-form-item label="风险评估">
          <n-select v-model:value="createForm.risk_level" :options="riskOptions" />
        </n-form-item>

        <n-form-item label="功能描述">
          <n-input 
            v-model:value="createForm.description" 
            type="textarea" 
            placeholder="详细描述该工具的功能，这将帮助 AI 更好地理解何时调用它..." 
            :rows="4" 
          />
        </n-form-item>

        <n-form-item label="立即启用">
          <n-switch v-model:value="createForm.is_enabled" :rail-style="() => ({ background: createForm.is_enabled ? 'black' : '#e5e7eb' })" />
        </n-form-item>
      </n-form>
      <template #footer>
        <div class="flex justify-end gap-3">
          <n-button @click="isCreateOpen = false">取消</n-button>
          <n-button 
            type="primary" 
            :disabled="!createForm.name" 
            @click="handleCreate"
            class="!bg-brand !font-bold"
          >
            完成注册
          </n-button>
        </div>
      </template>
    </n-modal>

    <!-- Description Preview/Edit Modal -->
    <n-modal 
      v-model:show="isDescModalOpen" 
      preset="card" 
      title="工具详细描述" 
      style="width: 600px; border-radius: 12px"
      :segmented="{ content: true, footer: true }"
    >
      <div v-if="currentDescTool" class="space-y-4">
        <div class="flex items-center gap-3 p-3 bg-gray-50 rounded-figma">
          <div class="w-10 h-10 bg-brand rounded-figma flex items-center justify-center text-white">
            <WrenchIcon class="w-5 h-5" />
          </div>
          <div>
            <p class="font-bold text-gray-900">{{ currentDescTool.title }}</p>
            <p class="text-xs text-gray-500 font-mono">{{ currentDescTool.name }}</p>
          </div>
        </div>
        <n-input 
          v-model:value="editingDesc" 
          type="textarea" 
          placeholder="输入工具的详细描述，帮助 AI 理解何时以及如何调用此工具..." 
          :rows="8"
        />
      </div>
      <template #footer>
        <div class="flex justify-end gap-3">
          <n-button @click="isDescModalOpen = false">取消</n-button>
          <n-button 
            type="primary" 
            @click="saveDesc"
            class="!bg-brand !font-bold"
          >
            保存描述
          </n-button>
        </div>
      </template>
    </n-modal>
  </div>
</template>

<style scoped>
:deep(.n-modal) {
  border-radius: 12px !important;
}
:deep(.n-input) {
  border-radius: 8px !important;
}
:deep(.n-switch.n-switch--active .n-switch__rail) {
  background-color: #000 !important;
}
</style>

