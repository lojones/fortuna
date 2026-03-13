<template>
  <!-- Spec output — completed specification-building progress bar -->
  <div v-if="message.message_type === 'spec_output'" class="flex justify-start">
    <div class="max-w-[80%] w-80 rounded-xl px-4 py-3 bg-cp-surface border border-cp-border/50 text-cp-text">
      <div class="flex items-center justify-between mb-2">
        <div class="flex items-center gap-2">
          <span class="text-xs font-semibold text-cp-yellow">{{ brandName }}</span>
          <span class="text-xs text-cp-muted">· Specification built</span>
        </div>
        <button
          @click="openModal('spec')"
          class="flex items-center gap-1 text-cp-muted hover:text-cp-yellow transition-colors p-1 rounded hover:bg-cp-yellow/10"
          title="View specification"
        >
          <!-- eye icon -->
          <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>
          </svg>
          <span class="text-xs">View</span>
        </button>
      </div>
      <!-- Completed progress bar (yellow) -->
      <div class="w-full bg-cp-border rounded-full h-1.5 overflow-hidden">
        <div class="h-1.5 rounded-full bg-cp-yellow transition-all w-full"></div>
      </div>
      <div class="text-xs mt-1.5 text-cp-muted opacity-60">{{ formatTime(message.timestamp) }}</div>
      <div v-if="message.cost_usd != null" class="text-xs mt-1 font-mono text-cp-muted opacity-60 text-left">
        {{ message.input_tokens?.toLocaleString() }}&thinsp;in &middot; {{ message.output_tokens?.toLocaleString() }}&thinsp;out &middot; ${{ formatCost(message.cost_usd) }}
      </div>
    </div>
  </div>

  <!-- HTML output — completed generation progress bar + visualization link -->
  <div v-else-if="message.message_type === 'html_output'" class="flex justify-start">
    <div class="max-w-[75%] rounded-xl px-4 py-3 bg-cp-surface border border-cp-cyan/40 text-cp-text">
      <div class="flex items-center gap-2 mb-2">
        <span class="text-xs font-semibold text-cp-yellow">{{ brandName }}</span>
      </div>

      <!-- Completed HTML generation progress bar (cyan/green) -->
      <div class="mb-3">
        <div class="flex items-center justify-between mb-1.5">
          <span class="text-xs text-cp-muted">· HTML visualization generated</span>
          <button
            @click="openModal('html')"
            class="flex items-center gap-1 text-cp-muted hover:text-cp-cyan transition-colors p-1 rounded hover:bg-cp-cyan/10 ml-2 shrink-0"
            title="View generated HTML source"
          >
            <!-- code/eye icon -->
            <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>
            </svg>
            <span class="text-xs">View</span>
          </button>
        </div>
        <div class="w-full bg-cp-border rounded-full h-2 overflow-hidden">
          <div class="h-2 rounded-full bg-cp-green transition-all w-full"></div>
        </div>
      </div>

      <!-- Visualization link -->
      <div
        class="flex items-center gap-2 cursor-pointer group"
        @click="openVisualization"
        title="Open visualization in new tab"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          class="h-5 w-5 text-cp-cyan shrink-0 group-hover:text-cp-cyan/70 transition-colors"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
          <polyline points="3 9 9 9 9 21"/>
          <polyline points="9 9 15 3 15 21"/>
          <polyline points="15 9 21 9"/>
        </svg>
        <span class="text-cp-cyan underline underline-offset-2 group-hover:text-cp-cyan/70 transition-colors text-sm font-medium">
          {{ vizTitle }} v{{ message._vizVersion }}
        </span>
      </div>

      <div class="text-xs mt-2 opacity-50 text-left text-cp-muted">
        {{ formatTime(message.timestamp) }}
      </div>
      <div v-if="message.cost_usd != null" class="text-xs mt-1 font-mono text-cp-muted opacity-60 text-left">
        {{ message.input_tokens?.toLocaleString() }}&thinsp;in &middot; {{ message.output_tokens?.toLocaleString() }}&thinsp;out &middot; ${{ formatCost(message.cost_usd) }}
      </div>
    </div>
  </div>

  <!-- Regular chat message (user / assistant clarification) -->
  <div
    v-else
    class="flex"
    :class="isUser ? 'justify-end' : 'justify-start'"
  >
    <div
      class="max-w-[75%] rounded-xl px-4 py-3"
      :class="{
        'bg-cp-yellow text-cp-black': isUser,
        'bg-cp-surface border border-cp-border text-cp-text': !isUser,
      }"
    >
      <!-- Label for assistant -->
      <div v-if="!isUser" class="flex items-center gap-2 mb-1">
        <span class="text-xs font-semibold text-cp-yellow">{{ brandName }}</span>
      </div>

      <!-- Markdown for assistant, plain text for user -->
      <div
        v-if="!isUser"
        class="text-sm prose-chat break-words"
        v-html="renderedContent"
      ></div>
      <div v-else class="text-sm whitespace-pre-wrap break-words">{{ message.content }}</div>

      <div
        class="text-xs mt-1 opacity-50"
        :class="isUser ? 'text-right text-cp-black' : 'text-left text-cp-muted'"
      >
        {{ formatTime(message.timestamp) }}
      </div>
      <div v-if="!isUser && message.cost_usd != null" class="text-xs mt-1 font-mono text-cp-muted opacity-60 text-left">
        {{ message.input_tokens?.toLocaleString() }}&thinsp;in &middot; {{ message.output_tokens?.toLocaleString() }}&thinsp;out &middot; ${{ formatCost(message.cost_usd) }}
      </div>
    </div>
  </div>

  <!-- Full-screen response viewer modal (teleported to <body>) -->
  <Teleport to="body">
    <Transition name="modal-fade">
      <div
        v-if="modalOpen"
        class="fixed inset-0 z-[999] flex items-center justify-center p-4"
        @click.self="closeModal"
        @keydown.esc="closeModal"
        tabindex="-1"
      >
        <!-- Backdrop -->
        <div class="absolute inset-0 bg-black/70 backdrop-blur-sm" @click="closeModal"></div>

        <!-- Modal panel -->
        <div class="relative z-10 flex flex-col bg-cp-black border border-cp-border rounded-xl shadow-2xl"
             style="width: 95vw; height: 92vh;">
          <!-- Header -->
          <div class="flex items-center justify-between px-5 py-3 border-b border-cp-border shrink-0">
            <div class="flex items-center gap-3">
              <!-- Icon -->
              <svg v-if="modalType === 'spec'" xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-cp-yellow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/>
              </svg>
              <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-cp-cyan" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/>
              </svg>
              <span class="text-sm font-semibold text-cp-text">
                {{ modalType === 'spec' ? 'Visualization Specification' : 'Generated HTML Source' }}
              </span>
              <span class="text-xs text-cp-muted px-2 py-0.5 rounded bg-cp-surface border border-cp-border/50">
                {{ modalType === 'spec' ? 'Markdown' : 'HTML' }}
              </span>
            </div>
            <button
              @click="closeModal"
              class="text-cp-muted hover:text-cp-text transition-colors p-1.5 rounded hover:bg-cp-surface"
              title="Close"
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
              </svg>
            </button>
          </div>

          <!-- Content area -->
          <div class="flex-1 overflow-auto bg-cp-black rounded-b-xl">
            <!-- Spec: rendered Markdown -->
            <div
              v-if="modalType === 'spec'"
              class="p-5 text-sm text-cp-text prose-chat break-words leading-relaxed"
              v-html="renderedModalContent"
            ></div>
            <!-- HTML: syntax-highlighted code -->
            <pre
              v-else
              class="h-full p-5 text-xs font-mono leading-relaxed"
            ><code class="language-html" v-html="highlightedModalContent"></code></pre>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import hljs from 'highlight.js/lib/core'
import xml from 'highlight.js/lib/languages/xml'
import 'highlight.js/styles/github-dark.min.css'
import { useVisualizationStore } from '../../stores/visualization'
import { BRAND_NAME } from '../../config/brand'

hljs.registerLanguage('xml', xml)

const props = defineProps({
  message: {
    type: Object,
    required: true,
  },
})

const vizStore = useVisualizationStore()
const router = useRouter()
const brandName = BRAND_NAME

// Configure marked with sensible defaults
marked.setOptions({ breaks: true, gfm: true })

const isUser = computed(() => props.message.role === 'user')

const vizTitle = computed(() => vizStore.currentVisualization?.title || 'Visualization')

const renderedContent = computed(() => {
  if (!props.message.content) return ''
  const raw = marked.parse(props.message.content)
  return DOMPurify.sanitize(raw, { USE_PROFILES: { html: true } })
})

// ── Modal state ────────────────────────────────────────────────────────────────
const modalOpen = ref(false)
const modalType = ref(null) // 'spec' | 'html'

const modalContent = computed(() => props.message.content ?? '')

const renderedModalContent = computed(() => {
  const raw = props.message.content ?? ''
  if (!raw) return ''
  const html = marked.parse(raw)
  return DOMPurify.sanitize(html, { USE_PROFILES: { html: true } })
})

const highlightedModalContent = computed(() => {
  const raw = props.message.content ?? ''
  if (!raw) return ''
  return hljs.highlight(raw, { language: 'xml' }).value
})

function openModal(type) {
  modalType.value = type
  modalOpen.value = true
}

function closeModal() {
  modalOpen.value = false
}

function handleKeydown(e) {
  if (e.key === 'Escape' && modalOpen.value) closeModal()
}

onMounted(() => document.addEventListener('keydown', handleKeydown))
onUnmounted(() => document.removeEventListener('keydown', handleKeydown))

// ── Navigation ─────────────────────────────────────────────────────────────────
function openVisualization() {
  const vizId = vizStore.currentVisualization?.id
  if (!vizId) return
  // Pass msgId so VisualizationView knows to show this specific version's HTML
  // rather than always defaulting to the latest current_draft_html.
  router.push({ path: `/visualization/${vizId}`, query: { msgId: props.message.message_id } })
}

// ── Formatting helpers ─────────────────────────────────────────────────────────
function formatTime(ts) {
  if (!ts) return ''
  const d = new Date(ts)
  return d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
}

function formatCost(usd) {
  if (usd == null || usd === 0) return ''
  const rounded = Math.max(0.01, Math.round(usd * 100) / 100)
  return rounded.toFixed(2)
}
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
