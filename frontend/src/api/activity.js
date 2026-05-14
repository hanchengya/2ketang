import request from './request'

export const getActivities = (params) => {
  return request.get('/activities/', { params })
}

export const getActivityDetail = (actId) => {
  return request.get(`/activities/${actId}`)
}

export const getActivityStats = () => {
  return request.get('/activities/stats/summary')
}

export const getActivityParticipants = (actId, params = {}) => {
  return request.get(`/activities/${actId}/participants`, { params })
}
