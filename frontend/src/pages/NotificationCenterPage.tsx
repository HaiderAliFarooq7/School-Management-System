import { useEffect, useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Autocomplete, Box, Button, Chip, Divider, FormControlLabel, MenuItem, Paper, Select, Switch,
  Table, TableBody, TableCell, TableHead, TableRow, TextField, Typography,
} from '@mui/material'
import {
  getNotifSettings, listNotificationLog, notifyAllAbsentees, sendNotification, updateNotifSettings,
  type Audience, type NotifType,
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

interface Template { label: string; title: string; body: string }

// Editable templates per type. Placeholders in [brackets] are filled in by the
// admin before sending; the fee-dues template auto-fills name/class/amount from
// the selected student.
const TEMPLATES: Record<NotifType, Template[]> = {
  announcement: [
    { label: 'Custom (blank)', title: '', body: '' },
    { label: 'General notice', title: 'School Announcement', body: 'Dear Parents, ' },
    { label: 'Holiday notice', title: 'Holiday Notice', body: 'Dear Parents, the school will remain closed on [date] on account of [reason]. Classes resume the next working day.' },
    { label: 'Parent-Teacher Meeting', title: 'Parent-Teacher Meeting', body: 'Dear Parents, a Parent-Teacher Meeting is scheduled on [date] at [time]. Your presence is requested.' },
    { label: 'Event', title: 'Upcoming Event', body: 'Dear Parents, [event] will be held on [date]. All students are encouraged to participate.' },
    { label: 'Exam schedule', title: 'Exam Schedule', body: 'Dear Parents, the [term] examinations will begin on [date]. Please ensure your child is well prepared.' },
    { label: 'Fee due date', title: 'Fee Due Reminder', body: 'Dear Parents, this month\'s fee is due by [date]. Kindly clear the dues at the school office to avoid a late fee.' },
  ],
  fee_reminder: [
    { label: 'Custom (blank)', title: '', body: '' },
    { label: 'Student dues (auto-fill)', title: 'Fee Reminder', body: 'Dear Parent, [amount] is pending for [student] ([class]). Kindly submit the remaining dues at the school office. Thank you.' },
    { label: 'General fee reminder', title: 'Fee Reminder', body: 'Dear Parents, please clear any outstanding fee dues at the school office at your earliest convenience.' },
  ],
  absent: [
    { label: 'Custom (blank)', title: '', body: '' },
    { label: 'Absent alert', title: 'Attendance Alert', body: 'Dear Parent, your child [student] ([class]) was marked absent today. Please contact the school office if this is unexpected.' },
  ],
}

function fillDuesTemplate(student: Student | null): { title: string; body: string } {
  const amount = `Rs. ${(student?.total_pending ?? 0).toLocaleString()}`
  const name = student?.name ?? '[student]'
  const klass = student?.class_name ?? '[class]'
  return {
    title: 'Fee Reminder',
    body: `Dear Parent, ${amount} is pending for ${name} (${klass}). Kindly submit the remaining dues at the school office. Thank you.`,
  }
}

export function NotificationCenterPage() {
  const queryClient = useQueryClient()
  const { role } = useAuth()
  const isAdmin = role === 'Admin'
  const isAccountant = role === 'Accountant'
  const allowedTypes: NotifType[] = isAccountant ? ['fee_reminder'] : ['announcement', 'fee_reminder', 'absent']

  const [notifType, setNotifType] = useState<NotifType>(allowedTypes[0])
  const [audience, setAudience] = useState<Audience>('school')
  const [title, setTitle] = useState('')
  const [body, setBody] = useState('')
  const [className, setClassName] = useState('')
  const [student, setStudent] = useState<Student | null>(null)
  const [templateLabel, setTemplateLabel] = useState('Custom (blank)')
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)

  const { data: grades } = useQuery({ queryKey: ['grades'], queryFn: listGrades })
  const { data: students } = useQuery({
    queryKey: ['students', 'notif'],
    queryFn: () => listStudents({}),
    enabled: audience === 'student',
  })
  const { data: log } = useQuery({ queryKey: ['notif-log'], queryFn: () => listNotificationLog(100) })
  const { data: settings } = useQuery({
    queryKey: ['notif-settings'],
    queryFn: getNotifSettings,
    enabled: isAdmin,
  })

  const templates = TEMPLATES[notifType]

  // Reset template when the type changes and it no longer applies.
  useEffect(() => {
    setTemplateLabel('Custom (blank)')
  }, [notifType])

  // Re-fill the dues template whenever the selected student changes.
  useEffect(() => {
    if (notifType === 'fee_reminder' && templateLabel.startsWith('Student dues') && student) {
      const t = fillDuesTemplate(student)
      setTitle(t.title)
      setBody(t.body)
    }
  }, [student, templateLabel, notifType])

  function applyTemplate(label: string) {
    setTemplateLabel(label)
    const t = templates.find((x) => x.label === label)
    if (!t) return
    if (label.startsWith('Student dues')) {
      const filled = fillDuesTemplate(student)
      setTitle(filled.title)
      setBody(filled.body)
    } else {
      setTitle(t.title)
      setBody(t.body)
    }
  }

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
      setTemplateLabel('Custom (blank)')
    },
    onError: (e) => { setNotice(null); setError(apiErrorMessage(e)) },
  })

  const absenteesMutation = useMutation({
    mutationFn: () => notifyAllAbsentees(),
    onSuccess: (res) => {
      queryClient.invalidateQueries({ queryKey: ['notif-log'] })
      setError(null)
      setNotice(res.detail)
    },
    onError: (e) => { setNotice(null); setError(apiErrorMessage(e)) },
  })

  const toggleAutoNotify = useMutation({
    mutationFn: (value: boolean) => updateNotifSettings(value),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['notif-settings'] }),
    onError: (e) => setError(apiErrorMessage(e)),
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

      {/* Admin-only controls: auto-notify toggle + one-click absentees broadcast. */}
      {isAdmin && (
        <Paper variant="outlined" sx={{ p: 2, mb: 3, maxWidth: 700 }}>
          <FormControlLabel
            control={
              <Switch
                checked={settings?.auto_notify_absent ?? true}
                onChange={(e) => toggleAutoNotify.mutate(e.target.checked)}
              />
            }
            label="Automatically notify parents when a student is marked absent"
          />
          <Box sx={{ mt: 1 }}>
            <Button
              variant="outlined"
              disabled={absenteesMutation.isPending}
              onClick={() => absenteesMutation.mutate()}
            >
              {absenteesMutation.isPending ? 'Sending…' : 'Notify all absentees (today)'}
            </Button>
            <Typography variant="caption" color="text.secondary" sx={{ ml: 1 }}>
              Sends an absent alert to the parents of every student marked absent today.
            </Typography>
          </Box>
        </Paper>
      )}

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

        {/* Template picker — prefills an editable title + message. */}
        <Select size="small" value={templateLabel} onChange={(e) => applyTemplate(e.target.value)} sx={{ maxWidth: 320 }}>
          {templates.map((t) => <MenuItem key={t.label} value={t.label}>{t.label}</MenuItem>)}
        </Select>

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

      <Divider sx={{ mb: 2 }} />
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
