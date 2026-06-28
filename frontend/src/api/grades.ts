import { apiClient } from './client'

export interface Grade {
  grade_id: number
  class_name: string
  fee_amount: number
  student_count: number
}

export async function listGrades(): Promise<Grade[]> {
  const { data } = await apiClient.get<Grade[]>('/grades')
  return data
}

export async function createGrade(class_name: string, fee_amount: number): Promise<Grade> {
  const { data } = await apiClient.post<Grade>('/grades', { class_name, fee_amount })
  return data
}

export async function updateGrade(gradeId: number, class_name: string, fee_amount: number): Promise<Grade> {
  const { data } = await apiClient.put<Grade>(`/grades/${gradeId}`, { class_name, fee_amount })
  return data
}

export async function deleteGrade(gradeId: number): Promise<void> {
  await apiClient.delete(`/grades/${gradeId}`)
}
