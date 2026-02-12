import type { UserFileItem } from "@/types/utils"
import { downloadBlob, requestR, requestRForm } from "@/api/http"

export async function uploadUserFile(file: File): Promise<UserFileItem> {
  const fd = new FormData()
  fd.append("file", file)
  return requestRForm<UserFileItem>("/api/utils/files/upload/", "POST", fd)
}

export async function listUserFiles(): Promise<UserFileItem[]> {
  return requestR<UserFileItem[]>("/api/utils/files/list/", { method: "GET" })
}

export async function deleteUserFile(fileId: number): Promise<null> {
  return requestR<null>(`/api/utils/files/${fileId}/`, { method: "DELETE" })
}

export async function downloadUserFile(fileId: number): Promise<{ blob: Blob; filename: string }> {
  return downloadBlob(`/api/utils/files/${fileId}/download/`)
}

export async function listAdminFiles(): Promise<UserFileItem[]> {
  return requestR<UserFileItem[]>("/api/utils/admin/files/list/", { method: "GET" })
}

export async function deleteAdminFile(fileId: number): Promise<null> {
  return requestR<null>(`/api/utils/admin/files/${fileId}/`, { method: "DELETE" })
}

