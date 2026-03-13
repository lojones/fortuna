<template>
  <div class="overflow-x-auto">
    <table class="w-full text-sm">
      <thead>
        <tr class="border-b border-cp-border">
          <th class="text-left py-3 px-2 font-medium text-cp-muted">Username</th>
          <th class="text-left py-3 px-2 font-medium text-cp-muted">Email</th>
          <th class="text-left py-3 px-2 font-medium text-cp-muted">Role</th>
          <th class="text-left py-3 px-2 font-medium text-cp-muted">Status</th>
          <th class="text-left py-3 px-2 font-medium text-cp-muted">Created</th>
          <th class="text-right py-3 px-2 font-medium text-cp-muted">Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-if="users.length === 0">
          <td colspan="6" class="py-8 text-center text-cp-muted">No users found</td>
        </tr>
        <tr v-for="user in users" :key="user.id" class="border-b border-cp-border/50 hover:bg-cp-surface2">
          <td class="py-3 px-2 font-medium text-cp-text">{{ user.username }}</td>
          <td class="py-3 px-2 text-cp-muted">{{ user.email }}</td>
          <td class="py-3 px-2">
            <span
              class="text-xs px-2 py-0.5 rounded-full"
              :class="{
                'bg-cp-cyan/10 text-cp-cyan border border-cp-cyan/30': user.role === 'admin',
                'bg-cp-surface2 text-cp-muted': user.role === 'user',
              }"
            >
              {{ user.role }}
            </span>
          </td>
          <td class="py-3 px-2">
            <span
              class="text-xs px-2 py-0.5 rounded-full"
              :class="{
                'bg-cp-yellow/10 text-cp-yellow border border-cp-yellow/30': user.status === 'pending',
                'bg-cp-green/10 text-cp-green border border-cp-green/30': user.status === 'active',
                'bg-cp-red/10 text-cp-red border border-cp-red/30': user.status === 'suspended',
              }"
            >
              {{ user.status }}
            </span>
          </td>
          <td class="py-3 px-2 text-cp-muted text-xs">{{ formatDate(user.created_at) }}</td>
          <td class="py-3 px-2 text-right">
            <div class="flex gap-1 justify-end">
              <button
                v-if="user.status === 'pending'"
                @click="approveUser(user.id)"
                class="text-xs px-2 py-1 bg-cp-green/10 text-cp-green border border-cp-green/30 rounded hover:bg-cp-green/20"
              >
                Approve
              </button>
              <button
                v-if="user.status === 'active'"
                @click="suspendUser(user.id)"
                class="text-xs px-2 py-1 bg-cp-yellow/10 text-cp-yellow border border-cp-yellow/30 rounded hover:bg-cp-yellow/20"
              >
                Suspend
              </button>
              <button
                v-if="user.status === 'suspended'"
                @click="approveUser(user.id)"
                class="text-xs px-2 py-1 bg-cp-green/10 text-cp-green border border-cp-green/30 rounded hover:bg-cp-green/20"
              >
                Activate
              </button>
              <button
                v-if="user.role === 'user'"
                @click="toggleRole(user.id, 'admin')"
                class="text-xs px-2 py-1 bg-cp-cyan/10 text-cp-cyan border border-cp-cyan/30 rounded hover:bg-cp-cyan/20"
              >
                Make Admin
              </button>
              <button
                v-if="user.role === 'admin'"
                @click="toggleRole(user.id, 'user')"
                class="text-xs px-2 py-1 bg-cp-surface2 text-cp-muted rounded hover:bg-cp-border"
              >
                Remove Admin
              </button>
              <button
                @click="deleteUser(user.id)"
                class="text-xs px-2 py-1 bg-cp-red/10 text-cp-red border border-cp-red/30 rounded hover:bg-cp-red/20"
              >
                Delete
              </button>
            </div>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import api from '../../services/api'
import { formatDate } from '../../utils/dateFormatter'

const emit = defineEmits(['updated'])

defineProps({
  users: {
    type: Array,
    required: true,
  },
})

async function approveUser(userId) {
  await api.patch(`/api/users/${userId}/approve`)
  emit('updated')
}

async function suspendUser(userId) {
  await api.patch(`/api/users/${userId}/suspend`)
  emit('updated')
}

async function toggleRole(userId, role) {
  await api.patch(`/api/users/${userId}/role`, { role })
  emit('updated')
}

async function deleteUser(userId) {
  if (confirm('Are you sure you want to delete this user?')) {
    await api.delete(`/api/users/${userId}`)
    emit('updated')
  }
}
</script>
