import { apiClient } from './client'

export interface Student {
  student_id: number
  registration_no: string
  name: string
  father_name: string
  class_name: string
  dob: string | null
  admission_date: string | null
  b_form: string | null
  cnic: string | null
  phone: string | null
  address: string | null
  photo_path: string | null
  status: string
  default_fee: number | null
  fee_status: string | null
  total_pending: number | null
}

export interface StudentCreate {
  name: string
  father_name: string
  class_name: string
  dob?: string | null
  admission_date?: string | null
  b_form?: string | null
  cnic?: string | null
  phone?: string | null
  address?: string | null
  default_fee?: number | null
  status?: string
}

export async function listStudents(params: {
  search?: string
  class_filter?: string
  status_filter?: string
}): Promise<Student[]> {
  const { data } = await apiClient.get<Student[]>('/students', { params })
  return data
}

export async function createStudent(payload: StudentCreate): Promise<Student> {
  const { data } = await apiClient.post<Student>('/students', payload)
  return data
}

export async function updateStudent(studentId: number, payload: StudentCreate): Promise<Student> {
  const { data } = await apiClient.put<Student>(`/students/${studentId}`, payload)
  return data
}

export interface StudentSearchParams {
  name?: string
  registration_no?: string
  cnic?: string
  phone?: string
  father_name?: string
  address?: string
  class_filter?: string
  status_filter?: string
  admission_year?: string
  dob_from?: string
  dob_to?: string
  fee_status_filter?: string
}

export async function searchStudentsAdvanced(params: StudentSearchParams): Promise<Student[]> {
  const { data } = await apiClient.post<Student[]>('/students/search-advanced', params)
  return data
}

export async function getStudent(studentId: number): Promise<Student> {
  const { data } = await apiClient.get<Student>(`/students/${studentId}`)
  return data
}

export async function setStudentStatus(studentId: number, newStatus: string): Promise<Student> {
  const { data } = await apiClient.patch<Student>(
    `/students/${studentId}/status`,
    null,
    { params: { new_status: newStatus } },
  )
  return data
}

export const CLASS_SEQUENCE = [
  'Playgroup', 'Nursery', 'Prep',
  'Grade 1', 'Grade 2', 'Grade 3', 'Grade 4', 'Grade 5',
  'Grade 6', 'Grade 7', 'Grade 8', 'Grade 9', 'Grade 10',
]

export interface ClassCount {
  class_name: string
  count: number
}

export async function getClassCounts(): Promise<ClassCount[]> {
  const { data } = await apiClient.get<ClassCount[]>('/students/class-counts')
  return data
}

export interface PromoteResult {
  promoted: number
  deactivated: number
}

export async function promoteAllStudents(increments: Record<string, number>): Promise<PromoteResult> {
  const { data } = await apiClient.post<PromoteResult>('/students/promote-all', { increments })
  return data
}

export interface PendingFeeStudent {
  student_id: number
  name: string
  registration_no: string
}

export async function getPendingFeeNames(class_name = ''): Promise<PendingFeeStudent[]> {
  const { data } = await apiClient.get<PendingFeeStudent[]>('/students/pending-fee-names', { params: { class_name } })
  return data
}
