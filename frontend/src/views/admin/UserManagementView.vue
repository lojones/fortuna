<template>
  <div class="min-h-screen bg-cp-black">
    <AppHeader />
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div class="mb-6">
        <div class="flex items-center gap-3 mb-4">
          <router-link to="/admin" class="text-cp-muted hover:text-cp-cyan">
            <span class="pi pi-arrow-left"></span>
          </router-link>
          <h2 class="text-2xl font-bold text-cp-text">User Management</h2>
        </div>

        <!-- Filter tabs -->
        <div class="flex gap-2 mb-6">
          <button
            v-for="f in filters"
            :key="f.value"
            @click="activeFilter = f.value"
            class="px-4 py-2 rounded-lg text-sm font-medium transition-colors"
            :class="{
              'bg-cp-yellow text-cp-black font-bold': activeFilter === f.value,
              'bg-cp-surface text-cp-muted border border-cp-border hover:bg-cp-surface2 hover:text-cp-text': activeFilter !== f.value,
            }"
          >
            {{ f.label }}
            <span v-if="f.count" class="ml-1 text-xs">({{ f.count }})</span>
          </button>
        </div>
      </div>

      <div class="bg-cp-surface rounded-xl border border-cp-border p-6">
        <UserTable :users="filteredUsers" @updated="refreshUsers" />
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '../../services/api'
import AppHeader from '../../components/common/AppHeader.vue'
import UserTable from '../../components/admin/UserTable.vue'

const allUsers = ref([])
const activeFilter = ref('all')

const filters = computed(() => [
  { label: 'All', value: 'all', count: allUsers.value.length },
  { label: 'Pending', value: 'pending', count: allUsers.value.filter(u => u.status === 'pending').length },
  { label: 'Active', value: 'active', count: allUsers.value.filter(u => u.status === 'active').length },
  { label: 'Suspended', value: 'suspended', count: allUsers.value.filter(u => u.status === 'suspended').length },
])

const filteredUsers = computed(() => {
  if (activeFilter.value === 'all') return allUsers.value
  return allUsers.value.filter((u) => u.status === activeFilter.value)
})

async function refreshUsers() {
  try {
    const response = await api.get('/api/users')
    allUsers.value = response.data
  } catch (err) {
    console.error('Failed to fetch users:', err)
  }
}

onMounted(refreshUsers)
</script>
