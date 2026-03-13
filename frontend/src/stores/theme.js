import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useThemeStore = defineStore('theme', () => {
  const isDark = ref(true)

  function initialize() {
    const saved = localStorage.getItem('fortuna_theme')
    isDark.value = saved ? saved === 'dark' : true
    applyTheme()
  }

  function toggle() {
    isDark.value = !isDark.value
    localStorage.setItem('fortuna_theme', isDark.value ? 'dark' : 'light')
    applyTheme()
  }

  function applyTheme() {
    document.documentElement.setAttribute('data-theme', isDark.value ? 'dark' : 'light')
  }

  return { isDark, initialize, toggle }
})
