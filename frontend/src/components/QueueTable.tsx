import { DataGrid, type GridColDef } from '@mui/x-data-grid'
import { Box, Chip } from '@mui/material'
import type { QueueEntry, NotificationStatus } from '../api/communication'

const STATUS_COLOR: Record<NotificationStatus, 'default' | 'info' | 'success' | 'error' | 'warning'> = {
  pending: 'default', processing: 'info', sent: 'success', failed: 'error', cancelled: 'warning',
}

export function QueueTable({ rows, loading }: { rows: QueueEntry[]; loading?: boolean }) {
  const columns: GridColDef<QueueEntry>[] = [
    { field: 'id', headerName: 'ID', width: 60 },
    { field: 'recipient_name', headerName: 'Recipient', flex: 1, valueGetter: (_v, row) => row.recipient_name ?? '—' },
    { field: 'recipient', headerName: 'Phone', width: 130 },
    { field: 'provider_type', headerName: 'Channel', width: 100 },
    { field: 'notification_type', headerName: 'Type', width: 140 },
    { field: 'message', headerName: 'Message', flex: 1.5 },
    {
      field: 'status', headerName: 'Status', width: 110,
      renderCell: (p) => <Chip size="small" label={p.value} color={STATUS_COLOR[p.value as NotificationStatus]} />,
    },
    { field: 'retry_count', headerName: 'Retries', width: 80, type: 'number' },
    {
      field: 'created_at', headerName: 'Created', width: 170,
      valueGetter: (_v, row) => new Date(row.created_at).toLocaleString(),
    },
  ]

  return (
    <Box sx={{ height: 550 }}>
      <DataGrid rows={rows} columns={columns} getRowId={(row) => row.id} loading={loading} density="compact" />
    </Box>
  )
}
