<template>
  <div class="notification-log">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>通知记录</span>
        </div>
      </template>

      <el-tabs v-model="activeTab" @tab-change="handleTabChange">
        <el-tab-pane label="通知记录" name="notifications">
          <div class="filter-container">
            <el-form :inline="true" :model="notificationFilters">
              <el-form-item label="活动名称">
                <el-input
                  v-model="notificationFilters.act_name"
                  placeholder="请输入活动名称"
                  clearable
                  style="width: 200px"
                />
              </el-form-item>

              <el-form-item label="通知类型">
                <el-select
                  v-model="notificationFilters.notification_type"
                  placeholder="请选择类型"
                  clearable
                  style="width: 150px"
                >
                  <el-option label="新活动" value="new_activity" />
                  <el-option label="签到提醒" value="sign_in" />
                  <el-option label="签退提醒" value="sign_out" />
                </el-select>
              </el-form-item>

              <el-form-item>
                <el-button type="primary" @click="handleNotificationSearch">
                  <el-icon><Search /></el-icon>
                  搜索
                </el-button>
                <el-button @click="handleNotificationReset">
                  <el-icon><Refresh /></el-icon>
                  重置
                </el-button>
              </el-form-item>
            </el-form>
          </div>

          <el-table
            v-loading="notificationLoading"
            :data="notifications"
            style="width: 100%"
            stripe
          >
            <el-table-column prop="id" label="ID" width="80" />
            <el-table-column prop="act_name" label="活动名称" min-width="200" show-overflow-tooltip />
            <el-table-column prop="notification_type" label="通知类型" width="120">
              <template #default="{ row }">
                <el-tag v-if="row.notification_type === 'new_activity'" type="success">新活动</el-tag>
                <el-tag v-else-if="row.notification_type === 'sign_in'" type="warning">签到提醒</el-tag>
                <el-tag v-else-if="row.notification_type === 'sign_out'" type="info">签退提醒</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="recipient_count" label="接收人数" width="100" />
            <el-table-column prop="success_count" label="成功" width="80">
              <template #default="{ row }">
                <span style="color: #67C23A; font-weight: bold;">{{ row.success_count }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="fail_count" label="失败" width="80">
              <template #default="{ row }">
                <span v-if="row.fail_count > 0" style="color: #F56C6C; font-weight: bold;">{{ row.fail_count }}</span>
                <span v-else>{{ row.fail_count }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="sent_at" label="发送时间" width="180" />
          </el-table>

          <div class="pagination-container">
            <el-pagination
              v-model:current-page="notificationPagination.page"
              v-model:page-size="notificationPagination.page_size"
              :page-sizes="[10, 20, 50, 100]"
              :total="notificationPagination.total"
              layout="total, sizes, prev, pager, next, jumper"
              @size-change="handleNotificationSizeChange"
              @current-change="handleNotificationPageChange"
            />
          </div>
        </el-tab-pane>

        <el-tab-pane label="邮件日志" name="emails">
          <div class="filter-container">
            <el-form :inline="true" :model="emailFilters">
              <el-form-item label="收件人">
                <el-input
                  v-model="emailFilters.recipient_email"
                  placeholder="请输入邮箱"
                  clearable
                  style="width: 200px"
                />
              </el-form-item>

              <el-form-item label="学号">
                <el-input
                  v-model="emailFilters.student_code"
                  placeholder="请输入学号"
                  clearable
                  style="width: 150px"
                />
              </el-form-item>

              <el-form-item label="发送状态">
                <el-select
                  v-model="emailFilters.status"
                  placeholder="请选择状态"
                  clearable
                  style="width: 120px"
                >
                  <el-option label="待发送" value="pending" />
                  <el-option label="已发送" value="sent" />
                  <el-option label="失败" value="failed" />
                </el-select>
              </el-form-item>

              <el-form-item>
                <el-button type="primary" @click="handleEmailSearch">
                  <el-icon><Search /></el-icon>
                  搜索
                </el-button>
                <el-button @click="handleEmailReset">
                  <el-icon><Refresh /></el-icon>
                  重置
                </el-button>
              </el-form-item>
            </el-form>
          </div>

          <el-table
            v-loading="emailLoading"
            :data="emails"
            style="width: 100%"
            stripe
          >
            <el-table-column prop="id" label="ID" width="80" />
            <el-table-column prop="recipient_email" label="收件人邮箱" min-width="180" />
            <el-table-column prop="student_code" label="学号" width="120" />
            <el-table-column prop="email_type" label="邮件类型" width="120">
              <template #default="{ row }">
                <el-tag v-if="row.email_type === 'new_activity'" type="success" size="small">新活动</el-tag>
                <el-tag v-else-if="row.email_type === 'sign_in'" type="warning" size="small">签到提醒</el-tag>
                <el-tag v-else-if="row.email_type === 'sign_out'" type="info" size="small">签退提醒</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="subject" label="邮件主题" min-width="200" show-overflow-tooltip />
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag v-if="row.status === 'sent'" type="success" size="small">已发送</el-tag>
                <el-tag v-else-if="row.status === 'pending'" type="warning" size="small">待发送</el-tag>
                <el-tag v-else type="danger" size="small">失败</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="sent_at" label="发送时间" width="180" />
            <el-table-column label="操作" width="100" fixed="right">
              <template #default="{ row }">
                <el-button
                  v-if="row.status === 'failed'"
                  type="primary"
                  size="small"
                  link
                  @click="handleViewError(row)"
                >
                  查看错误
                </el-button>
              </template>
            </el-table-column>
          </el-table>

          <div class="pagination-container">
            <el-pagination
              v-model:current-page="emailPagination.page"
              v-model:page-size="emailPagination.page_size"
              :page-sizes="[10, 20, 50, 100]"
              :total="emailPagination.total"
              layout="total, sizes, prev, pager, next, jumper"
              @size-change="handleEmailSizeChange"
              @current-change="handleEmailPageChange"
            />
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <el-dialog
      v-model="errorDialogVisible"
      title="错误信息"
      width="600px"
    >
      <el-alert
        :title="currentError"
        type="error"
        :closable="false"
        show-icon
      />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Refresh } from '@element-plus/icons-vue'
import { getNotifications, getEmailLogs } from '@/api/notification'

const activeTab = ref('notifications')
const notificationLoading = ref(false)
const emailLoading = ref(false)
const notifications = ref([])
const emails = ref([])
const errorDialogVisible = ref(false)
const currentError = ref('')

const notificationFilters = reactive({
  act_name: '',
  notification_type: ''
})

const notificationPagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

const emailFilters = reactive({
  recipient_email: '',
  student_code: '',
  status: ''
})

const emailPagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

const loadNotifications = async () => {
  notificationLoading.value = true
  try {
    const params = {
      skip: (notificationPagination.page - 1) * notificationPagination.page_size,
      limit: notificationPagination.page_size
    }
    // 只添加非空的筛选参数
    if (notificationFilters.act_name) params.act_name = notificationFilters.act_name
    if (notificationFilters.notification_type) params.notification_type = notificationFilters.notification_type

    const response = await getNotifications(params)
    notifications.value = response.items || []
    notificationPagination.total = response.total || 0
  } catch (error) {
    ElMessage.error('加载通知记录失败')
    console.error(error)
  } finally {
    notificationLoading.value = false
  }
}

const loadEmails = async () => {
  emailLoading.value = true
  try {
    const params = {
      skip: (emailPagination.page - 1) * emailPagination.page_size,
      limit: emailPagination.page_size
    }
    // 只添加非空的筛选参数
    if (emailFilters.recipient_email) params.recipient_email = emailFilters.recipient_email
    if (emailFilters.student_code) params.student_code = emailFilters.student_code
    if (emailFilters.status) params.status = emailFilters.status

    const response = await getEmailLogs(params)
    emails.value = response.items || []
    emailPagination.total = response.total || 0
  } catch (error) {
    ElMessage.error('加载邮件日志失败')
    console.error(error)
  } finally {
    emailLoading.value = false
  }
}

const handleTabChange = (tab) => {
  if (tab === 'notifications') {
    loadNotifications()
  } else {
    loadEmails()
  }
}

const handleNotificationSearch = () => {
  notificationPagination.page = 1
  loadNotifications()
}

const handleNotificationReset = () => {
  notificationFilters.act_name = ''
  notificationFilters.notification_type = ''
  notificationPagination.page = 1
  loadNotifications()
}

const handleNotificationSizeChange = () => {
  notificationPagination.page = 1
  loadNotifications()
}

const handleNotificationPageChange = () => {
  loadNotifications()
}

const handleEmailSearch = () => {
  emailPagination.page = 1
  loadEmails()
}

const handleEmailReset = () => {
  emailFilters.recipient_email = ''
  emailFilters.student_code = ''
  emailFilters.status = ''
  emailPagination.page = 1
  loadEmails()
}

const handleEmailSizeChange = () => {
  emailPagination.page = 1
  loadEmails()
}

const handleEmailPageChange = () => {
  loadEmails()
}

const handleViewError = (row) => {
  currentError.value = row.error_message || '未知错误'
  errorDialogVisible.value = true
}

onMounted(() => {
  loadNotifications()
})
</script>

<style scoped>
.notification-log {
  padding: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filter-container {
  margin-bottom: 20px;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
