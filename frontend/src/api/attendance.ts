import { apiClient } from './client'

export interface AttendanceRecord {
  attendance_id: number
  student_id: number
  class_name: string
  attendance_date: string
  period_name: string
  status: string
  remarks: string | null
}

export interface AttendanceSummaryRow {
  student_id: number
  registration_no: string
  name: string
  present: number
  absent: number
  late: number
  leave: number
  total_marked: number
  pct_present: number
}

export async function getAttendanceForClassDate(class_name: string, attendance_date: string): Promise<AttendanceRecord[]> {
  const { data } = await apiClient.get<AttendanceRecord[]>('/attendance', { params: { class_name, attendance_date } })
  return data
}

export async function markAttendance(
  class_name: string,
  attendance_date: string,
  entries: { student_id: number; status: string; remarks?: string | null }[],
): Promise<AttendanceRecord[]> {
  const { data } = await apiClient.post<AttendanceRecord[]>('/attendance/mark', {
    class_name, attendance_date, entries,
  })
  return data
}

export async function getAttendanceSummary(class_name: string, date_from: string, date_to: string): Promise<AttendanceSummaryRow[]> {
  const { data } = await apiClient.get<AttendanceSummaryRow[]>('/attendance/summary', {
    params: { class_name, date_from, date_to },
  })
  return data
}

export interface AttendanceDailyStatusRow {
  class_name: string
  total_active_students: number
  marked_count: number
  fully_marked: boolean
  any_marked: boolean
}

export async function getAttendanceDailyStatus(attendance_date?: string): Promise<AttendanceDailyStatusRow[]> {
  const { data } = await apiClient.get<AttendanceDailyStatusRow[]>('/attendance/daily-status', {
    params: attendance_date ? { attendance_date } : {},
  })
  return data
}

export interface AbsentTodayRow {
  student_id: number
  registration_no: string
  name: string
  father_name: string
  class_name: string
  phone: string | null
}

export async function getAbsentToday(params: { attendance_date?: string; class_name?: string } = {}): Promise<AbsentTodayRow[]> {
  const { data } = await apiClient.get<AbsentTodayRow[]>('/attendance/absent-today', { params })
  return data
}
