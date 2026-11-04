export class ApiError extends Error {
  status: number
  detail: unknown

  constructor(message: string, status: number, detail: unknown) {
    super(message)
    this.name = "ApiError"
    this.status = status
    this.detail = detail
  }
}

type RequestOptions = {
  redirectOn401?: boolean
  rawResponse?: boolean
  timeoutMs?: number
}

const API_BASE = import.meta.env.VITE_API_BASE ?? ""

function buildUrl(path: string): string {
  if (!path.startsWith("/")) {
    return `${API_BASE}/${path}`
  }
  return `${API_BASE}${path}`
}

function parseBody(text: string): unknown {
  if (!text) {
    return null
  }
  try {
    return JSON.parse(text)
  } catch {
    return text
  }
}

export async function apiFetch<T>(
  path: string,
  init: RequestInit = {},
  options: RequestOptions = {},
): Promise<T> {
  const { redirectOn401 = true, rawResponse = false, timeoutMs = rawResponse ? 0 : 45000 } = options
  const headers = new Headers(init.headers)
  const isForm = init.body instanceof FormData
  if (!isForm && init.body !== undefined && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json")
  }

  const controller = !init.signal && timeoutMs > 0 ? new AbortController() : null
  const timeoutId =
    controller && timeoutMs > 0
      ? window.setTimeout(() => {
          controller.abort()
        }, timeoutMs)
      : null

  let response: Response
  try {
    response = await fetch(buildUrl(path), {
      ...init,
      credentials: "include",
      headers,
      signal: init.signal ?? controller?.signal,
    })
  } catch (err) {
    if (timeoutId != null) {
      window.clearTimeout(timeoutId)
    }
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new ApiError("请求超时，请稍后重试", 408, null)
    }
    throw err
  }

  if (timeoutId != null) {
    window.clearTimeout(timeoutId)
  }

  if (response.status === 401 && redirectOn401 && window.location.pathname !== "/login") {
    window.location.href = "/login"
  }

  if (!response.ok) {
    const text = await response.text()
    const detail = parseBody(text)
    let message: string
    if (response.status === 413) {
      message = "上传文件过大，请压缩后重试（当前上限 120MB）"
    } else {
      message =
        typeof detail === "object" && detail !== null && "detail" in detail
          ? String((detail as { detail: unknown }).detail)
          : `Request failed: ${response.status}`
    }
    throw new ApiError(message, response.status, detail)
  }

  if (rawResponse) {
    return response as unknown as T
  }

  const contentType = response.headers.get("content-type") || ""
  if (!contentType.includes("application/json")) {
    return (await response.text()) as unknown as T
  }
  return (await response.json()) as T
}

export const api = {
  get: <T>(path: string, options?: RequestOptions) => apiFetch<T>(path, { method: "GET" }, options),
  post: <T>(path: string, body?: unknown, options?: RequestOptions) =>
    apiFetch<T>(
      path,
      {
        method: "POST",
        body: body instanceof FormData ? body : body === undefined ? undefined : JSON.stringify(body),
      },
      options,
    ),
  put: <T>(path: string, body?: unknown, options?: RequestOptions) =>
    apiFetch<T>(
      path,
      {
        method: "PUT",
        body: body instanceof FormData ? body : body === undefined ? undefined : JSON.stringify(body),
      },
      options,
    ),
  patch: <T>(path: string, body?: unknown, options?: RequestOptions) =>
    apiFetch<T>(
      path,
      {
        method: "PATCH",
        body: body instanceof FormData ? body : body === undefined ? undefined : JSON.stringify(body),
      },
      options,
    ),
  delete: <T>(path: string, options?: RequestOptions) => apiFetch<T>(path, { method: "DELETE" }, options),
}
