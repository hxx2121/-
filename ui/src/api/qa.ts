import type {
  AnswerMetricsData,
  DatasetPairDetailData,
  DatasetPairsPageData,
  DatasetSummaryData,
  MessageCreateRequest,
  MessageItem,
  PromptCreateRequest,
  PromptTemplateItem,
  PromptUpdateRequest,
  SendMessageResponse,
  ThreadCreateRequest,
  ThreadItem,
} from "@/types/qa"
import { requestR, requestRJson } from "@/api/http"

export async function qaAsk(payload: { question: string; prompt_scene?: string }): Promise<{ answer: string; evaluation?: unknown }> {
  return requestRJson<{ answer: string; evaluation?: unknown }>("/api/qa/qa/", "POST", payload)
}

export async function listThreads(): Promise<ThreadItem[]> {
  return requestR<ThreadItem[]>("/api/qa/threads/", { method: "GET" })
}

export async function createThread(payload: ThreadCreateRequest): Promise<ThreadItem> {
  return requestRJson<ThreadItem>("/api/qa/threads/", "POST", payload)
}

export async function deleteThread(threadId: number): Promise<boolean> {
  return requestR<boolean>(`/api/qa/threads/${threadId}/`, { method: "DELETE" })
}

export async function listMessages(threadId: number): Promise<MessageItem[]> {
  return requestR<MessageItem[]>(`/api/qa/threads/${threadId}/messages/`, { method: "GET" })
}

export async function sendMessage(threadId: number, payload: MessageCreateRequest): Promise<SendMessageResponse> {
  return requestRJson<SendMessageResponse>(`/api/qa/threads/${threadId}/messages/`, "POST", payload)
}

export async function listAdminPrompts(): Promise<PromptTemplateItem[]> {
  return requestR<PromptTemplateItem[]>("/api/qa/admin/prompts/", { method: "GET" })
}

export async function createAdminPrompt(payload: PromptCreateRequest): Promise<PromptTemplateItem> {
  return requestRJson<PromptTemplateItem>("/api/qa/admin/prompts/", "POST", payload)
}

export async function patchAdminPrompt(promptId: number, payload: PromptUpdateRequest): Promise<PromptTemplateItem> {
  return requestRJson<PromptTemplateItem>(`/api/qa/admin/prompts/${promptId}/`, "PATCH", payload)
}

export async function deleteAdminPrompt(promptId: number): Promise<boolean> {
  return requestR<boolean>(`/api/qa/admin/prompts/${promptId}/`, { method: "DELETE" })
}

export async function adminAnswerMetrics(): Promise<AnswerMetricsData> {
  return requestR<AnswerMetricsData>("/api/qa/admin/answer-metrics/", { method: "GET" })
}

export async function datasetSummary(): Promise<DatasetSummaryData> {
  return requestR<DatasetSummaryData>("/api/qa/dataset/summary/", { method: "GET" })
}

export async function listDatasetPairs(params: {
  q?: string
  tag?: string
  sort?: "answer_score" | "question_score" | "recent"
  page?: number
  page_size?: number
}): Promise<DatasetPairsPageData> {
  const qs = new URLSearchParams()
  if (params.q) qs.set("q", params.q)
  if (params.tag) qs.set("tag", params.tag)
  if (params.sort) qs.set("sort", params.sort)
  if (params.page) qs.set("page", String(params.page))
  if (params.page_size) qs.set("page_size", String(params.page_size))
  const url = `/api/qa/dataset/pairs/${qs.toString() ? `?${qs.toString()}` : ""}`
  return requestR<DatasetPairsPageData>(url, { method: "GET" })
}

export async function getDatasetPairDetail(pairId: number): Promise<DatasetPairDetailData> {
  return requestR<DatasetPairDetailData>(`/api/qa/dataset/pairs/${pairId}/`, { method: "GET" })
}
