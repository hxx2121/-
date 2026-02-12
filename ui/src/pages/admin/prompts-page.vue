<script setup lang="ts">
import { onMounted, reactive, ref, computed } from "vue"
import { 
  RectangleGroupIcon, 
  PlusIcon, 
  ArrowPathIcon, 
  TrashIcon, 
  CheckIcon, 
  CheckCircleIcon, 
  ClockIcon, 
  MagnifyingGlassIcon,
  ChatBubbleLeftRightIcon,
  CommandLineIcon,
  ChatBubbleLeftEllipsisIcon,
  HashtagIcon,
  ChartBarIcon,
  ClockIcon as HistoryIcon,
  InformationCircleIcon
} from "@heroicons/vue/24/outline"
import type { PromptCreateRequest, PromptTemplateItem, PromptUpdateRequest } from "@/types/qa"
import { createAdminPrompt, deleteAdminPrompt, listAdminPrompts, patchAdminPrompt } from "@/api/qa"
import { NModal, NForm, NFormItem, NInput, NSwitch, NPopconfirm, useMessage, NTag, NScrollbar, NButton } from "naive-ui"
import gsap from "gsap"

const message = useMessage()
const rows = ref<PromptTemplateItem[]>([])
const isLoading = ref(false)
const searchQuery = ref("")
const isCreateOpen = ref(false)

const createForm = reactive<PromptCreateRequest>({ 
  scene: "", 
  version: "v1", 
  system_prompt: "", 
  user_prompt_template: "", 
  is_active: false 
})

async function refresh() {
  isLoading.value = true
  try {
    rows.value = await listAdminPrompts()
  } catch {
    message.error("加载提示词模板失败")
  } finally {
    isLoading.value = false
  }
}

async function handleCreate() {
  if (!createForm.scene) return
  try {
    await createAdminPrompt(createForm)
    isCreateOpen.value = false
    createForm.scene = ""
    createForm.version = "v1"
    createForm.system_prompt = ""
    createForm.user_prompt_template = ""
    createForm.is_active = false
    message.success("模板创建成功")
    await refresh()
  } catch {
    message.error("创建失败")
  }
}

async function handleSave(row: PromptTemplateItem) {
  try {
    const payload: PromptUpdateRequest = {
      scene: row.scene,
      version: row.version,
      system_prompt: row.system_prompt,
      user_prompt_template: row.user_prompt_template,
      is_active: row.is_active,
    }
    await patchAdminPrompt(row.id, payload)
    message.success(`场景 ${row.scene} 的提示词模板已保存`)
    await refresh()
  } catch {
    message.error("保存失败")
  }
}

async function handleDelete(id: number) {
  try {
    await deleteAdminPrompt(id)
    message.success("模板已移除")
    await refresh()
  } catch {
    message.error("删除失败")
  }
}

const filteredRows = computed(() => {
  if (!searchQuery.value) return rows.value
  const q = searchQuery.value.toLowerCase()
  return rows.value.filter(r => 
    r.scene.toLowerCase().includes(q) || 
    r.version.toLowerCase().includes(q)
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
          <RectangleGroupIcon class="w-7 h-7 text-brand" />
          提示词模板库
        </h1>
        <p class="mt-1 text-gray-500 font-medium">设计和版本化 AI 助手在不同业务场景下的核心 Prompt 策略</p>
      </div>
      <div class="flex items-center gap-3">
        <div class="relative">
          <MagnifyingGlassIcon class="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input 
            v-model="searchQuery"
            type="text" 
            placeholder="搜索业务场景..." 
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
          新增模板
        </button>
      </div>
    </div>

    <!-- Main List -->
    <div class="space-y-6">
      <div v-for="(row, idx) in filteredRows" :key="row.id" 
        v-motion
        :initial="{ opacity: 0, y: 20 }"
        :enter="{ opacity: 1, y: 0, transition: { delay: idx * 50 } }"
        class="bg-white rounded-figma-lg border border-gray-100 shadow-figma hover:border-brand/10 transition-all overflow-hidden"
      >
        <!-- Card Top Bar -->
        <div class="px-6 py-4 border-b border-gray-50 flex items-center justify-between bg-gray-50/30">
          <div class="flex items-center gap-4">
            <div class="flex flex-col">
              <div class="flex items-center gap-2">
                <span class="text-xs font-bold text-gray-400 uppercase tracking-widest">ID: #{{ row.id }}</span>
                <span class="text-lg font-bold text-gray-900">{{ row.scene }}</span>
                <n-tag size="small" :bordered="false" class="!bg-gray-900 !text-white !text-[10px] font-bold">{{ row.version }}</n-tag>
              </div>
            </div>
          </div>
          <div class="flex items-center gap-4">
            <div class="flex items-center gap-2 mr-4">
              <span class="text-xs font-bold text-gray-400">当前激活</span>
              <n-switch v-model:value="row.is_active" size="small" :rail-style="() => ({ background: row.is_active ? 'black' : '#e5e7eb' })" />
            </div>
            <div class="flex items-center gap-2">
              <button @click="handleSave(row)" class="p-2 text-brand hover:bg-brand/5 rounded-figma transition-all" title="保存修改">
                <CheckIcon class="w-5 h-5" />
              </button>
              <n-popconfirm @positive-click="handleDelete(row.id)">
                <template #trigger>
                  <button class="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-figma transition-all">
                    <TrashIcon class="w-5 h-5" />
                  </button>
                </template>
                确认删除该提示词模板吗？该操作不可撤销。
              </n-popconfirm>
            </div>
          </div>
        </div>

        <!-- Prompt Content -->
        <div class="grid grid-cols-1 lg:grid-cols-2 divide-y lg:divide-y-0 lg:divide-x divide-gray-50">
          <!-- System Prompt -->
          <div class="p-6 space-y-3">
            <div class="flex items-center gap-2 text-[10px] font-bold text-gray-400 uppercase tracking-widest">
              <CommandLineIcon class="w-3 h-3" />
              系统角色设置 (System Prompt)
            </div>
            <textarea 
              v-model="row.system_prompt"
              rows="6"
              class="w-full bg-gray-50/50 border border-transparent focus:border-brand/10 focus:bg-white rounded-figma p-4 text-sm font-mono text-gray-700 leading-relaxed outline-none transition-all resize-none"
              placeholder="定义 AI 的角色定位和核心行为准则..."
            ></textarea>
          </div>

          <!-- User Prompt -->
          <div class="p-6 space-y-3">
            <div class="flex items-center gap-2 text-[10px] font-bold text-gray-400 uppercase tracking-widest">
              <ChatBubbleLeftEllipsisIcon class="w-3 h-3" />
              用户提示词模版 (User Prompt Template)
            </div>
            <textarea 
              v-model="row.user_prompt_template"
              rows="6"
              class="w-full bg-gray-50/50 border border-transparent focus:border-brand/10 focus:bg-white rounded-figma p-4 text-sm font-mono text-gray-700 leading-relaxed outline-none transition-all resize-none"
              placeholder="定义如何包装用户的输入请求，可以使用变量占位符..."
            ></textarea>
          </div>
        </div>
      </div>

      <!-- Empty State -->
      <div v-if="filteredRows.length === 0 && !isLoading" class="bg-white rounded-figma-lg border-2 border-dashed border-gray-200 p-20 flex flex-col items-center justify-center text-center space-y-6">
        <div class="w-20 h-20 bg-gray-50 rounded-full flex items-center justify-center text-gray-300">
          <RectangleGroupIcon class="w-10 h-10" />
        </div>
        <div>
          <h2 class="text-xl font-bold text-gray-900">未找到提示词模板</h2>
          <p class="text-gray-500 max-w-xs mt-2 font-medium">设计一个针对特定业务场景的提示词模板，让 AI 更好地理解其任务目标。</p>
        </div>
        <button 
          @click="isCreateOpen = true"
          class="px-6 py-2.5 bg-brand text-white rounded-figma font-bold text-sm shadow-figma hover:scale-105 transition-all"
        >
          创建首个模板
        </button>
      </div>
    </div>

    <!-- Create Modal -->
    <n-modal 
      v-model:show="isCreateOpen" 
      preset="card" 
      title="新建业务场景模板" 
      style="width: 800px; border-radius: 12px"
      :segmented="{ content: true, footer: true }"
    >
      <n-form label-placement="top">
        <div class="grid grid-cols-2 gap-6">
          <n-form-item label="业务场景标识 (Scene)" required>
            <n-input v-model:value="createForm.scene" placeholder="例如：customer_service, document_analysis" />
          </n-form-item>
          <n-form-item label="版本号 (Version)">
            <n-input v-model:value="createForm.version" placeholder="例如：v1.0.0" />
          </n-form-item>
        </div>
        
        <n-form-item label="立即激活">
          <n-switch v-model:value="createForm.is_active" :rail-style="() => ({ background: createForm.is_active ? 'black' : '#e5e7eb' })" />
        </n-form-item>

        <div class="grid grid-cols-1 gap-4">
          <n-form-item label="系统提示词 (System Prompt)">
            <n-input 
              v-model:value="createForm.system_prompt" 
              type="textarea" 
              placeholder="定义 AI 在此场景下的身份角色和必须遵循的约束规则..." 
              :rows="6" 
            />
          </n-form-item>
          <n-form-item label="用户请求模板 (User Prompt Template)">
            <n-input 
              v-model:value="createForm.user_prompt_template" 
              type="textarea" 
              placeholder="定义如何格式化来自用户的原始输入..." 
              :rows="6" 
            />
          </n-form-item>
        </div>
      </n-form>
      <template #footer>
        <div class="flex justify-end gap-3">
          <n-button @click="isCreateOpen = false">取消</n-button>
          <n-button 
            type="primary" 
            :disabled="!createForm.scene" 
            @click="handleCreate"
            class="!bg-brand !font-bold"
          >
            发布模板
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
