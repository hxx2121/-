export interface KnowledgeCollectionItem {
  id: number
  name: string
  description: string
  roles_json: string[]
  created_at: string
}

export interface KnowledgeCollectionCreateRequest {
  name: string
  description?: string
  roles_json?: string[]
}

export interface KnowledgeDocumentItem {
  id: number
  original_name: string
  status: string
  error_msg: string
  created_at: string
  vector_id_prefix?: string
  vector_id_count?: number
  vector_ids?: string[]
}

export interface KnowledgeDocumentUploadResult extends KnowledgeDocumentItem {
  chunks_added?: number
}

export interface KnowledgeChunkItem {
  chunk_index: number
  text: string
  meta_json: unknown
  vector_id: string
  created_at: string
}

export interface KnowledgeChunkPreviewItem {
  chunk_index: number
  text: string
  vector_id: string
}

export interface DocumentDetailData {
  id: number
  collection_id: number
  original_name: string
  status: string
  error_msg: string
  created_at: string
  vector_id_prefix?: string
  vector_id_count?: number
  chunks_preview?: KnowledgeChunkPreviewItem[]
}

export interface DocumentChunksData {
  document_id: number
  total: number
  offset: number
  limit: number
  items: KnowledgeChunkItem[]
}

export interface KnowledgeTextIngestRequest {
  title?: string
  content: string
}

export interface CitationItem {
  document_id: number
  chunk_index: number
  text: string
}

export interface ContextMessage {
  role: "user" | "assistant"
  content: string
}

export interface QARequest {
  collection_id: number
  question: string
  scene?: "normal" | "agent"
  context?: string
  context_messages?: ContextMessage[]
  enable_trace?: boolean
  include_meta?: boolean
}

export interface QAResponseData {
  answer: string
  citations: CitationItem[]
  scene?: string
  meta?: unknown
  trace_dir?: string
}

export interface RetrievedDocumentItem {
  doc_id: number
  collection_id: number
  original_name: string
  chunk_index: number
  snippet: string
  distance: number | null
  details_url: string
  download_url: string
}

export interface QASearchRequest {
  collection_id: number
  question: string
  kb_search?: boolean
  top_k?: number
  context_messages?: ContextMessage[]
}

export interface QASearchResponseData {
  answer: string
  documents: RetrievedDocumentItem[]
  search_query_used?: { original: string; generated: string }
  context_kept?: number
}

export interface ThreadItem {
  id: number
  title: string
  scene: string
  created_at: string
  updated_at: string
}

export interface ThreadCreateRequest {
  title?: string
  scene?: string
}

export interface EvaluationItem {
  id: number
  syntax_score: number
  logic_score: number
  utility_score: number
  readability_score: number
  total_score: number
  analysis_report: string
}

export interface MessageItem {
  id: number
  role: string
  content: string
  citations: unknown[]
  tool_events: unknown[]
  evaluation?: EvaluationItem
  created_at: string
}

export interface MessageCreateRequest {
  content: string
  collection_id?: number
  scene?: "normal" | "agent"
  kb_search?: boolean
  top_k?: number
  context_messages?: ContextMessage[]
}

export interface AdminCollectionOverviewItem {
  id: number
  name: string
  description: string
  roles_json: string[]
  created_at: string
  doc_total: number
  doc_ready: number
  doc_failed: number
}

export interface ToolDefinitionItem {
  id: number
  name: string
  title: string
  description: string
  is_enabled: boolean
  risk_level: string
  created_at: string
}

export interface ToolCreateRequest {
  name: string
  title?: string
  description?: string
  is_enabled?: boolean
  risk_level?: string
}

export interface ToolUpdateRequest {
  title?: string
  description?: string
  is_enabled?: boolean
  risk_level?: string
}

export interface ToolPolicyItem {
  id: number
  tool: number
  scope_type: string
  scope_id: number | null
  is_allowed: boolean
  allowed_domains: string[]
  rate_limit_per_day: number
  created_at: string
}

export interface ToolPolicyCreateRequest {
  tool: number
  scope_type: string
  scope_id?: number | null
  is_allowed?: boolean
  allowed_domains?: string[]
  rate_limit_per_day?: number
}

export interface ToolPolicyUpdateRequest {
  scope_type?: string
  scope_id?: number | null
  is_allowed?: boolean
  allowed_domains?: string[]
  rate_limit_per_day?: number
}

export interface PromptTemplateItem {
  id: number
  scene: string
  version: string
  system_prompt: string
  user_prompt_template: string
  is_active: boolean
  created_at: string
}

export interface PromptCreateRequest {
  scene: string
  version?: string
  system_prompt?: string
  user_prompt_template?: string
  is_active?: boolean
}

export interface PromptUpdateRequest {
  scene?: string
  version?: string
  system_prompt?: string
  user_prompt_template?: string
  is_active?: boolean
}

export interface AnswerAvgScores {
  syntax: number
  logic: number
  utility: number
  readability: number
  total: number
}

export interface AnswerDailyTrendItem {
  date: string
  avg_total: number
  count: number
}

export interface AnswerQualityDistribution {
  low: number
  medium: number
  good: number
  excellent: number
}

export interface AnswerDailyActivityItem {
  date: string
  count: number
}

export interface AnswerMetricsData {
  avg_scores: AnswerAvgScores
  daily_trend: AnswerDailyTrendItem[]
  quality_distribution: AnswerQualityDistribution
  daily_activity: AnswerDailyActivityItem[]
}

