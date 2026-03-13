<template>
  <div class="min-h-screen bg-cp-black">
    <AppHeader />
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <!-- Welcome -->
      <div class="mb-8">
        <h2 class="text-2xl font-bold text-cp-text">Welcome, <span class="text-cp-yellow">{{ authStore.user?.username }}</span></h2>
        <p class="text-cp-muted mt-1">Create and manage your visualizations</p>
      </div>

      <!-- Action Cards -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-10">
        <!-- New Visualization -->
        <div class="bg-cp-surface rounded-xl border border-cp-border p-6 hover:border-cp-yellow/50 transition-colors">
          <div class="flex items-center gap-3 mb-3">
            <span class="pi pi-sparkles text-2xl text-cp-yellow"></span>
            <h3 class="text-lg font-semibold text-cp-text">Create New Visualization</h3>
          </div>
          <p class="text-cp-muted mb-4">Start a new visualization from scratch</p>
          <button
            @click="showCreateModal = true"
            class="bg-cp-yellow text-cp-black font-bold px-4 py-2 rounded-lg hover:bg-cp-yellow/85 transition-colors"
          >
            New Visualization
          </button>
        </div>

        <!-- Continue Recent -->
        <div class="bg-cp-surface rounded-xl border border-cp-border p-6 hover:border-cp-cyan/50 transition-colors">
          <div class="flex items-center gap-3 mb-3">
            <span class="pi pi-pencil text-2xl text-cp-cyan"></span>
            <h3 class="text-lg font-semibold text-cp-text">Continue Recent Visualization</h3>
          </div>
          <p class="text-cp-muted mb-4">
            {{ recentViz ? recentViz.title : 'No visualizations yet' }}
          </p>
          <button
            @click="continueRecent"
            :disabled="!recentViz"
            class="bg-cp-cyan text-cp-black font-bold px-4 py-2 rounded-lg hover:bg-cp-cyan/85 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Continue
          </button>
        </div>
      </div>

      <!-- My Visualizations -->
      <div>
        <h3 class="text-xl font-semibold mb-4 text-cp-text">My Visualizations</h3>
        <div v-if="vizStore.isLoading" class="text-center py-8">
          <LoadingSpinner />
        </div>
        <div v-else-if="vizStore.visualizations.length === 0" class="text-center py-12 text-cp-muted">
          <span class="pi pi-chart-bar text-4xl block mb-3"></span>
          <p>No visualizations yet. Create your first one!</p>
        </div>
        <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <VisualizationCard
            v-for="viz in vizStore.visualizations"
            :key="viz.id"
            :visualization="viz"
            @click="goToVisualization(viz)"
            @delete="promptDelete(viz)"
          />
        </div>
      </div>
    </main>

    <!-- Create Modal -->
    <div v-if="showCreateModal" class="fixed inset-0 bg-black/70 flex items-center justify-center z-50">
      <div class="bg-cp-surface rounded-xl border border-cp-border p-6 w-full max-w-md mx-4" style="box-shadow: 0 0 40px rgba(0,240,255,0.08);">
        <h3 class="text-xl font-semibold mb-4 text-cp-text">New Visualization</h3>
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-cp-text mb-1">Title *</label>
            <input
              v-model="newVizTitle"
              type="text"
              class="w-full px-3 py-2 border border-cp-border rounded-lg bg-cp-black focus:ring-2 focus:ring-cp-yellow/50 focus:border-cp-yellow/50 outline-none"
              placeholder="My Visualization"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-cp-text mb-1">Description (optional)</label>
            <textarea
              v-model="newVizDescription"
              rows="3"
              class="w-full px-3 py-2 border border-cp-border rounded-lg bg-cp-black focus:ring-2 focus:ring-cp-yellow/50 focus:border-cp-yellow/50 outline-none"
              placeholder="Describe what you want to visualize..."
            ></textarea>
          </div>
          <div class="flex gap-3 justify-end">
            <button
              @click="showCreateModal = false"
              class="px-4 py-2 border border-cp-border rounded-lg text-cp-muted hover:bg-cp-surface2 hover:text-cp-text transition-colors"
            >
              Cancel
            </button>
            <button
              @click="createViz"
              :disabled="!newVizTitle.trim()"
              class="bg-cp-yellow text-cp-black font-bold px-4 py-2 rounded-lg hover:bg-cp-yellow/85 transition-colors disabled:opacity-50"
            >
              Create
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Delete Confirmation Modal -->
    <div v-if="vizToDelete" class="fixed inset-0 bg-black/70 flex items-center justify-center z-50">
      <div class="bg-cp-surface rounded-xl border border-cp-red/40 p-6 w-full max-w-md mx-4" style="box-shadow: 0 0 40px rgba(255,0,60,0.12);">
        <div class="flex items-center gap-3 mb-3">
          <span class="pi pi-exclamation-triangle text-2xl text-cp-red"></span>
          <h3 class="text-xl font-semibold text-cp-text">Delete Visualization</h3>
        </div>
        <p class="text-cp-muted mb-1">You are about to permanently delete:</p>
        <p class="font-semibold text-cp-text mb-4">"{{ vizToDelete.title }}"</p>
        <p class="text-sm text-cp-red/80 bg-cp-red/10 border border-cp-red/20 rounded-lg px-3 py-2 mb-6">
          This action is permanent and cannot be undone. All chat history and published versions will be lost.
        </p>
        <div class="flex gap-3 justify-end">
          <button
            @click="vizToDelete = null"
            class="px-4 py-2 border border-cp-border rounded-lg text-cp-muted hover:bg-cp-surface2 hover:text-cp-text transition-colors"
          >
            Cancel
          </button>
          <button
            @click="confirmDelete"
            :disabled="deleteInProgress"
            class="bg-cp-red text-white font-bold px-4 py-2 rounded-lg hover:bg-cp-red/85 transition-colors disabled:opacity-50 flex items-center gap-2"
          >
            <span v-if="deleteInProgress" class="pi pi-spin pi-spinner"></span>
            <span class="pi pi-trash" v-else></span>
            Delete Permanently
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useVisualizationStore } from '../stores/visualization'
import AppHeader from '../components/common/AppHeader.vue'
import LoadingSpinner from '../components/common/LoadingSpinner.vue'
import VisualizationCard from '../components/visualization/VisualizationCard.vue'

const router = useRouter()
const authStore = useAuthStore()
const vizStore = useVisualizationStore()

const showCreateModal = ref(false)
const newVizTitle = ref('')
const newVizDescription = ref('')
const recentViz = ref(null)
const vizToDelete = ref(null)
const deleteInProgress = ref(false)

onMounted(async () => {
  await vizStore.fetchMyVisualizations()
  recentViz.value = await vizStore.fetchRecentVisualization()
})

async function createViz() {
  try {
    const viz = await vizStore.createVisualization(newVizTitle.value.trim(), newVizDescription.value.trim() || null)
    showCreateModal.value = false
    newVizTitle.value = ''
    newVizDescription.value = ''
    router.push(`/chat/${viz.id}`)
  } catch (err) {
    // handled by store
  }
}

function continueRecent() {
  if (recentViz.value) {
    router.push(`/chat/${recentViz.value.id}`)
  }
}

function goToVisualization(viz) {
  if (viz.status === 'draft') {
    router.push(`/chat/${viz.id}`)
  } else {
    router.push(`/editor/${viz.id}`)
  }
}

function promptDelete(viz) {
  vizToDelete.value = viz
}

async function confirmDelete() {
  if (!vizToDelete.value) return
  deleteInProgress.value = true
  try {
    await vizStore.deleteVisualization(vizToDelete.value.id)
    vizToDelete.value = null
  } catch (err) {
    // error is set in store
  } finally {
    deleteInProgress.value = false
  }
}
</script>
