import { apiClient } from './client'

export interface School {
  school_id: number
  name: string
  address: string
  phone: string
  logo_path: string | null
  bank_name: string
  account_title: string
  account_number: string
  iban: string
  fee_due_day: number
  challan_note: string | null
  sms_enabled: boolean
  sms_gateway: string
  sms_api_key: string
  sms_api_secret: string
  sms_sender_id: string
  email_enabled: boolean
  smtp_server: string
  smtp_port: number
  smtp_email: string
  smtp_password: string
  auto_notify_absent: boolean
}

export async function getSchool(): Promise<School> {
  const { data } = await apiClient.get<School>('/school')
  return data
}

export async function updateSchool(payload: Partial<School>): Promise<School> {
  const { data } = await apiClient.put<School>('/school', payload)
  return data
}

export async function updateNotificationSettings(payload: Partial<School>): Promise<School> {
  const { data } = await apiClient.put<School>('/school/notification-settings', payload)
  return data
}

export async function updateCommunicationSettings(payload: { auto_notify_absent: boolean }): Promise<School> {
  const { data } = await apiClient.put<School>('/school/communication-settings', payload)
  return data
}

export async function uploadLogo(file: File): Promise<School> {
  const formData = new FormData()
  formData.append('file', file)
  const { data } = await apiClient.post<School>('/school/logo', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}
