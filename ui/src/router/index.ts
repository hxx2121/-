import { createRouter, createWebHistory } from "vue-router"

import { useAuthStore } from "@/stores/auth-store"

const AppShell = () => import("@/components/app-shell/app-shell.vue")

const LoginPage = () => import("@/pages/auth/login-page.vue")
const RegisterPage = () => import("@/pages/auth/register-page.vue")
const HomePage = () => import("@/pages/home-page.vue")
const QADashboardPage = () => import("@/pages/qa/dashboard-page.vue")
const QAChatPage = () => import("@/pages/qa/chat-page.vue")
const QADatasetPage = () => import("@/pages/qa/dataset-page.vue")
const AdminPromptsPage = () => import("@/pages/admin/prompts-page.vue")

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/",
      component: AppShell,
      meta: { requiresAuth: true },
      children: [
        { path: "", name: "home", component: HomePage },
        { path: "dashboard", name: "qa-dashboard", component: QADashboardPage },
        { path: "qa/dataset", name: "qa-dataset", component: QADatasetPage },
        { path: "qa/chat", name: "qa-chat", component: QAChatPage },
        { path: "admin/prompts", name: "admin-prompts", component: AdminPromptsPage, meta: { requiresAdmin: true } },
      ]
    },
    { path: "/login", name: "login", component: LoginPage },
    { path: "/register", name: "register", component: RegisterPage },
  ],
})

router.beforeEach((to) => {
  const authStore = useAuthStore()
  const isAuthed = authStore.isAuthenticated
  
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth)
  const requiresAdmin = to.matched.some(record => record.meta.requiresAdmin)

  if (requiresAuth && !isAuthed) {
    return { name: "login", query: { next: to.fullPath } }
  }
  if (requiresAdmin && !authStore.isAdmin) {
    return { name: "home" }
  }
  if ((to.name === "login" || to.name === "register") && isAuthed) {
    return { name: "home" }
  }
})
