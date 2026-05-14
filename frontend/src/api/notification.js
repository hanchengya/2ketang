import request from './request'

export const getNotifications = (params) => {
  return request.get('/notifications/', { params })
}

export const getEmailLogs = (params) => {
  return request.get('/notifications/email-logs', { params })
}

export const getNotificationStats = () => {
  return request.get('/notifications/stats/summary')
}
