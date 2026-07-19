<script setup>
import { cn } from '../../lib/utils'

const props = defineProps({
  variant: {
    type: String,
    default: 'default'
  },
  size: {
    type: String,
    default: 'default'
  },
  type: {
    type: String,
    default: 'button'
  },
  class: String
})

const buttonVariants = {
  default: 'bg-gray-900 text-gray-50 hover:bg-gray-800',
  outline: 'border border-gray-300 bg-white hover:bg-gray-50 hover:border-gray-400',
  ghost: 'hover:bg-gray-100',
  destructive: 'bg-gray-900 text-white hover:bg-gray-800'
}

const sizeClasses = {
  default: 'h-10 px-4 py-2',
  sm: 'h-8 px-3 text-xs',
  lg: 'h-11 px-6',
  icon: 'h-9 w-9'
}
</script>

<template>
  <button
    :type="props.type"
    :class="cn(
      'inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md border border-transparent text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gray-950 disabled:pointer-events-none disabled:opacity-50',
      buttonVariants[variant || 'default'],
      sizeClasses[size || 'default'],
      props.class
    )"
    v-bind="$attrs"
  >
    <slot />
  </button>
</template>
