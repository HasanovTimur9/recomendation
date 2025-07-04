<template>
  <div class="border p-4 rounded mb-3 shadow-sm bg-white">
    <h3 class="text-lg font-bold">{{ course.title }}</h3>
    <p class="text-sm text-gray-700 mb-1">ID: {{ course.id || course.course_id }}</p>

    <div class="flex flex-wrap gap-2 my-2">
      <span v-for="tag in course.tags" :key="tag" class="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full">{{ tag }}</span>
    </div>

    <div v-if="course.predicted_score">
      <p class="text-sm">Ожидаемая оценка: {{ course.predicted_score.toFixed(2) }}</p>
    </div>

    <div v-if="completed">
      <p class="text-sm text-green-600">Пройден с оценкой: {{ course.score }}</p>
    </div>
  </div>
</template>

<script setup>
defineProps({
  course: Object,
  completed: Boolean
})
</script>
