import { useMemo, useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { DataGrid, type GridColDef, type GridRowSelectionModel } from '@mui/x-data-grid'
import {
  Alert, Box, Button, MenuItem, Select, TextField, ToggleButton, ToggleButtonGroup, Typography,
} from '@mui/material'
import { getAbsentToday } from '../api/attendance'
import { getPendingReport } from '../api/feeReports'
import { listStudents } from '../api/students'
import { listGrades } from '../api/grades'
import { getSchool } from '../api/school'
import {
  createQueueEntriesBulk, listTemplates, renderTemplate,
  type NotificationCategory, type ProviderType, type QueueCreate,
} from '../api/communication'
import { useAuth } from '../context/AuthContext'

type Mode = 'absent' | 'fee' | 'custom'

interface Candidate {
  student_id: number
  name: string
  father_name: string
  class_name: string
  phone: string | null
  total_pending?: number
}

const MODE_LABEL: Record<Mode, string> = {
  absent: 'Absent Today', fee: 'Pending Fee', custom: 'Custom Message',
}
const MODE_NOTIFICATION_TYPE: Record<Mode, NotificationCategory> = {
  absent: 'attendance_absent', fee: 'fee_reminder', custom: 'custom',
}
const MODE_TEMPLATE_NAME: Record<Mode, string> = {
  absent: 'Attendance Absent', fee: 'Pending Fee', custom: 'Custom Message',
}

export function BulkSendPanel() {
  const { role } = useAuth()
  const allowedModes: Mode[] = role === 'Accountant' ? ['fee', 'custom'] : ['absent', 'fee', 'custom']
  const [mode, setMode] = useState<Mode>(allowedModes[0])
  const [classFilter, setClassFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('Unpaid')
  const [searchQuery, setSearchQuery] = useState('')
  const [channel, setChannel] = useState<ProviderType>('sms')
  const [customMessage, setCustomMessage] = useState('')
  const [selection, setSelection] = useState<GridRowSelectionModel>([])
  const [result, setResult] = useState<string | null>(null)

  const { data: grades } = useQuery({ queryKey: ['grades'], queryFn: listGrades })
  const { data: school } = useQuery({ queryKey: ['school'], queryFn: getSchool })
  const { data: templates } = useQuery({ queryKey: ['communication-templates'], queryFn: listTemplates })

  const { data: absentRows, isFetching: absentLoading } = useQuery({
    queryKey: ['bulk-absent-today', classFilter],
    queryFn: () => getAbsentToday({ class_name: classFilter || undefined }),
    enabled: mode === 'absent',
  })
  const { data: feeRows, isFetching: feeLoading } = useQuery({
    queryKey: ['bulk-pending-fee', classFilter, statusFilter],
    queryFn: () => getPendingReport({ class_names: classFilter ? [classFilter] : [], status_filter: statusFilter }),
    enabled: mode === 'fee',
  })
  const { data: customRows, isFetching: customLoading } = useQuery({
    queryKey: ['bulk-custom-search', searchQuery, classFilter],
    queryFn: () => listStudents({ search: searchQuery, class_filter: classFilter || undefined }),
    enabled: mode === 'custom' && (searchQuery.length > 0 || !!classFilter),
  })

  const candidates: Candidate[] = useMemo(() => {
    if (mode === 'absent') {
      return (absentRows ?? []).map((r) => ({
        student_id: r.student_id, name: r.name, father_name: r.father_name, class_name: r.class_name, phone: r.phone,
      }))
    }
    if (mode === 'fee') {
      return (feeRows ?? []).filter((r) => r.total_pending > 0).map((r) => ({
        student_id: r.student_id, name: r.name, father_name: r.father_name, class_name: r.class_name,
        phone: r.phone, total_pending: r.total_pending,
      }))
    }
    return (customRows ?? []).map((r) => ({
      student_id: r.student_id, name: r.name, father_name: r.father_name, class_name: r.class_name, phone: r.phone,
    }))
  }, [mode, absentRows, feeRows, customRows])

  const loading = mode === 'absent' ? absentLoading : mode === 'fee' ? feeLoading : customLoading

  const template = templates?.find((t) => t.name === MODE_TEMPLATE_NAME[mode])

  function renderFor(candidate: Candidate): string {
    if (mode === 'custom') {
      return renderTemplate(customMessage, {
        student_name: candidate.name, parent_name: candidate.father_name, class: candidate.class_name,
        date: new Date().toLocaleDateString(), school_name: school?.name ?? '',
      })
    }
    return renderTemplate(template?.message ?? '', {
      student_name: candidate.name,
      parent_name: candidate.father_name,
      class: candidate.class_name,
      date: new Date().toLocaleDateString(),
      school_name: school?.name ?? '',
      remaining_fee: (candidate.total_pending ?? 0).toFixed(0),
      voucher_no: 'N/A',
    })
  }

  const sendMutation = useMutation({
    mutationFn: (payload: QueueCreate[]) => createQueueEntriesBulk(payload),
    onSuccess: (rows) => { setResult(`Queued ${rows.length} message(s).`); setSelection([]) },
    onError: (e) => setResult(`Failed: ${String((e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? e)}`),
  })

  const selectedIds = new Set(Array.isArray(selection) ? selection : [])
  const selectedCandidates = candidates.filter((c) => selectedIds.has(c.student_id))
  const skippedNoPhone = selectedCandidates.filter((c) => !c.phone).length

  function handleSend() {
    const payload: QueueCreate[] = selectedCandidates
      .filter((c) => !!c.phone)
      .map((c) => ({
        student_id: c.student_id,
        recipient_name: c.name,
        provider_type: channel,
        notification_type: MODE_NOTIFICATION_TYPE[mode],
        recipient: c.phone as string,
        message: renderFor(c),
      }))
    if (payload.length > 0) sendMutation.mutate(payload)
  }

  const columns: GridColDef<Candidate>[] = [
    { field: 'name', headerName: 'Name', flex: 1 },
    { field: 'father_name', headerName: "Father's Name", flex: 1 },
    { field: 'class_name', headerName: 'Class', width: 110 },
    { field: 'phone', headerName: 'Phone', width: 130, valueGetter: (_v, row) => row.phone ?? 'No phone' },
    ...(mode === 'fee' ? [{ field: 'total_pending', headerName: 'Pending (Rs.)', width: 130, type: 'number' as const }] : []),
  ]

  return (
    <Box>
      <ToggleButtonGroup
        value={mode}
        exclusive
        size="small"
        onChange={(_e, v) => { if (v) { setMode(v); setSelection([]); setResult(null) } }}
        sx={{ mb: 2 }}
      >
        {allowedModes.map((m) => (
          <ToggleButton key={m} value={m}>{MODE_LABEL[m]}</ToggleButton>
        ))}
      </ToggleButtonGroup>

      <Box sx={{ display: 'flex', gap: 2, mb: 2, flexWrap: 'wrap', alignItems: 'center' }}>
        <Select size="small" value={classFilter} onChange={(e) => setClassFilter(e.target.value)} displayEmpty sx={{ width: 160 }}>
          <MenuItem value="">All Classes</MenuItem>
          {grades?.map((g) => <MenuItem key={g.grade_id} value={g.class_name}>{g.class_name}</MenuItem>)}
        </Select>
        {mode === 'fee' && (
          <Select size="small" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} sx={{ width: 150 }}>
            <MenuItem value="Unpaid">Unpaid</MenuItem>
            <MenuItem value="Partial">Partial</MenuItem>
            <MenuItem value="Overdue">Overdue</MenuItem>
          </Select>
        )}
        {mode === 'custom' && (
          <TextField
            size="small" label="Search students by name" value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)} sx={{ width: 250 }}
          />
        )}
        <Select size="small" value={channel} onChange={(e) => setChannel(e.target.value as ProviderType)} sx={{ width: 130 }}>
          <MenuItem value="sms">SMS</MenuItem>
          <MenuItem value="whatsapp">WhatsApp</MenuItem>
        </Select>
      </Box>

      {mode === 'custom' && (
        <TextField
          fullWidth multiline minRows={3} label="Message (supports {{student_name}}, {{parent_name}}, {{class}}, {{date}}, {{school_name}})"
          value={customMessage} onChange={(e) => setCustomMessage(e.target.value)} sx={{ mb: 2 }}
        />
      )}

      <Box sx={{ height: 420, mb: 2 }}>
        <DataGrid
          rows={candidates}
          columns={columns}
          getRowId={(row) => row.student_id}
          loading={loading}
          density="compact"
          checkboxSelection
          rowSelectionModel={selection}
          onRowSelectionModelChange={setSelection}
        />
      </Box>

      {selectedCandidates.length > 0 && (
        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
          Preview ({selectedCandidates[0].name}): {renderFor(selectedCandidates[0]) || '—'}
        </Typography>
      )}
      {skippedNoPhone > 0 && (
        <Alert severity="warning" sx={{ mb: 2 }}>{skippedNoPhone} of the selected students have no phone on file and will be skipped.</Alert>
      )}
      {result && <Alert severity={result.startsWith('Failed') ? 'error' : 'success'} sx={{ mb: 2 }}>{result}</Alert>}

      <Button
        variant="contained"
        disabled={selectedCandidates.length === 0 || (mode === 'custom' && !customMessage.trim()) || sendMutation.isPending}
        onClick={handleSend}
      >
        Send to {selectedCandidates.length} Selected
      </Button>
    </Box>
  )
}
