<template>
  <div class="h-screen bg-cp-black flex flex-col overflow-hidden">
    <!-- Header -->
    <div class="sticky top-0 z-10 bg-cp-black border-b border-cp-border px-4 py-3 flex items-center justify-between shrink-0">
      <div class="flex items-center gap-3">
        <router-link to="/dashboard" class="text-cp-muted hover:text-cp-cyan">
          <span class="pi pi-arrow-left"></span>
        </router-link>
        <h1 class="text-lg font-semibold text-cp-text">{{ vizStore.currentVisualization?.title || 'Chat' }}</h1>
        <span
          v-if="chatStore.currentSession"
          class="text-xs px-2 py-1 rounded-full font-mono"
          :class="{
            'bg-cp-cyan/10 text-cp-cyan border border-cp-cyan/30': chatStore.currentSession.llm_state === 'clarifying',
            'bg-cp-yellow/10 text-cp-yellow border border-cp-yellow/30': chatStore.currentSession.llm_state === 'generating' || chatStore.isGenerating,
            'bg-cp-green/10 text-cp-green border border-cp-green/30': chatStore.currentSession.llm_state === 'complete' && !chatStore.isGenerating,
          }"
        >
          {{ chatStore.isGenerating ? 'Generating...' :
             chatStore.currentSession.llm_state === 'clarifying' ? 'Clarifying...' :
             chatStore.currentSession.llm_state === 'generating' ? 'Generating...' : 'Complete' }}
        </span>
        <span
          v-if="totalCost > 0"
          class="text-xs px-2 py-1 rounded-full font-mono bg-cp-surface border border-cp-border text-cp-muted"
          title="Total LLM cost for this visualization so far"
        >
          ~${{ formatTotalCost(totalCost) }}
        </span>
      </div>
      <div class="flex items-center gap-3">
        <span
          class="w-2 h-2 rounded-full"
          :class="chatStore.isConnected ? 'bg-cp-green' : 'bg-cp-red'"
        ></span>
        <span class="text-xs text-cp-muted">{{ chatStore.isConnected ? 'Connected' : 'Disconnected' }}</span>
        <button
          @click="themeStore.toggle()"
          class="text-cp-muted hover:text-cp-text text-sm transition-colors p-1.5 rounded-md hover:bg-cp-surface2"
          :title="themeStore.isDark ? 'Switch to light mode' : 'Switch to dark mode'"
        >
          <span :class="themeStore.isDark ? 'pi pi-sun' : 'pi pi-moon'"></span>
        </button>
      </div>
    </div>

    <!-- Chat area -->
    <ChatWindow />
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { useChatStore } from '../stores/chat'
import { useVisualizationStore } from '../stores/visualization'
import { useThemeStore } from '../stores/theme'
import ChatWindow from '../components/chat/ChatWindow.vue'

const route = useRoute()
const chatStore = useChatStore()
const vizStore = useVisualizationStore()

const themeStore = useThemeStore()
const vizId = route.params.vizId

// Use the viz doc's total_cost_usd (persisted) as primary, fall back to session sum
// so the cost is always accurate after page reload.
const totalCost = computed(() => {
  const vizCost = vizStore.currentVisualization?.total_cost_usd ?? 0
  const sessionCost = chatStore.totalSessionCost
  return Math.max(vizCost, sessionCost)
})

onMounted(async () => {
  await vizStore.fetchVisualization(vizId)
  chatStore.connectToChat(vizId)
})

onUnmounted(() => {
  chatStore.disconnectFromChat()
})

function formatTotalCost(usd) {
  if (usd == null || usd === 0) return ''
  const rounded = Math.max(0.01, Math.round(usd * 100) / 100)
  return rounded.toFixed(2)
}
</script>
