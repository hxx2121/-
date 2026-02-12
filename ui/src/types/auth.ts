export interface UserMe {
  id: number
  username: string
  role: string
  is_admin: boolean
}

export interface AuthLoginRequest {
  username: string
  password: string
}

export interface AuthLoginResponse extends UserMe {
  token: string
}

export interface AuthRegisterRequest {
  username: string
  password: string
}

export interface AuthRegisterResponse extends UserMe {
  token: string
}

export interface AdminUserItem {
  id: number
  username: string
  is_staff: boolean
  is_superuser: boolean
  role: string
  date_joined: string
}

export interface AdminUserUpdateRequest {
  username?: string
  password?: string
  role?: string
}

