import { defineStore } from 'pinia'
import { ref } from 'vue'
import visualizationService from '../services/visualizationService'

export const useVisualizationStore = defineStore('visualization', () => {
  const visualizations = ref([])
  const currentVisualization = ref(null)
  const isLoading = ref(false)
  const error = ref(null)

  async function fetchMyVisualizations() {
    isLoading.value = true
    error.value = null
    try {
      const response = await visualizationService.getAll()
      visualizations.value = response.data
    } catch (err) {
      error.value = 'Failed to load visualizations'
    } finally {
      isLoading.value = false
    }
  }

  async function fetchVisualization(vizId) {
    isLoading.value = true
    error.value = null
    try {
      const response = await visualizationService.getById(vizId)
      currentVisualization.value = response.data
    } catch (err) {
      error.value = 'Failed to load visualization'
    } finally {
      isLoading.value = false
    }
  }

  async function fetchRecentVisualization() {
    try {
      const response = await visualizationService.getRecent()
      return response.data
    } catch {
      return null
    }
  }

  async function createVisualization(title, description) {
    isLoading.value = true
    error.value = null
    try {
      const response = await visualizationService.create(title, description)
      visualizations.value.unshift(response.data)
      return response.data
    } catch (err) {
      error.value = 'Failed to create visualization'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function publishVisualization(vizId) {
    isLoading.value = true
    error.value = null
    try {
      const response = await visualizationService.publish(vizId)
      currentVisualization.value = response.data
      // Update in list too
      const idx = visualizations.value.findIndex((v) => v.id === vizId)
      if (idx !== -1) {
        visualizations.value[idx] = response.data
      }
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to publish'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function deleteVisualization(vizId) {
    try {
      await visualizationService.delete(vizId)
      visualizations.value = visualizations.value.filter((v) => v.id !== vizId)
      if (currentVisualization.value?.id === vizId) {
        currentVisualization.value = null
      }
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to delete visualization'
      throw err
    }
  }

  async function publishVersion(vizId, versionNumber) {
    isLoading.value = true
    error.value = null
    try {
      const response = await visualizationService.publishVersion(vizId, versionNumber)
      currentVisualization.value = response.data
      const idx = visualizations.value.findIndex((v) => v.id === vizId)
      if (idx !== -1) {
        visualizations.value[idx] = response.data
      }
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to publish version'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function unpublishVisualization(vizId) {
    isLoading.value = true
    error.value = null
    try {
      const response = await visualizationService.unpublish(vizId)
      currentVisualization.value = response.data
      const idx = visualizations.value.findIndex((v) => v.id === vizId)
      if (idx !== -1) {
        visualizations.value[idx] = response.data
      }
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to unpublish'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  return {
    visualizations,
    currentVisualization,
    isLoading,
    error,
    fetchMyVisualizations,
    fetchVisualization,
    fetchRecentVisualization,
    createVisualization,
    publishVisualization,
    publishVersion,
    unpublishVisualization,
    deleteVisualization,
  }
})
