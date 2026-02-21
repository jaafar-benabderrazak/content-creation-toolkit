import axios from 'axios'
import { stackClientApp } from '@/stack/client'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export const api = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
})

api.interceptors.request.use(
  async (config) => {
    const user = await stackClientApp.getUser()
    if (user) {
      const { accessToken } = await user.getAuthJson()
      if (accessToken) {
        config.headers['x-stack-access-token'] = accessToken
      }
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

export default api
