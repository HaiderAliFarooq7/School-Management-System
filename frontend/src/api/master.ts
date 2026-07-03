import { apiClient } from './client'
import type { LoginResponse } from './auth'

export interface MasterSchool {
  school_id: number
  school_name: string
  campus_name: string
  database_name: string
  database_status: 'active' | 'disabled' | 'archived'
  created_at: string
  updated_at: string
}

export interface SchoolCreatePayload {
  school_name: string
  campus_name: string
  database_name: string
  admin_username: string
  admin_password: string
}

export interface SchoolStats {
  school_id: number
  active_students: number
  total_students: number
  users: number
  reachable: boolean
}

export interface SystemStats {
  total_schools: number
  schools_by_status: Record<string, number>
  routed_usernames: number
}

export async function listSchools(): Promise<MasterSchool[]> {
  const { data } = await apiClient.get<MasterSchool[]>('/master/schools')
  return data
}

export async function createSchool(payload: SchoolCreatePayload): Promise<MasterSchool> {
  const { data } = await apiClient.post<MasterSchool>('/master/schools', payload)
  return data
}

export async function setSchoolStatus(schoolId: number, database_status: string): Promise<MasterSchool> {
  const { data } = await apiClient.patch<MasterSchool>(`/master/schools/${schoolId}/status`, { database_status })
  return data
}

export async function archiveSchool(schoolId: number): Promise<MasterSchool> {
  const { data } = await apiClient.delete<MasterSchool>(`/master/schools/${schoolId}`)
  return data
}

export async function resetSchoolAdminPassword(
  schoolId: number, username: string, new_password: string,
): Promise<{ detail: string }> {
  const { data } = await apiClient.post<{ detail: string }>(
    `/master/schools/${schoolId}/reset-admin-password`, { username, new_password },
  )
  return data
}

export async function getSchoolStats(schoolId: number): Promise<SchoolStats> {
  const { data } = await apiClient.get<SchoolStats>(`/master/schools/${schoolId}/stats`)
  return data
}

export async function switchSchool(schoolId: number): Promise<LoginResponse> {
  const { data } = await apiClient.post<LoginResponse>(`/master/switch/${schoolId}`)
  return data
}

export async function getSystemStats(): Promise<SystemStats> {
  const { data } = await apiClient.get<SystemStats>('/master/stats')
  return data
}
