import type { AdminUserItem, AdminUserUpdateRequest, AuthLoginRequest, AuthLoginResponse, AuthRegisterRequest, AuthRegisterResponse, UserMe } from "@/types/auth"
import { requestR, requestRJson } from "@/api/http"

export async function register(payload: AuthRegisterRequest): Promise<AuthRegisterResponse> {
  return requestRJson<AuthRegisterResponse>("/api/auth/register/", "POST", payload)
}

export async function login(payload: AuthLoginRequest): Promise<AuthLoginResponse> {
  return requestRJson<AuthLoginResponse>("/api/auth/login/", "POST", payload)
}

export async function logout(): Promise<null> {
  return requestR<null>("/api/auth/logout/", { method: "POST" })
}

export async function getMe(): Promise<UserMe> {
  return requestR<UserMe>("/api/auth/me/", { method: "GET" })
}

export async function patchMe(payload: Partial<AdminUserUpdateRequest>): Promise<UserMe> {
  return requestRJson<UserMe>("/api/auth/me/", "PATCH", payload)
}

export async function listAdminUsers(): Promise<AdminUserItem[]> {
  return requestR<AdminUserItem[]>("/api/auth/admin/users/", { method: "GET" })
}

export async function patchAdminUser(userId: number, payload: AdminUserUpdateRequest): Promise<UserMe> {
  return requestRJson<UserMe>(`/api/auth/admin/users/${userId}/`, "PATCH", payload)
}

export async function deleteAdminUser(userId: number): Promise<null> {
  return requestR<null>(`/api/auth/admin/users/${userId}/`, { method: "DELETE" })
}

