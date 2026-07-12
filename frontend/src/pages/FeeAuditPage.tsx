import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Box, Chip, MenuItem, Table, TableBody, TableCell, TableHead, TableRow, TextField, Typography,
} from '@mui/material'
import { listFeeAudit } from '../api/feeAudit'

const ACTION_COLOR: Record<string, 'success' | 'warning' | 'info' | 'error' | 'default'> = {
  payment: 'success',
  discount: 'warning',
  edit: 'info',
  delete: 'error',
  generate: 'default',
}

export function FeeAuditPage() {
  const [action, setAction] = useState('')
  const { data: entries } = useQuery({
    queryKey: ['fee-audit', action],
    queryFn: () => listFeeAudit({ action: action || undefined, limit: 300 }),
  })

  return (
    <Box>
      <Typography variant="h5" gutterBottom>Fee Activity Log</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        A record of who took each fee action — payments received, discounts given (and the reason),
        and any edits or deletions. Kept for well over 3 months.
      </Typography>

      <TextField
        select size="small" label="Action" value={action}
        onChange={(e) => setAction(e.target.value)} sx={{ minWidth: 170, mb: 2 }}
      >
        <MenuItem value="">All actions</MenuItem>
        {(['payment', 'discount', 'edit', 'delete'] as const).map((a) => (
          <MenuItem key={a} value={a}>{a[0].toUpperCase() + a.slice(1)}</MenuItem>
        ))}
      </TextField>

      <Box sx={{ overflowX: 'auto' }}>
        <Table size="small" sx={{ minWidth: 940 }}>
          <TableHead>
            <TableRow>
              <TableCell>When</TableCell>
              <TableCell>User</TableCell>
              <TableCell>Action</TableCell>
              <TableCell>Student</TableCell>
              <TableCell>Item</TableCell>
              <TableCell align="right">Amount</TableCell>
              <TableCell>Reason / Note</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {entries?.map((e) => (
              <TableRow key={e.id}>
                <TableCell>{new Date(e.created_at).toLocaleString()}</TableCell>
                <TableCell>{e.actor_username}{e.actor_role ? ` (${e.actor_role})` : ''}</TableCell>
                <TableCell>
                  <Chip size="small" label={e.action} color={ACTION_COLOR[e.action] ?? 'default'} />
                </TableCell>
                <TableCell>{e.student_name || '—'}</TableCell>
                <TableCell>{e.target_type === 'fee_voucher' ? 'Fee' : 'Charge'}: {e.label}</TableCell>
                <TableCell align="right">
                  {e.amount != null ? `Rs. ${Math.round(e.amount).toLocaleString()}` : '—'}
                </TableCell>
                <TableCell>{e.reason || e.note || '—'}</TableCell>
              </TableRow>
            ))}
            {entries?.length === 0 && (
              <TableRow>
                <TableCell colSpan={7}>
                  <Typography color="text.secondary" sx={{ py: 2 }}>No activity recorded yet.</Typography>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </Box>
    </Box>
  )
}
