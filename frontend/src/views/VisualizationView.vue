<template>
  <div class="min-h-screen bg-cp-black flex flex-col">
    <!-- Header -->
    <div class="bg-cp-black border-b border-cp-border px-4 py-3 flex items-center justify-between">
      <div class="flex items-center gap-3">
        <!-- Navigation: back to chat for current/historical drafts, back to dashboard for published version review -->
        <button
          v-if="!viewingVersion || isDraftHistory"
          @click="isDraftHistory ? clearDraftHistoryView() : editVisualization()"
          class="flex items-center gap-1.5 text-cp-muted hover:text-cp-cyan transition-colors text-sm"
        >
          <span class="pi pi-arrow-left"></span>
          <span>{{ isDraftHistory ? 'Back to current draft' : 'Back to Chat' }}</span>
        </button>
        <router-link v-else to="/dashboard" class="text-cp-muted hover:text-cp-cyan">
          <span class="pi pi-arrow-left"></span>
        </router-link>
        <h1 class="text-lg font-semibold text-cp-text">{{ viz?.title || 'Visualization' }}</h1>
        <VersionBadge v-if="viz" :status="viz.status" :version="viz.latest_published_version" />
      </div>
      <div class="flex items-center gap-2">
        <button
          @click="themeStore.toggle()"
          class="text-cp-muted hover:text-cp-text text-sm transition-colors p-1.5 rounded-md hover:bg-cp-surface2"
          :title="themeStore.isDark ? 'Switch to light mode' : 'Switch to dark mode'"
        >
          <span :class="themeStore.isDark ? 'pi pi-sun' : 'pi pi-moon'"></span>
        </button>
        <button
          @click="editVisualization"
          class="flex items-center gap-1 px-3 py-2 border border-cp-border rounded-lg text-cp-muted hover:bg-cp-surface2 hover:text-cp-text transition-colors text-sm"
        >
          <span class="pi pi-pencil"></span>
          Edit
        </button>
        <PublishButton
          v-if="viz?.current_draft_html"
          :visualization="viz"
          @published="onPublished"
        />
        <button
          v-if="viz?.published_slug"
          @click="handleUnpublish"
          :disabled="vizStore.isLoading"
          class="flex items-center gap-1 px-3 py-2 border border-cp-red/50 rounded-lg text-cp-red hover:bg-cp-red/10 transition-colors text-sm disabled:opacity-50"
        >
          <span class="pi pi-cloud-download"></span>
          Unpublish
        </button>
      </div>
    </div>

    <!-- Published URL banner -->
    <div
      v-if="viz?.published_slug"
      class="bg-cp-surface border-b border-cp-border px-4 py-2 flex items-center gap-3"
    >
      <span class="pi pi-link text-cp-green text-sm"></span>
      <span class="text-xs text-cp-muted">Published at:</span>
      <a
        :href="publicUrl"
        target="_blank"
        rel="noopener"
        class="text-sm text-cp-cyan hover:text-cp-cyan/80 underline underline-offset-2 font-mono"
      >
        {{ publicUrl }}
      </a>
      <button
        @click="copyUrl"
        class="text-xs text-cp-muted hover:text-cp-text px-2 py-1 rounded border border-cp-border hover:bg-cp-surface2 transition-colors"
      >
        <span class="pi pi-copy"></span> Copy
      </button>
    </div>

    <!-- Main Content -->
    <div class="flex flex-1 overflow-hidden">
      <!-- Visualization iframe -->
      <div class="flex-1">
        <!-- Draft-history banner shown when viewing a historical draft from chat -->
        <div
          v-if="isDraftHistory"
          class="bg-cp-yellow/10 border-b border-cp-yellow/30 px-4 py-2 flex items-center justify-between text-xs"
        >
          <span class="text-cp-yellow font-medium">Viewing a historical draft — this is not the current version</span>
          <button @click="clearDraftHistoryView" class="text-cp-yellow hover:text-cp-yellow/70 underline">
            View current draft
          </button>
        </div>

        <VisualizationFrame
          v-if="viewingHtml || viz?.current_draft_html"
          :htmlContent="viewingHtml || viz.current_draft_html"
        />
        <div
          v-else
          class="flex items-center justify-center h-full text-cp-muted"
        >
          <div class="text-center">
            <span class="pi pi-chart-bar text-5xl block mb-3 text-cp-border"></span>
            <p class="text-lg text-cp-text">No visualization generated yet.</p>
            <p class="text-sm mt-1">Start chatting to create one.</p>
            <button
              @click="editVisualization"
              class="mt-4 bg-cp-yellow text-cp-black font-bold px-4 py-2 rounded-lg hover:bg-cp-yellow/85 transition-colors"
            >
              Start Chat
            </button>
          </div>
        </div>
      </div>

      <!-- Version History Sidebar -->
      <div
        v-if="viz?.published_versions?.length > 0"
        class="w-64 bg-cp-surface border-l border-cp-border overflow-y-auto"
      >
        <div class="p-4">
          <h3 class="font-semibold text-cp-text mb-3">Version History</h3>
          <div class="space-y-2">
            <div
              v-for="v in [...viz.published_versions].reverse()"
              :key="v.version_number"
              class="p-3 rounded-lg border cursor-pointer hover:bg-cp-surface2 transition-colors"
              :class="{
                'border-cp-yellow bg-cp-yellow/5': viewingVersion === v.version_number,
                'border-cp-border': viewingVersion !== v.version_number,
              }"
              @click="viewVersion(v)"
            >
              <div class="font-medium text-sm text-cp-text">Version {{ v.version_number }}</div>
              <div class="text-xs text-cp-muted mt-1">{{ formatDate(v.published_at) }}</div>
              <button
                @click.stop="restoreDraft(v)"
                class="text-xs text-cp-cyan hover:text-cp-cyan/80 mt-2"
              >
                Restore as Draft
              </button>
              <button
                @click.stop="publishSpecificVersion(v)"
                class="text-xs text-cp-yellow hover:text-cp-yellow/80 mt-1 block"
              >
                Publish this version
              </button>
            </div>
          </div>
          <button
            v-if="viewingVersion"
            @click="clearVersionView"
            class="mt-3 text-sm text-cp-muted hover:text-cp-text w-full text-center"
          >
            Back to current draft
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useVisualizationStore } from '../stores/visualization'
import { useThemeStore } from '../stores/theme'
import { useToast } from 'primevue/usetoast'
import { useConfirm } from 'primevue/useconfirm'
import VisualizationFrame from '../components/visualization/VisualizationFrame.vue'
import VersionBadge from '../components/visualization/VersionBadge.vue'
import PublishButton from '../components/visualization/PublishButton.vue'
import { formatDate } from '../utils/dateFormatter'
import chatService from '../services/chatService'

const route = useRoute()
const router = useRouter()
const vizStore = useVisualizationStore()
const themeStore = useThemeStore()
const toast = useToast()
const confirm = useConfirm()

const vizId = route.params.vizId
const viewingVersion = ref(null)   // non-null when viewing a published version from sidebar
const viewingHtml = ref(null)      // HTML override for both sidebar versions and draft history
const isDraftHistory = ref(false)  // true when viewing a historical draft from chat (via msgId)

const viz = computed(() => vizStore.currentVisualization)

const publicUrl = computed(() => {
  if (!viz.value?.published_slug) return ''
  const base = import.meta.env.VITE_API_BASE_URL || window.location.origin
  return `${base}/visualization/${viz.value.published_slug}`
})

onMounted(async () => {
  await vizStore.fetchVisualization(vizId)

  // If arriving from chat with a specific message ID, show that historical draft HTML
  const msgId = route.query.msgId
  if (msgId) {
    try {
      const response = await chatService.getSession(vizId)
      const session = response.data
      const htmlOutputs = session?.messages?.filter(m => m.message_type === 'html_output') ?? []
      const msgIndex = htmlOutputs.findIndex(m => m.message_id === msgId)
      if (msgIndex !== -1 && htmlOutputs[msgIndex]?.content) {
        viewingHtml.value = htmlOutputs[msgIndex].content
        // Only flag as historical if this is NOT the most recent html_output
        const isLatest = msgIndex === htmlOutputs.length - 1
        isDraftHistory.value = !isLatest
      }
    } catch {
      // If lookup fails just show the current draft silently
    }
  }
})

function editVisualization() {
  router.push(`/chat/${vizId}`)
}

function viewVersion(v) {
  viewingVersion.value = v.version_number
  viewingHtml.value = v.html_content
}

function clearVersionView() {
  viewingVersion.value = null
  viewingHtml.value = null
}

function clearDraftHistoryView() {
  isDraftHistory.value = false
  viewingHtml.value = null
  // Remove the msgId from the URL so a refresh doesn't re-activate history mode
  router.replace({ path: route.path })
}

async function restoreDraft(v) {
  // In a full implementation this would call an API endpoint
  if (viz.value) {
    viz.value.current_draft_html = v.html_content
    toast.add({ severity: 'success', summary: 'Restored', detail: `Version ${v.version_number} restored as draft`, life: 3000 })
    clearVersionView()
  }
}

async function onPublished() {
  await vizStore.fetchVisualization(vizId)
  toast.add({ severity: 'success', summary: 'Published', detail: `Visualization published at ${publicUrl.value}`, life: 5000 })
}

async function handleUnpublish() {
  confirm.require({
    message: 'This will remove the public URL. Unpublish?',
    header: 'Confirm Unpublish',
    acceptLabel: 'Unpublish',
    rejectLabel: 'Cancel',
    accept: async () => {
      try {
        await vizStore.unpublishVisualization(vizId)
        toast.add({ severity: 'info', summary: 'Unpublished', detail: 'Public URL removed', life: 3000 })
      } catch {
        // handled by store
      }
    },
  })
}

async function publishSpecificVersion(v) {
  confirm.require({
    message: `Publish Version ${v.version_number} as the live visualization?`,
    header: 'Publish Version',
    acceptLabel: 'Publish',
    rejectLabel: 'Cancel',
    accept: async () => {
      try {
        await vizStore.publishVersion(vizId, v.version_number)
        toast.add({ severity: 'success', summary: 'Published', detail: `Version ${v.version_number} is now live`, life: 3000 })
      } catch {
        // handled by store
      }
    },
  })
}

function copyUrl() {
  navigator.clipboard.writeText(publicUrl.value)
  toast.add({ severity: 'info', summary: 'Copied', detail: 'URL copied to clipboard', life: 2000 })
}
</script>
