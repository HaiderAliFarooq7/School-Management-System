import { apiClient, downloadFile } from './client'

export interface Voucher {
  voucher_id: number
  student_id: number
  fee_month: string
  fee_month_sort: string
  total_amount: number
  paid_amount: number
  discount_amount: number
  discount_reason: string | null
  remaining: number
  status: string
}

export interface VoucherWithStudent extends Voucher {
  student_name: string
  registration_no: string
}

export async function generateVoucher(student_id: number, year: number, month: number, total_amount: number): Promise<Voucher> {
  const { data } = await apiClient.post<Voucher>('/fee-vouchers/generate', { student_id, year, month, total_amount })
  return data
}

export async function bulkGenerate(class_names: string[], year: number, month: number): Promise<Voucher[]> {
  const { data } = await apiClient.post<Voucher[]>('/fee-vouchers/bulk-generate', { class_names, year, month })
  return data
}

export async function payVoucher(voucherId: number, amount: number): Promise<Voucher> {
  const { data } = await apiClient.post<Voucher>(`/fee-vouchers/${voucherId}/pay`, { amount })
  return data
}

export async function applyVoucherDiscount(voucherId: number, amount: number, reason: string): Promise<Voucher> {
  const { data } = await apiClient.post<Voucher>(`/fee-vouchers/${voucherId}/discount`, { amount, reason })
  return data
}

export async function bulkPay(class_name: string, year: number, month: number, amount_per_student: number): Promise<Voucher[]> {
  const { data } = await apiClient.post<Voucher[]>('/fee-vouchers/bulk-pay', { class_name, year, month, amount_per_student })
  return data
}

export async function deleteVoucher(voucherId: number): Promise<void> {
  await apiClient.delete(`/fee-vouchers/${voucherId}`)
}

export interface VoucherEditPayload {
  total_amount: number
  paid_amount: number
  discount_amount: number
  discount_reason: string | null
}

export async function editVoucher(voucherId: number, payload: VoucherEditPayload): Promise<Voucher> {
  const { data } = await apiClient.put<Voucher>(`/fee-vouchers/${voucherId}`, payload)
  return data
}

export async function getStudentVouchers(studentId: number): Promise<Voucher[]> {
  const { data } = await apiClient.get<Voucher[]>(`/students/${studentId}/vouchers`)
  return data
}

export interface VoucherSearchResult {
  voucher_id: number
  student_id: number
  registration_no: string
  name: string
  class_name: string
  phone: string | null
  cnic: string | null
  fee_month: string
  total_amount: number
  paid_amount: number
  discount_amount: number
  status: string
  other_pending: number
}

export async function searchVouchers(query: string): Promise<VoucherSearchResult[]> {
  const { data } = await apiClient.get<VoucherSearchResult[]>('/fee-vouchers/search', { params: { query } })
  return data
}

export interface VoucherFilterRow extends VoucherWithStudent {
  is_overdue: boolean
  charges_pending: number
}

export interface VoucherFilterParams {
  class_names?: string[]
  status_filter?: string[]
  year?: number | null
  month?: number | null
  overdue_only?: boolean
  charges_pending_only?: boolean
}

export async function filterVouchers(params: VoucherFilterParams): Promise<VoucherFilterRow[]> {
  const { data } = await apiClient.get<VoucherFilterRow[]>('/fee-vouchers/filter', {
    params: {
      class_names: params.class_names?.join(',') ?? '',
      status_filter: params.status_filter?.join(',') ?? '',
      year: params.year ?? undefined,
      month: params.month ?? undefined,
      overdue_only: params.overdue_only ?? false,
      charges_pending_only: params.charges_pending_only ?? false,
    },
  })
  return data
}

export interface BulkDeleteResult {
  deleted: number
  skipped: { voucher_id: number; reason: string }[]
}

export async function bulkDeleteVouchers(voucher_ids: number[]): Promise<BulkDeleteResult> {
  const { data } = await apiClient.post<BulkDeleteResult>('/fee-vouchers/bulk-delete', { voucher_ids })
  return data
}

export async function downloadVoucherPdf(voucherId: number) {
  await downloadFile(`/fee-vouchers/${voucherId}/pdf`, {}, `voucher_${voucherId}.pdf`)
}

export async function downloadSelectedVouchersPdf(voucher_ids: number[], mode: '4up' | 'individual' = '4up') {
  const response = await apiClient.post('/fee-vouchers/pdf/selected', { voucher_ids, mode }, { responseType: 'blob' })
  const blobUrl = window.URL.createObjectURL(response.data as Blob)
  const link = document.createElement('a')
  link.href = blobUrl
  link.download = 'fee_vouchers.pdf'
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(blobUrl)
}

export async function downloadAllChallans(params: {
  class_names?: string[]
  mode?: '4up' | 'individual'
  note?: string
}) {
  await downloadFile('/fee-vouchers/pdf/all-students', {
    class_names: params.class_names?.join(',') ?? '',
    mode: params.mode ?? '4up',
    note: params.note ?? '',
  }, 'all_challans.pdf')
}

export async function downloadStudentChallan(studentId: number, note?: string) {
  await downloadFile(`/fee-vouchers/pdf/student/${studentId}`, {
    note: note ?? '',
  }, `student_${studentId}_challan.pdf`)
}
