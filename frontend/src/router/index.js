import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    name: 'Layout',
    component: () => import('@/layout/index.vue'),
    redirect: '/dashboard',
    meta: { requiresAuth: true },
    children: [
      {
        path: '/dashboard',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: { title: '数据看板', icon: 'DataBoard' }
      },
      {
        path: '/activities',
        name: 'Activities',
        component: () => import('@/views/ActivityList.vue'),
        meta: { title: '活动管理', icon: 'Calendar' }
      },
      {
        path: '/activities/:id',
        name: 'ActivityDetail',
        component: () => import('@/views/ActivityList.vue'),
        meta: { title: '活动详情', hidden: true }
      },
      {
        path: '/students',
        name: 'Students',
        component: () => import('@/views/StudentList.vue'),
        meta: { title: '学生管理', icon: 'User' }
      },
      {
        path: '/notifications',
        name: 'Notifications',
        component: () => import('@/views/NotificationLog.vue'),
        meta: { title: '通知记录', icon: 'Bell' }
      },
      {
        path: '/crawler',
        name: 'Crawler',
        component: () => import('@/views/CrawlerManagement.vue'),
        meta: { title: '爬虫控制', icon: 'Setting' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/login')
  } else if (to.path === '/login' && authStore.isAuthenticated) {
    next('/')
  } else {
    next()
  }
})

export default router