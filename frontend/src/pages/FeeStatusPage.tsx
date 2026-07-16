import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import {
  Alert, Box, List, ListItem, ListItemText, MenuItem, Select, Table, TableBody, TableCell,
  TableContainer, TableHead, TableRow, Typography,
} from '@mui/material'
import { listGrades } from '../api/grades'
import { getPendingFeeNames } from '../api/students'
import { useAuth } from '../context/AuthContext'

export function FeeStatusPage() {
  const navigate = useNavigate()
  const { role, assignedClassName } = useAuth()
  // Admin/Accountant see pending amounts and can click through to the fee
  // window; Teachers get the names-only view (the backend enforces this too).
  const canManageFees = role === 'Admin' || role === 'Accountant'
  const { data: grades } = useQuery({ queryKey: ['grades'], queryFn: listGrades })
  const [className, setClassName] = useState(assignedClassName ?? '')

  const { data, isLoading, isError } = useQuery({
    queryKey: ['pending-fee-names', className],
    queryFn: () => getPendingFeeNames(className),
    enabled: !!className,
  })

  const totalPending = canManageFees
    ? (data ?? []).reduce((sum, s) => sum + (s.total_pending ?? 0), 0)
    : 0

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        Fee Status
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        {canManageFees
          ? 'Students with a pending fee voucher or charge, by class. Click a student to open their fee window and record a payment.'
          : 'Students with a pending fee voucher or charge, by class. No amounts are shown here — for payment or billing details, please direct parents to the school office.'}
      </Typography>

      <Select
        size="small"
        value={className}
        onChange={(e) => setClassName(e.target.value)}
        displayEmpty
        sx={{ width: 200, mb: 2 }}
      >
        <MenuItem value="" disabled>Select a class</MenuItem>
        {grades?.map((g) => <MenuItem key={g.grade_id} value={g.class_name}>{g.class_name}</MenuItem>)}
      </Select>

      {isLoading && <Typography color="text.secondary">Loading…</Typography>}
      {isError && <Alert severity="error">Could not load pending fees. Please try again.</Alert>}

      {!isLoading && !isError && className && data?.length === 0 && (
        <Alert severity="success">No pending fees — everyone in {className} is up to date.</Alert>
      )}

      {!isLoading && data && data.length > 0 && (
        canManageFees ? (
          <TableContainer sx={{ maxWidth: 600 }}>
            <Table size="small" sx={{ minWidth: 420 }}>
              <TableHead>
                <TableRow>
                  <TableCell>Reg No</TableCell>
                  <TableCell>Name</TableCell>
                  <TableCell align="right">Pending (Rs.)</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {data.map((s) => (
                  <TableRow
                    key={s.student_id}
                    hover
                    onClick={() => navigate(`/fees/student/${s.student_id}`)}
                    sx={{ cursor: 'pointer' }}
                  >
                    <TableCell>{s.registration_no}</TableCell>
                    <TableCell>{s.name}</TableCell>
                    <TableCell align="right">{(s.total_pending ?? 0).toFixed(0)}</TableCell>
                  </TableRow>
                ))}
                <TableRow>
                  <TableCell colSpan={2} sx={{ fontWeight: 'bold' }}>
                    Total ({data.length} student{data.length === 1 ? '' : 's'})
                  </TableCell>
                  <TableCell align="right" sx={{ fontWeight: 'bold' }}>
                    {totalPending.toFixed(0)}
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </TableContainer>
        ) : (
          <List sx={{ maxWidth: 400 }}>
            {data.map((s) => (
              <ListItem key={s.student_id} divider>
                <ListItemText primary={s.name} secondary={s.registration_no} />
              </ListItem>
            ))}
          </List>
        )
      )}
    </Box>
  )
}
