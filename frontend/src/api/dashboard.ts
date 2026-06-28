import { apiClient } from './client'

export interface DashboardStats {
  total_students: number
  total_classes: number
  total_collected: number | null
  total_discounted: number | null
  total_outstanding: number | null
  outstanding_charges: number | null
  by_class: { class_name: string; count: number }[]
}

export async function getDashboardStats(): Promise<DashboardStats> {
  const { data } = await apiClient.get<DashboardStats>('/dashboard/stats')
  return data
}
