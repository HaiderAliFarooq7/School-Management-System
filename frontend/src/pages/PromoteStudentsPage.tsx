import { useEffect, useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import {
  Alert, Box, Button, Dialog, DialogActions, DialogContent, DialogTitle, Table, TableBody, TableCell,
  TableHead, TableRow, TextField, Typography,
} from '@mui/material'
import { CLASS_SEQUENCE, getClassCounts, promoteAllStudents, type PromoteResult } from '../api/students'

export function PromoteStudentsPage() {
  const { data: counts, isLoading } = useQuery({ queryKey: ['class-counts'], queryFn: getClassCounts })
  const [increments, setIncrements] = useState<Record<string, string>>({})
  const [confirmOpen, setConfirmOpen] = useState(false)
  const [result, setResult] = useState<PromoteResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (counts) {
      setIncrements((prev) => {
        const next = { ...prev }
        for (const c of counts) {
          if (next[c.class_name] === undefined) next[c.class_name] = ''
        }
        return next
      })
    }
  }, [counts])

  const mutation = useMutation({
    mutationFn: () =>
      promoteAllStudents(
        Object.fromEntries(
          Object.entries(increments).map(([cls, v]) => [cls, Number(v) || 0]),
        ),
      ),
    onSuccess: (data) => {
      setResult(data)
      setError(null)
      setConfirmOpen(false)
    },
    onError: () => {
      setError('Promotion failed — no changes were saved. Please try again.')
      setConfirmOpen(false)
    },
  })

  const countFor = (className: string) => counts?.find((c) => c.class_name === className)?.count ?? 0
  const totalActive = counts?.reduce((sum, c) => sum + c.count, 0) ?? 0

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        Promote Students
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Promotes every active student to the next class. Enter a fee increase for each class — that
        amount is added to each student's monthly fee when they move up. Students currently in{' '}
        <strong>Grade 10</strong> are marked <strong>Inactive</strong> instead of promoted further.
        Promoting also cleans up the past year's data for every active student: fully-paid fee vouchers
        and extra charges are deleted (anything still pending is kept), and all attendance and
        notification history is permanently deleted to reduce database size.
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {result && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setResult(null)}>
          Promoted {result.promoted} student(s). Marked {result.deactivated} Grade 10 student(s) as Inactive.
        </Alert>
      )}

      <Table size="small" sx={{ maxWidth: 700, mb: 3 }}>
        <TableHead>
          <TableRow>
            <TableCell>Class</TableCell>
            <TableCell>Active Students</TableCell>
            <TableCell>Next Class</TableCell>
            <TableCell>Fee Increase (Rs.)</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {CLASS_SEQUENCE.map((cls, i) => (
            <TableRow key={cls}>
              <TableCell>{cls}</TableCell>
              <TableCell>{isLoading ? '…' : countFor(cls)}</TableCell>
              <TableCell>
                {i === CLASS_SEQUENCE.length - 1 ? 'Inactive (leaving school)' : CLASS_SEQUENCE[i + 1]}
              </TableCell>
              <TableCell>
                <TextField
                  size="small"
                  placeholder="0"
                  value={increments[cls] ?? ''}
                  onChange={(e) => setIncrements((prev) => ({ ...prev, [cls]: e.target.value }))}
                  sx={{ width: 120 }}
                />
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      <Button
        variant="contained"
        color="primary"
        disabled={totalActive === 0 || mutation.isPending}
        onClick={() => setConfirmOpen(true)}
      >
        Promote All Students
      </Button>

      <Dialog open={confirmOpen} onClose={() => setConfirmOpen(false)}>
        <DialogTitle>Confirm Promotion</DialogTitle>
        <DialogContent>
          <Typography>
            This will move every active student ({totalActive} total) to the next class and apply the
            fee increases you entered. Grade 10 students will be set to Inactive. It will also{' '}
            <strong>permanently delete</strong> all attendance and notification history for every active
            student, and delete any fee voucher or extra charge that's already fully paid (pending ones
            are kept). This action cannot be undone automatically — continue?
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfirmOpen(false)}>Cancel</Button>
          <Button variant="contained" color="primary" onClick={() => mutation.mutate()}>
            Yes, Promote
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
