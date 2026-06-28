import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Alert, Box, List, ListItem, ListItemText, MenuItem, Select, Typography } from '@mui/material'
import { listGrades } from '../api/grades'
import { getPendingFeeNames } from '../api/students'
import { useAuth } from '../context/AuthContext'

export function FeeStatusPage() {
  const { assignedClassName } = useAuth()
  const { data: grades } = useQuery({ queryKey: ['grades'], queryFn: listGrades })
  const [className, setClassName] = useState(assignedClassName ?? '')

  const { data, isLoading, isError } = useQuery({
    queryKey: ['pending-fee-names', className],
    queryFn: () => getPendingFeeNames(className),
    enabled: !!className,
  })

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        Fee Status
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Students with a pending fee voucher or charge, by class. No amounts are shown here —
        for payment or billing details, please direct parents to the school office.
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
        <List sx={{ maxWidth: 400 }}>
          {data.map((s) => (
            <ListItem key={s.student_id} divider>
              <ListItemText primary={s.name} secondary={s.registration_no} />
            </ListItem>
          ))}
        </List>
      )}
    </Box>
  )
}
