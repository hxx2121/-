<script setup lang="ts">
import { computed, onMounted, ref } from "vue"
import { useMessage, NButton, NInput, NPopconfirm, NScrollbar, NTag } from "naive-ui"
import type { MessageItem, ThreadItem } from "@/types/qa"
import { createThread, deleteThread, listMessages, listThreads, sendMessage } from "@/api/qa"
import hljs from "highlight.js/lib/core"
import python from "highlight.js/lib/languages/python"
import "highlight.js/styles/github.css"

// 注册Python语言高亮
hljs.registerLanguage("python", python)

const message = useMessage()

const threads = ref<ThreadItem[]>([])
const currentThreadId = ref<number | null>(null)
const messages = ref<MessageItem[]>([])

const promptScene = ref("cot_programming")
const input = ref("")

const isLoadingThreads = ref(false)
const isLoadingMessages = ref(false)
const isSending = ref(false)

const hasThread = computed(() => currentThreadId.value !== null)

async function refreshThreads() {
  isLoadingThreads.value = true
  try {
    threads.value = await listThreads()
    if (threads.value.length && currentThreadId.value === null) {
      const first = threads.value[0]
      if (first) await openThread(first.id)
    }
  } catch {
    threads.value = []
  } finally {
    isLoadingThreads.value = false
  }
}

async function openThread(id: number) {
  currentThreadId.value = id
  isLoadingMessages.value = true
  try {
    messages.value = await listMessages(id)
    // 等待DOM更新后执行代码高亮
    setTimeout(() => {
      document.querySelectorAll('pre code').forEach((block) => {
        hljs.highlightElement(block as HTMLElement)
      })
    }, 0)
  } catch {
    messages.value = []
  } finally {
    isLoadingMessages.value = false
  }
}

async function newThread() {
  const t = await createThread({ title: "" })
  await refreshThreads()
  await openThread(t.id)
}

async function removeThread(id: number) {
  try {
    await deleteThread(id)
    if (currentThreadId.value === id) {
      currentThreadId.value = null
      messages.value = []
    }
    await refreshThreads()
    message.success("会话已删除")
  } catch (e) {
    message.error((e as any)?.message || "删除失败")
  }
}

async function handleSend() {
  const text = input.value.trim()
  if (!text) return

  try {
    isSending.value = true
    if (!hasThread.value) {
      await newThread()
    }
    const threadId = currentThreadId.value as number
    const resp = await sendMessage(threadId, { content: text, prompt_scene: promptScene.value })
    messages.value.push(resp.user)
    messages.value.push(resp.assistant)
    input.value = ""
    
    // 等待DOM更新后执行代码高亮
    setTimeout(() => {
      document.querySelectorAll('pre code').forEach((block) => {
        hljs.highlightElement(block as HTMLElement)
      })
    }, 0)
  } catch (e) {
    message.error((e as any)?.message || "发送失败")
  } finally {
    isSending.value = false
  }
}

// 提取消息中的标签
function extractTags(content: string): string[] {
  // 尝试从JSON格式的回答中提取标签
  try {
    const jsonMatch = content.match(/\{[\s\S]*?\}/)
    if (jsonMatch) {
      const jsonContent = JSON.parse(jsonMatch[0])
      if (jsonContent.predicted_tags && Array.isArray(jsonContent.predicted_tags)) {
        return jsonContent.predicted_tags
      }
    }
  } catch {
    // 解析失败，返回空数组
  }
  return []
}

function getMatchAndRecommendPayload(m: MessageItem): { matches: any[]; recommendations: any[] } | null {
  const events = Array.isArray(m.tool_events) ? m.tool_events : []
  for (const ev of events) {
    if (!ev || typeof ev !== "object") continue
    const name = (ev as any).name
    if (name !== "qa_match_and_recommend") continue
    const toolOut = (ev as any).tool_out
    const result = toolOut?.result
    const matches = Array.isArray(result?.matches) ? result.matches : []
    const recommendations = Array.isArray(result?.recommendations) ? result.recommendations : []
    return { matches, recommendations }
  }
  return null
}

function fmtScore(v: unknown, digits = 3): string {
  const n = typeof v === "number" ? v : Number(v)
  if (!Number.isFinite(n)) return "-"
  return n.toFixed(digits)
}

onMounted(() => {
  refreshThreads()
})
</script>

<template>
  <div class="max-w-7xl mx-auto pb-12">
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-3xl font-bold text-gray-900 tracking-tight">编程问答</h1>
        <p class="mt-1 text-gray-500 font-medium">多轮对话 + 自动评分（语法/逻辑/通用性/可读性）</p>
      </div>
      <div class="flex items-center gap-3">
        <div class="w-56">
          <n-input v-model:value="promptScene" size="small" placeholder="prompt 场景，例如 cot_programming" />
        </div>
        <n-button type="primary" @click="newThread" :loading="isLoadingThreads">新建会话</n-button>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-4 gap-6">
      <div class="lg:col-span-1 bg-white rounded-figma-lg border border-gray-100 shadow-figma overflow-hidden">
        <div class="px-4 py-3 border-b border-gray-50 flex items-center justify-between">
          <span class="text-sm font-bold text-gray-900">会话列表</span>
          <n-button size="tiny" @click="refreshThreads" :loading="isLoadingThreads">刷新</n-button>
        </div>
        <n-scrollbar style="max-height: 520px">
          <div class="p-2 space-y-2">
            <button
              v-for="t in threads"
              :key="t.id"
              class="w-full text-left px-3 py-2 rounded-figma border transition-all"
              :class="currentThreadId === t.id ? 'border-brand/30 bg-brand/5' : 'border-gray-100 hover:border-gray-200 hover:bg-gray-50'"
              @click="openThread(t.id)"
            >
              <div class="flex items-center justify-between gap-2">
                <div class="min-w-0">
                  <p class="text-sm font-semibold text-gray-900 truncate">{{ t.title || `会话 #${t.id}` }}</p>
                  <p class="text-xs text-gray-400 mt-0.5">{{ t.updated_at }}</p>
                </div>
                <n-popconfirm @positive-click="removeThread(t.id)">
                  <template #trigger>
                    <span class="text-xs text-gray-400 hover:text-red-500 px-2 py-1">删除</span>
                  </template>
                  确认删除该会话吗？
                </n-popconfirm>
              </div>
            </button>
            <div v-if="!threads.length && !isLoadingThreads" class="px-4 py-10 text-center text-gray-400 text-sm">
              暂无会话
            </div>
          </div>
        </n-scrollbar>
      </div>

      <div class="lg:col-span-3 bg-white rounded-figma-lg border border-gray-100 shadow-figma overflow-hidden flex flex-col">
        <div class="px-6 py-4 border-b border-gray-50">
          <div class="flex items-center justify-between">
            <span class="text-sm font-bold text-gray-900">对话</span>
            <span class="text-xs text-gray-400" v-if="currentThreadId">Thread #{{ currentThreadId }}</span>
          </div>
        </div>

        <n-scrollbar style="max-height: 460px">
          <div class="p-6 space-y-4">
            <div v-if="isLoadingMessages" class="text-gray-400 text-sm">加载中...</div>
            <div v-if="!messages.length && !isLoadingMessages" class="text-gray-400 text-sm">
              发送一个编程问题开始对话。
            </div>

            <div v-for="m in messages" :key="m.id" class="space-y-2">
              <div class="flex items-center gap-2 flex-wrap">
                <n-tag size="small" :bordered="false" :type="m.role === 'assistant' ? 'success' : 'default'">
                  {{ m.role }}
                </n-tag>
                <span class="text-xs text-gray-400">{{ m.created_at }}</span>
                <n-tag
                  v-if="m.role === 'assistant' && m.evaluation"
                  size="small"
                  :bordered="false"
                  type="info"
                >
                  总分 {{ Number(m.evaluation.total_score).toFixed(1) }}
                </n-tag>
                
                <!-- 标签预测展示 -->
                <div v-if="m.role === 'assistant'" class="flex items-center gap-1 ml-2">
                  <span class="text-xs text-gray-500">标签:</span>
                  <n-tag
                    v-for="tag in extractTags(m.content)"
                    :key="tag"
                    size="small"
                    :bordered="false"
                    type="info"
                  >
                    {{ tag }}
                  </n-tag>
                </div>
              </div>

              <div v-if="m.role === 'assistant' && getMatchAndRecommendPayload(m)" class="border border-gray-100 rounded-figma p-4 bg-white">
                <div class="flex items-center justify-between">
                  <div class="text-sm font-semibold text-gray-900">问答匹配与回答推荐</div>
                  <div class="text-xs text-gray-400">向量召回 + 评分融合</div>
                </div>
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 mt-3">
                  <div>
                    <div class="text-xs font-semibold text-gray-700 mb-2">相似问题 Top {{ getMatchAndRecommendPayload(m)?.matches.length || 0 }}</div>
                    <div class="space-y-2">
                      <div
                        v-for="item in getMatchAndRecommendPayload(m)?.matches || []"
                        :key="String(item.question_id) + '-' + String(item.answer_id)"
                        class="p-3 rounded-figma border border-gray-100 bg-gray-50/50"
                      >
                        <div class="flex items-center justify-between gap-2">
                          <div class="text-sm font-semibold text-gray-900 truncate">{{ item.title }}</div>
                          <div class="text-xs text-gray-500 shrink-0">sim {{ fmtScore(item.similarity, 4) }}</div>
                        </div>
                        <div class="text-xs text-gray-500 mt-1">{{ item.question_excerpt }}</div>
                        <div class="flex items-center gap-2 mt-2 flex-wrap">
                          <span class="text-xs text-gray-400">upvotes {{ item.answer_score ?? 0 }}</span>
                          <n-tag
                            v-for="t in (Array.isArray(item.tags) ? item.tags.slice(0, 6) : [])"
                            :key="String(t)"
                            size="small"
                            :bordered="false"
                            type="info"
                          >
                            {{ t }}
                          </n-tag>
                        </div>
                      </div>
                      <div v-if="!(getMatchAndRecommendPayload(m)?.matches || []).length" class="text-xs text-gray-400">暂无匹配结果</div>
                    </div>
                  </div>

                  <div>
                    <div class="text-xs font-semibold text-gray-700 mb-2">推荐答案 Top {{ getMatchAndRecommendPayload(m)?.recommendations.length || 0 }}</div>
                    <div class="space-y-2">
                      <div
                        v-for="item in getMatchAndRecommendPayload(m)?.recommendations || []"
                        :key="'rec-' + String(item.question_id) + '-' + String(item.answer_id)"
                        class="p-3 rounded-figma border border-gray-100 bg-gray-50/50"
                      >
                        <div class="flex items-center justify-between gap-2">
                          <div class="text-sm font-semibold text-gray-900 truncate">{{ item.title }}</div>
                          <div class="text-xs text-gray-500 shrink-0">综合 {{ fmtScore(item.combined_score, 3) }}</div>
                        </div>
                        <div class="text-xs text-gray-500 mt-1">{{ item.answer_excerpt }}</div>
                        <div class="flex items-center gap-3 mt-2 flex-wrap text-xs text-gray-400">
                          <span>sim {{ fmtScore(item.similarity, 4) }}</span>
                          <span>upvotes {{ item.answer_score ?? 0 }}</span>
                          <span>质量 {{ fmtScore(item.quality?.total_score, 1) }}/10</span>
                        </div>
                      </div>
                      <div v-if="!(getMatchAndRecommendPayload(m)?.recommendations || []).length" class="text-xs text-gray-400">暂无推荐结果</div>
                    </div>
                  </div>
                </div>
              </div>
              
              <!-- 代码高亮显示 -->
              <div v-if="m.content.includes('```')" class="whitespace-pre-wrap text-sm leading-relaxed">
                <template v-for="(block, index) in m.content.split('```')" :key="index">
                  <span v-if="index % 2 === 0" class="text-gray-800">{{ block }}</span>
                  <pre v-else class="bg-gray-50/50 border border-gray-100 rounded-figma p-4 overflow-x-auto">
                    <code class="language-python">{{ block.replace(/^python\s*/i, '') }}</code>
                  </pre>
                </template>
              </div>
              <pre v-else class="whitespace-pre-wrap text-sm text-gray-800 leading-relaxed bg-gray-50/50 border border-gray-100 rounded-figma p-4">{{ m.content }}</pre>
              
              <div v-if="m.role === 'assistant' && m.evaluation" class="text-xs text-gray-500">
                语法 {{ Number(m.evaluation.syntax_score).toFixed(1) }} /
                逻辑 {{ Number(m.evaluation.logic_score).toFixed(1) }} /
                通用性 {{ Number(m.evaluation.utility_score).toFixed(1) }} /
                可读性 {{ Number(m.evaluation.readability_score).toFixed(1) }}
              </div>
            </div>
          </div>
        </n-scrollbar>

        <div class="px-6 py-4 border-t border-gray-50 space-y-3">
          <n-input
            v-model:value="input"
            type="textarea"
            :autosize="{ minRows: 3, maxRows: 8 }"
            placeholder="粘贴报错信息/代码片段/问题描述..."
            :disabled="isSending"
          />
          <div class="flex items-center justify-end gap-3">
            <n-button @click="input = ''" :disabled="isSending">清空</n-button>
            <n-button type="primary" @click="handleSend" :loading="isSending">发送</n-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* 自定义代码块样式 */
:deep(pre code) {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 13px;
  line-height: 1.5;
}

:deep(.hljs) {
  background: transparent;
  padding: 0;
}
</style>
