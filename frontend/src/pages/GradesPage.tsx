import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Box, Button, Chip, IconButton, Table, TableBody, TableCell, TableHead, TableRow, TextField, Typography,
} from '@mui/material'
import DeleteIcon from '@mui/icons-material/Delete'
import { createGrade, deleteGrade, listGrades, updateGrade } from '../api/grades'
import { useConfirm, useToast } from '../components/feedback'

function apiErrorMessage(e: unknown): string {
  return String((e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? e)
}

export function GradesPage() {
  const queryClient = useQueryClient()
  const { data: grades } = useQuery({ queryKey: ['grades'], queryFn: listGrades })
  const [newClassName, setNewClassName] = useState('')
  const [newFee, setNewFee] = useState('')
  const [deleteError, setDeleteError] = useState<string | null>(null)

  const createMutation = useMutation({
    mutationFn: () => createGrade(newClassName, Number(newFee) || 0),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['grades'] })
      setNewClassName('')
      setNewFee('')
      setDeleteError(null)
    },
    onError: (e) => setDeleteError(apiErrorMessage(e)),
  })

  const deleteMutation = useMutation({
    mutationFn: (gradeId: number) => deleteGrade(gradeId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['grades'] })
      setDeleteError(null)
    },
    onError: (e) => setDeleteError(apiErrorMessage(e)),
  })

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        Grades / Classes
      </Typography>
      {deleteError && (
        <Typography color="error" sx={{ mb: 2 }}>
          {deleteError}
        </Typography>
      )}
      <Table size="small" sx={{ maxWidth: 700, mb: 3 }}>
        <TableHead>
          <TableRow>
            <TableCell>Class Name</TableCell>
            <TableCell>Monthly Fee (Rs.)</TableCell>
            <TableCell>Students</TableCell>
            <TableCell />
          </TableRow>
        </TableHead>
        <TableBody>
          {grades?.map((g) => (
            <GradeRow
              key={g.grade_id}
              gradeId={g.grade_id}
              className={g.class_name}
              feeAmount={g.fee_amount}
              studentCount={g.student_count}
              onDelete={() => deleteMutation.mutate(g.grade_id)}
            />
          ))}
          <TableRow>
            <TableCell>
              <TextField
                size="small"
                placeholder="New class name"
                value={newClassName}
                onChange={(e) => setNewClassName(e.target.value)}
              />
            </TableCell>
            <TableCell>
              <TextField
                size="small"
                placeholder="Fee"
                value={newFee}
                onChange={(e) => setNewFee(e.target.value)}
              />
              <Button
                sx={{ ml: 1 }}
                size="small"
                variant="contained"
                disabled={!newClassName}
                onClick={() => createMutation.mutate()}
              >
                Add
              </Button>
            </TableCell>
            <TableCell />
            <TableCell />
          </TableRow>
        </TableBody>
      </Table>
    </Box>
  )
}

function GradeRow({
  gradeId, className, feeAmount, studentCount, onDelete,
}: { gradeId: number; className: string; feeAmount: number; studentCount: number; onDelete: () => void }) {
  const queryClient = useQueryClient()
  const toast = useToast()
  const confirmAction = useConfirm()
  const [name, setName] = useState(className)
  const [fee, setFee] = useState(String(feeAmount))

  const saveMutation = useMutation({
    mutationFn: () => updateGrade(gradeId, name, Number(fee) || 0),
    onSuccess: () => {
      toast('Class saved.')
      queryClient.invalidateQueries({ queryKey: ['grades'] })
    },
    onError: (e) => toast(apiErrorMessage(e), 'error'),
  })

  return (
    <TableRow>
      <TableCell>
        <TextField size="small" value={name} onChange={(e) => setName(e.target.value)} />
      </TableCell>
      <TableCell>
        <TextField size="small" value={fee} onChange={(e) => setFee(e.target.value)} />
        <Button sx={{ ml: 1 }} size="small" onClick={() => saveMutation.mutate()}>
          Save
        </Button>
      </TableCell>
      <TableCell>
        <Chip size="small" label={studentCount} color={studentCount > 0 ? 'primary' : 'default'} />
      </TableCell>
      <TableCell>
        <IconButton
          size="small"
          color="error"
          aria-label={`Delete class ${className}`}
          onClick={async () => {
            const ok = await confirmAction({
              title: `Delete class "${className}"?`,
              message: 'A class can only be deleted when no students are enrolled in it.',
              confirmLabel: 'Delete',
              destructive: true,
            })
            if (ok) onDelete()
          }}
        >
          <DeleteIcon fontSize="small" />
        </IconButton>
      </TableCell>
    </TableRow>
  )
}
