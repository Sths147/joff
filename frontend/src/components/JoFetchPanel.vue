<script setup lang="ts">
defineProps<{ fetching: boolean; disabled: boolean }>()
const emit = defineEmits<{ fetch: [] }>()
</script>

<template>
  <section>
    <button :disabled="disabled" @click="emit('fetch')">
      {{ fetching ? 'Fetching…' : 'Get latest JO' }}
    </button>
  </section>
</template>
