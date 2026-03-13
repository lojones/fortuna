<template>
  <div
    class="bg-cp-surface rounded-xl border border-cp-border p-4 hover:border-cp-cyan/40 transition-colors cursor-pointer relative group"
    @click="$emit('click')"
  >
    <!-- Delete button -->
    <button
      @click.stop="$emit('delete', visualization)"
      class="absolute top-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity text-cp-muted hover:text-cp-red p-1 rounded"
      title="Delete visualization"
    >
      <span class="pi pi-trash text-sm"></span>
    </button>

    <div class="flex items-start justify-between mb-2 pr-6">
      <h4 class="font-semibold text-cp-text truncate flex-1">{{ visualization.title }}</h4>
      <div class="flex items-center gap-1.5">
        <a
          v-if="visualization.published_slug"
          :href="publicUrl"
          target="_blank"
          rel="noopener"
          @click.stop
          class="flex items-center gap-1 text-xs text-cp-green bg-cp-green/10 border border-cp-green/30 px-2 py-0.5 rounded-full hover:bg-cp-green/20 transition-colors"
          title="Open published visualization"
        >
          <span class="pi pi-link text-[10px]"></span>
          Published
        </a>
        <VersionBadge :status="visualization.status" :version="visualization.latest_published_version" />
      </div>
    </div>
    <p v-if="visualization.description" class="text-sm text-cp-muted mb-3 line-clamp-2">
      {{ visualization.description }}
    </p>
    <div class="text-xs text-cp-muted/70">
      Updated {{ formatRelativeDate(visualization.updated_at) }}
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import VersionBadge from './VersionBadge.vue'
import { formatRelativeDate } from '../../utils/dateFormatter'

const props = defineProps({
  visualization: {
    type: Object,
    required: true,
  },
})

const publicUrl = computed(() => {
  if (!props.visualization.published_slug) return ''
  const base = import.meta.env.VITE_API_BASE_URL || window.location.origin
  return `${base}/visualization/${props.visualization.published_slug}`
})

defineEmits(['click', 'delete'])
</script>
