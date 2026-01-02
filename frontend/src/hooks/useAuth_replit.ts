'use client'

import { create } from 'zustand'
import { persist } from 'zustand/middleware'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface User {
  id: string
  email: string
  full_name: string
  role: string
  coffee_credits: number
}

interface AuthState {
  user: User | null
  token: string | null
  isLoading: boolean
  error: string | null
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, full_name: string, role: string) => Promise<void>
  logout: () => void
  fetchUser: () => Promise<void>
}

export const useAuth = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isLoading: false,
      error: null,

      register: async (email: string, password: string, full_name: string, role: string) => {
        set({ isLoading: true, error: null })
        console.log('🚀 Starting registration...')
        console.log('📧 Email:', email)
        console.log('👤 Name:', full_name)
        console.log('🎭 Role:', role)
        
        try {
          // Step 1: Register
          console.log('📤 Sending registration request...')
          const registerResponse = await fetch(`${API_URL}/api/v1/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password, full_name, role })
          })

          console.log('📥 Response status:', registerResponse.status)
          
          if (!registerResponse.ok) {
            const errorData = await registerResponse.json()
            console.error('❌ Registration failed:', errorData)
            throw new Error(errorData.detail || 'Registration failed')
          }

          const { access_token } = await registerResponse.json()
          console.log('✅ Registration successful, token received')

          // Step 2: Fetch user data
          console.log('👤 Fetching user data...')
          const userResponse = await fetch(`${API_URL}/api/v1/auth/me`, {
            headers: {
              'Authorization': `Bearer ${access_token}`
            }
          })

          if (!userResponse.ok) {
            console.error('❌ Failed to fetch user data')
            throw new Error('Failed to fetch user data')
          }

          const userData = await userResponse.json()
          console.log('✅ User data received:', userData)

          set({ 
            token: access_token,
            user: userData,
            isLoading: false,
            error: null
          })

          console.log('✅ Registration complete!')

        } catch (error: any) {
          console.error('❌ Registration error:', error)
          set({ 
            isLoading: false, 
            error: error.message || 'Registration failed'
          })
          throw error
        }
      },

      login: async (email: string, password: string) => {
        set({ isLoading: true, error: null })
        console.log('🔐 Starting login...')
        console.log('📧 Email:', email)
        
        try {
          // Step 1: Login
          console.log('📤 Sending login request...')
          const loginResponse = await fetch(`${API_URL}/api/v1/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
          })

          console.log('📥 Response status:', loginResponse.status)

          if (!loginResponse.ok) {
            const errorData = await loginResponse.json()
            console.error('❌ Login failed:', errorData)
            throw new Error(errorData.detail || 'Login failed')
          }

          const { access_token } = await loginResponse.json()
          console.log('✅ Login successful, token received')

          // Step 2: Fetch user data
          console.log('👤 Fetching user data...')
          const userResponse = await fetch(`${API_URL}/api/v1/auth/me`, {
            headers: {
              'Authorization': `Bearer ${access_token}`
            }
          })

          if (!userResponse.ok) {
            console.error('❌ Failed to fetch user data')
            throw new Error('Failed to fetch user data')
          }

          const userData = await userResponse.json()
          console.log('✅ User data received:', userData)

          set({ 
            token: access_token,
            user: userData,
            isLoading: false,
            error: null
          })

          console.log('✅ Login complete!')

        } catch (error: any) {
          console.error('❌ Login error:', error)
          set({ 
            isLoading: false, 
            error: error.message || 'Login failed'
          })
          throw error
        }
      },

      logout: () => {
        console.log('👋 Logging out...')
        set({ user: null, token: null, error: null })
      },

      fetchUser: async () => {
        const { token } = get()
        if (!token) {
          console.log('ℹ️  No token, skipping user fetch')
          return
        }

        console.log('👤 Fetching current user...')
        set({ isLoading: true })

        try {
          const response = await fetch(`${API_URL}/api/v1/auth/me`, {
            headers: {
              'Authorization': `Bearer ${token}`
            }
          })

          if (!response.ok) {
            console.error('❌ Failed to fetch user, logging out')
            set({ user: null, token: null, isLoading: false })
            return
          }

          const userData = await response.json()
          console.log('✅ User data refreshed:', userData)
          set({ user: userData, isLoading: false })

        } catch (error) {
          console.error('❌ Error fetching user:', error)
          set({ user: null, token: null, isLoading: false })
        }
      }
    }),
    {
      name: 'librework-auth',
      partialize: (state) => ({
        token: state.token,
        user: state.user
      })
    }
  )
)

