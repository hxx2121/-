export interface PromptTemplateItem {
  id: number
  scene: string
  version: string
  system_prompt: string
  user_prompt_template: string
  is_active: boolean
  created_at: string
  updated_at: string
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

export interface ThreadItem {
  id: number
  title: string
  created_at: string
  updated_at: string
}

export interface ThreadCreateRequest {
  title?: string
}

export interface EvaluationItem {
  id: number
  syntax_score: number
  logic_score: number
  utility_score: number
  readability_score: number
  total_score: number
  analysis_report: string
  created_at: string
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
  prompt_scene?: string
}

export interface SendMessageResponse {
  user: MessageItem
  assistant: MessageItem
}

export interface AvgScoresData {
  syntax: number
  logic: number
  utility: number
  readability: number
  total: number
}

export interface QualityDistributionData {
  low: number
  medium: number
  good: number
  excellent: number
}

export interface DailyActivityItem {
  date: string
  count: number
}

export interface AnswerMetricsData {
  avg_scores: AvgScoresData
  quality_distribution: QualityDistributionData
  daily_activity: DailyActivityItem[]
}

export interface DatasetTagCount {
  tag: string
  count: number
}

export interface DatasetPairItem {
  id: number
  question_id: number
  answer_id: number
  title: string
  tags: string[]
  question_score: number
  answer_score: number
  view_count: number | null
  question_creation_date: string | null
  answer_creation_date: string | null
  question_excerpt: string
  answer_excerpt: string
  created_at: string
}

export interface DatasetSummaryData {
  total: number
  top_tags: DatasetTagCount[]
  top_pairs: DatasetPairItem[]
}

export interface DatasetPairsPageData {
  page: number
  page_size: number
  total: number
  items: DatasetPairItem[]
}

export interface DatasetPairDetailData {
  id: number
  question_id: number
  answer_id: number
  title: string
  tags: string[]
  question_score: number
  answer_score: number
  view_count: number | null
  question_creation_date: string | null
  answer_creation_date: string | null
  question_body: string
  answer_body: string
  question_code_snippets_json: string[]
  answer_code_snippets_json: string[]
  created_at: string
}
