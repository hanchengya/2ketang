<template>
  <div class="settings">
    <el-row :gutter="20">
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>爬虫配置</span>
            </div>
          </template>

          <el-form :model="crawlerConfig" label-width="120px">
            <el-form-item label="爬取延迟">
              <el-input-number
                v-model="crawlerConfig.crawl_delay"
                :min="1"
                :max="60"
                :step="1"
              />
              <span style="margin-left: 10px; color: #909399;">秒</span>
            </el-form-item>

            <el-form-item label="每页显示数">
              <el-input-number
                v-model="crawlerConfig.page_size"
                :min="10"
                :max="200"
                :step="10"
              />
              <span style="margin-left: 10px; color: #909399;">条</span>
            </el-form-item>

            <el-form-item label="测试模式">
              <el-switch
                v-model="crawlerConfig.test_mode"
                active-text="开启"
                inactive-text="关闭"
              />
              <div style="margin-top: 5px; font-size: 12px; color: #909399;">
                测试模式下不会实际发送邮件
              </div>
            </el-form-item>

            <el-form-item>
              <el-button type="primary" @click="handleStartCrawler">
                <el-icon><VideoPlay /></el-icon>
                启动爬虫
              </el-button>
              <el-button @click="handleStopCrawler">
                <el-icon><VideoPause /></el-icon>
                停止爬虫
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>邮件配置</span>
            </div>
          </template>

          <el-form :model="emailConfig" label-width="120px">
            <el-form-item label="SMTP服务器">
              <el-input v-model="emailConfig.smtp_server" disabled />
            </el-form-item>

            <el-form-item label="SMTP端口">
              <el-input-number
                v-model="emailConfig.smtp_port"
                :min="1"
                :max="65535"
                disabled
              />
            </el-form-item>

            <el-form-item label="发件人邮箱">
              <el-input v-model="emailConfig.sender_email" disabled />
            </el-form-item>

            <el-form-item label="发件人名称">
              <el-input v-model="emailConfig.sender_name" />
            </el-form-item>

            <el-form-item label="邮件发送延迟">
              <el-input-number
                v-model="emailConfig.email_delay"
                :min="0"
                :max="10"
                :step="1"
              />
              <span style="margin-left: 10px; color: #909399;">秒</span>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>测试邮件发送</span>
            </div>
          </template>

          <el-form :model="testEmailForm" label-width="120px" style="max-width: 600px;">
            <el-form-item label="收件人邮箱">
              <el-input
                v-model="testEmailForm.recipient_email"
                placeholder="请输入收件人邮箱"
                clearable
              />
            </el-form-item>

            <el-form-item label="邮件主题">
              <el-input
                v-model="testEmailForm.subject"
                placeholder="请输入邮件主题"
                clearable
              />
            </el-form-item>

            <el-form-item label="邮件内容">
              <el-input
                v-model="testEmailForm.content"
                type="textarea"
                :rows="5"
                placeholder="请输入邮件内容"
              />
            </el-form-item>

            <el-form-item>
              <el-button
                type="primary"
                :loading="sendingTestEmail"
                @click="handleSendTestEmail"
              >
                <el-icon><Promotion /></el-icon>
                发送测试邮件
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>爬虫日志</span>
              <el-button type="primary" size="small" @click="loadCrawlerLogs">
                <el-icon><Refresh /></el-icon>
                刷新
              </el-button>
            </div>
          </template>

          <div class="log-container">
            <el-empty v-if="crawlerLogs.length === 0" description="暂无日志" />
            <div v-else class="log-content">
              <div v-for="(log, index) in crawlerLogs" :key="index" class="log-item">
                <span class="log-time">{{ log.time }}</span>
                <span :class="['log-level', `log-level-${log.level}`]">{{ log.level }}</span>
                <span class="log-message">{{ log.message }}</span>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { VideoPlay, VideoPause, Promotion, Refresh } from '@element-plus/icons-vue'
import request from '@/api/request'

const crawlerConfig = reactive({
  crawl_delay: 5,
  page_size: 100,
  test_mode: true
})

const emailConfig = reactive({
  smtp_server: 'smtp.qq.com',
  smtp_port: 465,
  sender_email: 'lcxlio@qq.com',
  sender_name: '数智维新工作室',
  email_delay: 1
})

const testEmailForm = reactive({
  recipient_email: '',
  subject: '测试邮件',
  content: '这是一封测试邮件，用于验证邮件发送功能是否正常。'
})

const sendingTestEmail = ref(false)
const crawlerLogs = ref([])

const handleStartCrawler = async () => {
  try {
    await request.post('/crawler/crawl-activities', { save_to_db: true })
    ElMessage.success('爬虫已启动，正在后台运行')
    loadCrawlerLogs()
  } catch (error) {
    ElMessage.error('启动爬虫失败')
    console.error(error)
  }
}

const handleStopCrawler = async () => {
  try {
    ElMessage.info('爬虫停止功能暂未实现')
  } catch (error) {
    ElMessage.error('停止爬虫失败')
    console.error(error)
  }
}

const handleSendTestEmail = async () => {
  if (!testEmailForm.recipient_email) {
    ElMessage.warning('请输入收件人邮箱')
    return
  }

  sendingTestEmail.value = true
  try {
    await request.post('/crawler/test-email', testEmailForm)
    ElMessage.success('测试邮件发送成功')
  } catch (error) {
    ElMessage.error('测试邮件发送失败')
    console.error(error)
  } finally {
    sendingTestEmail.value = false
  }
}

const loadCrawlerLogs = async () => {
  try {
    // 爬虫日志功能暂未实现
    crawlerLogs.value = []
  } catch (error) {
    console.error('加载爬虫日志失败:', error)
  }
}

onMounted(() => {
  loadCrawlerLogs()
})
</script>

<style scoped>
.settings {
  padding: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.log-container {
  min-height: 300px;
  max-height: 500px;
  overflow-y: auto;
}

.log-content {
  font-family: 'Courier New', monospace;
  font-size: 13px;
  background-color: #1e1e1e;
  color: #d4d4d4;
  padding: 15px;
  border-radius: 4px;
}

.log-item {
  margin-bottom: 8px;
  line-height: 1.6;
}

.log-time {
  color: #858585;
  margin-right: 10px;
}

.log-level {
  display: inline-block;
  width: 60px;
  text-align: center;
  padding: 2px 8px;
  border-radius: 3px;
  margin-right: 10px;
  font-weight: bold;
}

.log-level-INFO {
  background-color: #4fc3f7;
  color: #000;
}

.log-level-WARNING {
  background-color: #ffb74d;
  color: #000;
}

.log-level-ERROR {
  background-color: #e57373;
  color: #fff;
}

.log-level-SUCCESS {
  background-color: #81c784;
  color: #000;
}

.log-message {
  color: #d4d4d4;
}
</style>
