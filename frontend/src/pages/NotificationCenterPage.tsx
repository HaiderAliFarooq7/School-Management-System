import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Autocomplete, Box, Button, Chip, MenuItem, Select, Table, TableBody, TableCell, TableHead,
  TableRow, TextField, Typography,
} from '@mui/material'
import {
  listNotificationLog, sendNotification, type Audience, type NotifType,
} from '../api/parents'
import { listGrades } from '../api/grades'
import { listStudents, type Student } from '../api/students'
import { useAuth } from '../context/AuthContext'

function apiErrorMessage(e: unknown): string {
  return String((e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? e)
}

const TYPE_LABELS: Record<NotifType, string> = {
  announcement: 'Announcement',
  fee_reminder: 'Fee Reminder',
  absent: 'Absent Alert',
}
const AUDIENCE_LABELS: Record<Audience, string> = {
  student: 'One Student',
  class: 'A Class',
  school: 'Whole School',
}

export function NotificationCenterPage() {
  const queryClient = useQueryClient()
  const { role } = useAuth()
  // Accountants may only send fee reminders; Admins may send anything.
  const isAccountant = role === 'Accountant'
  const allowedTypes: NotifType[] = isAccountant ? ['fee_reminder'] : ['announcement', 'fee_reminder', 'absent']

  const [notifType, setNotifType] = useState<NotifType>(allowedTypes[0])
  const [audience, setAudience] = useState<Audience>('school')
  const [title, setTitle] = useState('')
  const [body, setBody] = useState('')
  const [className, setClassName] = useState('')
  const [student, setStudent] = useState<Student | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)

  const { data: grades } = useQuery({ queryKey: ['grades'], queryFn: listGrades })
  const { data: students } = useQuery({
    queryKey: ['students', 'notif'],
    queryFn: () => listStudents({}),
    enabled: audience === 'student',
  })
  const { data: log } = useQuery({ queryKey: ['notif-log'], queryFn: () => listNotificationLog(100) })

  const canSend = useMemo(() => {
    if (!title.trim() || !body.trim()) return false
    if (audience === 'student' && !student) return false
    if (audience === 'class' && !className) return false
    return true
  }, [title, body, audience, student, className])

  const sendMutation = useMutation({
    mutationFn: () =>
      sendNotification({
        notif_type: notifType,
        audience,
        title: title.trim(),
        body: body.trim(),
        student_id: audience === 'student' ? student?.student_id ?? null : null,
        class_name: audience === 'class' ? className : null,
      }),
    onSuccess: (res) => {
      queryClient.invalidateQueries({ queryKey: ['notif-log'] })
      setError(null)
      setNotice(`Sent to ${res.recipients_count} parent(s) · ${res.delivered_count} delivered, ${res.failed_count} failed.`)
      setTitle('')
      setBody('')
    },
    onError: (e) => { setNotice(null); setError(apiErrorMessage(e)) },
  })

  return (
    <Box>
      <Typography variant="h5" gutterBottom>Notification Center</Typography>
      {isAccountant && (
        <Typography color="text.secondary" sx={{ mb: 1 }}>
          As an Accountant you can send fee reminders.
        </Typography>
      )}
      {notice && <Typography color="primary" sx={{ mb: 1 }}>{notice}</Typography>}
      {error && <Typography color="error" sx={{ mb: 1 }}>{error}</Typography>}

      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, maxWidth: 640, mb: 4 }}>
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
          <Select size="small" value={notifType} onChange={(e) => setNotifType(e.target.value as NotifType)} sx={{ minWidth: 180 }}>
            {allowedTypes.map((t) => <MenuItem key={t} value={t}>{TYPE_LABELS[t]}</MenuItem>)}
          </Select>
          <Select size="small" value={audience} onChange={(e) => setAudience(e.target.value as Audience)} sx={{ minWidth: 180 }}>
            {(['school', 'class', 'student'] as Audience[]).map((a) => (
              <MenuItem key={a} value={a}>{AUDIENCE_LABELS[a]}</MenuItem>
            ))}
          </Select>
        </Box>

        {audience === 'class' && (
          <Select size="small" value={className} onChange={(e) => setClassName(e.target.value)} displayEmpty sx={{ maxWidth: 260 }}>
            <MenuItem value="">Select class…</MenuItem>
            {grades?.map((g) => <MenuItem key={g.grade_id} value={g.class_name}>{g.class_name}</MenuItem>)}
          </Select>
        )}
        {audience === 'student' && (
          <Autocomplete
            options={students ?? []}
            value={student}
            onChange={(_, v) => setStudent(v)}
            getOptionLabel={(s) => `${s.name} — ${s.registration_no} (${s.class_name})`}
            isOptionEqualToValue={(a, b) => a.student_id === b.student_id}
            renderInput={(params) => <TextField {...params} size="small" label="Select student" />}
            sx={{ maxWidth: 420 }}
          />
        )}

        <TextField label="Title" size="small" value={title} onChange={(e) => setTitle(e.target.value)} inputProps={{ maxLength: 150 }} />
        <TextField label="Message" size="small" multiline minRows={3} value={body} onChange={(e) => setBody(e.target.value)} inputProps={{ maxLength: 2000 }} />
        <Box>
          <Button variant="contained" disabled={!canSend || sendMutation.isPending} onClick={() => sendMutation.mutate()}>
            {sendMutation.isPending ? 'Sending…' : 'Send Notification'}
          </Button>
        </Box>
      </Box>

      <Typography variant="h6" gutterBottom>Notification History</Typography>
      <Box sx={{ overflowX: 'auto' }}>
        <Table size="small" sx={{ minWidth: 900 }}>
          <TableHead>
            <TableRow>
              <TableCell>When</TableCell>
              <TableCell>Type</TableCell>
              <TableCell>Audience</TableCell>
              <TableCell>Title</TableCell>
              <TableCell align="center">Recipients</TableCell>
              <TableCell align="center">Delivered</TableCell>
              <TableCell align="center">Failed</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {log?.map((row) => (
              <TableRow key={row.log_id}>
                <TableCell>{new Date(row.created_at).toLocaleString()}</TableCell>
                <TableCell><Chip size="small" label={TYPE_LABELS[row.notif_type]} /></TableCell>
                <TableCell>{AUDIENCE_LABELS[row.audience]}{row.class_name ? ` · ${row.class_name}` : ''}</TableCell>
                <TableCell>{row.title}</TableCell>
                <TableCell align="center">{row.recipients_count}</TableCell>
                <TableCell align="center">{row.delivered_count}</TableCell>
                <TableCell align="center">{row.failed_count}</TableCell>
              </TableRow>
            ))}
            {log?.length === 0 && (
              <TableRow><TableCell colSpan={7}><Typography color="text.secondary" sx={{ py: 2 }}>No notifications sent yet.</Typography></TableCell></TableRow>
            )}
          </TableBody>
        </Table>
      </Box>
    </Box>
  )
}
