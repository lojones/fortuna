import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/LoginView.vue'),
    meta: { guest: true },
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../views/RegisterView.vue'),
    meta: { guest: true },
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('../views/DashboardView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/chat/:vizId',
    name: 'Chat',
    component: () => import('../views/ChatView.vue'),
    meta: { requiresAuth: true },
    props: true,
  },
  {
    path: '/editor/:vizId',
    name: 'Visualization',
    component: () => import('../views/VisualizationView.vue'),
    meta: { requiresAuth: true },
    props: true,
  },
  {
    path: '/admin',
    name: 'AdminDashboard',
    component: () => import('../views/admin/AdminDashboardView.vue'),
    meta: { requiresAuth: true, requiresAdmin: true },
  },
  {
    path: '/admin/users',
    name: 'UserManagement',
    component: () => import('../views/admin/UserManagementView.vue'),
    meta: { requiresAuth: true, requiresAdmin: true },
  },
  {
    path: '/',
    redirect: '/dashboard',
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

let authInitialized = false

router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()

  if (!authInitialized) {
    await authStore.initializeAuth()
    authInitialized = true
  }

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/login')
  } else if (to.meta.requiresAdmin && !authStore.isAdmin) {
    next('/dashboard')
  } else if (to.meta.guest && authStore.isAuthenticated) {
    next('/dashboard')
  } else {
    next()
  }
})

export default router
