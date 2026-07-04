import { apiClient } from './client'

// --- Parent management ---

export interface ParentAccount {
  parent_id: number
  mobile_number: string
  full_name: string | null
  is_active: boolean
  must_change_password: boolean
  device_count: number
  student_count: number
  created_at: string
  last_login_at: string | null
}

export async function listParents(): Promise<ParentAccount[]> {
  const { data } = await apiClient.get<ParentAccount[]>('/admin/parents')
  return data
}

export async function createParent(payload: {
  mobile_number: string
  full_name?: string | null
  password?: string | null
}): Promise<ParentAccount> {
  const { data } = await apiClient.post<ParentAccount>('/admin/parents', payload)
  return data
}

export async function updateParent(
  parentId: number,
  payload: { full_name?: string | null; is_active?: boolean },
): Promise<ParentAccount> {
  const { data } = await apiClient.patch<ParentAccount>(`/admin/parents/${parentId}`, payload)
  return data
}

export async function resetParentPassword(parentId: number): Promise<{ detail: string }> {
  const { data } = await apiClient.post<{ detail: string }>(`/admin/parents/${parentId}/reset-password`)
  return data
}

export async function syncParentAccounts(): Promise<{ created: number; skipped: number; detail: string }> {
  const { data } = await apiClient.post<{ created: number; skipped: number; detail: string }>(
    '/admin/parents/sync',
  )
  return data
}

// --- Device management ---

export interface ParentDevice {
  device_id: number
  parent_id: number
  platform: string
  is_active: boolean
  created_at: string
  last_seen_at: string
}

export async function listParentDevices(parentId: number): Promise<ParentDevice[]> {
  const { data } = await apiClient.get<ParentDevice[]>(`/admin/parents/${parentId}/devices`)
  return data
}

export async function listAllDevices(): Promise<ParentDevice[]> {
  const { data } = await apiClient.get<ParentDevice[]>('/admin/parents/devices/all')
  return data
}

// --- Notification center ---

export type NotifType = 'absent' | 'fee_reminder' | 'announcement'
export type Audience = 'student' | 'class' | 'school'

export interface NotificationLog {
  log_id: number
  notif_type: NotifType
  audience: Audience
  title: string
  body: string
  student_id: number | null
  class_name: string | null
  sent_by_user_id: number | null
  recipients_count: number
  delivered_count: number
  failed_count: number
  created_at: string
}

export async function sendNotification(payload: {
  notif_type: NotifType
  audience: Audience
  title: string
  body: string
  student_id?: number | null
  class_name?: string | null
}): Promise<NotificationLog> {
  const { data } = await apiClient.post<NotificationLog>('/admin/notifications/send', payload)
  return data
}

export async function listNotificationLog(limit = 100): Promise<NotificationLog[]> {
  const { data } = await apiClient.get<NotificationLog[]>('/admin/notifications/log', { params: { limit } })
  return data
}
