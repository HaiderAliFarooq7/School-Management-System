import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Alert, Button, Dialog, DialogActions, DialogContent, DialogTitle, Divider, MenuItem, Select,
  TextField, Box, Typography,
} from '@mui/material'
import { useAuth } from '../context/AuthContext'
import { listGrades } from '../api/grades'
import { deleteStudent, updateStudent, type Student } from '../api/students'
import { useConfirm } from './feedback'

interface Props {
  student: Student | null
  open: boolean
  onClose: () => void
}

export function StudentEditDialog({ student, open, onClose }: Props) {
  const queryClient = useQueryClient()
  const confirmAction = useConfirm()
  const { role } = useAuth()
  const { data: grades } = useQuery({ queryKey: ['grades'], queryFn: listGrades })
  const [form, setForm] = useState({
    name: '', father_name: '', class_name: '', dob: '', admission_date: '',
    b_form: '', cnic: '', phone: '', address: '', default_fee: '', status: 'Active',
  })

  const [error, setError] = useState<string | null>(null)
  const [deleteError, setDeleteError] = useState<string | null>(null)

  useEffect(() => {
    if (open && student) {
      setForm({
        name: student.name,
        father_name: student.father_name,
        class_name: student.class_name,
        dob: student.dob ?? '',
        admission_date: student.admission_date ?? '',
        b_form: student.b_form ?? '',
        cnic: student.cnic ?? '',
        phone: student.phone ?? '',
        address: student.address ?? '',
        default_fee: student.default_fee != null ? String(student.default_fee) : '',
        status: student.status,
      })
      setError(null)
    }
  }, [open, student])

  const mutation = useMutation({
    mutationFn: () =>
      updateStudent(student!.student_id, {
        name: form.name,
        father_name: form.father_name,
        class_name: form.class_name,
        dob: form.dob || null,
        admission_date: form.admission_date || null,
        b_form: form.b_form || null,
        cnic: form.cnic || null,
        phone: form.phone || null,
        address: form.address || null,
        default_fee: form.default_fee ? Number(form.default_fee) : null,
        status: form.status,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['students'] })
      onClose()
    },
    onError: (e) => setError(String((e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? 'Could not save changes.')),
  })

  const deleteMutation = useMutation({
    mutationFn: () => deleteStudent(student!.student_id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['students'] })
      queryClient.invalidateQueries({ queryKey: ['class-counts'] })
      onClose()
    },
    onError: (e) => setDeleteError(String((e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? 'Could not delete this student.')),
  })

  async function handleDelete() {
    if (!student) return
    const confirmed = await confirmAction({
      title: `Permanently delete ${student.name}?`,
      message:
        `This deletes ${student.name} (${student.registration_no}) and every record tied to them — ` +
        'fee vouchers, extra charges, payment history, and attendance. This cannot be undone.',
      confirmLabel: 'Delete Student',
      destructive: true,
    })
    if (confirmed) deleteMutation.mutate()
  }

  const canSave = !!form.name.trim() && !!form.father_name.trim() && !!form.class_name
    && (!form.default_fee || Number(form.default_fee) >= 0)

  const set = (field: string) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((f) => ({ ...f, [field]: e.target.value }))

  if (!student) return null

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Edit Student — {student.registration_no}</DialogTitle>
      <DialogContent>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
          {error && <Alert severity="error">{error}</Alert>}
          <TextField label="Student Name" value={form.name} onChange={set('name')} required />
          <TextField label="Father's Name" value={form.father_name} onChange={set('father_name')} required />
          <Select value={form.class_name} onChange={(e) => setForm((f) => ({ ...f, class_name: e.target.value }))}>
            {grades?.map((g) => <MenuItem key={g.grade_id} value={g.class_name}>{g.class_name}</MenuItem>)}
          </Select>
          <TextField label="Date of Birth" type="date" value={form.dob} onChange={set('dob')} InputLabelProps={{ shrink: true }} />
          <TextField label="Admission Date" type="date" value={form.admission_date} onChange={set('admission_date')} InputLabelProps={{ shrink: true }} />
          <TextField label="B-Form No" value={form.b_form} onChange={set('b_form')} />
          <TextField label="CNIC" value={form.cnic} onChange={set('cnic')} />
          <TextField label="Phone" value={form.phone} onChange={set('phone')} />
          <TextField label="Address" value={form.address} onChange={set('address')} multiline />
          <TextField
            label="Monthly Fee (leave blank to use class default)"
            value={form.default_fee}
            onChange={set('default_fee')}
          />
          <Select value={form.status} onChange={(e) => setForm((f) => ({ ...f, status: e.target.value }))}>
            <MenuItem value="Active">Active</MenuItem>
            <MenuItem value="Inactive">Inactive</MenuItem>
          </Select>

          {role === 'Admin' && (
            <>
              <Divider sx={{ mt: 1 }} />
              <Box>
                <Typography variant="subtitle2" color="error" gutterBottom>
                  Danger Zone
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  Permanently deletes this student along with all of their fee vouchers, extra
                  charges, payment history, and attendance records. This cannot be undone.
                </Typography>
                {deleteError && <Alert severity="error" sx={{ mb: 1 }} onClose={() => setDeleteError(null)}>{deleteError}</Alert>}
                <Button
                  color="error"
                  variant="outlined"
                  disabled={deleteMutation.isPending}
                  onClick={handleDelete}
                >
                  {deleteMutation.isPending ? 'Deleting…' : 'Delete Student'}
                </Button>
              </Box>
            </>
          )}
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button variant="contained" disabled={!canSave} onClick={() => mutation.mutate()}>Save Changes</Button>
      </DialogActions>
    </Dialog>
  )
}
