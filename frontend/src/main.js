import './assets/index.css'

import { createApp } from 'vue'
import App from './App.vue'
import axios from 'axios'

axios.default.baseURL = 'http://localhost:8000'
axios.default.headers.post['Content-Type'] = 'application/json'

createApp(App).mount('#app')
