<template>
  <div class="max-w-3xl mx-auto p-4">
    <h1 class="text-2xl font-bold mb-6 text-center">Рекомендации курсов</h1>

    <UserForm @user-loaded="onUserLoaded" />

    <div v-if="userId">
      <div class="mb-6">
        <h2 class="text-xl font-semibold mb-2">Рекомендованные курсы</h2>
        <div v-if="recommendations.length">
          <CourseCard v-for="c in recommendations" :key="c.id" :course="c" />
        </div>
        <p v-else class="text-gray-600">Нет рекомендаций</p>
      </div>

      <div class="mb-6">
        <h2 class="text-xl font-semibold mb-2">Пройденные курсы</h2>
        <div v-if="passed.length">
          <CourseCard v-for="c in passed" :key="c.id" :course="c" completed />
        </div>
        <p v-else class="text-gray-600">Нет пройденных курсов</p>
      </div>

      <div>
        <h2 class="text-xl font-semibold mb-2">Непройденные курсы</h2>
        <div v-if="unpassed.length">
          <CourseCard v-for="c in unpassed" :key="c.course_id" :course="c" />
        </div>
        <p v-else class="text-gray-600">Нет непройденных курсов</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import axios from 'axios'
import UserForm from './components/UserForm.vue'
import CourseCard from './components/CourseCard.vue'

const userId = ref('')
const recommendations = ref([])
const passed = ref([])
const unpassed = ref([])

async function fetchData() {
  try {
    const [recs, pass, unpass] = await Promise.all([
      axios.get(`/api/recommendations/${userId.value}`),
      axios.get(`/api/courses/passed/${userId.value}`),
      axios.get(`/api/courses/unpassed/${userId.value}`),
    ])
    recommendations.value = recs.data.recommendations
    passed.value = pass.data.passed_courses
    unpassed.value = unpass.data.unpassed_courses
  } catch (err) {
    console.error(err)
  }
}

function onUserLoaded(id) {
  userId.value = id
  fetchData()
}
</script>

<style scoped>
body {
  background-color: #f9f9f9;
}
</style>
