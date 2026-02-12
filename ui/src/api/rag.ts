import type {
  AdminCollectionOverviewItem,
  KnowledgeCollectionCreateRequest,
  KnowledgeCollectionItem,
  DocumentChunksData,
  DocumentDetailData,
  KnowledgeDocumentItem,
  KnowledgeDocumentUploadResult,
  KnowledgeTextIngestRequest,
  MessageCreateRequest,
  MessageItem,
  PromptCreateRequest,
  PromptTemplateItem,
  PromptUpdateRequest,
  QARequest,
  QAResponseData,
  QASearchRequest,
  QASearchResponseData,
  ThreadCreateRequest,
  ThreadItem,
  ToolCreateRequest,
  ToolDefinitionItem,
  ToolPolicyCreateRequest,
  ToolPolicyItem,
  ToolPolicyUpdateRequest,
  ToolUpdateRequest,
  AnswerMetricsData,
} from "@/types/rag"
import { downloadBlob, requestR, requestRForm, requestRJson } from "@/api/http"

export async function listCollections(): Promise<KnowledgeCollectionItem[]> {
  return requestR<KnowledgeCollectionItem[]>("/api/rag/collections/", { method: "GET" })
}

export async function createCollection(payload: KnowledgeCollectionCreateRequest): Promise<KnowledgeCollectionItem> {
  return requestRJson<KnowledgeCollectionItem>("/api/rag/collections/", "POST", payload)
}

export async function deleteCollection(collectionId: number): Promise<null> {
  return requestR<null>(`/api/rag/collections/${collectionId}/`, { method: "DELETE" })
}

export async function listDocuments(collectionId: number): Promise<KnowledgeDocumentItem[]> {
  return requestR<KnowledgeDocumentItem[]>(`/api/rag/collections/${collectionId}/docs/`, { method: "GET" })
}

export async function uploadDocument(collectionId: number, file: File): Promise<KnowledgeDocumentUploadResult> {
  const fd = new FormData()
  fd.append("file", file)
  return requestRForm<KnowledgeDocumentUploadResult>(`/api/rag/collections/${collectionId}/docs/`, "POST", fd)
}

export async function ingestText(collectionId: number, payload: KnowledgeTextIngestRequest): Promise<KnowledgeDocumentUploadResult> {
  return requestRJson<KnowledgeDocumentUploadResult>(`/api/rag/collections/${collectionId}/texts/`, "POST", payload)
}

export async function deleteDocument(docId: number): Promise<null> {
  return requestR<null>(`/api/rag/docs/${docId}/`, { method: "DELETE" })
}

export async function getDocumentDetail(docId: number): Promise<DocumentDetailData> {
  return requestR<DocumentDetailData>(`/api/rag/docs/${docId}/details/`, { method: "GET" })
}

export async function getDocumentChunks(docId: number, params?: { offset?: number; limit?: number }): Promise<DocumentChunksData> {
  const usp = new URLSearchParams()
  if (params?.offset != null) usp.set("offset", String(params.offset))
  if (params?.limit != null) usp.set("limit", String(params.limit))
  const qs = usp.toString()
  return requestR<DocumentChunksData>(`/api/rag/docs/${docId}/chunks/${qs ? `?${qs}` : ""}`, { method: "GET" })
}

export function documentDownloadUrl(docId: number): string {
  return `/api/rag/docs/${docId}/download/`
}

export async function downloadDocument(docId: number): Promise<{ blob: Blob; filename: string }> {
  return downloadBlob(documentDownloadUrl(docId))
}

export async function askQA(payload: QARequest): Promise<QAResponseData> {
  return requestRJson<QAResponseData>("/api/rag/qa/", "POST", payload)
}

export async function qaSearch(payload: QASearchRequest): Promise<QASearchResponseData> {
  return requestRJson<QASearchResponseData>("/api/rag/qa-search/", "POST", payload)
}

export async function listThreads(): Promise<ThreadItem[]> {
  return requestR<ThreadItem[]>("/api/rag/threads/", { method: "GET" })
}

export async function createThread(payload: ThreadCreateRequest): Promise<ThreadItem> {
  return requestRJson<ThreadItem>("/api/rag/threads/", "POST", payload)
}

export async function deleteThread(threadId: number): Promise<null> {
  return requestR<null>(`/api/rag/threads/${threadId}/`, { method: "DELETE" })
}

export async function listMessages(threadId: number): Promise<MessageItem[]> {
  return requestR<MessageItem[]>(`/api/rag/threads/${threadId}/messages/`, { method: "GET" })
}

export async function sendMessage(threadId: number, payload: MessageCreateRequest): Promise<MessageItem> {
  return requestRJson<MessageItem>(`/api/rag/threads/${threadId}/messages/`, "POST", payload)
}

export async function adminCollectionOverview(): Promise<AdminCollectionOverviewItem[]> {
  return requestR<AdminCollectionOverviewItem[]>("/api/rag/admin/collections/", { method: "GET" })
}

export async function adminDeleteDoc(docId: number): Promise<null> {
  return requestR<null>(`/api/rag/admin/docs/${docId}/`, { method: "DELETE" })
}

export async function listAdminTools(): Promise<ToolDefinitionItem[]> {
  return requestR<ToolDefinitionItem[]>("/api/rag/admin/tools/", { method: "GET" })
}

export async function createAdminTool(payload: ToolCreateRequest): Promise<ToolDefinitionItem> {
  return requestRJson<ToolDefinitionItem>("/api/rag/admin/tools/", "POST", payload)
}

export async function patchAdminTool(toolId: number, payload: ToolUpdateRequest): Promise<ToolDefinitionItem> {
  return requestRJson<ToolDefinitionItem>(`/api/rag/admin/tools/${toolId}/`, "PATCH", payload)
}

export async function deleteAdminTool(toolId: number): Promise<null> {
  return requestR<null>(`/api/rag/admin/tools/${toolId}/`, { method: "DELETE" })
}

export async function listAdminToolPolicies(): Promise<ToolPolicyItem[]> {
  return requestR<ToolPolicyItem[]>("/api/rag/admin/tool-policies/", { method: "GET" })
}

export async function createAdminToolPolicy(payload: ToolPolicyCreateRequest): Promise<ToolPolicyItem> {
  return requestRJson<ToolPolicyItem>("/api/rag/admin/tool-policies/", "POST", payload)
}

export async function patchAdminToolPolicy(policyId: number, payload: ToolPolicyUpdateRequest): Promise<ToolPolicyItem> {
  return requestRJson<ToolPolicyItem>(`/api/rag/admin/tool-policies/${policyId}/`, "PATCH", payload)
}

export async function deleteAdminToolPolicy(policyId: number): Promise<null> {
  return requestR<null>(`/api/rag/admin/tool-policies/${policyId}/`, { method: "DELETE" })
}

export async function listAdminPrompts(): Promise<PromptTemplateItem[]> {
  return requestR<PromptTemplateItem[]>("/api/rag/admin/prompts/", { method: "GET" })
}

export async function createAdminPrompt(payload: PromptCreateRequest): Promise<PromptTemplateItem> {
  return requestRJson<PromptTemplateItem>("/api/rag/admin/prompts/", "POST", payload)
}

export async function patchAdminPrompt(promptId: number, payload: PromptUpdateRequest): Promise<PromptTemplateItem> {
  return requestRJson<PromptTemplateItem>(`/api/rag/admin/prompts/${promptId}/`, "PATCH", payload)
}

export async function deleteAdminPrompt(promptId: number): Promise<null> {
  return requestR<null>(`/api/rag/admin/prompts/${promptId}/`, { method: "DELETE" })
}

export async function adminAnswerMetrics(): Promise<AnswerMetricsData> {
  return requestR<AnswerMetricsData>("/api/rag/admin/answer-metrics/", { method: "GET" })
}
