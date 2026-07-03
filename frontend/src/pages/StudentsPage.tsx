import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { DataGrid, type GridColDef, type GridRowSelectionModel } from '@mui/x-data-grid'
import {
  Box, Button, Chip, Menu, MenuItem, Select, TextField, Typography,
} from '@mui/material'
import { useNavigate } from 'react-router-dom'
import { listStudents, type Student } from '../api/students'
import { listGrades } from '../api/grades'
import { exportStudents } from '../api/studentImport'
import { StudentEditDialog } from '../components/StudentEditDialog'
import { StudentImportWizard } from '../components/StudentImportWizard'
import { useAuth } from '../context/AuthContext'
import { useDebouncedValue } from '../hooks/useDebouncedValue'

export function StudentsPage() {
  const navigate = useNavigate()
  const { role } = useAuth()
  const isAdmin = role === 'Admin'
  const [search, setSearch] = useState('')
  const [classFilter, setClassFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('Active')
  const [editing, setEditing] = useState<Student | null>(null)
  const [selectionModel, setSelectionModel] = useState<GridRowSelectionModel>([])
  const [importOpen, setImportOpen] = useState(false)
  const [exportAnchor, setExportAnchor] = useState<null | HTMLElement>(null)
  const [exportFormat, setExportFormat] = useState<'xlsx' | 'csv'>('xlsx')

  const debouncedSearch = useDebouncedValue(search)
  const { data: grades } = useQuery({ queryKey: ['grades'], queryFn: listGrades })
  const { data: students, isLoading, isError } = useQuery({
    queryKey: ['students', debouncedSearch, classFilter, statusFilter],
    queryFn: () => listStudents({ search: debouncedSearch, class_filter: classFilter, status_filter: statusFilter }),
  })

  const selectedIds = Array.from(selectionModel as Iterable<number>)

  function handleExport(scope: 'all' | 'selected' | 'filtered' | 'search') {
    setExportAnchor(null)
    exportStudents({
      format: exportFormat,
      scope,
      student_ids: scope === 'selected' ? selectedIds : undefined,
      search: scope === 'search' ? search : undefined,
      class_filter: scope === 'filtered' ? classFilter : undefined,
      status_filter: scope === 'filtered' ? statusFilter : undefined,
    })
  }

  const columns: GridColDef<Student>[] = [
    { field: 'registration_no', headerName: 'Reg No', width: 110 },
    { field: 'name', headerName: 'Name', flex: 1 },
    { field: 'father_name', headerName: "Father's Name", flex: 1 },
    { field: 'class_name', headerName: 'Class', width: 100 },
    { field: 'phone', headerName: 'Phone', width: 130 },
    {
      field: 'status',
      headerName: 'Status',
      width: 110,
      renderCell: (params) => (
        <Chip size="small" label={params.value} color={params.value === 'Active' ? 'success' : 'default'} />
      ),
    },
    {
      field: 'fee_status',
      headerName: 'Fee Status',
      width: 120,
      renderCell: (params) => {
        const colorMap: Record<string, 'success' | 'warning' | 'error' | 'default'> = {
          Paid: 'success', Partial: 'warning', Unpaid: 'error',
        }
        return <Chip size="small" label={params.value} color={colorMap[params.value] ?? 'default'} />
      },
    },
    { field: 'total_pending', headerName: 'Pending (Rs.)', width: 130, type: 'number' },
    {
      field: 'actions',
      headerName: 'Actions',
      width: 180,
      sortable: false,
      renderCell: (params) => (
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button size="small" onClick={() => navigate(`/fees/student/${params.row.student_id}`)}>
            View Dues
          </Button>
          <Button size="small" onClick={() => setEditing(params.row)}>
            Edit
          </Button>
        </Box>
      ),
    },
  ]

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2, flexWrap: 'wrap', gap: 1 }}>
        <Typography variant="h5">Students</Typography>
        {isAdmin && (
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            <Button variant="outlined" onClick={() => setImportOpen(true)}>Import Students</Button>
            <Select size="small" value={exportFormat} onChange={(e) => setExportFormat(e.target.value as 'xlsx' | 'csv')} sx={{ width: 90 }}>
              <MenuItem value="xlsx">.xlsx</MenuItem>
              <MenuItem value="csv">.csv</MenuItem>
            </Select>
            <Button variant="outlined" onClick={(e) => setExportAnchor(e.currentTarget)}>Export</Button>
            <Menu anchorEl={exportAnchor} open={!!exportAnchor} onClose={() => setExportAnchor(null)}>
              <MenuItem onClick={() => handleExport('all')}>All Students</MenuItem>
              <MenuItem disabled={selectedIds.length === 0} onClick={() => handleExport('selected')}>
                Selected ({selectedIds.length})
              </MenuItem>
              <MenuItem disabled={!classFilter && !statusFilter} onClick={() => handleExport('filtered')}>
                Filtered (class/status)
              </MenuItem>
              <MenuItem disabled={!search} onClick={() => handleExport('search')}>Current Search Results</MenuItem>
            </Menu>
          </Box>
        )}
      </Box>
      {isError && <Typography color="error" sx={{ mb: 2 }}>Could not load students. Please try again.</Typography>}
      <Box sx={{ display: 'flex', gap: 2, mb: 2, flexWrap: 'wrap' }}>
        <TextField
          label="Search name / reg no / CNIC"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          size="small"
          sx={{ width: { xs: '100%', sm: 280 } }}
        />
        <Select size="small" value={classFilter} onChange={(e) => setClassFilter(e.target.value)} displayEmpty sx={{ width: 160 }}>
          <MenuItem value="">All Classes</MenuItem>
          {grades?.map((g) => <MenuItem key={g.grade_id} value={g.class_name}>{g.class_name}</MenuItem>)}
        </Select>
        <Select size="small" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} sx={{ width: 140 }}>
          <MenuItem value="">All</MenuItem>
          <MenuItem value="Active">Active</MenuItem>
          <MenuItem value="Inactive">Inactive</MenuItem>
        </Select>
      </Box>
      <Box sx={{ height: 600 }}>
        <DataGrid
          rows={students ?? []}
          columns={columns}
          getRowId={(row) => row.student_id}
          loading={isLoading}
          density="compact"
          checkboxSelection={isAdmin}
          rowSelectionModel={selectionModel}
          onRowSelectionModelChange={setSelectionModel}
        />
      </Box>

      <StudentEditDialog student={editing} open={!!editing} onClose={() => setEditing(null)} />
      <StudentImportWizard open={importOpen} onClose={() => setImportOpen(false)} />
    </Box>
  )
}
