<template>
  <iframe
    ref="iframeRef"
    :srcdoc="htmlContent"
    :sandbox="sandboxAttrs"
    class="w-full h-full border-0"
    @load="$emit('loaded')"
  ></iframe>
</template>

<script setup>
import { ref } from 'vue'
import { getSandboxAttributes } from '../../utils/htmlSandbox'

defineProps({
  htmlContent: {
    type: String,
    required: true,
  },
})

defineEmits(['loaded'])

const iframeRef = ref(null)
const sandboxAttrs = getSandboxAttributes()
</script>
