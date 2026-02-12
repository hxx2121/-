<script setup lang="ts">
import { computed, ref, onMounted } from "vue"
import { 
  ShieldCheckIcon, 
  ArrowPathIcon, 
  PlayIcon, 
  ArrowUturnLeftIcon, 
  CheckCircleIcon, 
  XCircleIcon, 
  ClockIcon, 
  QuestionMarkCircleIcon,
  CommandLineIcon,
  ChartBarIcon,
  BugAntIcon,
  BoltIcon,
  CpuChipIcon,
  ChevronRightIcon,
  CircleStackIcon,
  LockClosedIcon,
  MagnifyingGlassIcon
} from "@heroicons/vue/24/outline"
import { useAuthStore } from "@/stores/auth-store"
import { listAdminUsers } from "@/api/auth"
import { downloadUserFile, listUserFiles, uploadUserFile } from "@/api/utils"
import {
  adminCollectionOverview,
  createAdminPrompt,
  createAdminTool,
  createAdminToolPolicy,
  createCollection,
  createThread,
  deleteAdminPrompt,
  deleteAdminTool,
  deleteAdminToolPolicy,
  deleteCollection,
  deleteDocument,
  deleteThread,
  listAdminPrompts,
  listAdminToolPolicies,
  listAdminTools,
  listCollections,
  listDocuments,
  listMessages,
  listThreads,
  patchAdminPrompt,
  patchAdminTool,
  patchAdminToolPolicy,
  sendMessage,
  uploadDocument,
} from "@/api/rag"
import { useMessage, NTag, NSwitch, NProgress, NScrollbar, NTooltip } from "naive-ui"
import gsap from "gsap"

const authStore = useAuthStore()
const message = useMessage()

const rows = ref<Array<{ name: string; status: "idle" | "running" | "pass" | "fail" | "skip"; detail: string }>>([])
const isRunning = ref(false)
const includeSlow = ref(false)

const isAdmin = computed(() => authStore.me?.is_admin)

function resetRows() {
  rows.value = [
    { name: "auth.me", status: "idle", detail: "" },
    { name: "rag.collections.list", status: "idle", detail: "" },
    { name: "rag.collections.create", status: "idle", detail: "" },
    { name: "rag.docs.list", status: "idle", detail: "" },
    { name: "rag.docs.upload (slow)", status: "idle", detail: "" },
    { name: "rag.docs.delete (admin)", status: "idle", detail: "" },
    { name: "rag.threads.list", status: "idle", detail: "" },
    { name: "rag.threads.create", status: "idle", detail: "" },
    { name: "rag.messages.list", status: "idle", detail: "" },
    { name: "rag.messages.send (slow)", status: "idle", detail: "" },
    { name: "rag.threads.delete", status: "idle", detail: "" },
    { name: "utils.files.upload", status: "idle", detail: "" },
    { name: "utils.files.list", status: "idle", detail: "" },
    { name: "utils.files.download", status: "idle", detail: "" },
    { name: "auth.admin.users.list (admin)", status: "idle", detail: "" },
    { name: "rag.admin.collections.overview (admin)", status: "idle", detail: "" },
    { name: "rag.admin.tools.crud (admin)", status: "idle", detail: "" },
    { name: "rag.admin.policies.crud (admin)", status: "idle", detail: "" },
    { name: "rag.admin.prompts.crud (admin)", status: "idle", detail: "" },
    { name: "rag.collections.delete", status: "idle", detail: "" },
  ]
}

resetRows()

const stats = computed(() => {
  const total = rows.value.length
  const pass = rows.value.filter(r => r.status === 'pass').length
  const fail = rows.value.filter(r => r.status === 'fail').length
  const skip = rows.value.filter(r => r.status === 'skip').length
  const progress = total > 0 ? Math.round(((pass + fail + skip) / total) * 100) : 0
  return { total, pass, fail, skip, progress }
})

function findRow(name: string) {
  const row = rows.value.find((r) => r.name === name)
  if (!row) throw new Error(`missing row: ${name}`)
  return row
}

async function runCase(name: string, run: () => Promise<string>, opts?: { skip?: boolean }) {
  const row = findRow(name)
  if (opts?.skip) {
    row.status = "skip"
    row.detail = "跳过测试"
    return
  }
  row.status = "running"
  row.detail = ""
  try {
    const detail = await run()
    row.status = "pass"
    row.detail = detail
  } catch (e) {
    row.status = "fail"
    row.detail = e instanceof Error ? e.message : String(e)
    throw e
  }
}

async function runAll() {
  if (isRunning.value) return
  isRunning.value = true
  resetRows()
  const created: {
    collectionId?: number
    docId?: number
    threadId?: number
    fileId?: number
    toolId?: number
    policyId?: number
    promptId?: number
  } = {}

  try {
    await runCase("auth.me", async () => {
      await authStore.refreshMe()
      return `username=${authStore.me?.username || ""}`
    })

    await runCase("rag.collections.list", async () => {
      const out = await listCollections()
      return `count=${out.length}`
    })

    await runCase("rag.collections.create", async () => {
      const name = `api_check_${Date.now()}`
      const out = await createCollection({ name, description: "api-check", roles_json: [] })
      created.collectionId = out.id
      return `id=${out.id}`
    })

    await runCase("rag.docs.list", async () => {
      const out = await listDocuments(created.collectionId || 0)
      return `count=${out.length}`
    })

    await runCase(
      "rag.docs.upload (slow)",
      async () => {
        const f = new File([new Blob(["hello rag\n"], { type: "text/plain" })], "api-check.txt", { type: "text/plain" })
        const out = await uploadDocument(created.collectionId || 0, f)
        created.docId = out.id
        return `doc_id=${out.id} status=${out.status}`
      },
      { skip: !includeSlow.value },
    )

    await runCase(
      "rag.docs.delete (admin)",
      async () => {
        await deleteDocument(created.docId || 0)
        return `doc_id=${created.docId}`
      },
      { skip: !isAdmin.value || !created.docId },
    )

    await runCase("rag.threads.list", async () => {
      const out = await listThreads()
      return `count=${out.length}`
    })

    await runCase("rag.threads.create", async () => {
      const out = await createThread({ title: `api-check-${Date.now()}`, scene: "normal" })
      created.threadId = out.id
      return `thread_id=${out.id}`
    })

    await runCase("rag.messages.list", async () => {
      const out = await listMessages(created.threadId || 0)
      return `count=${out.length}`
    })

    await runCase(
      "rag.messages.send (slow)",
      async () => {
        const out = await sendMessage(created.threadId || 0, { content: "你好，简单回复即可", collection_id: created.collectionId || 1 })
        return `message_id=${out.id} role=${out.role}`
      },
      { skip: !includeSlow.value },
    )

    await runCase("rag.threads.delete", async () => {
      await deleteThread(created.threadId || 0)
      return `thread_id=${created.threadId}`
    })

    await runCase("utils.files.upload", async () => {
      const out = await uploadUserFile(new File([new Blob(["hello file\n"], { type: "text/plain" })], "api-file.txt", { type: "text/plain" }))
      created.fileId = out.id
      return `file_id=${out.id}`
    })

    await runCase("utils.files.list", async () => {
      const out = await listUserFiles()
      return `count=${out.length}`
    })

    await runCase("utils.files.download", async () => {
      const out = await downloadUserFile(created.fileId || 0)
      return `filename=${out.filename} size=${out.blob.size}`
    })

    await runCase("auth.admin.users.list (admin)", async () => {
      const out = await listAdminUsers()
      return `count=${out.length}`
    }, { skip: !isAdmin.value })

    await runCase("rag.admin.collections.overview (admin)", async () => {
      const out = await adminCollectionOverview()
      return `count=${out.length}`
    }, { skip: !isAdmin.value })

    await runCase(
      "rag.admin.tools.crud (admin)",
      async () => {
        const tool = await createAdminTool({ name: `api_tool_${Date.now()}`, title: "api tool", description: "api tool", is_enabled: true, risk_level: "low" })
        created.toolId = tool.id
        await patchAdminTool(tool.id, { description: "api tool updated" })
        const list = await listAdminTools()
        await deleteAdminTool(tool.id)
        return `created=${tool.id} listed=${list.length}`
      },
      { skip: !isAdmin.value },
    )

    await runCase(
      "rag.admin.policies.crud (admin)",
      async () => {
        const tool = await createAdminTool({ name: `api_tool_policy_${Date.now()}`, title: "t", description: "t", is_enabled: true, risk_level: "low" })
        created.toolId = tool.id
        const policy = await createAdminToolPolicy({ tool: tool.id, scope_type: "global", scope_id: null, is_allowed: true, allowed_domains: [], rate_limit_per_day: 0 })
        created.policyId = policy.id
        await patchAdminToolPolicy(policy.id, { is_allowed: false })
        const list = await listAdminToolPolicies()
        await deleteAdminToolPolicy(policy.id)
        await deleteAdminTool(tool.id)
        return `created=${policy.id} listed=${list.length}`
      },
      { skip: !isAdmin.value },
    )

    await runCase(
      "rag.admin.prompts.crud (admin)",
      async () => {
        const prompt = await createAdminPrompt({ scene: `api_scene_${Date.now()}`, version: "v1", system_prompt: "s", user_prompt_template: "u", is_active: false })
        created.promptId = prompt.id
        await patchAdminPrompt(prompt.id, { is_active: false })
        const list = await listAdminPrompts()
        await deleteAdminPrompt(prompt.id)
        return `created=${prompt.id} listed=${list.length}`
      },
      { skip: !isAdmin.value },
    )

    await runCase(
      "rag.collections.delete",
      async () => {
        await deleteCollection(created.collectionId || 0)
        return `collection_id=${created.collectionId}`
      },
      { skip: !isAdmin.value || !created.collectionId },
    )

    message.success("API 自检流程已完成")
  } catch (e) {
    message.error("检测过程中发现异常断点")
  } finally {
    isRunning.value = false
  }
}

onMounted(() => {
  gsap.from(".page-header", { opacity: 0, y: -20, duration: 0.5, ease: "power2.out" })
})
</script>

<template>
  <div class="max-w-5xl mx-auto space-y-8 pb-12">
    <!-- Header -->
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 page-header">
      <div>
        <h1 class="text-3xl font-bold text-gray-900 tracking-tight flex items-center gap-3">
          <BugAntIcon class="w-7 h-7 text-brand" />
          API 自动化自检
        </h1>
        <p class="mt-1 text-gray-500 font-medium">开发者专用：全链路接口可用性与数据结构契约测试</p>
      </div>
      <div class="flex items-center gap-3">
        <div class="px-3 py-1 bg-gray-100 rounded-full flex items-center gap-2">
          <div :class="['w-2 h-2 rounded-full', isAdmin ? 'bg-green-500' : 'bg-orange-500']"></div>
          <span class="text-[10px] font-bold text-gray-600 uppercase">{{ isAdmin ? 'Admin Context' : 'User Context' }}</span>
        </div>
        <button 
          @click="resetRows"
          class="p-2 rounded-figma border border-gray-200 bg-white text-gray-500 hover:text-brand hover:border-brand/20 transition-all shadow-sm"
        >
          <ArrowUturnLeftIcon class="w-5 h-5" />
        </button>
        <button 
          @click="runAll"
          :disabled="isRunning"
          class="flex items-center gap-2 px-6 py-2 bg-brand text-white rounded-figma font-bold text-sm hover:bg-gray-900 active:scale-95 transition-all shadow-figma disabled:opacity-50"
        >
          <PlayIcon class="w-5 h-5" v-if="!isRunning" />
          <ArrowPathIcon class="w-5 h-5 animate-spin" v-else />
          {{ isRunning ? '正在测试' : '运行全量测试' }}
        </button>
      </div>
    </div>

    <!-- Testing Controls & Status -->
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-8">
      <!-- Left: Summary -->
      <div class="lg:col-span-4 space-y-6">
        <div class="bg-white p-8 rounded-figma-lg border border-gray-100 shadow-figma space-y-8">
          <div class="flex flex-col items-center text-center space-y-4">
            <div class="w-20 h-20 bg-brand/5 rounded-figma-lg flex items-center justify-center text-brand shadow-inner">
              <ChartBarIcon class="w-10 h-10" />
            </div>
            <div>
              <h2 class="text-xl font-bold text-gray-900">执行进度</h2>
              <p class="text-sm text-gray-400 font-medium">测试用例总覆盖数: {{ stats.total }}</p>
            </div>
          </div>

          <div class="space-y-6 pt-4">
            <div class="space-y-2">
              <div class="flex justify-between text-xs font-bold uppercase tracking-widest text-gray-400 px-1">
                <span>Completion</span>
                <span>{{ stats.progress }}%</span>
              </div>
              <n-progress 
                type="line" 
                :percentage="stats.progress" 
                :show-indicator="false" 
                :height="8" 
                processing
                color="#000"
              />
            </div>

            <div class="grid grid-cols-3 gap-2">
              <div class="bg-green-50 p-3 rounded-figma text-center border border-green-100">
                <p class="text-lg font-bold text-green-600 leading-none">{{ stats.pass }}</p>
                <p class="text-[10px] font-bold text-green-600/60 uppercase mt-1">Pass</p>
              </div>
              <div class="bg-red-50 p-3 rounded-figma text-center border border-red-100">
                <p class="text-lg font-bold text-red-600 leading-none">{{ stats.fail }}</p>
                <p class="text-[10px] font-bold text-red-600/60 uppercase mt-1">Fail</p>
              </div>
              <div class="bg-gray-50 p-3 rounded-figma text-center border border-gray-100">
                <p class="text-lg font-bold text-gray-400 leading-none">{{ stats.skip }}</p>
                <p class="text-[10px] font-bold text-gray-400/60 uppercase mt-1">Skip</p>
              </div>
            </div>
          </div>

          <div class="pt-6 border-t border-gray-50">
            <label class="flex items-center justify-between cursor-pointer group">
              <div class="flex items-center gap-3">
                <div class="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center text-gray-400 group-hover:bg-brand/5 group-hover:text-brand transition-all">
                  <ClockIcon class="w-4 h-4" />
                </div>
                <div class="flex flex-col">
                  <span class="text-xs font-bold text-gray-700">包含慢速测试</span>
                  <span class="text-[10px] text-gray-400 font-medium uppercase tracking-tighter">LLM & Ingestion</span>
                </div>
              </div>
              <n-switch v-model:value="includeSlow" size="small" :rail-style="() => ({ background: includeSlow ? 'black' : '#e5e7eb' })" />
            </label>
          </div>
        </div>
      </div>

      <!-- Right: Detailed Steps -->
      <div class="lg:col-span-8">
        <div class="bg-white rounded-figma-lg border border-gray-100 shadow-figma overflow-hidden h-full flex flex-col">
          <div class="px-6 py-4 border-b border-gray-50 bg-gray-50/30 flex items-center gap-2">
            <CommandLineIcon class="w-4 h-4 text-gray-400" />
            <span class="text-[10px] font-bold text-gray-400 uppercase tracking-widest">测试步骤详情日志</span>
          </div>
          
          <n-scrollbar content-class="p-4 space-y-2">
            <div 
              v-for="r in rows" 
              :key="r.name"
              class="flex items-center justify-between p-3 rounded-figma border border-transparent hover:border-gray-100 hover:bg-gray-50/50 transition-all group"
            >
              <div class="flex items-center gap-3">
                <div 
                  :class="[
                    'w-2 h-2 rounded-full',
                    r.status === 'pass' ? 'bg-green-500' : 
                    r.status === 'fail' ? 'bg-red-500' : 
                    r.status === 'running' ? 'bg-orange-500 animate-pulse' : 
                    'bg-gray-200'
                  ]"
                ></div>
                <span class="text-sm font-mono font-bold text-gray-700">{{ r.name }}</span>
              </div>
              
              <div class="flex items-center gap-4">
                <div class="max-w-[20rem] truncate text-[11px] font-mono text-gray-400 text-right italic">
                  {{ r.detail }}
                </div>
                <div class="w-20 text-right">
                  <div 
                    v-if="r.status !== 'idle'"
                    :class="[
                      'inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider',
                      r.status === 'pass' ? 'bg-green-50 text-green-600' : 
                      r.status === 'fail' ? 'bg-red-50 text-red-600' : 
                      r.status === 'skip' ? 'bg-gray-100 text-gray-400' : 
                      'bg-orange-50 text-orange-600'
                    ]"
                  >
                    <component 
                      :is="r.status === 'pass' ? CheckCircleIcon : r.status === 'fail' ? XCircleIcon : r.status === 'skip' ? QuestionMarkCircleIcon : ArrowPathIcon" 
                      class="w-3 h-3"
                      :class="r.status === 'running' ? 'animate-spin' : ''"
                    />
                    {{ r.status }}
                  </div>
                  <span v-else class="text-[10px] font-bold text-gray-200 uppercase tracking-widest">Pending</span>
                </div>
              </div>
            </div>
          </n-scrollbar>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
:deep(.n-progress-graph-line-rail) {
  background-color: #f3f4f6 !important;
}
:deep(.n-switch.n-switch--active .n-switch__rail) {
  background-color: #000 !important;
}
</style>
