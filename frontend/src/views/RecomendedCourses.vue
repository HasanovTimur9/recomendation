<template>
  <div>
    <h2>Непройденные курсы</h2>
    <button @click="router.push('/unpassed')">Непройденные курсы</button>
    <button @click="router.push('/passed')">Пройденные курсы</button>
    <button @click="logout">Выйти</button>
    <CourseList :courses="courses">
      <template #default="{ course }">
        <button @click="markAsPassed(course)">Пройти курс</button>
      </template>
    </CourseList>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import api from '../api'
import CourseList from '../components/CourseList.vue'
import { useRouter } from 'vue-router'

interface Course {
  id: number
  name: string
  difficulty: string
  tags: string[]
}

const courses = ref<Course[]>([])
const router = useRouter()
const userId = localStorage.getItem('userId') || ''

onMounted(async () => {
  const res = await api.get(`/recommendations/${userId}`)
  courses.value = res.data.recommendations
})

async function markAsPassed(course: Course) {
  const raw = prompt(`Введите вашу оценку, по итогу прохождения курса "${course.name}" (от 0 до 5):`)
  const score = Number(raw)
  const raw2 = prompt(`Введите вашу оценку курсу "${course.name}", на сколько вам понравилось и было полезно (от 0 до 5):`)
  const performance = Number(raw2)

  let result = await api.post('/user_courses', {
    user_id: userId,
    course_id: course.id,
    score: score,
    performance: performance
  })
  courses.value = courses.value.filter(c => c.id !== course.id)
  alert(result.data.message)
}

function logout() {
  localStorage.removeItem('userId')
  router.push('/')
}
</script>