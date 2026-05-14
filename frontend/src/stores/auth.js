import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/utils/api'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const user = ref(null)

  const isAuthenticated = computed(() => !!token.value)

  // 登录
  const login = async (username, password) => {
    try {
      const response = await api.post('/auth/login', {
        username,
        password
      })

      token.value = response.access_token
      localStorage.setItem('token', token.value)

      // 获取用户信息
      await getUserInfo()

      return { success: true }
    } catch (error) {
      return {
        success: false,
        message: error.response?.data?.detail || '登录失败'
      }
    }
  }

  // 获取用户信息
  const getUserInfo = async () => {
    try {
      const response = await api.get('/auth/me')
      user.value = response.data
    } catch (error) {
      console.error('获取用户信息失败:', error)
    }
  }

  // 登出
  const logout = () => {
    token.value = ''
    user.value = null
    localStorage.removeItem('token')
  }

  // 初始化时获取用户信息
  if (token.value) {
    getUserInfo()
  }

  return {
    token,
    user,
    isAuthenticated,
    username: computed(() => user.value?.username || ''),
    login,
    logout,
    getUserInfo
  }
})