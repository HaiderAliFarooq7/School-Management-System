import { apiClient } from './client'

export interface CollectorRow {
  actor_user_id: number | null
  actor_username: string
  actor_role: string
  fee_collected: number
  charge_collected: number
  total_collected: number
  payment_count: number
}

export interface CollectionsSummary {
  rows: CollectorRow[]
  fee_collected: number
  charge_collected: number
  total_collected: number
  payment_count: number
}

export interface PaymentDetailRow {
  id: number
  created_at: string
  actor_user_id: number | null
  actor_username: string
  student_id: number | null
  student_name: string
  target_type: string        // fee_voucher | extra_charge
  label: string
  amount: number | null
}

export interface ReconciliationRow {
  actor_user_id: number | null
  actor_username: string
  actor_role: string
  total_collected: number
  total_handed_over: number
  balance: number
}

export interface Handover {
  id: number
  created_at: string
  accountant_user_id: number | null
  accountant_username: string
  amount: number
  handover_date: string      // YYYY-MM-DD
  note: string | null
  recorded_by_username: string
}

interface DateRange {
  date_from?: string
  date_to?: string
}

export async function getCollectionsSummary(params: DateRange): Promise<CollectionsSummary> {
  const { data } = await apiClient.get<CollectionsSummary>('/collections/summary', { params })
  return data
}

export async function getCollectionsDetail(
  params: DateRange & { actor_user_id?: number | null; limit?: number },
): Promise<PaymentDetailRow[]> {
  const { data } = await apiClient.get<PaymentDetailRow[]>('/collections/detail', {
    params: {
      actor_user_id: params.actor_user_id ?? undefined,
      date_from: params.date_from,
      date_to: params.date_to,
      limit: params.limit,
    },
  })
  return data
}

export async function getReconciliation(): Promise<ReconciliationRow[]> {
  const { data } = await apiClient.get<ReconciliationRow[]>('/collections/reconciliation')
  return data
}

export async function listHandovers(
  params: DateRange & { actor_user_id?: number | null } = {},
): Promise<Handover[]> {
  const { data } = await apiClient.get<Handover[]>('/collections/handovers', {
    params: {
      actor_user_id: params.actor_user_id ?? undefined,
      date_from: params.date_from,
      date_to: params.date_to,
    },
  })
  return data
}

export async function createHandover(payload: {
  accountant_user_id: number
  amount: number
  handover_date?: string
  note?: string | null
}): Promise<Handover> {
  const { data } = await apiClient.post<Handover>('/collections/handovers', payload)
  return data
}

export async function deleteHandover(handoverId: number): Promise<void> {
  await apiClient.delete(`/collections/handovers/${handoverId}`)
}
