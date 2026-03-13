<template>
  <form @submit.prevent="handleLogin" class="space-y-4">
    <div v-if="authStore.error" class="p-3 rounded-lg text-sm"
      :class="{
        'bg-cp-yellow/10 text-cp-yellow border border-cp-yellow/30': isPendingError,
        'bg-cp-red/10 text-cp-red border border-cp-red/30': !isPendingError,
      }"
    >
      {{ authStore.error }}
    </div>

    <div>
      <label class="block text-sm font-medium text-cp-text mb-1">Username</label>
      <input
        v-model="username"
        type="text"
        required
        class="w-full px-3 py-2 border border-cp-border rounded-lg bg-cp-black focus:ring-2 focus:ring-cp-yellow/50 focus:border-cp-yellow/50 outline-none"
        placeholder="Enter your username"
      />
    </div>

    <div>
      <label class="block text-sm font-medium text-cp-text mb-1">Password</label>
      <div class="relative">
        <input
          v-model="password"
          :type="showPassword ? 'text' : 'password'"
          required
          class="w-full px-3 py-2 border border-cp-border rounded-lg bg-cp-black focus:ring-2 focus:ring-cp-yellow/50 focus:border-cp-yellow/50 outline-none pr-10"
          placeholder="Enter your password"
        />
        <button
          type="button"
          @click="showPassword = !showPassword"
          class="absolute right-3 top-1/2 -translate-y-1/2 text-cp-muted hover:text-cp-text"
        >
          <span :class="showPassword ? 'pi pi-eye-slash' : 'pi pi-eye'"></span>
        </button>
      </div>
    </div>

    <button
      type="submit"
      :disabled="authStore.isLoading"
      class="w-full bg-cp-yellow text-cp-black font-bold py-2 rounded-lg hover:bg-cp-yellow/85 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
    >
      <span v-if="authStore.isLoading" class="pi pi-spinner pi-spin"></span>
      Sign In
    </button>
  </form>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useAuthStore } from '../../stores/auth'

const authStore = useAuthStore()
const username = ref('')
const password = ref('')
const showPassword = ref(false)

const isPendingError = computed(() =>
  authStore.error?.includes('pending')
)

async function handleLogin() {
  try {
    await authStore.login(username.value, password.value)
  } catch {
    // error is handled by store
  }
}
</script>
