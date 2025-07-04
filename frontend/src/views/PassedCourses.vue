<template>
  <div>
    <h2>Пройденные курсы</h2>
    <CourseList :courses="courses">
      <template #default="{ course }">
        <button @click="removeCourse(course.id)">Удалить</button>
      </template>
    </CourseList>
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
  const res = await api.get(`/courses/passed/${userId}`)
  courses.value = res.data.passed_courses
})

async function removeCourse(courseId: number) {
  await api.delete(`/user_courses/${userId}/${courseId}`)
  courses.value = courses.value.filter(c => c.id !== courseId)
}

function logout() {
  localStorage.removeItem('userId')
  router.push('/')
}
</script>