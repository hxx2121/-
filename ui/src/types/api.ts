export interface ApiResponse<T> {
  code: number
  msg: string
  data: T
}

export interface ApiError extends Error {
  httpStatus: number
  code: number
  data?: unknown
}

