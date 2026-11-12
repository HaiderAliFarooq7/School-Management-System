import { apiClient } from './client'

export interface Charge {
  charge_id: number
  student_id: number
  description: string
  amount: number
  paid_amount: number
  remaining_amount: number
  discount_amount: number
  discount_reason: string | null
  status: string
  created_at: string
}

export async function getStudentCharges(studentId: number): Promise<Charge[]> {
  const { data } = await apiClient.get<Charge[]>(`/students/${studentId}/charges`)
  return data
}

export async function addCharge(student_id: number, description: string, amount: number): Promise<Charge> {
  const { data } = await apiClient.post<Charge>('/extra-charges', { student_id, description, amount })
  return data
}

export async function payCharge(chargeId: number, amount: number): Promise<Charge> {
  const { data } = await apiClient.post<Charge>(`/extra-charges/${chargeId}/pay`, { amount })
  return data
}

export async function deleteCharge(chargeId: number): Promise<void> {
  await apiClient.delete(`/extra-charges/${chargeId}`)
}

export async function bulkAddCharge(class_names: string[], description: string, amount: number): Promise<Charge[]> {
  const { data } = await apiClient.post<Charge[]>('/extra-charges/bulk', { class_names, description, amount })
  return data
}

export async function applyChargeDiscount(chargeId: number, amount: number, reason: string): Promise<Charge> {
  const { data } = await apiClient.post<Charge>(`/extra-charges/${chargeId}/discount`, { amount, reason })
  return data
}

export interface BulkDeleteChargesResult {
  deleted: number
  skipped: { charge_id: number; reason: string }[]
}

export async function bulkDeleteCharges(charge_ids: number[]): Promise<BulkDeleteChargesResult> {
  const { data } = await apiClient.post<BulkDeleteChargesResult>('/extra-charges/bulk-delete', { charge_ids })
  return data
}

export interface ChargeGroup {
  description: string
  count: number
  total: number
}

export async function getChargeGroups(class_names: string[]): Promise<ChargeGroup[]> {
  const params = class_names.length ? { class_names: class_names.join(',') } : undefined
  const { data } = await apiClient.get<ChargeGroup[]>('/extra-charges/groups', { params })
  return data
}

export async function bulkDeleteChargesByFilter(
  class_names: string[],
  description: string | null,
): Promise<BulkDeleteChargesResult> {
  const { data } = await apiClient.post<BulkDeleteChargesResult>('/extra-charges/bulk-delete-by-filter', {
    class_names,
    description,
  })
  return data
}

export interface ChargeEditPayload {
  description: string
  amount: number
  paid_amount: number
  discount_amount: number
  discount_reason: string | null
}

export async function editCharge(chargeId: number, payload: ChargeEditPayload): Promise<Charge> {
  const { data } = await apiClient.put<Charge>(`/extra-charges/${chargeId}`, payload)
  return data
}
