import request from './request'

/**
 * 获取爬虫状态
 */
export function getCrawlerStatus() {
  return request({
    url: '/crawler/status',
    method: 'get'
  })
}

/**
 * 启动爬取活动列表
 */
export function crawlActivities() {
  return request({
    url: '/crawler/crawl-activities',
    method: 'post',
    data: { save_to_db: true }
  })
}

/**
 * 启动爬取活动详情
 */
export function crawlDetails(actIds) {
  return request({
    url: '/crawler/crawl-details',
    method: 'post',
    data: {
      act_ids: actIds,
      save_to_db: true
    }
  })
}

/**
 * 启动爬取学生信息
 */
export function crawlStudents() {
  return request({
    url: '/crawler/crawl-students',
    method: 'post'
  })
}

/**
 * 启动爬取参与者信息
 */
export function crawlParticipants(actIds) {
  return request({
    url: '/crawler/crawl-participants',
    method: 'post',
    data: {
      act_ids: actIds,
      save_to_db: true
    }
  })
}

/**
 * 停止任务
 */
export function stopTask(taskId) {
  return request({
    url: `/crawler/stop/${taskId}`,
    method: 'post'
  })
}

/**
 * 获取所有任务列表
 */
export function getTasks(params) {
  return request({
    url: '/crawler/tasks',
    method: 'get',
    params
  })
}

/**
 * 获取任务详情
 */
export function getTaskInfo(taskId) {
  return request({
    url: `/crawler/tasks/${taskId}`,
    method: 'get'
  })
}

/**
 * 获取任务日志
 */
export function getTaskLogs(taskId) {
  return request({
    url: `/crawler/logs/${taskId}`,
    method: 'get'
  })
}

/**
 * 启动定时任务
 */
export function startSchedule(data) {
  return request({
    url: '/crawler/schedule/start',
    method: 'post',
    data
  })
}

/**
 * 停止定时任务
 */
export function stopSchedule(scheduleId) {
  return request({
    url: `/crawler/schedule/stop/${scheduleId}`,
    method: 'post'
  })
}

/**
 * 获取定时任务状态
 */
export function getScheduleStatus() {
  return request({
    url: '/crawler/schedule/status',
    method: 'get'
  })
}
