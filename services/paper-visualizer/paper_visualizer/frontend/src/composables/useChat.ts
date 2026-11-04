import { ref } from 'vue'
import { streamChat, type ChatRequest } from '@/api'
import { useChatStore } from '@/stores/chat'

export function useChat(slug: string) {
  const chat = useChatStore()
  const pending = ref(false)
  const error = ref<string | null>(null)

  async function send(message: string, lang: 'zh' | 'en') {
    error.value = null
    pending.value = true
    chat.append(slug, { role: 'user', content: message })
    chat.append(slug, { role: 'assistant', content: '' })
    const history = chat.get(slug).slice(0, -2)
    const req: ChatRequest = {
      paper_slug: slug,
      message,
      history,
      lang,
    }
    await streamChat(
      req,
      (text) => chat.appendToLast(slug, text),
      () => {
        pending.value = false
      },
      (msg) => {
        error.value = msg
        pending.value = false
      },
    )
  }

  return { pending, error, send }
}
