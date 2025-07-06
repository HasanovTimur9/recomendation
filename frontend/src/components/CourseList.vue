<template>
  <div class="course-list">
    <div
        class="course-card"
        v-for="course in courses"
        :key="course.id"
    >
      <h3 class="text-lg font-semibold">{{ course.name }}</h3>
      <p class="text-sm text-gray-600">{{ course.description }}</p>
      <p class="text-sm text-gray-600">Сложность: {{ course.difficulty }}</p>
      <p class="text-sm text-gray-600">
        Теги:
        <span v-for="(tag, idx) in course.tags" :key="idx">
          {{ tag }}<span v-if="idx < course.tags.length - 1">, </span>
        </span>
      </p>
      <p v-if="course.performance !== null" class="text-sm text-gray-600">Оценка за курс: {{ course.performance }}</p>

      <div class="mt-2">
        <slot :course="course" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  courses: {
    id: number
    name: string
    description: string
    difficulty: string
    tags: string[]
    performance: number
  }[]
}>()
</script>

<style scoped>
</style>
