import { DataGrid, type GridColDef } from '@mui/x-data-grid'
import { Box, Chip } from '@mui/material'
import type { HistoryEntry } from '../api/communication'

export function HistoryTable({ rows, loading }: { rows: HistoryEntry[]; loading?: boolean }) {
  const columns: GridColDef<HistoryEntry>[] = [
    { field: 'log_id', headerName: 'ID', width: 60 },
    { field: 'student_id', headerName: 'Student ID', width: 100 },
    { field: 'recipient', headerName: 'Recipient', width: 130, valueGetter: (_v, row) => row.recipient ?? '—' },
    { field: 'provider', headerName: 'Provider', width: 130, valueGetter: (_v, row) => row.provider ?? '—' },
    { field: 'notification_type', headerName: 'Type', width: 140 },
    { field: 'template', headerName: 'Template', width: 130, valueGetter: (_v, row) => row.template ?? '—' },
    { field: 'message', headerName: 'Message', flex: 1.5 },
    {
      field: 'status', headerName: 'Status', width: 110,
      renderCell: (p) => <Chip size="small" label={p.value} color={p.value === 'sent' ? 'success' : 'error'} />,
    },
    { field: 'meta_message_id', headerName: 'Meta Message ID', width: 160, valueGetter: (_v, row) => row.meta_message_id ?? '—' },
    { field: 'http_status', headerName: 'HTTP', width: 70, valueGetter: (_v, row) => row.http_status ?? '—' },
    { field: 'error', headerName: 'Error', flex: 1, valueGetter: (_v, row) => row.error ?? '—' },
    {
      field: 'created_at', headerName: 'Created', width: 170,
      valueGetter: (_v, row) => new Date(row.created_at).toLocaleString(),
    },
  ]

  return (
    <Box sx={{ height: 550 }}>
      <DataGrid rows={rows} columns={columns} getRowId={(row) => row.log_id} loading={loading} density="compact" />
    </Box>
  )
}
