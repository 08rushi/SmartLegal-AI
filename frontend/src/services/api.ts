import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export const apiClient = axios.create({
  baseURL: `${BASE_URL}/api/v1`,
  timeout: 60000,
  headers: {
    'Accept': 'application/json',
  },
})

// TEMPORARILY DISABLED - add back after auth is built
// apiClient.interceptors.request.use((config) => {
//   const token = localStorage.getItem('sl_token')
//   if (token) {
//     config.headers.Authorization = `Bearer ${token}`
//   }
//   return config
// })

// TEMPORARILY DISABLED - redirecting to login on 401
// apiClient.interceptors.response.use(
//   (response) => response,
//   (error) => {
//     if (error.response?.status === 401) {
//       localStorage.removeItem('sl_token')
//       window.location.href = '/login'
//     }
//     return Promise.reject(error)
//   }
// )