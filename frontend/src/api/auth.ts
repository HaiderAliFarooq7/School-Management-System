import { apiClient } from './client'

export interface LoginResponse {
  access_token: string
  token_type: string
  role: string
  assigned_class_name: string | null
}

export interface MeResponse {
  user_id: number
  username: string
  full_name: string
  role: string
  assigned_class_name: string | null
}

export async function login(username: string, password: string): Promise<LoginResponse> {
  const { data } = await apiClient.post<LoginResponse>('/auth/login', { username, password })
  return data
}

export async function me(): Promise<MeResponse> {
  const { data } = await apiClient.get<MeResponse>('/auth/me')
  return data
}

export async function changePassword(current_password: string, new_password: string): Promise<{ detail: string }> {
  const { data } = await apiClient.post<{ detail: string }>('/auth/change-password', { current_password, new_password })
  return data
}
