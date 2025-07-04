<template>
  <form @submit.prevent="submit">
    <input v-model="userId" placeholder="Введите user ID" />
    <button type="submit">Войти</button>
  </form>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const userId = ref('')
const router = useRouter()

function submit() {
  localStorage.setItem('userId', userId.value)
  router.push('/unpassed')
}
</script>