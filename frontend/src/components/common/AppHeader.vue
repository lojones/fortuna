<template>
  <header class="bg-cp-black border-b border-cp-border px-4 py-3">
    <div class="max-w-7xl mx-auto flex items-center justify-between">
      <div class="flex items-center gap-3">
        <router-link to="/dashboard" class="text-xl font-bold text-cp-yellow hover:text-cp-yellow/80 tracking-widest uppercase">
          {{ brandName }}
        </router-link>
      </div>
      <div class="flex items-center gap-4">
        <router-link
          v-if="authStore.isAdmin"
          to="/admin"
          class="text-cp-cyan hover:text-cp-cyan/80 text-sm font-medium"
        >
          <span class="pi pi-cog mr-1"></span>
          Admin Panel
        </router-link>
        <div class="flex items-center gap-2">
          <span class="text-sm text-cp-muted">{{ authStore.user?.username }}</span>
          <span
            class="text-xs px-2 py-0.5 rounded-full font-mono"
            :class="{
              'bg-cp-cyan/10 text-cp-cyan border border-cp-cyan/30': authStore.user?.role === 'admin',
              'bg-cp-surface2 text-cp-muted': authStore.user?.role === 'user',
            }"
          >
            {{ authStore.user?.role }}
          </span>
        </div>
        <button
          @click="themeStore.toggle()"
          class="text-cp-muted hover:text-cp-text text-sm transition-colors p-1.5 rounded-md hover:bg-cp-surface2"
          :title="themeStore.isDark ? 'Switch to light mode' : 'Switch to dark mode'"
        >
          <span :class="themeStore.isDark ? 'pi pi-sun' : 'pi pi-moon'"></span>
        </button>
        <button
          @click="authStore.logout()"
          class="text-cp-muted hover:text-cp-red text-sm transition-colors"
        >
          <span class="pi pi-sign-out mr-1"></span>
          Logout
        </button>
      </div>
    </div>
  </header>
</template>

<script setup>
import { useAuthStore } from '../../stores/auth'
import { useThemeStore } from '../../stores/theme'
import { BRAND_NAME } from '../../config/brand'
const authStore = useAuthStore()
const themeStore = useThemeStore()
const brandName = BRAND_NAME
</script>
