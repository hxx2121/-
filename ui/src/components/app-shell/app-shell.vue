<script setup lang="ts">
import { computed, ref, onMounted } from "vue"
import { useRoute, useRouter } from "vue-router"
import { useAuthStore } from "@/stores/auth-store"
import { 
  NLayout, 
  NLayoutSider, 
  NLayoutHeader, 
  NLayoutContent, 
  NDropdown, 
  NAvatar, 
  NIcon, 
  NTooltip 
} from "naive-ui"
import { 
  HomeIcon, 
  ArrowRightOnRectangleIcon, 
  UserIcon, 
  ChevronLeftIcon,
  ChevronRightIcon,
  ChatBubbleLeftRightIcon,
  MagnifyingGlassIcon,
  CircleStackIcon,
  RectangleGroupIcon,
  SparklesIcon,
} from "@heroicons/vue/24/outline"

const authStore = useAuthStore()
const route = useRoute()
const router = useRouter()

const collapsed = ref(false)

const username = computed(() => authStore.me?.username || "访客")
const isAdmin = computed(() => authStore.isAdmin)

onMounted(async () => {
  if (authStore.isAuthenticated && !authStore.me) {
    await authStore.refreshMe()
  }
})

const activeKey = computed(() => route.name as string)

const menuGroups = computed(() => {
  const groups = [
    {
      title: "概览",
      items: [
        { label: "首页", name: "home", icon: HomeIcon },
      ]
    },
    {
      title: "问答与推荐",
      items: [
        { label: "推荐仪表盘", name: "qa-dashboard", icon: ChatBubbleLeftRightIcon },
        { label: "数据集浏览", name: "qa-dataset", icon: CircleStackIcon },
        { label: "编程问答", name: "qa-chat", icon: ChatBubbleLeftRightIcon },
      ]
    },
  ]

  if (isAdmin.value) {
    groups.push({
      title: "系统配置",
      items: [
        { label: "提示词模板", name: "admin-prompts", icon: RectangleGroupIcon },
      ]
    })
  }

  return groups
})

const userOptions = [
  {
    label: "退出登录",
    key: "logout",
  }
]

async function handleUserSelect(key: string) {
  if (key === "logout") {
    await authStore.logout()
    await router.replace({ name: "login" })
  }
}

const navigateTo = (name: string) => {
  router.push({ name })
}
</script>

<template>
  <n-layout has-sider class="h-full bg-canvas">
    <!-- Sidebar -->
    <n-layout-sider
      bordered
      collapse-mode="width"
      :collapsed-width="80"
      :width="260"
      :collapsed="collapsed"
      class="h-full !bg-canvas-sidebar border-r border-gray-200 transition-all duration-300 ease-in-out"
    >
      <div class="flex flex-col h-full">
        <!-- Logo Area -->
        <div class="h-20 flex items-center px-6 mb-4">
          <div 
            class="w-10 h-10 bg-brand rounded-figma flex items-center justify-center text-white shrink-0 shadow-figma"
            v-motion
            :initial="{ scale: 0.8, opacity: 0 }"
            :enter="{ scale: 1, opacity: 1 }"
          >
            <SparklesIcon class="w-5 h-5" stroke-width="2.5" />
          </div>
          <span 
            v-if="!collapsed" 
            class="ml-3 text-lg font-bold tracking-tight text-brand animate-fade-in"
          >
            编程问答匹配与推荐系统
          </span>
        </div>

        <!-- Navigation -->
        <div class="flex-1 overflow-y-auto px-3 space-y-6 pb-6 custom-scrollbar">
          <div v-for="group in menuGroups" :key="group.title" class="space-y-1">
            <p 
              v-if="!collapsed" 
              class="px-3 text-[11px] font-bold text-gray-400 uppercase tracking-widest mb-2"
            >
              {{ group.title }}
            </p>
            <div class="space-y-1">
              <button
                v-for="item in group.items"
                :key="item.name"
                @click="navigateTo(item.name)"
                :class="[
                  'w-full flex items-center px-3 py-2.5 rounded-figma transition-all duration-200 group relative',
                  activeKey === item.name 
                    ? 'bg-gray-100 text-brand' 
                    : 'text-gray-500 hover:bg-gray-50 hover:text-gray-900'
                ]"
              >
                <div 
                  class="flex items-center justify-center w-6 h-6 shrink-0"
                  :class="activeKey === item.name ? 'text-brand' : 'text-gray-400 group-hover:text-gray-600'"
                >
                  <component :is="item.icon" class="w-5 h-5" :stroke-width="activeKey === item.name ? 2.5 : 2" />
                </div>
                <span 
                  v-if="!collapsed" 
                  class="ml-3 text-sm font-medium whitespace-nowrap overflow-hidden transition-all duration-300"
                >
                  {{ item.label }}
                </span>
                
                <!-- Active Indicator -->
                <div 
                  v-if="activeKey === item.name"
                  class="absolute left-0 w-1 h-6 bg-brand rounded-r-full"
                  v-motion
                  :initial="{ scaleY: 0 }"
                  :enter="{ scaleY: 1 }"
                />
              </button>
            </div>
          </div>
        </div>

        <!-- Sider Toggle -->
        <div class="p-4 border-t border-gray-100">
          <button 
            @click="collapsed = !collapsed"
            class="w-full flex items-center justify-center py-2 text-gray-400 hover:text-gray-600 hover:bg-gray-50 rounded-figma transition-colors"
          >
            <ChevronLeftIcon v-if="!collapsed" class="w-5 h-5" />
            <ChevronRightIcon v-else class="w-5 h-5" />
          </button>
        </div>
      </div>
    </n-layout-sider>

    <n-layout class="h-full bg-canvas">
      <!-- Header -->
      <n-layout-header 
        class="h-16 flex items-center justify-between px-8 !bg-canvas border-b border-gray-100"
      >
        <div class="flex items-center gap-4">
          <n-tooltip trigger="hover">
            <template #trigger>
              <button 
                @click="collapsed = !collapsed"
                class="p-2 rounded-figma border border-gray-200 bg-white text-gray-500 hover:text-brand hover:border-brand/30 hover:bg-brand/5 transition-all shadow-sm"
              >
                <ChevronLeftIcon v-if="!collapsed" class="w-4 h-4" />
                <ChevronRightIcon v-else class="w-4 h-4" />
              </button>
            </template>
            <span>{{ collapsed ? "展开侧边栏" : "收起侧边栏" }}</span>
          </n-tooltip>
          <div class="relative group">
            <MagnifyingGlassIcon class="w-[18px] h-[18px] absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 group-focus-within:text-brand transition-colors" />
            <input 
              type="text" 
              placeholder="搜索任何内容..." 
              class="pl-10 pr-4 py-2 bg-gray-100/50 border-transparent focus:bg-white focus:border-brand/20 border rounded-figma text-sm w-64 transition-all outline-none"
            />
          </div>
        </div>

        <div class="flex items-center gap-6">
          <div class="h-4 w-[1px] bg-gray-200 mx-2" />
          
          <n-dropdown :options="userOptions" @select="handleUserSelect" trigger="click">
            <div class="flex items-center gap-3 cursor-pointer group">
              <div class="text-right hidden sm:block">
                <p class="text-sm font-bold text-gray-900 leading-none mb-1">{{ username }}</p>
                <p class="text-[11px] text-gray-500 font-medium uppercase tracking-tight">{{ isAdmin ? '管理员' : '标准用户' }}</p>
              </div>
              <div class="relative">
                <n-avatar 
                  round 
                  :size="40" 
                  class="ring-2 ring-transparent group-hover:ring-brand/10 transition-all shadow-sm bg-brand text-white font-bold"
                >
                  {{ username.charAt(0).toUpperCase() }}
                </n-avatar>
                <div class="absolute bottom-0 right-0 w-3 h-3 bg-green-500 border-2 border-white rounded-full" />
              </div>
            </div>
          </n-dropdown>
        </div>
      </n-layout-header>
      
      <!-- Content Area -->
      <n-layout-content 
        content-style="padding: 0;" 
        class="!bg-canvas h-[calc(100vh-64px)] relative"
      >
        <div class="h-full w-full overflow-y-auto custom-scrollbar p-8">
          <Suspense>
            <router-view v-slot="{ Component }">
              <transition
                enter-active-class="transition duration-300 ease-out"
                enter-from-class="transform translate-y-4 opacity-0"
                enter-to-class="transform translate-y-0 opacity-100"
                leave-active-class="transition duration-200 ease-in"
                leave-from-class="transform translate-y-0 opacity-100"
                leave-to-class="transform translate-y-4 opacity-0"
                mode="out-in"
              >
                <component :is="Component" />
              </transition>
            </router-view>
            <template #fallback>
              <div class="flex flex-col items-center justify-center h-full space-y-4">
                <div class="w-12 h-12 border-4 border-brand border-t-transparent rounded-full animate-spin" />
                <p class="text-sm font-medium text-gray-400">正在加载模块...</p>
              </div>
            </template>
          </Suspense>
        </div>
      </n-layout-content>
    </n-layout>
  </n-layout>
</template>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #E5E7EB;
  border-radius: 10px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #D1D5DB;
}

:deep(.n-layout-sider-scroll-container) {
  overflow: hidden !important;
}

.animate-fade-in {
  animation: fadeIn 0.3s ease-out forwards;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateX(-10px); }
  to { opacity: 1; transform: translateX(0); }
}
</style>
