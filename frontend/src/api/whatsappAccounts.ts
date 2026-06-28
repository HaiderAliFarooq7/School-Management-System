import { apiClient } from './client'
import type { WhatsAppConnectionResult, WhatsAppTestMessageResult } from './communication'

export interface WhatsAppAccount {
  id: number
  name: string
  business_account_id: string | null
  phone_number_id: string | null
  graph_version: string | null
  use_templates: boolean
  enabled: boolean
  is_default: boolean
  has_access_token: boolean
  has_webhook_verify_token: boolean
  has_webhook_secret: boolean
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

export interface WhatsAppAccountCreate {
  name: string
  business_account_id?: string | null
  phone_number_id: string
  access_token: string
  graph_version?: string
  use_templates?: boolean
  webhook_verify_token?: string | null
  webhook_secret?: string | null
  enabled?: boolean
}

export interface WhatsAppAccountUpdate {
  name?: string
  business_account_id?: string | null
  phone_number_id?: string
  access_token?: string | null // blank/omitted keeps the existing token
  graph_version?: string
  use_templates?: boolean
  webhook_verify_token?: string | null
  webhook_secret?: string | null
  enabled?: boolean
}

export interface WhatsAppAccountTestDraft {
  access_token: string
  phone_number_id: string
  business_account_id?: string | null
  graph_version?: string
}

export async function listWhatsAppAccounts(): Promise<WhatsAppAccount[]> {
  const { data } = await apiClient.get<WhatsAppAccount[]>('/communication/whatsapp-accounts')
  return data
}

export async function createWhatsAppAccount(payload: WhatsAppAccountCreate): Promise<WhatsAppAccount> {
  const { data } = await apiClient.post<WhatsAppAccount>('/communication/whatsapp-accounts', payload)
  return data
}

export async function updateWhatsAppAccount(id: number, payload: WhatsAppAccountUpdate): Promise<WhatsAppAccount> {
  const { data } = await apiClient.put<WhatsAppAccount>(`/communication/whatsapp-accounts/${id}`, payload)
  return data
}

export async function deleteWhatsAppAccount(id: number): Promise<void> {
  await apiClient.delete(`/communication/whatsapp-accounts/${id}`)
}

export async function setDefaultWhatsAppAccount(id: number): Promise<WhatsAppAccount> {
  const { data } = await apiClient.post<WhatsAppAccount>(`/communication/whatsapp-accounts/${id}/set-default`)
  return data
}

export async function testWhatsAppAccount(id: number): Promise<WhatsAppConnectionResult> {
  const { data } = await apiClient.post<WhatsAppConnectionResult>(`/communication/whatsapp-accounts/${id}/test`)
  return data
}

export async function testWhatsAppAccountDraft(payload: WhatsAppAccountTestDraft): Promise<WhatsAppConnectionResult> {
  const { data } = await apiClient.post<WhatsAppConnectionResult>('/communication/whatsapp-accounts/test-draft', payload)
  return data
}

export async function sendWhatsAppAccountTestMessage(
  id: number, recipient: string, template_name = 'hello_world', language_code = 'en_US',
): Promise<WhatsAppTestMessageResult> {
  const { data } = await apiClient.post<WhatsAppTestMessageResult>(
    `/communication/whatsapp-accounts/${id}/send-test-message`, { recipient, template_name, language_code },
  )
  return data
}
