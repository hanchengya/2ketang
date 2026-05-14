import { defineStore } from 'pinia'
import { ref } from 'vue'
import { login as loginApi, getMe } from '@/api/auth'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || '')
  const userInfo = ref(null)

  const login = async (username, password) => {
    try {
      const data = await loginApi(username, password)
      token.value = data.access_token
      localStorage.setItem('token', data.access_token)

      // 获取用户信息
      await fetchUserInfo()

      return true
    } catch (error) {
      console.error('Login failed:', error)
      return false
    }
  }

  const logout = () => {
    token.value = ''
    userInfo.value = null
    localStorage.removeItem('token')
  }

  const fetchUserInfo = async () => {
    try {
      const data = await getMe()
      userInfo.value = data
    } catch (error) {
      console.error('Fetch user info failed:', error)
      logout()
    }
  }

  return {
    token,
    userInfo,
    login,
    logout,
    fetchUserInfo
  }
})
