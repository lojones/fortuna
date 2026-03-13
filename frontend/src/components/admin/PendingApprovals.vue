<template>
  <div class="bg-cp-surface rounded-xl border border-cp-border p-6">
    <div class="flex items-center gap-2 mb-4">
      <h3 class="text-lg font-semibold text-cp-text">Pending Approvals</h3>
      <span
        v-if="users.length > 0"
        class="bg-cp-yellow/10 text-cp-yellow border border-cp-yellow/30 text-xs font-bold px-2 py-0.5 rounded-full"
      >
        {{ users.length }}
      </span>
    </div>

    <div v-if="users.length === 0" class="text-cp-muted text-sm">
      No pending approvals
    </div>

    <div v-else class="space-y-3">
      <div
        v-for="user in users"
        :key="user.id"
        class="flex items-center justify-between p-3 bg-cp-yellow/5 rounded-lg border border-cp-yellow/20"
      >
        <div>
          <span class="font-medium text-cp-text">{{ user.username }}</span>
          <span class="text-cp-muted text-sm ml-2">{{ user.email }}</span>
        </div>
        <div class="flex gap-2">
          <button
            @click="$emit('approve', user.id)"
            class="text-xs px-3 py-1 bg-cp-green text-cp-black font-bold rounded hover:opacity-85 transition-colors"
          >
            Approve
          </button>
          <button
            @click="$emit('reject', user.id)"
            class="text-xs px-3 py-1 bg-cp-red/10 text-cp-red border border-cp-red/30 rounded hover:bg-cp-red/20 transition-colors"
          >
            Reject
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  users: {
    type: Array,
    required: true,
  },
})

defineEmits(['approve', 'reject'])
</script>
