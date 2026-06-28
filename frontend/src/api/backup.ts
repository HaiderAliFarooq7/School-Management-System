import { apiClient, downloadFile } from './client'

/** Downloads a fresh database backup straight to the user's computer. The
 * server streams the dump and deletes its temp copy immediately — nothing is
 * retained on the host. */
export async function runBackup(): Promise<void> {
  await downloadFile('/backup/database', {}, 'sms_backup.dump')
}

export async function restoreBackup(file: File): Promise<{ detail: string }> {
  const formData = new FormData()
  formData.append('file', file)
  const { data } = await apiClient.post('/backup/restore', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

export function exportStudentsUrl(): string {
  return '/api/backup/export-students.xlsx'
}

export async function importStudents(file: File): Promise<{ imported: number }> {
  const formData = new FormData()
  formData.append('file', file)
  const { data } = await apiClient.post('/backup/import-students', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

export async function resetDatabase(): Promise<{ detail: string }> {
  const { data } = await apiClient.post('/backup/reset', { confirm: true })
  return data
}
