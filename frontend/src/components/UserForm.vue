<template>
  <form @submit.prevent="submit">
    <input v-model="userId" placeholder="Введите user ID" />
    <button type="submit">Войти</button>
  </form>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import api from "@/api";

const userId = ref('')
const router = useRouter()

async function submit() {
  await api.post('/users', {
    user_id: userId.value
  })
  localStorage.setItem('userId', userId.value)
  await router.push('/unpassed')
}
</script>