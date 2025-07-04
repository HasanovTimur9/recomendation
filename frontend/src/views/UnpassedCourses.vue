<template>
  <div>
    <h2>Непройденные курсы</h2>
    <CourseList :courses="courses">
      <template #default="{ course }">
        <button @click="markAsPassed(course.id)">Пройти курс</button>
      </template>
    </CourseList>
    <button @click="retrain">Переобучить модель</button>
    <button @click="logout">Выйти</button>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import api from '../api'
import CourseList from '../components/CourseList.vue'
import { useRouter } from 'vue-router'

const courses = ref([])
const router = useRouter()
const userId = localStorage.getItem('userId') || ''

onMounted(async () => {
  const res = await api.get(`/courses/unpassed/${userId}`)
  courses.value = res.data.unpassed_courses
})

async function markAsPassed(courseId: number) {
  await api.post('/user_courses', {
    user_id: userId,
    course_id: courseId,
    score: 5
  })
  courses.value = courses.value.filter(c => c.id !== courseId)
}

async function retrain() {
  try {
    await api.post('/retrain_model')
    alert('Модель успешно переобучена')
  } catch {
    alert('Ошибка при переобучении модели')
  }
}

function logout() {
  localStorage.removeItem('userId')
  router.push('/')
}
</script>