import request from './request'

export const login = (username, password) => {
  return request.post('/auth/login', { username, password })
}

export const getMe = () => {
  return request.get('/auth/me')
}

export const logout = () => {
  return request.post('/auth/logout')
}
