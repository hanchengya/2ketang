import request from './request'

export const getStudents = (params) => {
  return request.get('/students/', { params })
}

export const getStudent = (code) => {
  return request.get(`/students/${code}`)
}

export const updateStudentEmail = (code, email) => {
  return request.put(`/students/${code}/email`, { email })
}

export const getStudentStats = () => {
  return request.get('/students/stats/summary')
}
