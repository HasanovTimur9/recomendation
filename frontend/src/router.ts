import { createRouter, createWebHistory } from 'vue-router'
import HomeView from './views/HomeView.vue'
import UnpassedCourses from './views/UnpassedCourses.vue'
import PassedCourses from './views/PassedCourses.vue'

const routes = [
  { path: '/', component: HomeView },
  { path: '/unpassed', component: UnpassedCourses },
  { path: '/passed', component: PassedCourses },
]

export default createRouter({
  history: createWebHistory(),
  routes
})