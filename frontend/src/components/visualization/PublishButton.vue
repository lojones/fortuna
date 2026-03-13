<template>
  <button
    @click="handlePublish"
    :disabled="vizStore.isLoading"
    class="flex items-center gap-1 px-3 py-2 bg-cp-cyan text-cp-black font-bold rounded-lg hover:bg-cp-cyan/85 transition-colors text-sm disabled:opacity-50"
  >
    <span class="pi pi-cloud-upload"></span>
    Publish
  </button>
</template>

<script setup>
import { useConfirm } from 'primevue/useconfirm'
import { useVisualizationStore } from '../../stores/visualization'

const props = defineProps({
  visualization: {
    type: Object,
    required: true,
  },
})

const emit = defineEmits(['published'])
const confirm = useConfirm()
const vizStore = useVisualizationStore()

function handlePublish() {
  const nextVersion = (props.visualization.published_versions?.length || 0) + 1
  confirm.require({
    message: `Publish this visualization as Version ${nextVersion}?`,
    header: 'Confirm Publish',
    acceptLabel: 'Publish',
    rejectLabel: 'Cancel',
    accept: async () => {
      try {
        await vizStore.publishVisualization(props.visualization.id)
        emit('published')
      } catch {
        //  handled by store
      }
    },
  })
}
</script>
