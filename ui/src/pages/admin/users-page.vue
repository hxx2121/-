<script setup lang="ts">
import { onMounted, ref, computed } from "vue"
import { 
  UsersIcon, 
  MagnifyingGlassIcon, 
  ArrowPathIcon, 
  CheckIcon, 
  TrashIcon, 
  UserIcon as UserCheckIcon, 
  ShieldCheckIcon, 
  Cog6ToothIcon, 
  EllipsisVerticalIcon,
  EnvelopeIcon,
  CalendarIcon,
  ChevronRightIcon,
  ShieldCheckIcon as ShieldIcon,
  UserIcon
} from "@heroicons/vue/24/outline"
import type { AdminUserItem, AdminUserUpdateRequest } from "@/types/auth"
import { deleteAdminUser, listAdminUsers, patchAdminUser } from "@/api/auth"
import { useMessage, NTag, NInput, NSwitch, NPopconfirm, NAvatar, NScrollbar } from "naive-ui"
import gsap from "gsap"

const message = useMessage()
const rows = ref<AdminUserItem[]>([])
const isLoading = ref(false)
const searchQuery = ref("")

async function refresh() {
  isLoading.value = true
  try {
    rows.value = await listAdminUsers()
  } catch {
    message.error("加载用户列表失败")
  } finally {
    isLoading.value = false
  }
}

async function handleSave(row: AdminUserItem) {
  try {
    const payload: AdminUserUpdateRequest = { role: row.role }
    await patchAdminUser(row.id, payload)
    message.success(`用户 ${row.username} 权限已更新`)
    await refresh()
  } catch {
    message.error("更新失败")
  }
}

async function handleDelete(id: number) {
  try {
    await deleteAdminUser(id)
    message.success("用户已移除")
    await refresh()
  } catch {
    message.error("删除失败")
  }
}

const filteredRows = computed(() => {
  if (!searchQuery.value) return rows.value
  const q = searchQuery.value.toLowerCase()
  return rows.value.filter(r => 
    r.username.toLowerCase().includes(q) || 
    r.role?.toLowerCase().includes(q) ||
    r.id.toString().includes(q)
  )
})

onMounted(() => {
  refresh()
  gsap.from(".page-header", { opacity: 0, y: -20, duration: 0.5, ease: "power2.out" })
})
</script>

<template>
  <div class="max-w-7xl mx-auto space-y-8 pb-12">
    <!-- Header -->
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 page-header">
      <div>
        <h1 class="text-3xl font-bold text-gray-900 tracking-tight flex items-center gap-3">
          <UsersIcon class="w-7 h-7 text-brand" />
          用户与权限管理
        </h1>
        <p class="mt-1 text-gray-500 font-medium">管理系统成员、分配业务角色以及审计访问权限</p>
      </div>
      <div class="flex items-center gap-3">
        <div class="relative">
          <MagnifyingGlassIcon class="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input 
            v-model="searchQuery"
            type="text" 
            placeholder="搜索用户名或角色..." 
            class="pl-10 pr-4 py-2 bg-white border border-gray-200 rounded-figma text-sm w-64 focus:border-brand/30 outline-none transition-all shadow-sm"
          />
        </div>
        <button 
          @click="refresh"
          :class="['p-2 rounded-figma border border-gray-200 bg-white text-gray-500 hover:text-brand hover:border-brand/20 transition-all shadow-sm', isLoading && 'animate-spin text-brand']"
        >
          <ArrowPathIcon class="w-5 h-5" />
        </button>
      </div>
    </div>

    <!-- Quick Stats Summary -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <div class="bg-white p-6 rounded-figma-lg border border-gray-100 shadow-figma flex items-center gap-4">
        <div class="w-12 h-12 bg-brand/5 rounded-figma flex items-center justify-center text-brand">
          <UserCheckIcon class="w-6 h-6" />
        </div>
        <div>
          <p class="text-2xl font-bold text-gray-900 leading-none">{{ rows.length }}</p>
          <p class="text-xs text-gray-400 font-bold uppercase tracking-widest mt-1">注册总数</p>
        </div>
      </div>
      <div class="bg-white p-6 rounded-figma-lg border border-gray-100 shadow-figma flex items-center gap-4">
        <div class="w-12 h-12 bg-purple-50 rounded-figma flex items-center justify-center text-purple-600">
          <ShieldCheckIcon class="w-6 h-6" />
        </div>
        <div>
          <p class="text-2xl font-bold text-gray-900 leading-none">{{ rows.filter(r => r.is_superuser).length }}</p>
          <p class="text-xs text-gray-400 font-bold uppercase tracking-widest mt-1">超级管理员</p>
        </div>
      </div>
      <div class="bg-white p-6 rounded-figma-lg border border-gray-100 shadow-figma flex items-center gap-4">
        <div class="w-12 h-12 bg-emerald-50 rounded-figma flex items-center justify-center text-emerald-600">
          <Cog6ToothIcon class="w-6 h-6" />
        </div>
        <div>
          <p class="text-2xl font-bold text-gray-900 leading-none">{{ rows.filter(r => r.is_staff).length }}</p>
          <p class="text-xs text-gray-400 font-bold uppercase tracking-widest mt-1">工作人员</p>
        </div>
      </div>
    </div>

    <!-- Users List -->
    <div class="bg-white rounded-figma-lg shadow-figma border border-gray-100 overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-left border-collapse">
          <thead>
            <tr class="bg-gray-50/50 border-b border-gray-100">
              <th class="px-6 py-4 text-[10px] font-bold text-gray-400 uppercase tracking-widest">用户 ID</th>
              <th class="px-6 py-4 text-[10px] font-bold text-gray-400 uppercase tracking-widest">基本信息</th>
              <th class="px-6 py-4 text-[10px] font-bold text-gray-400 uppercase tracking-widest">业务角色</th>
              <th class="px-6 py-4 text-[10px] font-bold text-gray-400 uppercase tracking-widest text-center">系统标识</th>
              <th class="px-6 py-4 text-[10px] font-bold text-gray-400 uppercase tracking-widest text-right">操作</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-50">
            <tr 
              v-for="(row, idx) in filteredRows" 
              :key="row.id"
              class="hover:bg-gray-50/30 transition-colors group"
            >
              <td class="px-6 py-4 text-xs font-mono text-gray-400">#{{ row.id }}</td>
              <td class="px-6 py-4">
                <div class="flex items-center gap-3">
                  <n-avatar 
                    round 
                    :size="40" 
                    class="ring-2 ring-transparent group-hover:ring-brand/10 transition-all shadow-sm bg-brand text-white font-bold"
                  >
                    {{ row.username.charAt(0).toUpperCase() }}
                  </n-avatar>
                  <div class="flex flex-col">
                    <span class="text-sm font-bold text-gray-900">{{ row.username }}</span>
                    <div class="flex items-center gap-1 text-[10px] text-gray-400">
                      <EnvelopeIcon class="w-3 h-3" />
                      <span>无邮箱记录</span>
                    </div>
                  </div>
                </div>
              </td>
              <td class="px-6 py-4">
                <div class="flex items-center gap-2 max-w-[160px]">
                  <input 
                    v-model="row.role" 
                    class="bg-transparent border-b border-transparent focus:border-brand/20 outline-none text-xs font-bold text-gray-700 w-full py-1 transition-all"
                    placeholder="未分配角色"
                  />
                </div>
              </td>
              <td class="px-6 py-4">
                <div class="flex items-center justify-center gap-2">
                  <n-tag v-if="row.is_superuser" size="small" :bordered="false" class="!bg-purple-50 !text-purple-600 !text-[10px] font-bold uppercase">Super</n-tag>
                  <n-tag v-if="row.is_staff" size="small" :bordered="false" class="!bg-emerald-50 !text-emerald-600 !text-[10px] font-bold uppercase">Staff</n-tag>
                  <n-tag v-if="!row.is_staff && !row.is_superuser" size="small" :bordered="false" class="!bg-gray-100 !text-gray-400 !text-[10px] font-bold uppercase">User</n-tag>
                </div>
              </td>
              <td class="px-6 py-4">
                <div class="flex items-center justify-end gap-2">
                  <button 
                    @click="handleSave(row)"
                    class="p-2 text-brand hover:bg-brand/5 rounded-figma transition-all"
                    title="保存角色修改"
                  >
                    <CheckIcon class="w-5 h-5" />
                  </button>
                  <n-popconfirm @positive-click="handleDelete(row.id)">
                    <template #trigger>
                      <button class="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-figma transition-all">
                        <TrashIcon class="w-5 h-5" />
                      </button>
                    </template>
                    确认永久注销并删除该用户及其所有关联数据吗？
                  </n-popconfirm>
                </div>
              </td>
            </tr>
            <tr v-if="filteredRows.length === 0 && !isLoading">
              <td colspan="5" class="px-6 py-20 text-center text-gray-400 font-medium italic">
                没有找到匹配的用户
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<style scoped>
:deep(.n-tag) {
  border-radius: 4px !important;
}
</style>

