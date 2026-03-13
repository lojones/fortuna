<template>
  <div class="border-t border-cp-border p-4 bg-cp-black">
    <form @submit.prevent="handleSend" class="flex gap-2 items-end">
      <textarea
        ref="textareaRef"
        v-model="message"
        :disabled="disabled"
        rows="1"
        class="flex-1 px-4 py-2 border border-cp-border rounded-lg bg-cp-surface focus:ring-2 focus:ring-cp-yellow/50 focus:border-cp-yellow/50 outline-none disabled:opacity-40 disabled:cursor-not-allowed resize-none leading-6 overflow-y-auto"
        style="max-height: 9rem;"
        placeholder="Describe your visualization..."
        @keydown.enter.exact.prevent="handleSend"
        @keydown.enter.shift.exact="() => {}"
        @input="autoResize"
      ></textarea>
      <button
        type="submit"
        :disabled="disabled || !message.trim()"
        class="bg-cp-yellow text-cp-black font-bold px-4 py-2 rounded-lg hover:bg-cp-yellow/85 transition-colors disabled:opacity-40 disabled:cursor-not-allowed self-end"
      >
        <span class="pi pi-send"></span>
      </button>
    </form>
  </div>
</template>

<script setup>
import { ref, nextTick, watch } from 'vue'

const props = defineProps({
  disabled: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['send'])

const message = ref('')
const textareaRef = ref(null)

// line-height is 1.5rem (24px), 6 lines = 144px = 9rem
const MAX_HEIGHT = 144

function autoResize() {
  const el = textareaRef.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = Math.min(el.scrollHeight, MAX_HEIGHT) + 'px'
}

function handleSend() {
  if (message.value.trim() && !props.disabled) {
    emit('send', message.value.trim())
    message.value = ''
    nextTick(() => {
      if (textareaRef.value) {
        textareaRef.value.style.height = 'auto'
      }
    })
  }
}

// Reset height when message is cleared externally
watch(message, (val) => {
  if (!val) {
    nextTick(() => {
      if (textareaRef.value) textareaRef.value.style.height = 'auto'
    })
  }
})
</script>
