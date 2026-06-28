import { apiClient } from './client'

export interface User {
  user_id: number
  username: string
  full_name: string
  role_name: string
  assigned_class_name: string | null
  is_active: boolean
  created_at: string
  last_login_at: string | null
}

export async function listUsers(): Promise<User[]> {
  const { data } = await apiClient.get<User[]>('/users')
  return data
}

export async function createUser(payload: {
  username: string
  full_name: string
  password: string
  role_name: string
  assigned_class_name?: string | null
}): Promise<User> {
  const { data } = await apiClient.post<User>('/users', payload)
  return data
}

export interface UserUpdatePayload {
  username?: string
  full_name?: string
  role_name?: string
  assigned_class_name?: string | null
  password?: string
}

export async function updateUser(userId: number, payload: UserUpdatePayload): Promise<User> {
  const { data } = await apiClient.put<User>(`/users/${userId}`, payload)
  return data
}

export async function deactivateUser(userId: number): Promise<User> {
  const { data } = await apiClient.patch<User>(`/users/${userId}/deactivate`)
  return data
}

export async function activateUser(userId: number): Promise<User> {
  const { data } = await apiClient.patch<User>(`/users/${userId}/activate`)
  return data
}

export async function resetUserPassword(userId: number, newPassword: string): Promise<void> {
  await apiClient.post(`/users/${userId}/reset-password`, { new_password: newPassword })
}

export async function deleteUser(userId: number): Promise<void> {
  await apiClient.delete(`/users/${userId}`)
}
