import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import websocketService from '../services/websocketService'
import chatService from '../services/chatService'
import { useVisualizationStore } from './visualization'
import { useAuthStore } from './auth'

export const useChatStore = defineStore('chat', () => {
  const currentSession = ref(null)
  const isConnected = ref(false)
  const isStreaming = ref(false)
  const isSpecStreaming = ref(false)
  const isGenerating = ref(false)
  const streamingStartTime = ref(null)
  const generationStartTime = ref(null)
  const statusMessage = ref(null)
  const streamBuffer = ref('')
  const specStreamBuffer = ref('')
  const htmlStreamBuffer = ref('')
  const currentVizId = ref(null)
  const error = ref(null)
  const specUsage = ref(null)

  const totalSessionCost = computed(() => {
    if (!currentSession.value?.messages) return 0
    return currentSession.value.messages
      .filter(m => m.cost_usd != null)
      .reduce((sum, m) => sum + m.cost_usd, 0)
  })

  function connectToChat(vizId) {
    const authStore = useAuthStore()
    currentVizId.value = vizId
    error.value = null
    statusMessage.value = null

    websocketService.connect(vizId, authStore.token, {
      onOpen() {
        isConnected.value = true
      },
      onInit(session) {
        currentSession.value = session
      },
      onChunk(chunk) {
        streamBuffer.value += chunk
        // Update the last assistant message in real-time
        if (currentSession.value) {
          const msgs = currentSession.value.messages
          const lastMsg = msgs[msgs.length - 1]
          if (lastMsg && lastMsg.role === 'assistant' && lastMsg._streaming) {
            lastMsg.content = streamBuffer.value
          }
        }
      },
      onSpecStreaming() {
        isSpecStreaming.value = true
        specStreamBuffer.value = ''
      },
      onSpecChunk(chunk) {
        specStreamBuffer.value += chunk
      },
      onHtmlChunk(chunk) {
        htmlStreamBuffer.value += chunk
      },
      onComplete(usage) {
        isStreaming.value = false
        streamingStartTime.value = null
        // Capture phase 1 usage for spec_output message
        if (usage) {
          specUsage.value = usage
        }
        // Finalize the streaming message and attach usage
        if (currentSession.value) {
          const msgs = currentSession.value.messages
          const lastMsg = msgs[msgs.length - 1]
          if (lastMsg && lastMsg._streaming) {
            lastMsg.content = streamBuffer.value
            delete lastMsg._streaming
            if (usage) {
              lastMsg.input_tokens = usage.input_tokens
              lastMsg.output_tokens = usage.output_tokens
              lastMsg.cost_usd = usage.cost_usd
            }
          }
        }
        streamBuffer.value = ''
      },
      onStatus(message) {
        // "Generating visualization..." phase indicator
        statusMessage.value = message
        isGenerating.value = true
        generationStartTime.value = Date.now()
        isStreaming.value = false
        isSpecStreaming.value = false
        streamingStartTime.value = null
        streamBuffer.value = ''
        htmlStreamBuffer.value = ''
        if (currentSession.value) {
          const msgs = currentSession.value.messages
          // Remove the last assistant message if it is empty/whitespace
          // (the streaming placeholder may have been finalized with no real content
          // if the LLM went straight to <<<SPEC_READY>>> without pre-text)
          const lastMsg = msgs[msgs.length - 1]
          if (lastMsg && lastMsg.role === 'assistant' && !lastMsg.content?.trim()) {
            msgs.pop()
          }
          // Push the spec_output message NOW so the completed spec progress bar
          // remains visible throughout HTML generation (not just after it finishes)
          if (specStreamBuffer.value) {
            const su = specUsage.value
            msgs.push({
              message_id: crypto.randomUUID(),
              role: 'assistant',
              content: specStreamBuffer.value,
              message_type: 'spec_output',
              timestamp: new Date().toISOString(),
              input_tokens: su?.input_tokens ?? null,
              output_tokens: su?.output_tokens ?? null,
              cost_usd: su?.cost_usd ?? null,
            })
            specUsage.value = null
          }
        }
      },
      onVisualizationReady(html, spec, vizId, usage) {
        isStreaming.value = false
        isGenerating.value = false
        isSpecStreaming.value = false
        streamingStartTime.value = null
        generationStartTime.value = null
        statusMessage.value = null
        streamBuffer.value = ''
        htmlStreamBuffer.value = ''
        const vizStore = useVisualizationStore()
        if (vizStore.currentVisualization) {
          vizStore.currentVisualization.current_draft_html = html
        }
        // spec_output message was already pushed in onStatus; don't push again
        // Add the html_output message to the local session for display
        if (currentSession.value) {
          currentSession.value.messages.push({
            message_id: crypto.randomUUID(),
            role: 'assistant',
            content: html,
            message_type: 'html_output',
            timestamp: new Date().toISOString(),
            input_tokens: usage?.input_tokens ?? null,
            output_tokens: usage?.output_tokens ?? null,
            cost_usd: usage?.cost_usd ?? null,
          })
        }
      },
      onError(message) {
        error.value = message
        isStreaming.value = false
        isGenerating.value = false
        isSpecStreaming.value = false
        streamingStartTime.value = null
        generationStartTime.value = null
        statusMessage.value = null
      },
      onClose() {
        isConnected.value = false
      },
    })
  }

  function sendMessage(content) {
    if (!content.trim()) return

    // Optimistically add user message
    if (currentSession.value) {
      currentSession.value.messages.push({
        message_id: crypto.randomUUID(),
        role: 'user',
        content: content,
        message_type: 'chat',
        timestamp: new Date().toISOString(),
      })

      // Add a placeholder for assistant streaming response
      currentSession.value.messages.push({
        message_id: crypto.randomUUID(),
        role: 'assistant',
        content: '',
        message_type: 'clarification',
        timestamp: new Date().toISOString(),
        _streaming: true,
      })
    }

    isStreaming.value = true
    isSpecStreaming.value = false
    streamingStartTime.value = Date.now()
    isGenerating.value = false
    statusMessage.value = null
    streamBuffer.value = ''
    specStreamBuffer.value = ''
    htmlStreamBuffer.value = ''
    websocketService.sendMessage(content)
  }

  function disconnectFromChat() {
    websocketService.disconnect()
    isConnected.value = false
    currentVizId.value = null
    isStreaming.value = false
    isGenerating.value = false
    isSpecStreaming.value = false
    streamingStartTime.value = null
    generationStartTime.value = null
    statusMessage.value = null
    specStreamBuffer.value = ''
    htmlStreamBuffer.value = ''
  }

  async function loadSession(vizId) {
    try {
      const response = await chatService.getSession(vizId)
      currentSession.value = response.data
    } catch (err) {
      error.value = 'Failed to load chat session'
    }
  }

  return {
    currentSession,
    isConnected,
    isStreaming,
    isSpecStreaming,
    isGenerating,
    streamingStartTime,
    generationStartTime,
    statusMessage,
    streamBuffer,
    specStreamBuffer,
    htmlStreamBuffer,
    currentVizId,
    error,
    totalSessionCost,
    connectToChat,
    sendMessage,
    disconnectFromChat,
    loadSession,
  }
})
