<template>
  <div class="min-h-screen bg-cp-black">
    <AppHeader />
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div class="mb-8">
        <h2 class="text-2xl font-bold text-cp-text">Admin Dashboard</h2>
        <p class="text-cp-muted mt-1">Manage users and monitor the platform</p>
      </div>

      <!-- Stats -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <div class="bg-cp-surface rounded-xl border border-cp-border p-6">
          <div class="text-3xl font-bold text-cp-cyan">{{ allUsers.length }}</div>
          <div class="text-cp-muted text-sm mt-1">Total Users</div>
        </div>
        <div class="bg-cp-surface rounded-xl border border-cp-yellow/30 p-6">
          <div class="text-3xl font-bold text-cp-yellow">{{ pendingUsers.length }}</div>
          <div class="text-cp-muted text-sm mt-1">Pending Approvals</div>
        </div>
        <div class="bg-cp-surface rounded-xl border border-cp-green/30 p-6">
          <div class="text-3xl font-bold text-cp-green">{{ activeUsers.length }}</div>
          <div class="text-cp-muted text-sm mt-1">Active Users</div>
        </div>
      </div>

      <!-- Pending Approvals -->
      <PendingApprovals
        :users="pendingUsers"
        @approve="handleApprove"
        @reject="handleReject"
        class="mb-8"
      />

      <!-- All Users -->
      <div class="bg-cp-surface rounded-xl border border-cp-border p-6">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-cp-text">All Users</h3>
          <router-link
            to="/admin/users"
            class="text-cp-cyan hover:text-cp-cyan/80 text-sm font-medium"
          >
            Full Management →
          </router-link>
        </div>
        <UserTable :users="allUsers" @updated="refreshUsers" />
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '../../services/api'
import AppHeader from '../../components/common/AppHeader.vue'
import UserTable from '../../components/admin/UserTable.vue'
import PendingApprovals from '../../components/admin/PendingApprovals.vue'

const allUsers = ref([])
const pendingUsers = computed(() => allUsers.value.filter((u) => u.status === 'pending'))
const activeUsers = computed(() => allUsers.value.filter((u) => u.status === 'active'))

async function refreshUsers() {
  try {
    const response = await api.get('/api/users')
    allUsers.value = response.data
  } catch (err) {
    console.error('Failed to fetch users:', err)
  }
}

async function handleApprove(userId) {
  try {
    await api.patch(`/api/users/${userId}/approve`)
    await refreshUsers()
  } catch (err) {
    console.error('Failed to approve user:', err)
  }
}

async function handleReject(userId) {
  try {
    await api.patch(`/api/users/${userId}/suspend`)
    await refreshUsers()
  } catch (err) {
    console.error('Failed to reject user:', err)
  }
}

onMounted(refreshUsers)
</script>
