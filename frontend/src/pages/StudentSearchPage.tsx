import { useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { DataGrid, type GridColDef } from '@mui/x-data-grid'
import { Box, Button, Chip, MenuItem, Select, TextField, Typography } from '@mui/material'
import { useNavigate } from 'react-router-dom'
import { searchStudentsAdvanced, type Student, type StudentSearchParams } from '../api/students'
import { listGrades } from '../api/grades'

export function StudentSearchPage() {
  const navigate = useNavigate()
  const { data: grades } = useQuery({ queryKey: ['grades'], queryFn: listGrades })
  const [params, setParams] = useState<StudentSearchParams>({})

  const mutation = useMutation({
    mutationFn: () => searchStudentsAdvanced(params),
  })

  const set = (field: keyof StudentSearchParams) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setParams((p) => ({ ...p, [field]: e.target.value }))

  const columns: GridColDef<Student>[] = [
    { field: 'registration_no', headerName: 'Reg No', width: 110 },
    { field: 'name', headerName: 'Name', flex: 1 },
    { field: 'father_name', headerName: "Father's Name", flex: 1 },
    { field: 'class_name', headerName: 'Class', width: 100 },
    { field: 'cnic', headerName: 'CNIC', width: 130 },
    { field: 'phone', headerName: 'Phone', width: 130 },
    {
      field: 'fee_status', headerName: 'Fee Status', width: 120,
      renderCell: (p) => {
        const colorMap: Record<string, 'success' | 'warning' | 'error' | 'default'> = {
          Paid: 'success', Partial: 'warning', Unpaid: 'error', Overdue: 'error',
        }
        return <Chip size="small" label={p.value} color={colorMap[p.value as string] ?? 'default'} />
      },
    },
    { field: 'total_pending', headerName: 'Pending (Rs.)', width: 130, type: 'number' },
    {
      field: 'actions', headerName: '', width: 130, sortable: false,
      renderCell: (p) => (
        <Button size="small" onClick={() => navigate(`/fees/student/${p.row.student_id}`)}>
          View Dues
        </Button>
      ),
    },
  ]

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        Advanced Student Search
      </Typography>
      <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mb: 2, maxWidth: 1000 }}>
        <TextField label="Name" size="small" value={params.name ?? ''} onChange={set('name')} />
        <TextField label="Registration No" size="small" value={params.registration_no ?? ''} onChange={set('registration_no')} />
        <TextField label="CNIC" size="small" value={params.cnic ?? ''} onChange={set('cnic')} />
        <TextField label="Phone" size="small" value={params.phone ?? ''} onChange={set('phone')} />
        <TextField label="Father's Name" size="small" value={params.father_name ?? ''} onChange={set('father_name')} />
        <TextField label="Address" size="small" value={params.address ?? ''} onChange={set('address')} />
        <Select
          size="small"
          value={params.class_filter ?? ''}
          onChange={(e) => setParams((p) => ({ ...p, class_filter: e.target.value }))}
          displayEmpty
          sx={{ width: 150 }}
        >
          <MenuItem value="">Any Class</MenuItem>
          {grades?.map((g) => <MenuItem key={g.grade_id} value={g.class_name}>{g.class_name}</MenuItem>)}
        </Select>
        <Select
          size="small"
          value={params.status_filter ?? ''}
          onChange={(e) => setParams((p) => ({ ...p, status_filter: e.target.value }))}
          displayEmpty
          sx={{ width: 130 }}
        >
          <MenuItem value="">Any Status</MenuItem>
          <MenuItem value="Active">Active</MenuItem>
          <MenuItem value="Inactive">Inactive</MenuItem>
        </Select>
        <Select
          size="small"
          value={params.fee_status_filter ?? ''}
          onChange={(e) => setParams((p) => ({ ...p, fee_status_filter: e.target.value }))}
          displayEmpty
          sx={{ width: 150 }}
        >
          <MenuItem value="">Any Fee Status</MenuItem>
          <MenuItem value="Paid">Paid</MenuItem>
          <MenuItem value="Partial">Partial</MenuItem>
          <MenuItem value="Unpaid">Unpaid</MenuItem>
          <MenuItem value="Overdue">Overdue</MenuItem>
          <MenuItem value="No Vouchers">No Vouchers</MenuItem>
        </Select>
        <TextField label="Admission Year" size="small" value={params.admission_year ?? ''} onChange={set('admission_year')} sx={{ width: 130 }} />
        <Button variant="contained" onClick={() => mutation.mutate()}>
          Search
        </Button>
      </Box>

      <Box sx={{ height: 600 }}>
        <DataGrid
          rows={mutation.data ?? []}
          columns={columns}
          getRowId={(row) => row.student_id}
          loading={mutation.isPending}
          density="compact"
        />
      </Box>
    </Box>
  )
}
