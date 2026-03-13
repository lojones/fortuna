<template>
  <form @submit.prevent="handleRegister" class="space-y-4">
    <div v-if="successMessage" class="bg-cp-cyan/10 text-cp-cyan border border-cp-cyan/30 p-3 rounded-lg text-sm">
      {{ successMessage }}
    </div>

    <div v-if="authStore.error" class="bg-cp-red/10 text-cp-red border border-cp-red/30 p-3 rounded-lg text-sm">
      {{ authStore.error }}
    </div>

    <div>
      <label class="block text-sm font-medium text-cp-text mb-1">Username</label>
      <input
        v-model="username"
        type="text"
        required
        class="w-full px-3 py-2 border border-cp-border rounded-lg bg-cp-black focus:ring-2 focus:ring-cp-yellow/50 focus:border-cp-yellow/50 outline-none"
        placeholder="Choose a username"
      />
    </div>

    <div>
      <label class="block text-sm font-medium text-cp-text mb-1">Email</label>
      <input
        v-model="email"
        type="email"
        required
        class="w-full px-3 py-2 border border-cp-border rounded-lg bg-cp-black focus:ring-2 focus:ring-cp-yellow/50 focus:border-cp-yellow/50 outline-none"
        placeholder="your@email.com"
      />
    </div>

    <div>
      <label class="block text-sm font-medium text-cp-text mb-1">Password</label>
      <input
        v-model="password"
        type="password"
        required
        minlength="8"
        class="w-full px-3 py-2 border border-cp-border rounded-lg bg-cp-black focus:ring-2 focus:ring-cp-yellow/50 focus:border-cp-yellow/50 outline-none"
        placeholder="Minimum 8 characters"
      />
      <div class="mt-1 h-1 rounded-full bg-cp-surface2">
        <div
          class="h-1 rounded-full transition-all"
          :class="strengthColor"
          :style="{ width: strengthPercent + '%' }"
        ></div>
      </div>
    </div>

    <div>
      <label class="block text-sm font-medium text-cp-text mb-1">Confirm Password</label>
      <input
        v-model="confirmPassword"
        type="password"
        required
        class="w-full px-3 py-2 border border-cp-border rounded-lg bg-cp-black focus:ring-2 focus:ring-cp-yellow/50 focus:border-cp-yellow/50 outline-none"
        placeholder="Re-enter your password"
      />
      <p v-if="confirmPassword && password !== confirmPassword" class="text-cp-red text-xs mt-1">
        Passwords do not match
      </p>
    </div>

    <button
      type="submit"
      :disabled="authStore.isLoading || password !== confirmPassword || password.length < 8"
      class="w-full bg-cp-yellow text-cp-black font-bold py-2 rounded-lg hover:bg-cp-yellow/85 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
    >
      <span v-if="authStore.isLoading" class="pi pi-spinner pi-spin"></span>
      Create Account
    </button>
  </form>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const username = ref('')
const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const successMessage = ref('')

const strengthPercent = computed(() => {
  const len = password.value.length
  if (len === 0) return 0
  if (len < 8) return 25
  if (len < 12) return 50
  if (len < 16) return 75
  return 100
})

const strengthColor = computed(() => {
  const p = strengthPercent.value
  if (p <= 25) return 'bg-red-400'
  if (p <= 50) return 'bg-yellow-400'
  if (p <= 75) return 'bg-blue-400'
  return 'bg-green-400'
})

async function handleRegister() {
  if (password.value !== confirmPassword.value) return

  try {
    const result = await authStore.register(username.value, email.value, password.value)
    successMessage.value = result.message || 'Registration submitted. Awaiting admin approval.'
    setTimeout(() => {
      router.push('/login')
    }, 3000)
  } catch {
    // error is handled by store
  }
}
</script>
