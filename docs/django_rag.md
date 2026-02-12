# django_rag的APP的要求
## 代码实现说明
- 负责公司知识库的入库与问答能力（可逐步演进到 LangChain / RAG / Agent）
- 知识库合集（collection）作为一级概念，用于隔离不同知识集合
- 支持上传Word文档并解析为文本分块（chunk），存储chunk与元数据
- 现阶段对话与工具调用走内置 ConversationFlow（normal/agent 分阶段提示词 + 工具执行）
- 统一返回格式django_main\R.py
- 使用序列化器，并且视图函数继承GenericAPIView
- 需求之外的不要写，如果有额外必须的，请和我确认再写

## 功能模块
- 知识库合集管理（创建、列表、删除）
- 文档上传与入库（解析、分块、向量化、索引）
- 文档列表与删除（按合集维度）
- 问答接口（指定合集进行检索增强回答，返回答案与引用来源）
- 对话流接口（normal/agent）：基于 PromptTemplate 与 ToolDefinition 动态执行工具并回答
- 管理员可以查看所有知识库与文档信息
- 管理员可以删除任意知识库与文档

## 具体代码实现
- urls.py
  - /collections/：GET(列表)、POST(创建)
  - /collections/<int:collection_id>/：DELETE(删除)
  - /collections/<int:collection_id>/docs/：GET(文档列表)、POST(上传并入库)
  - /docs/<int:doc_id>/：GET(文档详情)、DELETE(删除文档及其chunk/索引；仅管理员)
  - /docs/<int:doc_id>/download/：GET(下载原始文件)
  - /docs/<int:doc_id>/chunks/：GET(分页查看分块文本/向量ID)
  - /qa/：POST(问答，支持 scene=normal/agent；传 collection_id、question，可选 context/context_messages)
  - /threads/：GET(会话列表)、POST(创建会话)
  - /threads/<int:thread_id>/：DELETE(删除会话)
  - /threads/<int:thread_id>/messages/：GET(消息列表)、POST(发送消息并追加记忆)
  - /admin/tools/：GET(工具列表)、POST(创建工具)
  - /admin/tools/<int:tool_id>/：PATCH(修改工具)、DELETE(删除工具)
  - /admin/tool-policies/：GET(策略列表)、POST(创建策略)
  - /admin/tool-policies/<int:policy_id>/：PATCH(修改策略)、DELETE(删除策略)
  - /admin/prompts/：GET(提示词模板列表)、POST(创建模板)
  - /admin/prompts/<int:prompt_id>/：PATCH(修改模板)、DELETE(删除模板)
  - /admin/collections/：GET(管理员查看全部合集/文档统计)
  - /admin/docs/<int:doc_id>/：DELETE(管理员删除任意文档)
- models.py
  - KnowledgeCollection：name、description、roles_json(多角色)、updated_by、created_at
  - KnowledgeDocument：collection(FK)、uploader、file(FileField)、original_name、status(待入库/入库中/可用/失败)、error_msg、created_at
  - KnowledgeChunk：document(FK)、chunk_index、text、meta_json、vector_id(向量库引用)、created_at
  - ConversationThread：owner、title、scene(普通/Agent)、created_at、updated_at
  - ConversationMessage：thread(FK)、role(user/assistant/tool)、content、citations_json、tool_events_json、created_at
  - ToolDefinition：name(工具名)、title、description、is_enabled、risk_level、created_at
  - ToolPolicy：tool(FK)、scope_type(全局/合集/用户/角色)、scope_id、is_allowed、allowed_domains、rate_limit_per_day、created_at
  - PromptTemplate：scene(普通/RAG/Agent)、version、system_prompt、user_prompt_template、is_active、created_at

- serializers.py
  - CollectionCreateSerializer / CollectionListSerializer
  - DocumentUploadSerializer（file、collection_id）
  - DocumentListSerializer（id、original_name、status、created_at、vector_id_prefix、vector_id_count、vector_ids）
  - QARequestSerializer（collection_id、question、scene、context、context_messages、enable_trace、include_meta）与 QAResponseSerializer（answer、citations）
  - ThreadCreateSerializer / ThreadListSerializer / ThreadDeleteSerializer
  - MessageCreateSerializer（content）/ MessageListSerializer（role、content、citations、created_at）
  - ToolCreateSerializer / ToolListSerializer / ToolUpdateSerializer
  - ToolPolicyCreateSerializer / ToolPolicyListSerializer / ToolPolicyUpdateSerializer
  - PromptCreateSerializer / PromptListSerializer / PromptUpdateSerializer

- views.py（全部继承GenericAPIView）
  - CollectionListCreateView：创建/列表（按用户角色过滤；管理员可看全部）
  - CollectionDeleteView：删除合集（仅管理员）
  - DocumentListUploadIngestView：上传docx并触发入库（按角色可用；管理员可操作全部）
  - DocumentDeleteView：GET(详情)；DELETE(删除文档与chunk并清理向量索引；仅管理员)
  - DocumentDownloadView：下载文档文件
  - DocumentChunksView：分页查看文档 chunk 与 vector_id
  - QAView：透传 scene/context/context_messages 到 ConversationFlow；返回答案与引用；include_meta=1 时附带 meta/trace_dir
  - ThreadListCreateView：会话创建/列表（用户只看自己的会话）
  - ThreadDeleteView：删除会话（仅owner或管理员）
  - MessageListCreateView：消息列表/发送消息（写入ConversationMessage；发送时按thread.scene选择普通/Agent链路）
  - AdminCollectionOverviewView / AdminDocumentDeleteView：管理员查看与删除
  - AdminToolListCreateView / AdminToolDetailView：工具表CRUD（仅管理员）
  - AdminToolPolicyListCreateView / AdminToolPolicyDetailView：工具策略CRUD（仅管理员）
  - AdminPromptListCreateView / AdminPromptDetailView：提示词模板CRUD（仅管理员）


## 对话流（ConversationFlow）说明

### 工具目录与启用
- 运行时从 ToolDefinition 表读取 `is_enabled=true` 的工具作为“模型可见工具列表”。工具 schema 来自代码中 UnifiedTool.spec() 的 `input_schema/output_schema`。
- 工具执行时会自动补齐常用参数：
  - `collection_id/top_k/persist_directory`（KB 工具）
  - `max_pages/max_chars/fetch_pages`（Web 工具；当 max_pages>0 时自动 fetch_pages=true）

### normal 流程
- step 1：`normal_tool_select`（严格 JSON）选择是否调用工具与 tool_calls
- step 2：执行工具（按 tool_calls 顺序），得到 `tool_events`
- step 3：`normal`（自然语言）基于 `question/context/tool_events` 输出回答

### agent 流程
- step 1：`agent_tool_select`（严格 JSON）选择本轮工具 tool_calls
- step 2：执行工具得到 `tool_events_round1`
- step 3：`agent_answer` 输出草稿回答
- step 4：`agent_self_check`（严格 JSON）决定是否 retry
- step 5（可选）：`agent_tool_retry` 生成第二轮 tool_calls → 执行工具得到 `tool_events_round2`
- step 6：`agent_final` 基于 best_answer + evidence 输出最终回答

### tool_events 结构（用于落盘/消息存储）
每次工具调用会记录为一个 event（便于写入 ConversationMessage.tool_events_json）：
- `name`：工具名
- `payload`：实际入参（包含自动补齐字段）
- `elapsed_ms`：耗时
- `tool_out`：统一返回结构（ok/result/error/meta），其中 `meta.tool` 标识来源工具
