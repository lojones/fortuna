<template>
  <footer class="bg-cp-black border-t border-cp-border py-4 text-center text-sm text-cp-muted">
    {{ brandName }} &copy; {{ new Date().getFullYear() }}
  </footer>
</template>

<script setup>
import { BRAND_NAME } from '../../config/brand'
const brandName = BRAND_NAME
</script>
