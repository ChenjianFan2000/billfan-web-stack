import { api, apiFetch } from "./client"
import type {
  AgentStreamEvent,
  ApiUser,
  CategoryNode,
  ChatAttachment,
  ChatMessage,
  ClassificationGuidance,
  Conversation,
  ExportPdfResponse,
  ExportTextResponse,
  ExportReferencesPdfResponse,
  ExportReferencesTextResponse,
  Paper,
  QuarantinePaper,
  StatsPayload,
  UploadJobStatus,
} from "../lib/types"

const API_BASE = import.meta.env.VITE_API_BASE ?? ""

export function listUsers() {
  return api.get<ApiUser[]>("/api/auth/users", { redirectOn401: false })
}

export function login(username: string, password: string) {
  return api.post<{ ok: boolean; username: string }>("/api/auth/login", { username, password }, { redirectOn401: false })
}

export function logout() {
  return api.post<{ ok: boolean }>("/api/auth/logout")
}

export function me() {
  return api.get<ApiUser>("/api/auth/me", { redirectOn401: false })
}

export function listCategories() {
  return api.get<CategoryNode[]>("/api/categories")
}

export function createCategory(payload: { name: string; parent_id?: number | null; order_index?: number }) {
  return api.post<CategoryNode>("/api/categories", payload)
}

export function updateCategory(categoryId: number, payload: { name?: string; parent_id?: number | null; order_index?: number }) {
  return api.put<CategoryNode>(`/api/categories/${categoryId}`, payload)
}

export function deleteCategory(categoryId: number) {
  return api.delete<{ ok: boolean }>(`/api/categories/${categoryId}`)
}

export function listPapers(categoryId?: number | null) {
  const query = categoryId == null ? "" : `?category_id=${categoryId}`
  return api.get<Paper[]>(`/api/papers${query}`)
}

export function listQuarantinedPapers() {
  return api.get<QuarantinePaper[]>("/api/papers-quarantine")
}

export function getPaper(paperId: number) {
  return api.get<Paper>(`/api/papers/${paperId}`)
}

export function getPaperFileUrl(paperId: number, mode: "preview" | "download" = "preview") {
  return `${API_BASE}/api/papers/${paperId}/file?mode=${mode}`
}

export function updatePaper(paperId: number, payload: Partial<Paper>) {
  return api.put<Paper>(`/api/papers/${paperId}`, payload)
}

export function deletePaper(paperId: number) {
  return api.delete<{ ok: boolean }>(`/api/papers/${paperId}`)
}

export function getStats() {
  return api.get<StatsPayload>("/api/stats")
}

export function uploadPaper(file: File) {
  const formData = new FormData()
  formData.append("file", file)
  return api.post<{ job_id: number; paper_id: number }>("/api/upload", formData, { timeoutMs: 120000 })
}

export function getJobStatus(jobId: number) {
  return api.get<UploadJobStatus>(`/api/jobs/${jobId}`)
}

export function getClassificationGuidance() {
  return api.get<ClassificationGuidance>("/api/settings/classification-guidance")
}

export function updateClassificationGuidance(content: string) {
  return api.put<ClassificationGuidance>("/api/settings/classification-guidance", { content })
}

export function listConversations() {
  return api.get<Conversation[]>("/api/agent/conversations")
}

export function createConversation(title?: string) {
  return api.post<Conversation>("/api/agent/conversations", title ? { title } : {})
}

export function renameConversation(conversationId: number, title: string) {
  return api.patch<Conversation>(`/api/agent/conversations/${conversationId}`, { title })
}

export function deleteConversation(conversationId: number) {
  return api.delete<{ ok: boolean }>(`/api/agent/conversations/${conversationId}`)
}

export function listConversationMessages(conversationId: number) {
  return api.get<ChatMessage[]>(`/api/agent/conversations/${conversationId}/messages`)
}

export function uploadChatAttachment(file: File) {
  const formData = new FormData()
  formData.append("file", file)
  return api.post<ChatAttachment>("/api/agent/attachments", formData, { timeoutMs: 180000 })
}

export async function streamAgentChat(
  conversationId: number,
  payload: { content: string; attachment_ids?: number[]; paper_ids?: number[] },
  onEvent: (event: AgentStreamEvent) => void,
): Promise<void> {
  const response = await apiFetch<Response>(
    `/api/agent/conversations/${conversationId}/chat`,
    {
      method: "POST",
      body: JSON.stringify(payload),
      headers: {
        "Content-Type": "application/json",
      },
    },
    { rawResponse: true },
  )

  if (!response.body) {
    return
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ""

  while (true) {
    const { done, value } = await reader.read()
    if (done) {
      break
    }

    buffer += decoder.decode(value, { stream: true })
    const chunks = buffer.split("\n\n")
    buffer = chunks.pop() ?? ""

    for (const chunk of chunks) {
      const lines = chunk
        .split("\n")
        .map((line) => line.trim())
        .filter((line) => line.startsWith("data:"))
      if (!lines.length) {
        continue
      }

      const payloadText = lines.map((line) => line.slice(5).trim()).join("\n")
      if (!payloadText) {
        continue
      }

      try {
        onEvent(JSON.parse(payloadText) as AgentStreamEvent)
      } catch {
        onEvent({ type: "chunk", content: payloadText })
      }
    }
  }
}

export function exportPdfs(payload: { category_ids?: number[] }) {
  return api.post<ExportPdfResponse>("/api/export/pdfs", payload, { timeoutMs: 180000 })
}

export function exportTexts(payload: { category_ids?: number[] }) {
  return api.post<ExportTextResponse>("/api/export/texts", payload, { timeoutMs: 180000 })
}

export function exportReferences(payload: {
  format: "apa" | "bibtex"
  output: "text" | "pdf"
  category_ids?: number[]
}) {
  return api.post<ExportReferencesTextResponse | ExportReferencesPdfResponse>("/api/export/references", payload, {
    timeoutMs: 180000,
  })
}
