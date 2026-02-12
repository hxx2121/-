<script setup lang="ts">
import { onMounted, reactive, ref, computed } from "vue"
import { 
  ShieldCheckIcon, 
  PlusIcon, 
  ArrowPathIcon, 
  TrashIcon, 
  CheckIcon, 
  GlobeAltIcon, 
  BoltIcon, 
  MagnifyingGlassIcon,
  ChevronRightIcon,
  ShieldCheckIcon as ShieldIcon,
  InformationCircleIcon,
  LockClosedIcon,
  LockOpenIcon,
  Cog6ToothIcon
} from "@heroicons/vue/24/outline"
import type { ToolPolicyCreateRequest, ToolPolicyItem, ToolPolicyUpdateRequest } from "@/types/rag"
import { createAdminToolPolicy, deleteAdminToolPolicy, listAdminToolPolicies, patchAdminToolPolicy } from "@/api/rag"
import { NModal, NForm, NFormItem, NInput, NSwitch, NPopconfirm, useMessage, NTag, NInputNumber, NSelect } from "naive-ui"
import gsap from "gsap"

const message = useMessage()
const rows = ref<ToolPolicyItem[]>([])
const isLoading = ref(false)
const searchQuery = ref("")
const isCreateOpen = ref(false)

const createForm = reactive<ToolPolicyCreateRequest>({
  tool: 0,
  scope_type: "global",
  scope_id: null,
  is_allowed: true,
  allowed_domains: [],
  rate_limit_per_day: 0,
})

const scopeOptions = [
  { label: "全局 (Global)", value: "global" },
  { label: "合集专用 (Collection)", value: "collection" },
  { label: "特定用户 (User)", value: "user" }
]

async function refresh() {
  isLoading.value = true
  try {
    rows.value = await listAdminToolPolicies()
  } catch {
    message.error("加载工具策略失败")
  } finally {
    isLoading.value = false
  }
}

async function handleCreate() {
  if (!createForm.tool) return
  try {
    await createAdminToolPolicy(createForm)
    isCreateOpen.value = false
    // Reset form
    createForm.tool = 0
    createForm.scope_type = "global"
    createForm.scope_id = null
    createForm.is_allowed = true
    createForm.allowed_domains = []
    createForm.rate_limit_per_day = 0
    message.success("新策略已发布")
    await refresh()
  } catch {
    message.error("创建失败")
  }
}

async function handleSave(row: ToolPolicyItem) {
  try {
    const payload: ToolPolicyUpdateRequest = {
      scope_type: row.scope_type,
      scope_id: row.scope_id,
      is_allowed: row.is_allowed,
      allowed_domains: row.allowed_domains,
      rate_limit_per_day: row.rate_limit_per_day,
    }
    await patchAdminToolPolicy(row.id, payload)
    message.success(`策略 #${row.id} 已更新`)
    await refresh()
  } catch {
    message.error("保存失败")
  }
}

async function handleDelete(id: number) {
  try {
    await deleteAdminToolPolicy(id)
    message.success("策略已废弃")
    await refresh()
  } catch {
    message.error("删除失败")
  }
}

const filteredRows = computed(() => {
  if (!searchQuery.value) return rows.value
  const q = searchQuery.value.toLowerCase()
  return rows.value.filter(r => 
    r.scope_type.toLowerCase().includes(q) || 
    r.id.toString().includes(q) ||
    r.tool.toString().includes(q)
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
          <ShieldCheckIcon class="w-7 h-7 text-brand" />
          工具调用策略
        </h1>
        <p class="mt-1 text-gray-500 font-medium">精细化控制不同范围下的 AI 工具使用权限与频次限制</p>
      </div>
      <div class="flex items-center gap-3">
        <div class="relative">
          <MagnifyingGlassIcon class="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input 
            v-model="searchQuery"
            type="text" 
            placeholder="搜索策略或工具 ID..." 
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
          制定新策略
        </button>
      </div>
    </div>

    <!-- Stats/Context Banner -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div class="bg-gray-900 rounded-figma-lg p-6 text-white shadow-2xl flex items-center justify-between overflow-hidden relative">
        <div class="relative z-10">
          <p class="text-xs font-bold text-white/40 uppercase tracking-widest mb-1">活跃安全策略</p>
          <h2 class="text-3xl font-bold">{{ rows.filter(r => r.is_allowed).length }} <span class="text-sm font-medium text-white/40 ml-1">Active</span></h2>
        </div>
        <div class="w-16 h-16 bg-white/10 rounded-full flex items-center justify-center relative z-10">
          <ShieldIcon class="w-8 h-8 text-white/80" />
        </div>
        <div class="absolute -right-4 -bottom-4 w-32 h-32 bg-brand rounded-full blur-3xl opacity-20"></div>
      </div>
      <div class="bg-white rounded-figma-lg p-6 border border-gray-100 shadow-figma flex items-center justify-between">
        <div>
          <p class="text-xs font-bold text-gray-400 uppercase tracking-widest mb-1">拦截调用总数 (模拟)</p>
          <h2 class="text-3xl font-bold text-gray-900">142 <span class="text-sm font-medium text-gray-400 ml-1">Blocked</span></h2>
        </div>
        <div class="w-16 h-16 bg-red-50 rounded-full flex items-center justify-center">
          <LockClosedIcon class="w-8 h-8 text-red-500" />
        </div>
      </div>
    </div>

    <!-- Policies List -->
    <div class="bg-white rounded-figma-lg shadow-figma border border-gray-100 overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-left border-collapse">
          <thead>
            <tr class="bg-gray-50 border-b border-gray-100">
              <th class="px-6 py-4 text-[10px] font-bold text-gray-400 uppercase tracking-widest">策略 ID / 工具</th>
              <th class="px-6 py-4 text-[10px] font-bold text-gray-400 uppercase tracking-widest">生效范围</th>
              <th class="px-6 py-4 text-[10px] font-bold text-gray-400 uppercase tracking-widest text-center">状态</th>
              <th class="px-6 py-4 text-[10px] font-bold text-gray-400 uppercase tracking-widest">每日额度</th>
              <th class="px-6 py-4 text-[10px] font-bold text-gray-400 uppercase tracking-widest">白名单域名</th>
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
                  <span class="text-[10px] font-mono text-gray-400">Policy #{{ row.id }}</span>
                  <div class="flex items-center gap-2 mt-1">
                    <div class="w-6 h-6 bg-gray-100 rounded flex items-center justify-center text-gray-500">
                      <Cog6ToothIcon class="w-4 h-4" />
                    </div>
                    <span class="text-sm font-bold text-gray-900">Tool ID: {{ row.tool }}</span>
                  </div>
                </div>
              </td>
              <td class="px-6 py-4">
                <div class="flex flex-col gap-1.5">
                  <n-select 
                    v-model:value="row.scope_type" 
                    :options="scopeOptions" 
                    size="small" 
                    class="!w-32"
                  />
                  <div class="flex items-center gap-2">
                    <span class="text-[10px] font-bold text-gray-400 uppercase tracking-tighter">Scope ID</span>
                    <n-input-number 
                      v-model:value="row.scope_id" 
                      size="tiny" 
                      :min="0" 
                      placeholder="N/A"
                      class="!w-20"
                      :show-button="false"
                    />
                  </div>
                </div>
              </td>
              <td class="px-6 py-4">
                <div class="flex flex-col items-center gap-2">
                  <n-switch v-model:value="row.is_allowed" size="small" :rail-style="() => ({ background: row.is_allowed ? 'black' : '#e5e7eb' })" />
                  <span :class="['text-[10px] font-bold uppercase', row.is_allowed ? 'text-green-600' : 'text-red-500']">
                    {{ row.is_allowed ? 'Allowed' : 'Denied' }}
                  </span>
                </div>
              </td>
              <td class="px-6 py-4">
                <div class="flex items-center gap-2">
                  <n-input-number 
                    v-model:value="row.rate_limit_per_day" 
                    size="small" 
                    :min="0" 
                    class="!w-24"
                  />
                  <span class="text-[10px] text-gray-400 font-bold">req/day</span>
                </div>
              </td>
              <td class="px-6 py-4">
                <textarea 
                  :value="(row.allowed_domains || []).join(',')"
                  @input="(e) => (row.allowed_domains = (e.target as HTMLTextAreaElement).value.split(',').map(x => x.trim()).filter(Boolean))"
                  rows="1"
                  class="bg-transparent border-b border-transparent focus:border-brand/20 outline-none text-xs text-gray-500 w-full py-1 resize-none transition-all"
                  placeholder="domain.com, api.org..."
                ></textarea>
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
                    确认永久废弃并删除该策略定义吗？
                  </n-popconfirm>
                </div>
              </td>
            </tr>
            <tr v-if="filteredRows.length === 0 && !isLoading">
              <td colspan="6" class="px-6 py-20 text-center text-gray-400 font-medium italic">
                没有找到匹配的策略记录
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
      title="制定新的安全策略" 
      style="width: 560px; border-radius: 12px"
      :segmented="{ content: true, footer: true }"
    >
      <n-form label-placement="top">
        <div class="grid grid-cols-2 gap-4">
          <n-form-item label="关联工具 (Tool ID)" required>
            <n-input-number v-model:value="createForm.tool" :min="1" placeholder="输入工具 ID" class="w-full" />
          </n-form-item>
          <n-form-item label="允许访问">
            <n-switch v-model:value="createForm.is_allowed" :rail-style="() => ({ background: createForm.is_allowed ? 'black' : '#e5e7eb' })" />
          </n-form-item>
        </div>

        <div class="grid grid-cols-2 gap-4">
          <n-form-item label="作用域类型" required>
            <n-select v-model:value="createForm.scope_type" :options="scopeOptions" />
          </n-form-item>
          <n-form-item label="作用域 ID (可选)">
            <n-input-number v-model:value="createForm.scope_id" :min="0" placeholder="对应合集或用户 ID" class="w-full" />
          </n-form-item>
        </div>

        <n-form-item label="每日调用频次上限 (0 为无限制)">
          <n-input-number v-model:value="createForm.rate_limit_per_day" :min="0" class="w-full" />
        </n-form-item>

        <n-form-item label="域名白名单 (逗号分隔)">
          <n-input 
            :value="(createForm.allowed_domains || []).join(',')"
            @update:value="(v) => (createForm.allowed_domains = v.split(',').map(x => x.trim()).filter(Boolean))"
            type="textarea" 
            placeholder="例如：google.com, github.com" 
            :rows="3" 
          />
        </n-form-item>
      </n-form>
      <template #footer>
        <div class="flex justify-end gap-3">
          <n-button @click="isCreateOpen = false">取消</n-button>
          <n-button 
            type="primary" 
            :disabled="!createForm.tool" 
            @click="handleCreate"
            class="!bg-brand !font-bold"
          >
            发布策略
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
:deep(.n-input), :deep(.n-input-number) {
  border-radius: 8px !important;
}
:deep(.n-switch.n-switch--active .n-switch__rail) {
  background-color: #000 !important;
}
</style>

