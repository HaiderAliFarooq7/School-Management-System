import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Alert, Box, Button, MenuItem, Select, TextField, Typography } from '@mui/material'
import { listGrades } from '../api/grades'
import { createStudent } from '../api/students'

export function AdmissionPage() {
  const queryClient = useQueryClient()
  const { data: grades } = useQuery({ queryKey: ['grades'], queryFn: listGrades })

  const [form, setForm] = useState({
    name: '', father_name: '', class_name: '', dob: '', admission_date: '',
    b_form: '', cnic: '', phone: '', address: '', default_fee: '',
  })
  const [result, setResult] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const grade = grades?.find((g) => g.class_name === form.class_name)

  const mutation = useMutation({
    mutationFn: () =>
      createStudent({
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
      }),
    onSuccess: (student) => {
      setResult(`Admitted: ${student.registration_no} — ${student.name}`)
      setError(null)
      queryClient.invalidateQueries({ queryKey: ['students'] })
      setForm({ name: '', father_name: '', class_name: '', dob: '', admission_date: '', b_form: '', cnic: '', phone: '', address: '', default_fee: '' })
    },
    onError: (e) => {
      setError(String((e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? 'Admission failed. Please try again.'))
    },
  })

  const set = (field: string) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((f) => ({ ...f, [field]: e.target.value }))

  return (
    <Box sx={{ maxWidth: 600 }}>
      <Typography variant="h5" gutterBottom>
        New Admission
      </Typography>
      {result && <Alert severity="success" sx={{ mb: 2 }}>{result}</Alert>}
      {error && <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>{error}</Alert>}
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        <TextField label="Student Name" value={form.name} onChange={set('name')} required />
        <TextField label="Father's Name" value={form.father_name} onChange={set('father_name')} required />
        <Select value={form.class_name} onChange={(e) => setForm((f) => ({ ...f, class_name: e.target.value }))} displayEmpty>
          <MenuItem value="" disabled>Select Class</MenuItem>
          {grades?.map((g) => <MenuItem key={g.grade_id} value={g.class_name}>{g.class_name}</MenuItem>)}
        </Select>
        <TextField label="Date of Birth" type="date" value={form.dob} onChange={set('dob')} InputLabelProps={{ shrink: true }} />
        <TextField label="Admission Date" type="date" value={form.admission_date} onChange={set('admission_date')} InputLabelProps={{ shrink: true }} />
        <TextField label="B-Form No" value={form.b_form} onChange={set('b_form')} />
        <TextField label="CNIC" value={form.cnic} onChange={set('cnic')} />
        <TextField label="Phone" value={form.phone} onChange={set('phone')} />
        <TextField label="Address" value={form.address} onChange={set('address')} multiline />
        <TextField
          label={`Monthly Fee (leave blank to use class default${grade ? `: Rs. ${grade.fee_amount}` : ''})`}
          value={form.default_fee}
          onChange={set('default_fee')}
          helperText="Enter this student's own fee here if it differs from the class default — bulk voucher generation will use it automatically."
        />
        <Button
          variant="contained"
          onClick={() => mutation.mutate()}
          disabled={!form.name || !form.father_name || !form.class_name}
        >
          Admit Student
        </Button>
      </Box>
    </Box>
  )
}
