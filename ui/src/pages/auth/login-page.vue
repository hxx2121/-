<script setup lang="ts">
import { reactive, ref } from "vue"
import { useRoute, useRouter } from "vue-router"
import { NForm, NFormItem, NInput, NButton, useMessage } from "naive-ui"
import { 
  ArrowRightOnRectangleIcon, 
  UserIcon, 
  LockClosedIcon, 
  ArrowRightIcon 
} from "@heroicons/vue/24/outline"
import { useAuthStore } from "@/stores/auth-store"

const authStore = useAuthStore()
const route = useRoute()
const router = useRouter()
const message = useMessage()

const form = reactive({ username: "", password: "" })
const isSubmitting = ref(false)

async function handleSubmit() {
  if (isSubmitting.value) return
  if (!form.username || !form.password) {
    message.warning("请输入用户名和密码")
    return
  }
  
  isSubmitting.value = true
  try {
    await authStore.login(form.username, form.password)
    message.success("欢迎回来")
    const next = typeof route.query.next === "string" ? route.query.next : "/"
    await router.replace(next)
  } catch (e) {
    const msg = e instanceof Error ? e.message : "登录失败"
    message.error(msg)
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <div class="flex h-full min-h-screen bg-canvas overflow-hidden relative">
    <!-- Background Accents -->
    <div class="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-brand/5 rounded-full blur-[120px] pointer-events-none" />
    <div class="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-accent/5 rounded-full blur-[120px] pointer-events-none" />

    <!-- Left Side: Visual/Branding -->
    <div class="hidden lg:flex flex-1 items-center justify-center p-12 relative overflow-hidden bg-brand">
      <div 
        class="absolute inset-0 opacity-10" 
        style="background-image: radial-gradient(circle at 2px 2px, white 1px, transparent 0); background-size: 40px 40px;"
      />
      <div 
        class="relative z-10 max-w-lg text-white"
        v-motion
        :initial="{ opacity: 0, x: -50 }"
        :enter="{ opacity: 1, x: 0, transition: { duration: 800 } }"
      >
        <div class="w-16 h-16 bg-white rounded-figma-lg flex items-center justify-center mb-8 shadow-2xl">
          <ArrowRightOnRectangleIcon class="w-8 h-8 text-brand" />
        </div>
        <h1 class="text-5xl font-bold tracking-tight mb-6 leading-tight">
          开启您的智能<br/>编程问答之旅
        </h1>
        <p class="text-xl text-white/80 font-medium leading-relaxed">
        </p>
        
        <div class="mt-12 space-y-4">
          <div class="flex items-center gap-4 bg-white/10 p-4 rounded-figma border border-white/10 backdrop-blur-sm">
            <div class="w-10 h-10 rounded-full bg-white/20 flex items-center justify-center">
              <span class="font-bold text-sm">01</span>
            </div>
            <p class="font-medium text-sm">高效的问答匹配与回答推荐系统</p>
          </div>
          <div class="flex items-center gap-4 bg-white/10 p-4 rounded-figma border border-white/10 backdrop-blur-sm">
            <div class="w-10 h-10 rounded-full bg-white/20 flex items-center justify-center">
              <span class="font-bold text-sm">02</span>
            </div>
            <p class="font-medium text-sm">集成编程领域大模型</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Right Side: Login Form -->
    <div class="flex-1 flex items-center justify-center p-6 md:p-12">
      <div 
        class="w-full max-w-md space-y-8"
        v-motion
        :initial="{ opacity: 0, y: 20 }"
        :enter="{ opacity: 1, y: 0, transition: { duration: 600 } }"
      >
        <div class="text-center lg:text-left">
          <h2 class="text-3xl font-bold text-gray-900 tracking-tight">登录账号</h2>
          <p class="mt-2 text-gray-500 font-medium">输入您的凭据以继续访问</p>
        </div>

        <div class="space-y-6">
          <n-form @submit.prevent="handleSubmit" label-placement="top">
            <n-form-item label="用户名" class="font-medium">
              <n-input 
                v-model:value="form.username" 
                placeholder="请输入您的用户名" 
                size="large"
                class="!rounded-figma !bg-white !border-gray-200"
              >
                <template #prefix>
                  <UserIcon class="w-5 h-5 text-gray-400 mr-2" />
                </template>
              </n-input>
            </n-form-item>
            
            <n-form-item label="密码" class="font-medium">
              <n-input
                v-model:value="form.password"
                type="password"
                show-password-on="click"
                placeholder="请输入您的密码"
                size="large"
                class="!rounded-figma !bg-white !border-gray-200"
                @keyup.enter="handleSubmit"
              >
                <template #prefix>
                  <LockClosedIcon class="w-5 h-5 text-gray-400 mr-2" />
                </template>
              </n-input>
            </n-form-item>

            <div class="flex items-center justify-between mb-4">
              <label class="flex items-center gap-2 cursor-pointer group">
                <input type="checkbox" class="w-4 h-4 rounded border-gray-300 text-brand focus:ring-brand" />
                <span class="text-sm font-medium text-gray-600 group-hover:text-gray-900 transition-colors">记住我</span>
              </label>
              <a href="#" class="text-sm font-bold text-brand hover:underline">忘记密码？</a>
            </div>

            <button 
              type="submit"
              :disabled="isSubmitting"
              class="w-full h-12 bg-brand text-white rounded-figma font-bold text-base flex items-center justify-center gap-2 hover:bg-gray-900 active:scale-[0.98] transition-all disabled:opacity-50 shadow-figma mt-2"
            >
              <span>{{ isSubmitting ? '正在登录...' : '登录' }}</span>
              <ArrowRightIcon v-if="!isSubmitting" class="w-5 h-5" />
            </button>
          </n-form>

          <div class="relative py-4">
            <div class="absolute inset-0 flex items-center"><div class="w-full border-t border-gray-100"></div></div>
            <div class="relative flex justify-center text-xs uppercase tracking-widest"><span class="bg-canvas px-4 text-gray-400 font-bold">或者通过</span></div>
          </div>

          <div class="grid grid-cols-1 gap-4">
            <!-- <button class="flex items-center justify-center gap-3 w-full h-12 bg-white border border-gray-200 rounded-figma font-bold text-sm text-gray-700 hover:bg-gray-50 transition-all shadow-sm">
              <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>
              <span></span>
            </button> -->
          </div>
        </div>

        <p class="text-center text-sm font-medium text-gray-500">
          还没有账号？
          <router-link 
            class="text-brand font-bold hover:underline ml-1" 
            to="/register"
          >
            立即注册
          </router-link>
        </p>
      </div>
    </div>
  </div>
</template>

<style scoped>
:deep(.n-input) {
  --n-border-radius: 8px !important;
  --n-border: 1px solid #E5E7EB !important;
  --n-border-hover: 1px solid #000000 !important;
  --n-border-focus: 1px solid #000000 !important;
  --n-box-shadow-focus: 0 0 0 2px rgba(0,0,0,0.05) !important;
}

:deep(.n-form-item .n-form-item-label) {
  font-size: 0.875rem;
  color: #4B5563;
  margin-bottom: 0.5rem;
}
</style>

