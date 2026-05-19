<template>
  <div class="activity-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>活动列表</span>
        </div>
      </template>

      <div class="filter-container">
        <el-form :inline="true" :model="filters">
          <el-form-item label="主办方">
            <el-input
              v-model="filters.org_name"
              placeholder="请输入主办方"
              clearable
              style="width: 200px"
            />
          </el-form-item>

          <el-form-item label="活动状态">
            <el-select
              v-model="filters.finish_status"
              placeholder="请选择状态"
              clearable
              style="width: 150px"
            >
              <!-- 平台实际 9 个状态 (顺序按学生关注度) -->
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
          </el-form-item>

          <el-form-item>
            <el-button type="primary" @click="handleSearch">
              <el-icon><Search /></el-icon>
              搜索
            </el-button>
            <el-button @click="handleReset">
              <el-icon><Refresh /></el-icon>
              重置
            </el-button>
          </el-form-item>
        </el-form>
      </div>

      <el-table
        v-loading="loading"
        :data="activities"
        style="width: 100%"
        stripe
      >
        <el-table-column prop="act_id" label="活动ID" width="80" />
        <el-table-column prop="act_name" label="活动名称" min-width="200" show-overflow-tooltip />
        <el-table-column prop="class_name" label="活动分类" width="120" />
        <el-table-column prop="org_name" label="主办方" width="150" show-overflow-tooltip />
        <el-table-column prop="finish_status" label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="getStatusTagType(row.finish_status)">
              {{ row.finish_status || '未知' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="start_time" label="开始时间" width="180">
          <template #default="{ row }">{{ formatTime(row.start_time) }}</template>
        </el-table-column>
        <el-table-column prop="end_time" label="结束时间" width="180">
          <template #default="{ row }">{{ formatTime(row.end_time) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" link @click="handleView(row)">
              查看详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <el-dialog
      v-model="detailDialogVisible"
      title="活动详情"
      width="800px"
      destroy-on-close
    >
      <el-descriptions v-if="currentActivity" :column="2" border>
        <el-descriptions-item label="活动ID">{{ currentActivity.act_id }}</el-descriptions-item>
        <el-descriptions-item label="活动名称">{{ currentActivity.act_name }}</el-descriptions-item>
        <el-descriptions-item label="活动分类">{{ currentActivity.class_name }}</el-descriptions-item>
        <el-descriptions-item label="主办方">{{ currentActivity.org_name }}</el-descriptions-item>
        <el-descriptions-item label="活动状态">
          <el-tag :type="getStatusTagType(currentActivity.finish_status)">
            {{ currentActivity.finish_status || '未知' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="活动场地">{{ currentActivity.pitch_address || '待定' }}</el-descriptions-item>
        <el-descriptions-item label="开始时间">{{ formatTime(currentActivity.start_time) }}</el-descriptions-item>
        <el-descriptions-item label="结束时间">{{ formatTime(currentActivity.end_time) }}</el-descriptions-item>
        <el-descriptions-item label="报名截止时间">{{ formatTime(currentActivity.enroll_end_time) }}</el-descriptions-item>
        <el-descriptions-item label="限制人数">{{ currentActivity.people_limit || '不限' }}</el-descriptions-item>
        <el-descriptions-item label="可参与院系" :span="2">{{ currentActivity.college_name || '不限' }}</el-descriptions-item>
        <el-descriptions-item label="可参与年级" :span="2">{{ currentActivity.grade_name || '不限' }}</el-descriptions-item>
        <el-descriptions-item label="是否需要作业">{{ currentActivity.job ? '是' : '否' }}</el-descriptions-item>
        <el-descriptions-item label="QQ群">{{ currentActivity.qq_groups || '暂无' }}</el-descriptions-item>
        <el-descriptions-item label="活动简介" :span="2">
          <div style="max-height: 200px; overflow-y: auto;">
            {{ currentActivity.introduce || '暂无' }}
          </div>
        </el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <el-button type="primary" @click="showParticipants">
          <el-icon><User /></el-icon>
          查看参与者 ({{ participantCount }})
        </el-button>
      </template>
    </el-dialog>

    <!-- 参与者列表对话框 -->
    <el-dialog
      v-model="participantDialogVisible"
      title="参与者列表"
      width="900px"
      destroy-on-close
    >
      <el-table
        v-loading="participantLoading"
        :data="participants"
        stripe
        max-height="400"
      >
        <el-table-column prop="student_code" label="学号" width="150" />
        <el-table-column prop="student_name" label="姓名" width="120" />
        <el-table-column prop="sign_in_time" label="签到时间" width="180">
          <template #default="{ row }">{{ row.sign_in_time || '-' }}</template>
        </el-table-column>
        <el-table-column prop="sign_out_time" label="签退时间" width="180">
          <template #default="{ row }">{{ row.sign_out_time || '-' }}</template>
        </el-table-column>
        <el-table-column prop="credits" label="学分" width="100">
          <template #default="{ row }">{{ row.credits || '-' }}</template>
        </el-table-column>
      </el-table>
      <div style="margin-top: 15px; text-align: right;">
        <span style="color: #909399;">共 {{ participantTotal }} 人</span>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Refresh, User } from '@element-plus/icons-vue'
import { getActivities, getActivityDetail, getActivityParticipants } from '@/api/activity'

const loading = ref(false)
const activities = ref([])
const detailDialogVisible = ref(false)
const currentActivity = ref(null)

// 参与者相关
const participantDialogVisible = ref(false)
const participantLoading = ref(false)
const participants = ref([])
const participantTotal = ref(0)
const participantCount = ref(0)

const filters = reactive({
  finish_status: '',
  org_name: ''
})

const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

// 平台 9 个状态 → el-tag 颜色
const STATUS_TAG_TYPE = {
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
const getStatusTagType = (status) => STATUS_TAG_TYPE[status] || 'info'

// 格式化时间，去掉T并显示友好格式
const formatTime = (time) => {
  if (!time) return '-'
  return time.replace('T', ' ').substring(0, 19)
}

const loadActivities = async () => {
  loading.value = true
  try {
    const params = {
      skip: (pagination.page - 1) * pagination.page_size,
      limit: pagination.page_size
    }
    // 只添加非空的筛选参数
    if (filters.finish_status) params.finish_status = filters.finish_status
    if (filters.org_name) params.org_name = filters.org_name

    const response = await getActivities(params)
    activities.value = response.items || []
    pagination.total = response.total || 0
  } catch (error) {
    ElMessage.error('加载活动列表失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  loadActivities()
}

const handleReset = () => {
  filters.org_name = ''
  filters.finish_status = ''
  pagination.page = 1
  loadActivities()
}

const handleSizeChange = () => {
  pagination.page = 1
  loadActivities()
}

const handlePageChange = () => {
  loadActivities()
}

const handleView = async (row) => {
  try {
    const detail = await getActivityDetail(row.act_id)
    currentActivity.value = detail
    // 获取参与者数量
    const participantRes = await getActivityParticipants(row.act_id, { limit: 1 })
    participantCount.value = participantRes.total || 0
    detailDialogVisible.value = true
  } catch (error) {
    ElMessage.error('加载活动详情失败')
    console.error(error)
  }
}

const showParticipants = async () => {
  if (!currentActivity.value) return
  
  participantDialogVisible.value = true
  participantLoading.value = true
  
  try {
    const res = await getActivityParticipants(currentActivity.value.act_id, { limit: 500 })
    participants.value = res.items || []
    participantTotal.value = res.total || 0
  } catch (error) {
    ElMessage.error('加载参与者列表失败')
    console.error(error)
  } finally {
    participantLoading.value = false
  }
}

onMounted(() => {
  loadActivities()
})
</script>

<style scoped>
.activity-list {
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

/* 详情对话框: 防止 label 列被压成竖排 (el-descriptions 在某些环境
   下会把宽 label 收得极窄, 导致 "活动 ID" 4 个字一字一行) */
:deep(.el-descriptions__label) {
  width: 110px;
  min-width: 110px;
  white-space: nowrap;
}
:deep(.el-descriptions__content) {
  word-break: break-word;
}
</style>
