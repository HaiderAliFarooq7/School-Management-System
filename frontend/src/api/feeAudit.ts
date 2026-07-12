import { apiClient } from './client'

export interface FeeAuditEntry {
  id: number
  created_at: string
  actor_username: string
  actor_role: string
  action: string          // payment | discount | edit | delete | generate
  target_type: string     // fee_voucher | extra_charge
  student_id: number | null
  student_name: string
  label: string
  amount: number | null
  reason: string | null
  note: string | null
}

export async function listFeeAudit(
  params: { limit?: number; action?: string } = {},
): Promise<FeeAuditEntry[]> {
  const { data } = await apiClient.get<FeeAuditEntry[]>('/fee-audit', { params })
  return data
}
