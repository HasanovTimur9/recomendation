<template>
  <form @submit.prevent="submitUser" class="mb-6 p-4 border rounded bg-white shadow">
    <label class="block mb-2 font-semibold">ID пользователя</label>
    <input v-model="userId" class="border p-2 rounded w-full mb-4" required />

    <div class="mb-4">
      <label class="block mb-2 font-semibold">Интересы (теги через запятую)</label>
      <input v-model="interestsInput" class="border p-2 rounded w-full" />
    </div>

    <button class="bg-blue-500 text-white px-4 py-2 rounded" type="submit">Загрузить</button>

    <div v-if="interests.length" class="mt-4">
      <h3 class="font-semibold mb-2">Интересы пользователя:</h3>
      <div class="flex flex-wrap gap-2">
        <span v-for="tag in interests" :key="tag" class="bg-green-100 text-green-800 text-xs px-2 py-1 rounded-full">
          {{ tag }}
        </span>
      </div>
    </div>
  </form>
</template>

<script setup>
import { ref, emit } from 'vue'
import axios from 'axios'

const userId = ref('')
const interestsInput = ref('')
const interests = ref([])

const emitUserLoaded = defineEmits(['user-loaded'])

async function submitUser() {
  try {
    const { data } = await axios.get(`/api/users/${userId.value}`)
    interests.value = data.interests
    emitUserLoaded(userId.value)
  } catch (err) {
    // если не найден — пробуем создать
    try {
      const interestsList = interestsInput.value
          .split(',')
          .map(t => t.trim())
          .filter(Boolean)
      const { data } = await axios.post('/api/users', {
        user_id: userId.value,
        interests: interestsList
      })
      interests.value = data.user.interests
      emitUserLoaded(userId.value)
    } catch (e) {
      console.error(e)
      alert(e.response?.data?.detail || 'Ошибка')
    }
  }
}
</script>

<style scoped></style>
