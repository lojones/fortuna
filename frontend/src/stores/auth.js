import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import authService from '../services/authService'
import router from '../router'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const token = ref(null)
  const isLoading = ref(false)
  const error = ref(null)

  const isAuthenticated = computed(() => !!token.value && !!user.value)
  const isAdmin = computed(() => user.value?.role === 'admin')
  const isPending = computed(() => user.value?.status === 'pending')

  async function login(username, password) {
    isLoading.value = true
    error.value = null
    try {
      const response = await authService.login(username, password)
      token.value = response.data.access_token
      user.value = response.data.user
      localStorage.setItem('fortuna_token', token.value)
      router.push('/dashboard')
    } catch (err) {
      const detail = err.response?.data?.detail || 'Login failed'
      error.value = detail
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function register(username, email, password) {
    isLoading.value = true
    error.value = null
    try {
      const response = await authService.register(username, email, password)
      return response.data
    } catch (err) {
      const detail = err.response?.data?.detail || 'Registration failed'
      error.value = detail
      throw err
    } finally {
      isLoading.value = false
    }
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('fortuna_token')
    router.push('/login')
  }

  async function fetchCurrentUser() {
    try {
      const response = await authService.getMe()
      user.value = response.data
    } catch (err) {
      logout()
    }
  }

  async function initializeAuth() {
    const savedToken = localStorage.getItem('fortuna_token')
    if (savedToken) {
      token.value = savedToken
      await fetchCurrentUser()
    }
  }

  return {
    user,
    token,
    isLoading,
    error,
    isAuthenticated,
    isAdmin,
    isPending,
    login,
    register,
    logout,
    fetchCurrentUser,
    initializeAuth,
  }
})
