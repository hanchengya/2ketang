<template>
  <div class="student-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>学生列表</span>
        </div>
      </template>

      <div class="filter-container">
        <el-form :inline="true" :model="filters">
          <el-form-item label="学号/姓名">
            <el-input
              v-model="filters.keyword"
              placeholder="请输入学号或姓名"
              clearable
              style="width: 200px"
            />
          </el-form-item>

          <el-form-item label="院系">
            <el-input
              v-model="filters.college_name"
              placeholder="请输入院系"
              clearable
              style="width: 150px"
            />
          </el-form-item>

          <el-form-item label="年级">
            <el-input
              v-model="filters.grade_name"
              placeholder="请输入年级"
              clearable
              style="width: 120px"
            />
          </el-form-item>

          <el-form-item label="邮箱状态">
            <el-select
              v-model="filters.has_email"
              placeholder="请选择"
              clearable
              style="width: 120px"
            >
              <el-option label="已绑定" value="true" />
              <el-option label="未绑定" value="false" />
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
        :data="students"
        style="width: 100%"
        stripe
      >
        <el-table-column prop="code" label="学号" width="120" />
        <el-table-column prop="name" label="姓名" width="100" />
        <el-table-column prop="college_name" label="院系" min-width="150" show-overflow-tooltip />
        <el-table-column prop="grade_name" label="年级" width="100" />
        <el-table-column prop="class_name" label="班级" width="120" show-overflow-tooltip />
        <el-table-column prop="credit" label="信誉分" width="80" align="center">
          <template #default="{ row }">
            <span>{{ row.credit ?? '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="sum_score" label="二课总分" width="90" align="center">
          <template #default="{ row }">
            <span>{{ row.sum_score ?? '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="mobile" label="手机号" width="120" />
        <el-table-column prop="email" label="邮箱" min-width="180" show-overflow-tooltip>
          <template #default="{ row }">
            <span v-if="row.email">{{ row.email }}</span>
            <el-tag v-else type="info" size="small">未绑定</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" link @click="handleEditEmail(row)">
              {{ row.email ? '修改邮箱' : '绑定邮箱' }}
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
      v-model="emailDialogVisible"
      :title="currentStudent?.email ? '修改邮箱' : '绑定邮箱'"
      width="500px"
    >
      <el-form
        ref="emailFormRef"
        :model="emailForm"
        :rules="emailRules"
        label-width="80px"
      >
        <el-form-item label="学号">
          <el-input v-model="currentStudent.code" disabled />
        </el-form-item>
        <el-form-item label="姓名">
          <el-input v-model="currentStudent.name" disabled />
        </el-form-item>
        <el-form-item label="邮箱地址" prop="email">
          <el-input
            v-model="emailForm.email"
            placeholder="请输入邮箱地址"
            clearable
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="emailDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmitEmail">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Refresh } from '@element-plus/icons-vue'
import { getStudents, updateStudentEmail } from '@/api/student'

const loading = ref(false)
const submitting = ref(false)
const students = ref([])
const emailDialogVisible = ref(false)
const currentStudent = ref(null)
const emailFormRef = ref(null)

const filters = reactive({
  keyword: '',
  college_name: '',
  grade_name: '',
  has_email: null
})

const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

const emailForm = reactive({
  email: ''
})

const emailRules = {
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ]
}

const loadStudents = async () => {
  loading.value = true
  try {
    const params = {
      skip: (pagination.page - 1) * pagination.page_size,
      limit: pagination.page_size
    }
    // 只添加非空的筛选参数
    if (filters.keyword) params.keyword = filters.keyword
    if (filters.college_name) params.college_name = filters.college_name
    if (filters.grade_name) params.grade_name = filters.grade_name
    if (filters.has_email !== null) params.has_email = filters.has_email

    const response = await getStudents(params)
    students.value = response.items || []
    pagination.total = response.total || 0
  } catch (error) {
    ElMessage.error('加载学生列表失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  loadStudents()
}

const handleReset = () => {
  filters.keyword = ''
  filters.college_name = ''
  filters.grade_name = ''
  filters.has_email = null
  pagination.page = 1
  loadStudents()
}

const handleSizeChange = () => {
  pagination.page = 1
  loadStudents()
}

const handlePageChange = () => {
  loadStudents()
}

const handleEditEmail = (row) => {
  currentStudent.value = { ...row }
  emailForm.email = row.email || ''
  emailDialogVisible.value = true
}

const handleSubmitEmail = async () => {
  if (!emailFormRef.value) return

  await emailFormRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true
      try {
        await updateStudentEmail(currentStudent.value.code, emailForm.email)
        ElMessage.success('邮箱更新成功')
        emailDialogVisible.value = false
        loadStudents()
      } catch (error) {
        ElMessage.error('邮箱更新失败')
        console.error(error)
      } finally {
        submitting.value = false
      }
    }
  })
}

onMounted(() => {
  loadStudents()
})
</script>

<style scoped>
.student-list {
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
