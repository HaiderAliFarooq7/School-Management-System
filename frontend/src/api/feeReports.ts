import { apiClient, downloadFile } from './client'

export async function getMonthlyCollection(year: number, month: number, class_name = '') {
  const { data } = await apiClient.get('/fee-reports/monthly-collection', { params: { year, month, class_name } })
  return data
}

export async function getClassSummary(class_name: string, year: number, month: number) {
  const { data } = await apiClient.get('/fee-reports/class-summary', { params: { class_name, year, month } })
  return data
}

export interface BalanceSheetVoucher {
  voucher_id: number
  fee_month: string
  total_amount: number
  paid_amount: number
  discount_amount: number
  discount_reason: string | null
  status: string
}

export interface BalanceSheetCharge {
  charge_id: number
  description: string
  amount: number
  paid_amount: number
  discount_amount: number
  discount_reason: string | null
  status: string
}

export interface BalanceSheet {
  student: { student_id: number; registration_no: string; name: string; class_name: string }
  vouchers: BalanceSheetVoucher[]
  charges: BalanceSheetCharge[]
  total_fees_due: number
  total_paid: number
  total_discounted: number
  total_pending: number
}

export async function getBalanceSheet(studentId: number): Promise<BalanceSheet> {
  const { data } = await apiClient.get<BalanceSheet>(`/fee-reports/balance-sheet/${studentId}`)
  return data
}

export interface PendingReportRow {
  student_id: number
  registration_no: string
  name: string
  father_name: string
  class_name: string
  phone: string | null
  cnic: string | null
  vouchers_pending: number
  charges_pending: number
  total_pending: number
  fee_status: string
  is_overdue: boolean
}

export async function getPendingReport(params: { class_names?: string[]; status_filter?: string; due_day?: number }): Promise<PendingReportRow[]> {
  const { data } = await apiClient.get<PendingReportRow[]>('/fee-reports/pending', {
    params: {
      class_names: params.class_names?.join(',') ?? '',
      status_filter: params.status_filter ?? '',
      due_day: params.due_day ?? 10,
    },
  })
  return data
}

export const PENDING_REPORT_COLUMNS: { key: string; label: string }[] = [
  { key: 'registration_no', label: 'Reg No' },
  { key: 'name', label: 'Name' },
  { key: 'father_name', label: "Father's Name" },
  { key: 'class_name', label: 'Class' },
  { key: 'phone', label: 'Phone' },
  { key: 'cnic', label: 'CNIC' },
  { key: 'vouchers_pending', label: 'Fee Pending (Rs.)' },
  { key: 'charges_pending', label: 'Charges Pending (Rs.)' },
  { key: 'total_pending', label: 'Total Pending (Rs.)' },
  { key: 'fee_status', label: 'Fee Status' },
]

export async function downloadPendingReportPdf(params: { class_names?: string[]; status_filter?: string; columns?: string[] }) {
  await downloadFile('/fee-reports/pending/pdf', {
    class_names: params.class_names?.join(',') ?? '',
    status_filter: params.status_filter ?? '',
    columns: params.columns?.join(',') ?? '',
  }, 'pending_fee_report.pdf')
}

export async function downloadPendingReportExcel(params: { class_names?: string[]; status_filter?: string; columns?: string[] }) {
  await downloadFile('/fee-reports/pending/xlsx', {
    class_names: params.class_names?.join(',') ?? '',
    status_filter: params.status_filter ?? '',
    columns: params.columns?.join(',') ?? '',
  }, 'pending_fee_report.xlsx')
}

export interface FeeAnalytics {
  total_billed: number
  total_collected: number
  total_discounted: number
  total_outstanding: number
  voucher_status_counts: Record<string, number>
  charges_total: number
  charges_collected: number
  charges_discounted: number
  charges_pending: number
  by_class: { class_name: string; student_count: number; total: number; collected: number; discounted: number; pending: number }[]
  monthly_trend: { month: string; billed: number; collected: number; discounted: number }[]
}

export async function getFeeAnalytics(months = 6, class_name = ''): Promise<FeeAnalytics> {
  const { data } = await apiClient.get<FeeAnalytics>('/fee-reports/analytics', { params: { months, class_name } })
  return data
}
