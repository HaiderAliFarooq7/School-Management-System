import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Alert, Box, Button, Card, CardContent, Chip, Dialog, DialogActions, DialogContent, DialogTitle,
  Grid, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, TextField, Typography,
} from '@mui/material'
import AddBusinessIcon from '@mui/icons-material/AddBusiness'
import SwapHorizIcon from '@mui/icons-material/SwapHoriz'
import { useNavigate } from 'react-router-dom'
import {
  archiveSchool, createSchool, getSchoolStats, getSystemStats, listSchools,
  resetSchoolAdminPassword, setSchoolStatus, switchSchool, type MasterSchool,
} from '../api/master'
import { useConfirm, useToast } from '../components/feedback'
import { useAuth } from '../context/AuthContext'

const STATUS_COLOR: Record<string, 'success' | 'warning' | 'default'> = {
  active: 'success', disabled: 'warning', archived: 'default',
}

function apiErrorMessage(e: unknown, fallback: string): string {
  return String((e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? fallback)
}

/** Super-admin only: the SaaS control panel — every school, its status,
 * statistics, provisioning, and switching. */
export function SchoolsPage() {
  const { isSuper, school, applySession } = useAuth()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const toast = useToast()
  const confirmAction = useConfirm()
  const [createOpen, setCreateOpen] = useState(false)
  const [resetTarget, setResetTarget] = useState<MasterSchool | null>(null)

  const { data: schools, isLoading } = useQuery({ queryKey: ['master-schools'], queryFn: listSchools, enabled: isSuper })
  const { data: stats } = useQuery({ queryKey: ['master-stats'], queryFn: getSystemStats, enabled: isSuper })

  const refresh = () => queryClient.invalidateQueries({ queryKey: ['master-schools'] })

  const statusMutation = useMutation({
    mutationFn: ({ id, status }: { id: number; status: string }) => setSchoolStatus(id, status),
    onSuccess: (s) => { toast(`School "${s.school_name}" is now ${s.database_status}.`); refresh() },
    onError: (e) => toast(apiErrorMessage(e, 'Could not update the school.'), 'error'),
  })
  const archiveMutation = useMutation({
    mutationFn: (id: number) => archiveSchool(id),
    onSuccess: (s) => { toast(`School "${s.school_name}" archived. Its database is retained.`); refresh() },
    onError: (e) => toast(apiErrorMessage(e, 'Could not archive the school.'), 'error'),
  })
  const switchMutation = useMutation({
    mutationFn: (id: number) => switchSchool(id),
    onSuccess: (session) => {
      applySession(session)
      queryClient.clear()
      toast(`Now managing ${session.school_name}${session.campus_name ? ` — ${session.campus_name}` : ''}.`)
      navigate('/')
    },
    onError: (e) => toast(apiErrorMessage(e, 'Could not switch school.'), 'error'),
  })

  if (!isSuper) {
    return <Alert severity="error">Only the global super admin can manage schools.</Alert>
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2, flexWrap: 'wrap', gap: 1 }}>
        <Typography variant="h5">Schools</Typography>
        <Button variant="contained" startIcon={<AddBusinessIcon />} onClick={() => setCreateOpen(true)}>
          Create School
        </Button>
      </Box>

      {stats && (
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid size={{ xs: 12, sm: 4 }}>
            <Card><CardContent>
              <Typography color="text.secondary">Total Schools</Typography>
              <Typography variant="h4">{stats.total_schools}</Typography>
            </CardContent></Card>
          </Grid>
          <Grid size={{ xs: 12, sm: 4 }}>
            <Card><CardContent>
              <Typography color="text.secondary">Active</Typography>
              <Typography variant="h4">{stats.schools_by_status.active ?? 0}</Typography>
            </CardContent></Card>
          </Grid>
          <Grid size={{ xs: 12, sm: 4 }}>
            <Card><CardContent>
              <Typography color="text.secondary">Routed Usernames</Typography>
              <Typography variant="h4">{stats.routed_usernames}</Typography>
            </CardContent></Card>
          </Grid>
        </Grid>
      )}

      <TableContainer>
        <Table size="small" sx={{ minWidth: 760 }}>
          <TableHead>
            <TableRow>
              <TableCell>School</TableCell>
              <TableCell>Campus</TableCell>
              <TableCell>Database</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Students</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {schools?.map((s) => (
              <SchoolRow
                key={s.school_id}
                school={s}
                isCurrent={s.school_id === school.schoolId}
                onSwitch={() => switchMutation.mutate(s.school_id)}
                onStatus={(status) => statusMutation.mutate({ id: s.school_id, status })}
                onArchive={async () => {
                  const ok = await confirmAction({
                    title: `Archive "${s.school_name} — ${s.campus_name}"?`,
                    message: 'Logins will be blocked and the school hidden. The database is kept and can be re-activated later by support.',
                    confirmLabel: 'Archive',
                    destructive: true,
                  })
                  if (ok) archiveMutation.mutate(s.school_id)
                }}
                onResetPassword={() => setResetTarget(s)}
              />
            ))}
            {!isLoading && (schools?.length ?? 0) === 0 && (
              <TableRow><TableCell colSpan={6}>
                <Typography color="text.secondary" sx={{ py: 1 }}>No schools yet — create the first one.</Typography>
              </TableCell></TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>

      <CreateSchoolDialog open={createOpen} onClose={() => setCreateOpen(false)} onCreated={refresh} />
      <ResetPasswordDialog school={resetTarget} onClose={() => setResetTarget(null)} />
    </Box>
  )
}

function SchoolRow({
  school, isCurrent, onSwitch, onStatus, onArchive, onResetPassword,
}: {
  school: MasterSchool
  isCurrent: boolean
  onSwitch: () => void
  onStatus: (status: string) => void
  onArchive: () => void
  onResetPassword: () => void
}) {
  const { data: stats } = useQuery({
    queryKey: ['master-school-stats', school.school_id],
    queryFn: () => getSchoolStats(school.school_id),
    enabled: school.database_status === 'active',
    staleTime: 60_000,
  })
  return (
    <TableRow>
      <TableCell>
        {school.school_name}
        {isCurrent && <Chip size="small" label="current" color="primary" sx={{ ml: 1 }} />}
      </TableCell>
      <TableCell>{school.campus_name || '—'}</TableCell>
      <TableCell><code>{school.database_name}</code></TableCell>
      <TableCell>
        <Chip size="small" label={school.database_status} color={STATUS_COLOR[school.database_status] ?? 'default'} />
      </TableCell>
      <TableCell>{stats ? `${stats.active_students} active / ${stats.total_students}` : '—'}</TableCell>
      <TableCell>
        <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
          {school.database_status !== 'archived' && !isCurrent && (
            <Button size="small" startIcon={<SwapHorizIcon />} onClick={onSwitch}>Switch</Button>
          )}
          {school.database_status === 'active' && (
            <Button size="small" color="warning" onClick={() => onStatus('disabled')}>Disable</Button>
          )}
          {school.database_status !== 'active' && (
            <Button size="small" color="success" onClick={() => onStatus('active')}>Activate</Button>
          )}
          <Button size="small" onClick={onResetPassword}>Reset Password</Button>
          {school.database_status !== 'archived' && (
            <Button size="small" color="error" onClick={onArchive}>Delete</Button>
          )}
        </Box>
      </TableCell>
    </TableRow>
  )
}

function CreateSchoolDialog({ open, onClose, onCreated }: { open: boolean; onClose: () => void; onCreated: () => void }) {
  const toast = useToast()
  const [form, setForm] = useState({
    school_name: '', campus_name: '', database_name: '', admin_username: '', admin_password: '',
  })
  const [error, setError] = useState<string | null>(null)

  const mutation = useMutation({
    mutationFn: () => createSchool(form),
    onSuccess: (s) => {
      toast(`School "${s.school_name}" created — database ${s.database_name} is migrated and ready.`)
      setForm({ school_name: '', campus_name: '', database_name: '', admin_username: '', admin_password: '' })
      setError(null)
      onCreated()
      onClose()
    },
    onError: (e) => setError(apiErrorMessage(e, 'School creation failed.')),
  })

  const set = (field: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((f) => ({ ...f, [field]: e.target.value }))

  const valid = form.school_name.length >= 2 && form.database_name.length >= 3
    && form.admin_username.length >= 3 && form.admin_password.length >= 8

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Create School</DialogTitle>
      <DialogContent>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Creates the PostgreSQL database, runs all migrations, seeds the default roles, and creates
          the school's Admin account — fully automatic.
        </Typography>
        {error && <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>{error}</Alert>}
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
          <TextField label="School Name" value={form.school_name} onChange={set('school_name')} autoFocus />
          <TextField label="Campus Name" value={form.campus_name} onChange={set('campus_name')} />
          <TextField
            label="Database Name" value={form.database_name} onChange={set('database_name')}
            helperText="lowercase letters, digits, underscores — e.g. bright_future_haider_db"
          />
          <TextField label="Admin Username" value={form.admin_username} onChange={set('admin_username')} />
          <TextField
            label="Admin Password" type="password" value={form.admin_password} onChange={set('admin_password')}
            helperText="At least 8 characters"
          />
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button variant="contained" disabled={!valid || mutation.isPending} onClick={() => mutation.mutate()}>
          {mutation.isPending ? 'Creating…' : 'Create School'}
        </Button>
      </DialogActions>
    </Dialog>
  )
}

function ResetPasswordDialog({ school, onClose }: { school: MasterSchool | null; onClose: () => void }) {
  const toast = useToast()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)

  const mutation = useMutation({
    mutationFn: () => resetSchoolAdminPassword(school!.school_id, username, password),
    onSuccess: (r) => { toast(r.detail); setUsername(''); setPassword(''); setError(null); onClose() },
    onError: (e) => setError(apiErrorMessage(e, 'Password reset failed.')),
  })

  return (
    <Dialog open={!!school} onClose={onClose} maxWidth="xs" fullWidth>
      <DialogTitle>Reset Password — {school?.school_name} {school?.campus_name && `(${school.campus_name})`}</DialogTitle>
      <DialogContent>
        {error && <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>{error}</Alert>}
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
          <TextField label="Username in this school" value={username} onChange={(e) => setUsername(e.target.value)} autoFocus />
          <TextField label="New Password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} helperText="At least 8 characters" />
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button variant="contained" disabled={!username || password.length < 8 || mutation.isPending} onClick={() => mutation.mutate()}>
          Reset
        </Button>
      </DialogActions>
    </Dialog>
  )
}
