<template>
  <div v-for="course in courses" :key="course.id" class="course">
    <p><strong>{{ course.name }}</strong></p>
    <slot :course="course" />
  </div>
</template>

<script setup lang="ts">
defineProps<{
  courses: any[]
}>()
</script>