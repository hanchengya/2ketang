<template>
  <div class="crawler-management">
    <el-row :gutter="20">
      <!-- 爬虫卡片 -->
      <el-col :span="6" v-for="crawler in crawlers" :key="crawler.type">
        <el-card class="crawler-card" :class="{'running': crawler.running}">
          <div class="crawler-header">
            <div class="crawler-title">
              <el-icon :size="20"><component :is="crawler.icon" /></el-icon>
              <span>{{ crawler.name }}</span>
            </div>
            <el-tag :type="getStatusType(crawler.status)" size="small">
              {{ getStatusText(crawler.status) }}
            </el-tag>
          </div>

          <div class="crawler-description">
            {{ crawler.description }}
          </div>

          <div class="crawler-progress" v-if="crawler.running && crawler.current_count">
            <el-progress
              :percentage="getProgressPercentage(crawler.current_count, crawler.total_count)"
              :color="'#409EFF'"
            />
            <div class="progress-text">
              {{ crawler.current_count }} / {{ crawler.total_count }}
            </div>
          </div>

          <div class="crawler-actions">
            <el-button
              type="primary"
              :loading="crawler.starting"
              :disabled="crawler.running"
              @click="startCrawler(crawler)"
            >
              启动
            </el-button>
            <el-button
              type="danger"
              :disabled="!crawler.running"
              @click="stopCrawler(crawler)"
            >
              停止
            </el-button>
          </div>

          <div class="crawler-info" v-if="crawler.lastRun">
            <div class="info-item">
              <span class="label">最近运行:</span>
              <span class="value">{{ formatTime(crawler.lastRun) }}</span>
            </div>
          </div>

          <!-- 定时任务配置 -->
          <div class="schedule-config" v-if="crawler.canSchedule">
            <el-divider />
            <div class="schedule-header">
              <span>定时爬取</span>
              <el-switch
                v-model="crawler.scheduleEnabled"
                :loading="crawler.scheduleLoading"
                @change="toggleSchedule(crawler)"
              />
            </div>
            <div class="schedule-settings">
              <span style="color: #606266; font-size: 13px;">间隔:</span>
              <el-time-picker
                v-model="crawler.intervalTime"
                :disabled="crawler.scheduleRunning"
                size="small"
                format="HH:mm:ss"
                value-format="HH:mm:ss"
                :clearable="false"
                style="width: 130px"
                @change="(val) => updateIntervalMinutes(crawler, val)"
              />
            </div>
            <div class="schedule-status" v-if="crawler.scheduleRunning" style="margin-top: 8px;">
              <el-tag type="success" size="small">运行中</el-tag>
              <span style="color: #67C23A; font-size: 14px; margin-left: 10px; font-family: 'Courier New', monospace;">
                {{ formatCountdown(crawler.remainingSeconds) }}
              </span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 自动化通知脚本 -->
    <el-card style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <span>自动化通知脚本</span>
        </div>
      </template>
      <el-row :gutter="20">
        <el-col :span="8" v-for="script in scripts" :key="script.type">
          <el-card class="crawler-card" :class="{'running': script.running}">
            <div class="crawler-header">
              <div class="crawler-title">
                <el-icon :size="20"><component :is="script.icon" /></el-icon>
                <span>{{ script.name }}</span>
              </div>
              <el-tag :type="getStatusType(script.status)" size="small">
                {{ getStatusText(script.status) }}
              </el-tag>
            </div>

            <div class="crawler-description">
              {{ script.description }}
            </div>

            <div class="crawler-actions">
              <el-button
                :type="script.buttonType"
                :loading="script.starting"
                :disabled="script.running"
                @click="startScript(script)"
              >
                启动
              </el-button>
              <el-button
                type="danger"
                :disabled="!script.running"
                @click="stopScript(script)"
              >
                停止
              </el-button>
            </div>

            <div class="crawler-info" v-if="script.lastRun">
              <div class="info-item">
                <span class="label">最近运行:</span>
                <span class="value">{{ formatTime(script.lastRun) }}</span>
              </div>
            </div>

            <!-- 定时任务配置 -->
            <div class="schedule-config">
              <el-divider />
              <div class="schedule-header">
                <span>定时爬取</span>
                <el-switch
                  v-model="script.scheduleEnabled"
                  :loading="script.scheduleLoading"
                  @change="toggleScriptSchedule(script)"
                />
              </div>
              <div class="schedule-settings">
                <span style="color: #606266; font-size: 13px;">间隔:</span>
                <el-time-picker
                  v-model="script.intervalTime"
                  :disabled="script.scheduleRunning"
                  size="small"
                  format="HH:mm:ss"
                  value-format="HH:mm:ss"
                  :clearable="false"
                  style="width: 130px"
                  @change="(val) => updateScriptIntervalMinutes(script, val)"
                />
              </div>
              <div class="schedule-status" v-if="script.scheduleRunning" style="margin-top: 8px;">
                <el-tag type="success" size="small">运行中</el-tag>
                <span style="color: #67C23A; font-size: 14px; margin-left: 10px; font-family: 'Courier New', monospace;">
                  {{ formatCountdown(script.remainingSeconds) }}
                </span>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </el-card>

    <!-- 任务列表 -->
    <el-card style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <span>任务历史</span>
          <el-button type="primary" size="small" @click="refreshTasks">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </template>

      <el-table :data="tasks" style="width: 100%">
        <el-table-column prop="id" label="ID" width="70">
          <template #default="{ row }">
            <span>{{ row.id }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="task_type" label="任务类型" width="120">
          <template #default="{ row }">
            <el-tag :type="getTaskTypeColor(row.task_type)" size="small">{{ getTaskTypeName(row.task_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="progress" label="进度" width="150">
          <template #default="{ row }">
            <span v-if="row.total_count">
              {{ row.current_count }} / {{ row.total_count }}
            </span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="started_at" label="开始时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.started_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="finished_at" label="完成时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.finished_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" fixed="right" width="150">
          <template #default="{ row }">
            <el-button type="primary" size="small" link @click="viewLogs(row)">
              查看日志
            </el-button>
            <el-button
              v-if="row.status === 'running'"
              type="danger"
              size="small"
              link
              @click="stopTaskById(row.task_id)"
            >
              停止
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50]"
        :total="totalTasks"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="loadTasks"
        @current-change="loadTasks"
        style="margin-top: 20px; justify-content: flex-end;"
      />
    </el-card>

    <!-- 活动选择对话框 -->
    <el-dialog
      v-model="activityDialogVisible"
      title="选择活动"
      width="70%"
      :close-on-click-modal="false"
    >
      <div class="activity-filter" style="margin-bottom: 15px; display: flex; gap: 10px; flex-wrap: wrap;">
        <el-input
          v-model="activitySearchKeyword"
          placeholder="搜索活动名称"
          clearable
          style="width: 200px;"
          @keyup.enter="loadActivities"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-select
          v-model="activityStatusFilter"
          placeholder="活动状态"
          clearable
          style="width: 120px;"
          @change="loadActivities"
        >
          <!-- 平台实际 9 个状态 -->
          <el-option label="报名中" value="报名中" />
          <el-option label="待开始" value="待开始" />
          <el-option label="进行中" value="进行中" />
          <el-option label="待完结" value="待完结" />
          <el-option label="已完结" value="已完结" />
          <el-option label="审核中" value="审核中" />
          <el-option label="被驳回" value="被驳回" />
          <el-option label="完结审核中" value="完结审核中" />
          <el-option label="完结被驳回" value="完结被驳回" />
        </el-select>
        <el-button type="primary" @click="loadActivities">搜索</el-button>
        <el-button @click="resetActivityFilter">重置</el-button>
        <el-button
          type="success"
          plain
          :loading="selectAllLoading"
          :disabled="activityTotal === 0"
          @click="selectAllMatchingActivities"
        >
          选择全部 {{ activityTotal }} 个
        </el-button>
        <el-button
          :disabled="selectedActivities.length === 0"
          @click="clearActivitySelection"
        >
          清空已选
        </el-button>
      </div>
      <el-table
        ref="activityTableRef"
        :data="activityList"
        row-key="act_id"
        style="width: 100%"
        max-height="400"
        @selection-change="handleActivitySelectionChange"
        v-loading="activityLoading"
      >
        <el-table-column type="selection" width="55" :reserve-selection="true" />
        <el-table-column prop="act_id" label="ID" width="80" />
        <el-table-column prop="act_name" label="活动名称" min-width="200" show-overflow-tooltip />
        <el-table-column prop="org_name" label="主办方" width="180" show-overflow-tooltip />
        <el-table-column prop="finish_status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getActivityTagType(row.finish_status)" size="small">{{ row.finish_status || '未知' }}</el-tag>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination
        v-model:current-page="activityPage"
        v-model:page-size="activityPageSize"
        :total="activityTotal"
        layout="total, prev, pager, next"
        @current-change="loadActivities"
        style="margin-top: 15px; justify-content: flex-end;"
      />
      <template #footer>
        <el-button @click="activityDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmActivitySelection" :disabled="selectedActivities.length === 0">
          确定 (已选 {{ selectedActivities.length }} 个)
        </el-button>
      </template>
    </el-dialog>

    <!-- 日志查看对话框 -->
    <el-dialog
      v-model="logDialogVisible"
      title="任务日志"
      width="70%"
      :close-on-click-modal="false"
      @close="stopLogAutoRefresh"
    >
      <div class="log-header">
        <el-tag :type="getStatusType(currentTask?.status)" size="small">
          {{ getStatusText(currentTask?.status) }}
        </el-tag>
        <div style="display: flex; align-items: center; gap: 15px;">
          <el-checkbox v-model="logAutoRefresh" @change="toggleLogAutoRefresh">
            自动刷新
          </el-checkbox>
          <el-button size="small" @click="refreshLogs">
            <el-icon><Refresh /></el-icon>
            刷新日志
          </el-button>
        </div>
      </div>
      <div class="log-content" ref="logContentRef">
        <pre>{{ logContent }}</pre>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, reactive, markRaw, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Calendar,
  User,
  List,
  DataAnalysis,
  VideoPlay,
  VideoPause,
  Refresh,
  Document,
  Search,
  Bell,
  Clock
} from '@element-plus/icons-vue'
import {
  crawlActivities,
  crawlDetails,
  crawlStudents,
  crawlParticipants,
  stopTask,
  getTasks,
  getTaskLogs,
  startSchedule,
  stopSchedule,
  getScheduleStatus
} from '@/api/crawler'
import { getActivities } from '@/api/activity'

// 爬虫配置
const crawlers = reactive([
  {
    type: 'activities',
    name: '活动列表',
    description: '爬取报名中、进行中的活动列表',
    icon: markRaw(Calendar),
    running: false,
    starting: false,
    status: 'idle',
    task_id: null,
    current_count: 0,
    total_count: 0,
    lastRun: null,
    canSchedule: true,
    scheduleEnabled: false,
    scheduleRunning: false,
    scheduleLoading: false,
    intervalMinutes: 60,
    intervalTime: '01:00:00',
    remainingSeconds: 0
  },
  {
    type: 'details',
    name: '活动详情',
    description: '爬取活动的详细信息（需先选择活动）',
    icon: markRaw(Document),
    running: false,
    starting: false,
    status: 'idle',
    task_id: null,
    current_count: 0,
    total_count: 0,
    lastRun: null
  },
  {
    type: 'students',
    name: '学生信息',
    description: '爬取学生列表信息，支持翻页',
    icon: markRaw(User),
    running: false,
    starting: false,
    status: 'idle',
    task_id: null,
    current_count: 0,
    total_count: 0,
    lastRun: null,
    canSchedule: true,
    scheduleEnabled: false,
    scheduleRunning: false,
    scheduleLoading: false,
    intervalMinutes: 120,
    intervalTime: '02:00:00',
    remainingSeconds: 0
  },
  {
    type: 'participants',
    name: '参与者信息',
    description: '爬取活动参与者和签到信息（需先选择活动）',
    icon: markRaw(List),
    running: false,
    starting: false,
    status: 'idle',
    task_id: null,
    current_count: 0,
    total_count: 0,
    lastRun: null
  }
])

// 任务列表
const tasks = ref([])
const currentPage = ref(1)
const pageSize = ref(10)
const totalTasks = ref(0)

// 日志对话框
const logDialogVisible = ref(false)
const logContent = ref('')
const currentTask = ref(null)
const logContentRef = ref(null)

// 脚本加载状态
const scriptLoading = reactive({
  newActivity: false,
  signIn: false,
  signOut: false
})

// 脚本配置
const scripts = reactive([
  {
    type: 'script_new_activity',
    apiEndpoint: 'new-activity',
    name: '新活动报名通知',
    description: '爬取报名中活动，匹配系部年级发送通知',
    icon: markRaw(Bell),
    buttonType: 'primary',
    running: false,
    starting: false,
    status: 'idle',
    task_id: null,
    lastRun: null,
    scheduleEnabled: false,
    scheduleRunning: false,
    scheduleLoading: false,
    intervalMinutes: 30,
    intervalTime: '00:30:00',
    remainingSeconds: 0
  },
  {
    type: 'script_sign_in',
    apiEndpoint: 'sign-in',
    name: '签到通知',
    description: '检测进行中活动的签到时间，发送签到通知',
    icon: markRaw(Clock),
    buttonType: 'success',
    running: false,
    starting: false,
    status: 'idle',
    task_id: null,
    lastRun: null,
    scheduleEnabled: false,
    scheduleRunning: false,
    scheduleLoading: false,
    intervalMinutes: 15,
    intervalTime: '00:15:00',
    remainingSeconds: 0
  },
  {
    type: 'script_sign_out',
    apiEndpoint: 'sign-out',
    name: '签退通知',
    description: '检测进行中活动的签退时间，发送签退通知',
    icon: markRaw(Clock),
    buttonType: 'warning',
    running: false,
    starting: false,
    status: 'idle',
    task_id: null,
    lastRun: null,
    scheduleEnabled: false,
    scheduleRunning: false,
    scheduleLoading: false,
    intervalMinutes: 15,
    intervalTime: '00:15:00',
    remainingSeconds: 0
  }
])

// 活动选择对话框
const activityDialogVisible = ref(false)
const activityList = ref([])
const activityPage = ref(1)
const activityPageSize = ref(20)
const activityTotal = ref(0)
const activityLoading = ref(false)
const selectAllLoading = ref(false)
const selectedActivities = ref([])
const selectedActivityMap = ref(new Map())
const activityTableRef = ref(null)
const pendingCrawlerType = ref(null)
const activitySearchKeyword = ref('')
const activityStatusFilter = ref('')

// 轮询定时器
let pollTimer = null

// 启动爬虫
const startCrawler = async (crawler) => {
  try {
    crawler.starting = true

    let response
    switch (crawler.type) {
      case 'activities':
        response = await crawlActivities()
        break
      case 'details':
        pendingCrawlerType.value = 'details'
        await openActivityDialog()
        return
      case 'students':
        response = await crawlStudents()
        break
      case 'participants':
        pendingCrawlerType.value = 'participants'
        await openActivityDialog()
        return
    }

    if (response.task_id) {
      crawler.running = true
      crawler.task_id = response.task_id
      crawler.status = 'running'
      ElMessage.success(response.message)

      // 开始轮询任务状态
      startPolling()
    }
  } catch (error) {
    ElMessage.error(error.message || '启动失败')
  } finally {
    crawler.starting = false
  }
}

// 停止爬虫
const stopCrawler = async (crawler) => {
  if (!crawler.task_id) return

  try {
    await stopTask(crawler.task_id)
    ElMessage.success('停止请求已发送')
    
    // 立即更新UI状态
    crawler.running = false
    crawler.starting = false
    crawler.status = 'stopped'
    
    // 刷新任务列表
    await loadTasks()
  } catch (error) {
    ElMessage.error(error.message || '停止失败')
  }
}

// 停止任务（通过任务ID）
const stopTaskById = async (taskId) => {
  try {
    await stopTask(taskId)
    ElMessage.success('停止请求已发送')
    await loadTasks()
  } catch (error) {
    ElMessage.error(error.message || '停止失败')
  }
}

// 加载任务列表
const loadTasks = async () => {
  try {
    const response = await getTasks({
      skip: (currentPage.value - 1) * pageSize.value,
      limit: pageSize.value
    })
    tasks.value = response.items
    totalTasks.value = response.total

    // 更新爬虫卡片状态
    updateCrawlerStatus()
  } catch (error) {
    console.error('加载任务列表失败:', error)
  }
}

// 更新爬虫卡片状态
const updateCrawlerStatus = () => {
  crawlers.forEach(crawler => {
    const runningTask = tasks.value.find(
      t => t.task_type === crawler.type && t.status === 'running'
    )

    if (runningTask) {
      crawler.running = true
      crawler.task_id = runningTask.task_id
      crawler.status = runningTask.status
      crawler.current_count = runningTask.current_count
      crawler.total_count = runningTask.total_count
    } else {
      crawler.running = false
      crawler.task_id = null
      crawler.status = 'idle'
    }

    // 更新最近运行时间
    const latestTask = tasks.value
      .filter(t => t.task_type === crawler.type)
      .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))[0]

    if (latestTask) {
      crawler.lastRun = latestTask.started_at
    }
  })

  // 同时更新脚本状态
  updateScriptStatus()
}

// 开始轮询(只要页面打开就持续刷新任务历史,以便看到定时任务新建的条目)
// - 有 running 任务  : 3 秒/次,看到实时进度
// - 否则             : 5 秒/次,负担小但能看到定时任务新创建的条目
// 注意:不再因为"没有 running"就自杀,只在 onUnmounted 停止
const startPolling = () => {
  if (pollTimer) return

  const tick = async () => {
    await loadTasks()
    const hasRunning = tasks.value.some(t => t.status === 'running')
    // 根据是否有 running 任务动态调整下一次轮询的间隔
    const nextDelay = hasRunning ? 3000 : 5000
    if (pollTimer !== null) {
      pollTimer = setTimeout(tick, nextDelay)
    }
  }

  // 使用 setTimeout 链式调度,避免 setInterval 在慢请求时堆积
  pollTimer = setTimeout(tick, 3000)
}

// 停止轮询(只在组件卸载时调用)
const stopPolling = () => {
  if (pollTimer) {
    clearTimeout(pollTimer)
    pollTimer = null
  }
}

// 查看日志
const viewLogs = async (task) => {
  currentTask.value = task
  logDialogVisible.value = true
  await refreshLogs()
  // 如果自动刷新开启，启动定时刷新
  if (logAutoRefresh.value) {
    startLogAutoRefresh()
  }
}

// 刷新日志
const refreshLogs = async () => {
  if (!currentTask.value) return

  try {
    const response = await getTaskLogs(currentTask.value.task_id)
    logContent.value = response.log_content || '暂无日志'

    // 滚动到底部
    setTimeout(() => {
      if (logContentRef.value) {
        logContentRef.value.scrollTop = logContentRef.value.scrollHeight
      }
    }, 100)
  } catch (error) {
    ElMessage.error('加载日志失败')
  }
}

// 刷新任务列表
const refreshTasks = () => {
  loadTasks()
  ElMessage.success('已刷新')
}

// 格式化时间
const formatTime = (time) => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

// 格式化倒计时 (xx:xx:xx)
const formatCountdown = (seconds) => {
  if (!seconds || seconds <= 0) return '00:00:00'
  const hours = Math.floor(seconds / 3600)
  const mins = Math.floor((seconds % 3600) / 60)
  const secs = seconds % 60
  return `${String(hours).padStart(2, '0')}:${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`
}

// 时间字符串转换为分钟数
const updateIntervalMinutes = (crawler, timeStr) => {
  if (!timeStr) return
  const parts = timeStr.split(':')
  const hours = parseInt(parts[0]) || 0
  const mins = parseInt(parts[1]) || 0
  const secs = parseInt(parts[2]) || 0
  crawler.intervalMinutes = hours * 60 + mins + Math.ceil(secs / 60)
  if (crawler.intervalMinutes < 1) crawler.intervalMinutes = 1
}

// 定时任务开关
const toggleSchedule = async (crawler) => {
  crawler.scheduleLoading = true
  try {
    if (crawler.scheduleEnabled) {
      // 启动定时任务
      const res = await startSchedule({
        crawler_type: crawler.type,
        interval_minutes: crawler.intervalMinutes
      })
      if (res.status === 'success') {
        crawler.scheduleRunning = true
        ElMessage.success(`${crawler.name}定时任务已启动`)
        startSchedulePolling()
        // 立即同步一次后端状态 + 任务历史,免得用户等 3-5 秒才看到反馈
        await updateScheduleStatus()
        await loadTasks()
      } else {
        crawler.scheduleEnabled = false
        ElMessage.error(res.message || '启动失败')
      }
    } else {
      // 停止定时任务
      const scheduleId = `schedule_${crawler.type}`
      const res = await stopSchedule(scheduleId)
      if (res.status === 'success') {
        crawler.scheduleRunning = false
        crawler.remainingSeconds = 0
        ElMessage.success(`${crawler.name}定时任务已停止`)
      } else {
        crawler.scheduleEnabled = true
        ElMessage.error(res.message || '停止失败')
      }
    }
  } catch (error) {
    crawler.scheduleEnabled = !crawler.scheduleEnabled
    ElMessage.error('操作失败')
    console.error(error)
  } finally {
    crawler.scheduleLoading = false
  }
}

// 定时任务轮询
let scheduleTimer = null
let scheduleStatusTimer = null

const startSchedulePolling = () => {
  if (scheduleTimer) return

  // 每秒更新倒计时
  scheduleTimer = setInterval(() => {
    // 更新爬虫倒计时
    crawlers.forEach(crawler => {
      if (crawler.scheduleRunning && crawler.remainingSeconds > 0) {
        crawler.remainingSeconds--
      }
    })
    // 更新脚本倒计时
    scripts.forEach(script => {
      if (script.scheduleRunning && script.remainingSeconds > 0) {
        script.remainingSeconds--
      }
    })
  }, 1000)

  // 每10秒从后端同步一次状态
  scheduleStatusTimer = setInterval(async () => {
    await updateScheduleStatus()
  }, 10000)
}

const stopSchedulePolling = () => {
  if (scheduleTimer) {
    clearInterval(scheduleTimer)
    scheduleTimer = null
  }
  if (scheduleStatusTimer) {
    clearInterval(scheduleStatusTimer)
    scheduleStatusTimer = null
  }
}

// 运行通知脚本（旧方法，保留兼容）
const runScript = async (scriptType) => {
  const loadingKey = scriptType === 'new-activity' ? 'newActivity'
    : scriptType === 'sign-in' ? 'signIn' : 'signOut'

  scriptLoading[loadingKey] = true

  try {
    const response = await fetch(`/api/crawler/scripts/${scriptType}-notify`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    })

    if (response.ok) {
      const result = await response.json()
      ElMessage.success(result.message || '脚本已在后台启动')
      // 刷新任务列表
      await loadTasks()
      startPolling()
    } else {
      ElMessage.error('启动脚本失败')
    }
  } catch (error) {
    console.error('运行脚本失败:', error)
    ElMessage.error('运行脚本失败')
  } finally {
    scriptLoading[loadingKey] = false
  }
}

// 启动脚本
const startScript = async (script) => {
  try {
    script.starting = true

    const response = await fetch(`/api/crawler/scripts/${script.apiEndpoint}-notify`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    })

    if (response.ok) {
      const result = await response.json()
      if (result.task_id) {
        script.running = true
        script.task_id = result.task_id
        script.status = 'running'
        ElMessage.success(result.message || '脚本已启动')
        startPolling()
      }
    } else {
      ElMessage.error('启动脚本失败')
    }
  } catch (error) {
    console.error('启动脚本失败:', error)
    ElMessage.error('启动脚本失败')
  } finally {
    script.starting = false
  }
}

// 停止脚本
const stopScript = async (script) => {
  if (!script.task_id) return

  try {
    await stopTask(script.task_id)
    ElMessage.success('停止请求已发送')

    // 立即更新UI状态
    script.running = false
    script.starting = false
    script.status = 'stopped'

    // 刷新任务列表
    await loadTasks()
  } catch (error) {
    ElMessage.error(error.message || '停止失败')
  }
}

// 更新脚本状态
const updateScriptStatus = () => {
  scripts.forEach(script => {
    const runningTask = tasks.value.find(
      t => t.task_type === script.type && t.status === 'running'
    )

    if (runningTask) {
      script.running = true
      script.task_id = runningTask.task_id
      script.status = runningTask.status
    } else {
      script.running = false
      script.task_id = null
      script.status = 'idle'
    }

    // 更新最近运行时间
    const latestTask = tasks.value
      .filter(t => t.task_type === script.type)
      .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))[0]

    if (latestTask) {
      script.lastRun = latestTask.started_at
    }
  })
}

// 脚本定时任务开关
const toggleScriptSchedule = async (script) => {
  script.scheduleLoading = true
  try {
    if (script.scheduleEnabled) {
      // 启动定时任务
      const res = await startSchedule({
        crawler_type: script.type,
        interval_minutes: script.intervalMinutes
      })
      if (res.status === 'success') {
        script.scheduleRunning = true
        ElMessage.success(`${script.name}定时任务已启动`)
        startSchedulePolling()
      } else {
        script.scheduleEnabled = false
        ElMessage.error(res.message || '启动失败')
      }
    } else {
      // 停止定时任务
      const scheduleId = `schedule_${script.type}`
      const res = await stopSchedule(scheduleId)
      if (res.status === 'success') {
        script.scheduleRunning = false
        script.remainingSeconds = 0
        ElMessage.success(`${script.name}定时任务已停止`)
      } else {
        script.scheduleEnabled = true
        ElMessage.error(res.message || '停止失败')
      }
    }
  } catch (error) {
    script.scheduleEnabled = !script.scheduleEnabled
    ElMessage.error('操作失败')
    console.error(error)
  } finally {
    script.scheduleLoading = false
  }
}

// 更新脚本间隔时间
const updateScriptIntervalMinutes = (script, timeStr) => {
  if (!timeStr) return
  const parts = timeStr.split(':')
  const hours = parseInt(parts[0]) || 0
  const mins = parseInt(parts[1]) || 0
  const secs = parseInt(parts[2]) || 0
  script.intervalMinutes = hours * 60 + mins + Math.ceil(secs / 60)
  if (script.intervalMinutes < 1) script.intervalMinutes = 1
}

// 日志自动刷新
const logAutoRefresh = ref(true)
let logRefreshTimer = null

const toggleLogAutoRefresh = (enabled) => {
  if (enabled) {
    startLogAutoRefresh()
  } else {
    stopLogAutoRefresh()
  }
}

const startLogAutoRefresh = () => {
  if (logRefreshTimer) return
  logRefreshTimer = setInterval(async () => {
    if (logDialogVisible.value && currentTask.value) {
      await refreshLogs()
    }
  }, 2000) // 每2秒刷新一次
}

const stopLogAutoRefresh = () => {
  if (logRefreshTimer) {
    clearInterval(logRefreshTimer)
    logRefreshTimer = null
  }
}

const updateScheduleStatus = async () => {
  try {
    const statuses = await getScheduleStatus()
    let hasRunning = false

    // 更新爬虫定时任务状态
    crawlers.forEach(crawler => {
      if (!crawler.canSchedule) return

      const scheduleId = `schedule_${crawler.type}`
      const status = statuses[scheduleId]

      if (status) {
        crawler.scheduleRunning = status.status !== 'stopped'
        crawler.scheduleEnabled = crawler.scheduleRunning
        crawler.remainingSeconds = status.remaining_seconds || 0
        if (crawler.scheduleRunning) hasRunning = true
      } else {
        crawler.scheduleRunning = false
        crawler.scheduleEnabled = false
        crawler.remainingSeconds = 0
      }
    })

    // 更新脚本定时任务状态
    scripts.forEach(script => {
      const scheduleId = `schedule_${script.type}`
      const status = statuses[scheduleId]

      if (status) {
        script.scheduleRunning = status.status !== 'stopped'
        script.scheduleEnabled = script.scheduleRunning
        script.remainingSeconds = status.remaining_seconds || 0
        if (script.scheduleRunning) hasRunning = true
      } else {
        script.scheduleRunning = false
        script.scheduleEnabled = false
        script.remainingSeconds = 0
      }
    })

    if (!hasRunning) {
      stopSchedulePolling()
    }
  } catch (error) {
    console.error('获取定时任务状态失败:', error)
  }
}

// 获取进度百分比
const getProgressPercentage = (current, total) => {
  if (!total) return 0
  return Math.round((current / total) * 100)
}

// 获取状态类型
const getStatusType = (status) => {
  const typeMap = {
    pending: 'info',
    running: 'warning',
    completed: 'success',
    stopped: 'info',
    failed: 'danger',
    idle: 'info'
  }
  return typeMap[status] || 'info'
}

// 获取状态文本
const getStatusText = (status) => {
  const textMap = {
    pending: '等待中',
    running: '运行中',
    completed: '已完成',
    stopped: '已停止',
    failed: '失败',
    idle: '空闲'
  }
  return textMap[status] || status
}

// 打开活动选择对话框
const openActivityDialog = async () => {
  activityDialogVisible.value = true
  activityPage.value = 1
  selectedActivities.value = []
  selectedActivityMap.value = new Map()
  activitySearchKeyword.value = ''
  activityStatusFilter.value = ''
  await loadActivities()
}

// 重置活动筛选
const resetActivityFilter = () => {
  activitySearchKeyword.value = ''
  activityStatusFilter.value = ''
  activityPage.value = 1
  clearActivitySelection()
  loadActivities()
}

const getActivityQueryParams = (override = {}) => {
  const params = { ...override }
  if (activitySearchKeyword.value) {
    params.org_name = activitySearchKeyword.value
  }
  if (activityStatusFilter.value) {
    params.finish_status = activityStatusFilter.value
  }
  return params
}

const refreshSelectedActivities = () => {
  selectedActivities.value = Array.from(selectedActivityMap.value.values())
}

const syncCurrentPageSelection = async () => {
  await nextTick()
  if (!activityTableRef.value) return

  activityTableRef.value.clearSelection()
  activityList.value.forEach(activity => {
    if (selectedActivityMap.value.has(activity.act_id)) {
      activityTableRef.value.toggleRowSelection(activity, true)
    }
  })
}

// 加载活动列表
const loadActivities = async () => {
  activityLoading.value = true
  try {
    const params = getActivityQueryParams({
      skip: (activityPage.value - 1) * activityPageSize.value,
      limit: activityPageSize.value
    })
    const response = await getActivities(params)
    activityList.value = response.items || response
    activityTotal.value = response.total || activityList.value.length
    await syncCurrentPageSelection()
  } catch (error) {
    ElMessage.error('加载活动列表失败')
  } finally {
    activityLoading.value = false
  }
}

// 处理活动选择变化
const handleActivitySelectionChange = (selection) => {
  const currentPageIds = new Set(activityList.value.map(activity => activity.act_id))
  const nextMap = new Map(selectedActivityMap.value)

  currentPageIds.forEach(actId => {
    nextMap.delete(actId)
  })
  selection.forEach(activity => {
    nextMap.set(activity.act_id, activity)
  })

  selectedActivityMap.value = nextMap
  refreshSelectedActivities()
}

const selectAllMatchingActivities = async () => {
  if (activityTotal.value === 0) return

  selectAllLoading.value = true
  try {
    const response = await getActivities(getActivityQueryParams({
      skip: 0,
      limit: activityTotal.value
    }))
    const activities = response.items || response || []
    selectedActivityMap.value = new Map(
      activities.map(activity => [activity.act_id, activity])
    )
    refreshSelectedActivities()
    await syncCurrentPageSelection()
    ElMessage.success(`已选择全部 ${selectedActivities.value.length} 个活动`)
  } catch (error) {
    ElMessage.error('选择全部活动失败')
  } finally {
    selectAllLoading.value = false
  }
}

const clearActivitySelection = () => {
  selectedActivityMap.value = new Map()
  selectedActivities.value = []
  if (activityTableRef.value) {
    activityTableRef.value.clearSelection()
  }
}

// 确认活动选择
const confirmActivitySelection = async () => {
  if (selectedActivities.value.length === 0) {
    ElMessage.warning('请至少选择一个活动')
    return
  }

  const actIds = selectedActivities.value.map(a => a.act_id)
  const crawler = crawlers.find(c => c.type === pendingCrawlerType.value)
  if (!crawler) return

  try {
    crawler.starting = true
    activityDialogVisible.value = false

    let response
    if (pendingCrawlerType.value === 'details') {
      response = await crawlDetails(actIds)
    } else if (pendingCrawlerType.value === 'participants') {
      response = await crawlParticipants(actIds)
    }

    if (response && response.task_id) {
      crawler.running = true
      crawler.task_id = response.task_id
      crawler.status = 'running'
      ElMessage.success(response.message)
      startPolling()
    }
  } catch (error) {
    ElMessage.error(error.message || '启动失败')
  } finally {
    crawler.starting = false
  }
}

// 获取活动状态标签类型 (平台 9 状态)
const getActivityTagType = (status) => {
  const typeMap = {
    '审核中':     'warning',
    '被驳回':     'danger',
    '报名中':     'primary',
    '待开始':     'primary',
    '进行中':     'success',
    '待完结':     'warning',
    '完结审核中': 'warning',
    '完结被驳回': 'danger',
    '已完结':     'info'
  }
  return typeMap[status] || 'info'
}

// 获取任务类型颜色
const getTaskTypeColor = (type) => {
  const colorMap = {
    activities: 'primary',
    details: 'info',
    students: '',
    participants: 'warning',
    script_new_activity: 'success',
    script_sign_in: 'primary',
    script_sign_out: 'danger'
  }
  return colorMap[type] || 'info'
}

// 获取任务类型名称
const getTaskTypeName = (type) => {
  const nameMap = {
    activities: '活动列表',
    details: '活动详情',
    students: '学生信息',
    participants: '参与者信息',
    script_new_activity: '新活动通知',
    script_sign_in: '签到通知',
    script_sign_out: '签退通知'
  }
  return nameMap[type] || type
}

// 组件挂载
onMounted(async () => {
  loadTasks()
  startPolling()
  // 初始化定时任务状态
  await updateScheduleStatus()
  // 如果有运行中的定时任务，启动轮询
  const hasCrawlerScheduleRunning = crawlers.some(c => c.scheduleRunning)
  const hasScriptScheduleRunning = scripts.some(s => s.scheduleRunning)
  if (hasCrawlerScheduleRunning || hasScriptScheduleRunning) {
    startSchedulePolling()
  }
})

// 组件卸载
onUnmounted(() => {
  stopPolling()
  stopSchedulePolling()
  stopLogAutoRefresh()
})
</script>

<style scoped>
.crawler-management {
  padding: 0;
}

.crawler-card {
  margin-bottom: 20px;
  transition: all 0.3s;
}

.crawler-card.running {
  border-color: #409EFF;
  box-shadow: 0 2px 12px rgba(64, 158, 255, 0.3);
}

.crawler-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.crawler-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: bold;
  color: #303133;
}

.crawler-description {
  font-size: 14px;
  color: #606266;
  margin-bottom: 15px;
  min-height: 40px;
}

.crawler-progress {
  margin-bottom: 15px;
}

.progress-text {
  text-align: center;
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}

.crawler-actions {
  display: flex;
  gap: 10px;
  margin-bottom: 15px;
}

.crawler-actions .el-button {
  flex: 1;
}

.crawler-info {
  border-top: 1px solid #EBEEF5;
  padding-top: 10px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #909399;
}

.info-item .label {
  font-weight: bold;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.log-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  padding-bottom: 10px;
  border-bottom: 1px solid #EBEEF5;
}

.log-content {
  max-height: 500px;
  overflow-y: auto;
  background-color: #F5F7FA;
  padding: 15px;
  border-radius: 4px;
}

.log-content pre {
  margin: 0;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  line-height: 1.6;
  color: #303133;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.schedule-config {
  margin-top: 10px;
}

.schedule-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  font-size: 14px;
  color: #606266;
}

.schedule-settings {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

.schedule-status {
  display: flex;
  align-items: center;
  margin-left: auto;
}

.script-card {
  text-align: center;
  padding: 15px;
}

.script-title {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 16px;
  font-weight: bold;
  margin-bottom: 10px;
}

.script-desc {
  color: #909399;
  font-size: 13px;
  margin-bottom: 15px;
  min-height: 40px;
}
</style>
