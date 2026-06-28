import { apiClient, downloadFile } from './client'

export type ImportMode = 'delete_all' | 'update_or_add' | 'new_only'

export interface AnalyzeResponse {
  columns: string[]
  suggested_mapping: Record<string, string | null>
  available_fields: Record<string, string>
  raw_rows: Record<string, unknown>[]
  total_rows: number
  distinct_class_values: string[]
  suggested_class_mapping: Record<string, string | null>
  known_classes: string[]
}

export interface PreviewRow {
  row_number: number
  data: Record<string, unknown>
  status: 'valid' | 'invalid' | 'duplicate'
  errors: string[]
  missing_fields: string[]
}

export interface PreviewResponse {
  total_rows: number
  valid_rows: number
  invalid_rows: number
  duplicate_rows: number
  missing_fields_rows: number
  rows: PreviewRow[]
}

export interface ExecuteResult {
  imported: number
  updated: number
  skipped: number
  failed: number
  errors: { row_number: number; reason: string }[]
}

export async function analyzeImportFile(file: File): Promise<AnalyzeResponse> {
  const formData = new FormData()
  formData.append('file', file)
  const { data } = await apiClient.post<AnalyzeResponse>('/students/import/analyze', formData)
  return data
}

export async function previewImport(payload: {
  raw_rows: Record<string, unknown>[]
  mapping: Record<string, string | null>
  class_value_mapping: Record<string, string>
  import_mode: ImportMode
}): Promise<PreviewResponse> {
  const { data } = await apiClient.post<PreviewResponse>('/students/import/preview', payload)
  return data
}

export async function executeImport(payload: {
  raw_rows: Record<string, unknown>[]
  mapping: Record<string, string | null>
  class_value_mapping: Record<string, string>
  import_mode: ImportMode
  only_valid_rows: boolean
  confirm_delete_all: boolean
}): Promise<ExecuteResult> {
  const { data } = await apiClient.post<ExecuteResult>('/students/import/execute', payload)
  return data
}

export type ExportScope = 'all' | 'selected' | 'filtered' | 'search'

export async function exportStudents(params: {
  format: 'xlsx' | 'csv'
  scope: ExportScope
  student_ids?: number[]
  search?: string
  class_filter?: string
  status_filter?: string
}): Promise<void> {
  await downloadFile('/students/export', {
    format: params.format,
    scope: params.scope,
    student_ids: params.student_ids?.join(',') ?? '',
    search: params.search ?? '',
    class_filter: params.class_filter ?? '',
    status_filter: params.status_filter ?? '',
  }, `students_export.${params.format}`)
}
