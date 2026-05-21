import axios from 'axios'

// Dev: /api → Vite proxies to http://localhost:5000 (backend must be running)
// Prod: set VITE_API_URL in .env to your deployed API URL
const API_URL =
  import.meta.env.VITE_API_URL ||
  (import.meta.env.DEV ? '/api' : 'http://localhost:5000/api')

const api = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 60000,
})

// Attach JWT token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Handle 401 - redirect to login
api.interceptors.response.use(
  (res) => res,
  async (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('user')
      if (!window.location.pathname.includes('/login')) {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

export default api

// Auth
export const authAPI = {
  register: (data) => api.post('/auth/register', data),
  login: (data) => api.post('/auth/login', data),
  me: () => api.get('/auth/me'),
  updateProfile: (data) => api.put('/auth/profile', data),
  changePassword: (data) => api.put('/auth/change-password', data),
}

// Videos
export const videoAPI = {
  process: (data) => api.post('/videos/process', data),
  list: (params) => api.get('/videos', { params }),
  get: (id) => api.get(`/videos/${id}`),
  getContent: (id) => api.get(`/videos/${id}/content`),
  delete: (id) => api.delete(`/videos/${id}`),
  search: (q) => api.get('/videos/search', { params: { q } }),
  updateProgress: (id, data) => api.post(`/videos/${id}/progress`, data),
}

// Chatbot
export const chatAPI = {
  send: (videoId, message) => api.post(`/chatbot/${videoId}`, { message }),
  history: (videoId) => api.get(`/chatbot/${videoId}/history`),
  clear: (videoId) => api.delete(`/chatbot/${videoId}/history`),
}

// Dashboard
export const dashboardAPI = {
  stats: () => api.get('/dashboard/stats'),
  notifications: () => api.get('/dashboard/notifications'),
  markRead: (id) => api.put(`/dashboard/notifications/${id}/read`),
}

// Download
export const downloadAPI = {
  notes: (id) => api.get(`/download/${id}/notes`, { responseType: 'blob' }),
  mcqs: (id) => api.get(`/download/${id}/mcqs`, { responseType: 'blob' }),
  summary: (id) => api.get(`/download/${id}/summary`, { responseType: 'blob' }),
}

// Translate
export const translateAPI = {
  translate: (data) => api.post('/translate', data),
}

// Admin
export const adminAPI = {
  users: (page) => api.get('/admin/users', { params: { page } }),
  deleteUser: (id) => api.delete(`/admin/users/${id}`),
  toggleUser: (id) => api.put(`/admin/users/${id}/toggle`),
  videos: (page) => api.get('/admin/videos', { params: { page } }),
  deleteVideo: (id) => api.delete(`/admin/videos/${id}`),
  stats: () => api.get('/admin/stats'),
  logs: () => api.get('/admin/logs'),
}

// Bookmarks
export const bookmarkAPI = {
  list: () => api.get('/bookmarks'),
  add: (data) => api.post('/bookmarks', data),
  remove: (id) => api.delete(`/bookmarks/${id}`),
}

export const downloadBlob = (blob, filename) => {
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  window.URL.revokeObjectURL(url)
}
