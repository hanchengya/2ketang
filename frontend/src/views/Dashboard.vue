<template>
  <div class="dashboard">
    <el-row :gutter="20">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background-color: #409EFF;">
              <el-icon :size="32"><Calendar /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ activityStats.total || 0 }}</div>
              <div class="stat-label">活动总数</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background-color: #67C23A;">
              <el-icon :size="32"><User /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ studentStats.total || 0 }}</div>
              <div class="stat-label">学生总数</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background-color: #E6A23C;">
              <el-icon :size="32"><Message /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ studentStats.with_email || 0 }}</div>
              <div class="stat-label">已绑定邮箱</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background-color: #F56C6C;">
              <el-icon :size="32"><Bell /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ notificationStats.total || 0 }}</div>
              <div class="stat-label">通知总数</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>活动状态分布</span>
            </div>
          </template>
          <div class="chart-container">
            <el-empty v-if="!activityStats.by_status" description="暂无数据" />
            <div v-else>
              <div v-for="(count, status) in activityStats.by_status" :key="status" class="status-item">
                <span class="status-label">{{ status }}</span>
                <el-progress :percentage="getPercentage(count, activityStats.total)" :color="getStatusColor(status)" />
                <span class="status-count">{{ count }}</span>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>邮件发送统计</span>
            </div>
          </template>
          <div class="chart-container">
            <el-empty v-if="!notificationStats.sent_count" description="暂无数据" />
            <div v-else class="email-stats">
              <div class="email-stat-item">
                <div class="email-stat-label">已发送</div>
                <div class="email-stat-value success">{{ notificationStats.sent_count || 0 }}</div>
              </div>
              <div class="email-stat-item">
                <div class="email-stat-label">发送中</div>
                <div class="email-stat-value pending">{{ notificationStats.pending_count || 0 }}</div>
              </div>
              <div class="email-stat-item">
                <div class="email-stat-label">失败</div>
                <div class="email-stat-value failed">{{ notificationStats.failed_count || 0 }}</div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>最近通知记录</span>
              <el-button type="primary" size="small" @click="$router.push('/notifications')">
                查看全部
              </el-button>
            </div>
          </template>
          <el-table :data="recentNotifications" style="width: 100%">
            <el-table-column prop="act_name" label="活动名称" min-width="200" />
            <el-table-column prop="notification_type" label="通知类型" width="120">
              <template #default="{ row }">
                <el-tag v-if="row.notification_type === 'new_activity'" type="success">新活动</el-tag>
                <el-tag v-else-if="row.notification_type === 'sign_in'" type="warning">签到提醒</el-tag>
                <el-tag v-else-if="row.notification_type === 'sign_out'" type="info">签退提醒</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="recipient_count" label="接收人数" width="100" />
            <el-table-column prop="success_count" label="成功" width="80" />
            <el-table-column prop="fail_count" label="失败" width="80" />
            <el-table-column prop="sent_at" label="发送时间" width="180" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Calendar, User, Message, Bell } from '@element-plus/icons-vue'
import { getActivityStats } from '@/api/activity'
import { getStudentStats } from '@/api/student'
import { getNotificationStats } from '@/api/notification'

const activityStats = ref({})
const studentStats = ref({})
const notificationStats = ref({})
const recentNotifications = ref([])

const loadStats = async () => {
  try {
    const [activityRes, studentRes, notificationRes] = await Promise.all([
      getActivityStats(),
      getStudentStats(),
      getNotificationStats()
    ])
    activityStats.value = activityRes
    studentStats.value = studentRes
    notificationStats.value = notificationRes
    recentNotifications.value = notificationRes.recent_notifications || []
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
}

const getPercentage = (count, total) => {
  if (!total) return 0
  return Math.round((count / total) * 100)
}

const getStatusColor = (status) => {
  const colors = {
    '待审核': '#E6A23C',
    '报名中': '#409EFF',
    '进行中': '#67C23A',
    '已结束': '#909399',
    '未知': '#C0C4CC'
  }
  return colors[status] || '#909399'
}

onMounted(() => {
  loadStats()
})
</script>

<style scoped>
.dashboard {
  padding: 0;
}

.stat-card {
  cursor: pointer;
  transition: all 0.3s;
}

.stat-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 20px;
}

.stat-icon {
  width: 64px;
  height: 64px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 5px;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chart-container {
  min-height: 200px;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 15px;
}

.status-label {
  width: 80px;
  font-size: 14px;
  color: #606266;
}

.status-count {
  width: 50px;
  text-align: right;
  font-weight: bold;
  color: #303133;
}

.email-stats {
  display: flex;
  justify-content: space-around;
  padding: 40px 0;
}

.email-stat-item {
  text-align: center;
}

.email-stat-label {
  font-size: 14px;
  color: #909399;
  margin-bottom: 10px;
}

.email-stat-value {
  font-size: 36px;
  font-weight: bold;
}

.email-stat-value.success {
  color: #67C23A;
}

.email-stat-value.pending {
  color: #E6A23C;
}

.email-stat-value.failed {
  color: #F56C6C;
}
</style>
