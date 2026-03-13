<template>
  <Toast />
  <ConfirmDialog />
  <router-view />
</template>

<script setup>
import { onMounted } from 'vue'
import Toast from 'primevue/toast'
import ConfirmDialog from 'primevue/confirmdialog'
import { useAuthStore } from './stores/auth'
import { useThemeStore } from './stores/theme'

const authStore = useAuthStore()
const themeStore = useThemeStore()

onMounted(() => {
  themeStore.initialize()
  authStore.initializeAuth()
})
</script>
