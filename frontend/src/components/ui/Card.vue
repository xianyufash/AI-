<script setup>
import { cn } from '../../lib/utils'

const props = defineProps({
  class: String
})
</script>

<template>
  <div
    :class="cn('rounded-lg border border-gray-200 bg-white', props.class)"
    v-bind="$attrs"
  >
    <slot />
  </div>
</template>
