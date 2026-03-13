<template>
  <div class="flex flex-col flex-1 min-h-0">
    <!-- Messages -->
    <div ref="messagesContainer" class="flex-1 overflow-y-auto p-4 space-y-4">
      <div v-if="!chatStore.currentSession" class="flex items-center justify-center h-full">
        <LoadingSpinner />
      </div>

      <div v-else-if="displayMessages.length === 0" class="flex justify-start">
        <div class="max-w-[75%] rounded-xl px-4 py-3 bg-cp-surface border border-cp-border text-cp-text">
          <div class="flex items-center gap-2 mb-1">
            <span class="text-xs font-semibold text-cp-yellow">{{ brandName }}</span>
          </div>
          <div class="text-sm whitespace-pre-wrap break-words">{{ welcomeTyped }}<span v-if="!welcomeDone" class="inline-block w-px h-3.5 bg-cp-cyan ml-0.5 align-middle animate-pulse"></span></div>
        </div>
      </div>

      <template v-else>
        <ChatMessage
          v-for="msg in displayMessages"
          :key="msg.message_id"
          :message="msg"
        />
      </template>

      <TypingIndicator v-if="chatStore.isStreaming && !lastMessageIsStreaming" />

      <!-- Phase 1: Specification building progress bar (only when spec marker detected) -->
      <div v-if="chatStore.isSpecStreaming" class="flex justify-start">
        <div class="max-w-[80%] w-80 rounded-xl px-4 py-3 bg-cp-surface border border-cp-border/50 text-cp-text">
          <div class="flex items-center justify-between mb-2">
            <div class="flex items-center gap-2">
              <span class="text-xs font-semibold text-cp-yellow">{{ brandName }}</span>
              <span class="text-xs text-cp-muted">· Building specification</span>
            </div>
            <button
              @click="openLiveModal('spec')"
              class="flex items-center gap-1 text-cp-muted hover:text-cp-yellow transition-colors p-1 rounded hover:bg-cp-yellow/10"
              title="View specification as it streams"
            >
              <!-- eye icon -->
              <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
              <span class="text-xs">View</span>
            </button>
          </div>
          <div class="w-full bg-cp-border rounded-full h-1.5 overflow-hidden">
            <div
              class="h-1.5 rounded-full transition-all bg-cp-yellow/70"
              :style="{ width: streamingProgress + '%' }"
            ></div>
          </div>
        </div>
      </div>

      <!-- Phase 2: HTML generation progress bar -->
      <div v-if="chatStore.isGenerating" class="flex justify-start">
        <div class="max-w-[80%] w-80 rounded-xl px-4 py-3 bg-cp-surface border border-cp-cyan/30 text-cp-text">
          <div class="flex items-center justify-between mb-3">
            <div class="flex items-center gap-2">
              <span class="text-xs font-semibold text-cp-yellow">{{ brandName }}</span>
              <span class="text-xs text-cp-muted">· Generating HTML visualization</span>
            </div>
            <button
              @click="openLiveModal('html')"
              class="flex items-center gap-1 text-cp-muted hover:text-cp-cyan transition-colors p-1 rounded hover:bg-cp-cyan/10"
              title="View HTML as it streams"
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
              <span class="text-xs">View</span>
            </button>
          </div>
          <!-- Progress bar -->
          <div class="w-full bg-cp-border rounded-full h-2 overflow-hidden">
            <div
              class="h-2 rounded-full transition-all"
              :class="generationProgress >= 100 ? 'bg-cp-green' : 'bg-cp-cyan'"
              :style="{ width: generationProgress + '%' }"
            ></div>
          </div>
          <div class="text-right mt-1">
            <span class="text-xs text-cp-muted font-mono">{{ Math.floor(generationProgress) }}%</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Disconnected banner -->
    <div v-if="!chatStore.isConnected && chatStore.currentSession" class="bg-cp-red/10 border-t border-cp-red/30 px-4 py-2 flex items-center justify-between">
      <span class="text-cp-red text-sm">Connection lost</span>
      <button
        @click="reconnect"
        class="text-cp-red hover:text-cp-red/80 text-sm font-medium"
      >
        Reconnect
      </button>
    </div>

    <!-- Input -->
    <ChatInput
      @send="handleSend"
      :disabled="chatStore.isStreaming || chatStore.isGenerating || !chatStore.isConnected"
    />
  </div>

  <!-- Live streaming response viewer modal -->
  <Teleport to="body">
    <Transition name="modal-fade">
      <div
        v-if="liveModalOpen"
        class="fixed inset-0 z-[999] flex items-center justify-center p-4"
        @click.self="closeLiveModal"
      >
        <!-- Backdrop -->
        <div class="absolute inset-0 bg-black/70 backdrop-blur-sm" @click="closeLiveModal"></div>

        <!-- Panel -->
        <div class="relative z-10 flex flex-col bg-cp-black border border-cp-border rounded-xl shadow-2xl"
             style="width: 95vw; height: 92vh;">
          <!-- Header -->
          <div class="flex items-center justify-between px-5 py-3 border-b border-cp-border shrink-0">
            <div class="flex items-center gap-3">
              <svg v-if="liveModalType === 'spec'" xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-cp-yellow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/>
              </svg>
              <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-cp-cyan" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/>
              </svg>
              <span class="text-sm font-semibold text-cp-text">
                {{ liveModalType === 'spec' ? 'Specification' : 'HTML Generation' }}
              </span>
              <!-- Live dot pulsing while still streaming -->
              <span
                v-if="(liveModalType === 'spec' && chatStore.isSpecStreaming) || (liveModalType === 'html' && chatStore.isGenerating)"
                class="flex items-center gap-1.5 text-xs text-cp-muted"
              >
                <span class="inline-block w-2 h-2 rounded-full bg-cp-green animate-pulse"></span>
                Streaming…
              </span>
              <span v-else class="text-xs text-cp-muted">Complete</span>
              <span class="text-xs text-cp-muted px-2 py-0.5 rounded bg-cp-surface border border-cp-border/50">
                {{ liveModalType === 'spec' ? 'Markdown' : 'HTML' }}
              </span>
            </div>
            <button
              @click="closeLiveModal"
              class="text-cp-muted hover:text-cp-text transition-colors p-1.5 rounded hover:bg-cp-surface"
              title="Close (Esc)"
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
              </svg>
            </button>
          </div>
          <!-- Scrollable content -->
          <div ref="liveModalScrollEl" class="flex-1 overflow-auto">
            <!-- Spec: rendered Markdown -->
            <div
              v-if="liveModalType === 'spec'"
              class="p-5 text-sm text-cp-text prose-chat break-words leading-relaxed min-h-full"
              v-html="renderedSpecStream"
            ></div>
            <!-- HTML: syntax-highlighted code -->
            <pre
              v-else
              class="p-5 text-xs font-mono leading-relaxed min-h-full"
            ><code class="language-html" v-html="highlightedHtmlStream"></code></pre>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, nextTick, watch, computed, onMounted, onUnmounted } from 'vue'
import { useChatStore } from '../../stores/chat'
import ChatMessage from './ChatMessage.vue'
import ChatInput from './ChatInput.vue'
import TypingIndicator from './TypingIndicator.vue'
import LoadingSpinner from '../common/LoadingSpinner.vue'
import { BRAND_NAME } from '../../config/brand'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import hljs from 'highlight.js/lib/core'
import xml from 'highlight.js/lib/languages/xml'
import 'highlight.js/styles/github-dark.min.css'

hljs.registerLanguage('xml', xml)

const chatStore = useChatStore()
const brandName = BRAND_NAME
const messagesContainer = ref(null)

// ── Progress bars (Phase 1: spec streaming, Phase 2: HTML generation) ─────────
// Asymptotic schedule: 0→80% in 10 min, 80→90% in 10 min, 90→95% in 10 min, …
const SEGMENTS = [
  { start: 0,    end: 600,  from: 0,  to: 80  },
  { start: 600,  end: 1200, from: 80, to: 90  },
  { start: 1200, end: 1800, from: 90, to: 95  },
  { start: 1800, end: 2400, from: 95, to: 97.5 },
  { start: 2400, end: 3000, from: 97.5, to: 98.75 },
]

function calcProgress(elapsedSec) {
  for (const seg of SEGMENTS) {
    if (elapsedSec <= seg.end) {
      const t = (elapsedSec - seg.start) / (seg.end - seg.start)
      return seg.from + (seg.to - seg.from) * Math.min(t, 1)
    }
  }
  return 99
}

// Phase 1 — specification streaming progress
const streamingProgress = ref(0)
let streamingTimer = null

watch(
  () => chatStore.isSpecStreaming,
  (specStreaming) => {
    if (specStreaming) {
      streamingProgress.value = 0
      streamingTimer = setInterval(() => {
        const start = chatStore.streamingStartTime
        if (!start) return
        const elapsed = (Date.now() - start) / 1000
        streamingProgress.value = calcProgress(elapsed)
      }, 250)
    } else {
      if (streamingTimer) { clearInterval(streamingTimer); streamingTimer = null }
      streamingProgress.value = 100
      setTimeout(() => { streamingProgress.value = 0 }, 400)
    }
  }
)

// Phase 2 — HTML generation progress
const generationProgress = ref(0)
let progressTimer = null

watch(
  () => chatStore.isGenerating,
  (generating) => {
    if (generating) {
      generationProgress.value = 0
      progressTimer = setInterval(() => {
        const start = chatStore.generationStartTime
        if (!start) return
        const elapsed = (Date.now() - start) / 1000
        generationProgress.value = calcProgress(elapsed)
      }, 250)
    } else {
      // Done — animate to 100% then clear
      if (progressTimer) { clearInterval(progressTimer); progressTimer = null }
      generationProgress.value = 100
      setTimeout(() => { generationProgress.value = 0 }, 600)
    }
  }
)

// Typewriter welcome message
const WELCOME_TEXT = "Tell me what you want to build? Include all the details you can think of \u2014 the type of data, how you want it displayed, any specific colors or styles, and the story you want it to tell."
const welcomeTyped = ref('')
const welcomeDone = ref(false)
let typingTimer = null

function startWelcomeTyping() {
  welcomeTyped.value = ''
  welcomeDone.value = false
  let i = 0
  typingTimer = setInterval(() => {
    if (i < WELCOME_TEXT.length) {
      welcomeTyped.value += WELCOME_TEXT[i]
      i++
    } else {
      clearInterval(typingTimer)
      typingTimer = null
      welcomeDone.value = true
    }
  }, 22)
}

// Trigger typing when session loads with no messages; scroll to bottom when it has messages
watch(
  () => chatStore.currentSession,
  async (session) => {
    if (!session) return
    if (displayMessages.value.length === 0) {
      startWelcomeTyping()
    } else {
      await nextTick()
      if (messagesContainer.value) {
        messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
      }
    }
  }
)

onUnmounted(() => {
  if (typingTimer) clearInterval(typingTimer)
  if (streamingTimer) clearInterval(streamingTimer)
  if (progressTimer) clearInterval(progressTimer)
  document.removeEventListener('keydown', handleModalKeydown)
})

// ── Live streaming modal ───────────────────────────────────────────────────────
const liveModalOpen = ref(false)
const liveModalType = ref(null)  // 'spec' | 'html'
const liveModalScrollEl = ref(null)

function openLiveModal(type) {
  liveModalType.value = type
  liveModalOpen.value = true
  nextTick(() => scrollLiveModal())
}

function closeLiveModal() {
  liveModalOpen.value = false
}

// Rendered content for live modals
const renderedSpecStream = computed(() => {
  const raw = chatStore.specStreamBuffer || ''
  if (!raw) return ''
  const html = marked.parse(raw)
  return DOMPurify.sanitize(html, { USE_PROFILES: { html: true } })
})

const highlightedHtmlStream = computed(() => {
  const raw = chatStore.htmlStreamBuffer || ''
  if (!raw) return ''
  return hljs.highlight(raw, { language: 'xml' }).value
})

function scrollLiveModal() {
  if (liveModalScrollEl.value) {
    liveModalScrollEl.value.scrollTop = liveModalScrollEl.value.scrollHeight
  }
}

function handleModalKeydown(e) {
  if (e.key === 'Escape' && liveModalOpen.value) closeLiveModal()
}

onMounted(() => document.addEventListener('keydown', handleModalKeydown))

// Auto-scroll modal when spec buffer grows
watch(
  () => chatStore.specStreamBuffer,
  async () => {
    if (liveModalOpen.value && liveModalType.value === 'spec') {
      await nextTick()
      scrollLiveModal()
    }
  }
)

// Auto-scroll modal when html buffer grows
watch(
  () => chatStore.htmlStreamBuffer,
  async () => {
    if (liveModalOpen.value && liveModalType.value === 'html') {
      await nextTick()
      scrollLiveModal()
    }
  }
)

const displayMessages = computed(() => {
  if (!chatStore.currentSession) return []
  let vizCount = 0
  return chatStore.currentSession.messages
    .filter(m => m.message_type !== 'spec_output' || m.content)  // show spec_output only when it has content
    .map(m => {
      if (m.message_type === 'html_output') {
        vizCount++
        return { ...m, _vizVersion: vizCount }
      }
      return m
    })
})

const lastMessageIsStreaming = computed(() => {
  const msgs = chatStore.currentSession?.messages
  if (!msgs || msgs.length === 0) return false
  return msgs[msgs.length - 1]._streaming
})

function handleSend(content) {
  chatStore.sendMessage(content)
}

function reconnect() {
  if (chatStore.currentVizId) {
    chatStore.connectToChat(chatStore.currentVizId)
  }
}

// Auto-scroll to bottom when new messages arrive
watch(
  () => chatStore.currentSession?.messages?.length,
  async () => {
    await nextTick()
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  }
)

// Also scroll on stream buffer changes
watch(
  () => chatStore.streamBuffer,
  async () => {
    await nextTick()
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  }
)
</script>

<style scoped>
.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.18s ease;
}
.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}
</style>
