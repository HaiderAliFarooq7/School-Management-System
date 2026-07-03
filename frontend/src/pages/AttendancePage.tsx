import { useEffect, useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Alert, Box, Button, MenuItem, Select, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, TextField, ToggleButton, ToggleButtonGroup, Typography,
} from '@mui/material'
import { listGrades } from '../api/grades'
import { listStudents } from '../api/students'
import { getAttendanceForClassDate, getAttendanceSummary, markAttendance } from '../api/attendance'
import { useAuth } from '../context/AuthContext'

const STATUSES = ['Present', 'Absent', 'Late', 'Leave']

function todayIso() {
  return new Date().toISOString().slice(0, 10)
}

export function AttendancePage() {
  const { role, assignedClassName } = useAuth()
  const queryClient = useQueryClient()
  const { data: grades } = useQuery({ queryKey: ['grades'], queryFn: listGrades })

  const [className, setClassName] = useState(role === 'Teacher' ? assignedClassName ?? '' : '')
  const [date, setDate] = useState(todayIso())
  const [marks, setMarks] = useState<Record<number, string>>({})
  const [saveMessage, setSaveMessage] = useState<{ text: string; severity: 'success' | 'error' } | null>(null)

  const { data: students } = useQuery({
    queryKey: ['students', '', className, 'Active'],
    queryFn: () => listStudents({ class_filter: className, status_filter: 'Active' }),
    enabled: !!className,
  })

  const { data: existing } = useQuery({
    queryKey: ['attendance', className, date],
    queryFn: () => getAttendanceForClassDate(className, date),
    enabled: !!className,
  })

  // Sync `marks` from `existing` once per class/date selection, not on every
  // background refetch of the same selection (e.g. window refocus) — a plain
  // `[existing]` dependency would otherwise silently overwrite any
  // in-progress unsaved edits whenever react-query refetches in the background.
  const lastSyncedKeyRef = useRef('')
  useEffect(() => {
    const key = `${className}|${date}`
    if (existing && lastSyncedKeyRef.current !== key) {
      const map: Record<number, string> = {}
      existing.forEach((r) => { map[r.student_id] = r.status })
      setMarks(map)
      lastSyncedKeyRef.current = key
    }
  }, [existing, className, date])

  const markMutation = useMutation({
    mutationFn: () =>
      markAttendance(
        className,
        date,
        (students ?? []).map((s) => ({ student_id: s.student_id, status: marks[s.student_id] ?? 'Present' })),
      ),
    onSuccess: () => {
      setSaveMessage({ text: 'Attendance saved.', severity: 'success' })
      queryClient.invalidateQueries({ queryKey: ['attendance', className, date] })
    },
    onError: () => setSaveMessage({ text: 'Could not save attendance. Please try again.', severity: 'error' }),
  })

  const { data: summary } = useQuery({
    queryKey: ['attendance-summary', className, date],
    queryFn: () => getAttendanceSummary(className, date.slice(0, 8) + '01', date),
    enabled: !!className,
  })

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        Attendance
      </Typography>
      {saveMessage && (
        <Alert severity={saveMessage.severity} sx={{ mb: 2 }} onClose={() => setSaveMessage(null)}>
          {saveMessage.text}
        </Alert>
      )}
      <Box sx={{ display: 'flex', gap: 2, mb: 2, flexWrap: 'wrap', alignItems: 'center' }}>
        <Select
          size="small"
          value={className}
          onChange={(e) => setClassName(e.target.value)}
          displayEmpty
          disabled={role === 'Teacher'}
          sx={{ width: { xs: '100%', sm: 180 } }}
        >
          <MenuItem value="" disabled>Select a class</MenuItem>
          {/* Teachers may only ever mark their own assigned class. */}
          {(role === 'Teacher'
            ? grades?.filter((g) => g.class_name === assignedClassName)
            : grades
          )?.map((g) => <MenuItem key={g.grade_id} value={g.class_name}>{g.class_name}</MenuItem>)}
        </Select>
        <TextField type="date" size="small" value={date} onChange={(e) => setDate(e.target.value)} />
        <Button variant="contained" disabled={!className || !students?.length} onClick={() => markMutation.mutate()}>
          Save Attendance
        </Button>
        <Button
          onClick={() => {
            const all: Record<number, string> = {}
            students?.forEach((s) => { all[s.student_id] = 'Present' })
            setMarks(all)
          }}
        >
          Mark All Present
        </Button>
      </Box>

      {className && (
        <TableContainer sx={{ maxWidth: 700, mb: 4 }}>
          <Table size="small" sx={{ minWidth: 540 }}>
          <TableHead>
            <TableRow>
              <TableCell>Reg No</TableCell>
              <TableCell>Name</TableCell>
              <TableCell>Status</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {students?.map((s) => (
              <TableRow key={s.student_id}>
                <TableCell>{s.registration_no}</TableCell>
                <TableCell>{s.name}</TableCell>
                <TableCell>
                  <ToggleButtonGroup
                    size="small"
                    exclusive
                    value={marks[s.student_id] ?? 'Present'}
                    onChange={(_, v) => v && setMarks((prev) => ({ ...prev, [s.student_id]: v }))}
                  >
                    {STATUSES.map((st) => (
                      <ToggleButton key={st} value={st}>{st}</ToggleButton>
                    ))}
                  </ToggleButtonGroup>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
          </Table>
        </TableContainer>
      )}

      {summary && summary.length > 0 && (
        <>
          <Typography variant="h6" gutterBottom>
            This Month's Summary
          </Typography>
          <TableContainer sx={{ maxWidth: 700 }}>
            <Table size="small" sx={{ minWidth: 560 }}>
            <TableHead>
              <TableRow>
                <TableCell>Reg No</TableCell>
                <TableCell>Name</TableCell>
                <TableCell>Present</TableCell>
                <TableCell>Absent</TableCell>
                <TableCell>Late</TableCell>
                <TableCell>Leave</TableCell>
                <TableCell>% Present</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {summary.map((row) => (
                <TableRow key={row.student_id}>
                  <TableCell>{row.registration_no}</TableCell>
                  <TableCell>{row.name}</TableCell>
                  <TableCell>{row.present}</TableCell>
                  <TableCell>{row.absent}</TableCell>
                  <TableCell>{row.late}</TableCell>
                  <TableCell>{row.leave}</TableCell>
                  <TableCell>{row.pct_present.toFixed(0)}%</TableCell>
                </TableRow>
              ))}
            </TableBody>
            </Table>
          </TableContainer>
        </>
      )}
    </Box>
  )
}
