import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8000',
})

axios.defaults.headers.common['Access-Control-Allow-Origin'] = '*';
axios.defaults.headers.get['Accepts'] = 'application/json'
axios.defaults.headers.post['Content-Type'] = 'application/json; charset=utf-8'

export default api