<template>
  <span
    class="text-xs px-2 py-1 rounded-full font-medium"
    :class="{
      'bg-cp-surface2 text-cp-muted border border-cp-border': status === 'draft',
      'bg-cp-cyan/10 text-cp-cyan border border-cp-cyan/30': status === 'published',
    }"
  >
    {{ status === 'published' ? `v${version}` : 'Draft' }}
  </span>
</template>

<script setup>
defineProps({
  status: {
    type: String,
    required: true,
  },
  version: {
    type: Number,
    default: null,
  },
})
</script>
