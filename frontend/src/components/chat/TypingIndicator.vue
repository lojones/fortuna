<template>
  <div class="flex justify-start">
    <div class="bg-cp-surface border border-cp-border rounded-xl px-4 py-3">
      <div class="flex items-center gap-2 mb-1">
        <span class="text-xs font-semibold text-cp-yellow">{{ brandName }}</span>
      </div>
      <div class="flex gap-1">
        <span class="w-2 h-2 bg-cp-cyan rounded-full animate-bounce" style="animation-delay: 0ms"></span>
        <span class="w-2 h-2 bg-cp-cyan rounded-full animate-bounce" style="animation-delay: 150ms"></span>
        <span class="w-2 h-2 bg-cp-cyan rounded-full animate-bounce" style="animation-delay: 300ms"></span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { BRAND_NAME } from '../../config/brand'
const brandName = BRAND_NAME
</script>
