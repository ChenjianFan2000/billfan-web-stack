export type ApiUser = {
  id?: number
  username: string
}

export type CategoryNode = {
  id: number
  name: string
  parent_id: number | null
  order_index: number
  count: number
  children: CategoryNode[]
}

export type Paper = {
  id: number
  title: string
  authors: string[]
  year: number | null
  publisher: string
  doi: string
  abstract_original: string
  abstract_zh: string
  summary_one_line: string
  category_id: number | null
  category_ids: number[]
  file_path?: string
  text_cache_path?: string
  created_at?: string
}

export type StatsCategory = {
  id: number
  name: string
  count: number
}

export type StatsPayload = {
  total: number
  categories: StatsCategory[]
}

export type Conversation = {
  id: number
  title: string
  updated_at: string
}

export type ChatMessage = {
  id: number
  role: "user" | "assistant"
  content: string
  attachments: number[]
  created_at: string
}

export type UploadJobStatus = {
  job_id: number
  status: "pending" | "processing" | "done" | "error" | "skipped"
  error_msg?: string
}

export type ChatAttachment = {
  attachment_id: number
  type: "image" | "pdf"
  file_path: string
  processed_data?: Record<string, unknown>
}

export type AgentStreamEvent = {
  type: string
  content?: string
  name?: string
  status?: string
  error?: string
  duration_ms?: number
}

export type ClassificationGuidance = {
  content: string
}

export type QuarantinePaper = {
  id: number
  title: string
  file_path: string
  text_cache_path: string
  created_at?: string
  quarantine_reason: string
  latest_job_id?: number | null
  latest_job_status?: string
  latest_job_error?: string
}

export type ExportPdfResponse = {
  download_url: string
  file_path: string
  count: number
}

export type ExportTextResponse = {
  download_url: string
  file_path: string
  count: number
}

export type ExportReferencesTextResponse = {
  format: "apa" | "bibtex"
  output: "text"
  content: string
}

export type ExportReferencesPdfResponse = {
  format: "apa" | "bibtex"
  output: "pdf"
  download_url: string
  file_path: string
}
