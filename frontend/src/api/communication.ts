import { apiClient } from './client'

export interface Provider {
  id: number
  name: string
  type: string
  enabled: boolean
  configuration_json: Record<string, string>
  business_name: string | null
  phone_number_display: string | null
  api_version: string | null
  last_tested_at: string | null
  last_test_status: 'connected' | 'disconnected' | null
  last_error: string | null
  messages_sent_today: number
  created_at: string
  updated_at: string
}

export interface ProviderUpdate {
  name?: string
  enabled?: boolean
  configuration_json?: Record<string, string>
}

export interface Template {
  id: number
  name: string
  type: string
  message: string
  variables: string[]
  enabled: boolean
  whatsapp_template_name: string | null
  created_at: string
  updated_at: string
}

export interface TemplateUpdate {
  message?: string
  variables?: string[]
  enabled?: boolean
  whatsapp_template_name?: string | null
}

export type NotificationStatus = 'pending' | 'processing' | 'sent' | 'failed' | 'cancelled'
export type ProviderType = 'sms' | 'whatsapp'
export type NotificationCategory = 'custom' | 'attendance_absent' | 'fee_reminder'

export interface QueueCreate {
  student_id?: number | null
  recipient_name?: string | null
  provider_type: ProviderType
  notification_type: NotificationCategory
  recipient: string
  message: string
}

export interface QueueEntry {
  id: number
  student_id: number | null
  recipient_name: string | null
  provider_type: string
  notification_type: string
  recipient: string
  message: string
  status: NotificationStatus
  retry_count: number
  scheduled_at: string | null
  sent_at: string | null
  error_message: string | null
  provider_response: string | null
  created_by: number | null
  created_at: string
  updated_at: string
}

export interface HistoryEntry {
  log_id: number
  student_id: number | null
  provider: string | null
  recipient: string | null
  notification_type: string
  message: string | null
  status: string
  response: string | null
  error: string | null
  template: string | null
  meta_message_id: string | null
  http_status: number | null
  sent_at: string | null
  created_at: string
}

export interface HistoryFilters {
  student_id?: number
  phone?: string
  status_filter?: string
  date_from?: string
  date_to?: string
}

export async function listProviders(): Promise<Provider[]> {
  const { data } = await apiClient.get<Provider[]>('/communication/providers')
  return data
}

export async function updateProvider(id: number, payload: ProviderUpdate): Promise<Provider> {
  const { data } = await apiClient.put<Provider>(`/communication/providers/${id}`, payload)
  return data
}

export async function testProvider(providerId: number): Promise<{ status: string; error?: string; provider_response?: unknown }> {
  const { data } = await apiClient.post('/communication/test-provider', { provider_id: providerId })
  return data
}

// WhatsApp accounts are now multi-account (see ../api/whatsappAccounts.ts) —
// these two result shapes are still shared by both the saved-account and
// draft test-connection endpoints.
export interface WhatsAppConnectionResult {
  status: 'connected' | 'disconnected'
  business_name: string | null
  phone_number: string | null
  api_version: string | null
  quality_rating: string | null
  error: string | null
}

export interface WhatsAppTestMessageResult {
  status: 'sent' | 'failed'
  message_id: string | null
  http_status: number | null
  error: string | null
  provider_response: Record<string, unknown> | null
}

export async function listTemplates(): Promise<Template[]> {
  const { data } = await apiClient.get<Template[]>('/communication/templates')
  return data
}

export async function updateTemplate(id: number, payload: TemplateUpdate): Promise<Template> {
  const { data } = await apiClient.put<Template>(`/communication/templates/${id}`, payload)
  return data
}

export async function listQueue(statusFilter?: string): Promise<QueueEntry[]> {
  const { data } = await apiClient.get<QueueEntry[]>('/communication/queue', { params: { status_filter: statusFilter } })
  return data
}

export async function createQueueEntry(payload: QueueCreate): Promise<QueueEntry> {
  const { data } = await apiClient.post<QueueEntry>('/communication/queue', payload)
  return data
}

export async function createQueueEntriesBulk(payload: QueueCreate[]): Promise<QueueEntry[]> {
  const { data } = await apiClient.post<QueueEntry[]>('/communication/queue/bulk', payload)
  return data
}

export async function getHistory(filters: HistoryFilters = {}): Promise<HistoryEntry[]> {
  const { data } = await apiClient.get<HistoryEntry[]>('/communication/history', { params: filters })
  return data
}

export interface AnalyticsDayCount {
  [key: string]: string | number
  day: string
  sent: number
  failed: number
}

export interface Analytics {
  pending: number
  processing: number
  sent_today: number
  failed_today: number
  by_day: AnalyticsDayCount[]
}

export async function getCommunicationAnalytics(): Promise<Analytics> {
  const { data } = await apiClient.get<Analytics>('/communication/analytics')
  return data
}

/** Replaces {{var}} placeholders client-side, mirroring the backend's
 * render_template, so Preview shows exactly what will be sent. */
export function renderTemplate(message: string, variables: Record<string, string>): string {
  return message.replace(/\{\{\s*(\w+)\s*\}\}/g, (_match, key: string) => variables[key] ?? '')
}
