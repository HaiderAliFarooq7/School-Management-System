import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Box, Button, Chip, Dialog, DialogActions, DialogContent, DialogTitle, Table, TableBody,
  TableCell, TableHead, TableRow, TextField, Tooltip, Typography,
} from '@mui/material'
import {
  createParent, listParentDevices, listParents, resetParentPassword, syncParentAccounts,
  updateParent, type ParentAccount,
} from '../api/parents'

function apiErrorMessage(e: unknown): string {
  return String((e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? e)
}

export function ParentManagementPage() {
  const queryClient = useQueryClient()
  const { data: parents } = useQuery({ queryKey: ['parents'], queryFn: listParents })
  const [editTarget, setEditTarget] = useState<ParentAccount | null>(null)
  const [devicesTarget, setDevicesTarget] = useState<ParentAccount | null>(null)

  const [form, setForm] = useState({ mobile_number: '', full_name: '', password: '' })
  const [createError, setCreateError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)

  const createMutation = useMutation({
    mutationFn: () =>
      createParent({
        mobile_number: form.mobile_number.trim(),
        full_name: form.full_name.trim() || null,
        password: form.password || null,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['parents'] })
      setForm({ mobile_number: '', full_name: '', password: '' })
      setCreateError(null)
    },
    onError: (e) => setCreateError(apiErrorMessage(e)),
  })

  const toggleActiveMutation = useMutation({
    mutationFn: (p: ParentAccount) => updateParent(p.parent_id, { is_active: !p.is_active }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['parents'] }),
    onError: (e) => alert(apiErrorMessage(e)),
  })

  const resetMutation = useMutation({
    mutationFn: (parentId: number) => resetParentPassword(parentId),
    onSuccess: (res) => setNotice(res.detail),
    onError: (e) => alert(apiErrorMessage(e)),
  })

  const syncMutation = useMutation({
    mutationFn: () => syncParentAccounts(),
    onSuccess: (res) => {
      queryClient.invalidateQueries({ queryKey: ['parents'] })
      setNotice(res.detail)
    },
    onError: (e) => alert(apiErrorMessage(e)),
  })

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1, flexWrap: 'wrap', gap: 1 }}>
        <Typography variant="h5">Parent Management</Typography>
        <Tooltip title="Create login accounts for every parent mobile number found on students. Default password is the mobile number.">
          <span>
            <Button variant="outlined" disabled={syncMutation.isPending} onClick={() => syncMutation.mutate()}>
              {syncMutation.isPending ? 'Syncing…' : 'Sync from Students'}
            </Button>
          </span>
        </Tooltip>
      </Box>

      {notice && <Typography color="primary" sx={{ mb: 1 }}>{notice}</Typography>}
      {createError && <Typography color="error" sx={{ mb: 1 }}>{createError}</Typography>}

      <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mb: 3, maxWidth: 900 }}>
        <TextField label="Mobile Number" size="small" value={form.mobile_number}
          onChange={(e) => setForm((f) => ({ ...f, mobile_number: e.target.value }))} />
        <TextField label="Parent Name (optional)" size="small" value={form.full_name}
          onChange={(e) => setForm((f) => ({ ...f, full_name: e.target.value }))} />
        <TextField label="Password (optional)" size="small" type="password" value={form.password}
          onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))}
          helperText="Blank = mobile number" />
        <Button variant="contained" disabled={form.mobile_number.trim().length < 6}
          onClick={() => createMutation.mutate()}>
          Add Parent
        </Button>
      </Box>

      <Box sx={{ overflowX: 'auto' }}>
        <Table size="small" sx={{ minWidth: 900 }}>
          <TableHead>
            <TableRow>
              <TableCell>Mobile</TableCell>
              <TableCell>Name</TableCell>
              <TableCell align="center">Students</TableCell>
              <TableCell align="center">Devices</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Last Login</TableCell>
              <TableCell></TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {parents?.map((p) => (
              <TableRow key={p.parent_id}>
                <TableCell>{p.mobile_number}</TableCell>
                <TableCell>{p.full_name ?? '—'}</TableCell>
                <TableCell align="center">{p.student_count}</TableCell>
                <TableCell align="center">
                  <Button size="small" onClick={() => setDevicesTarget(p)}>{p.device_count}</Button>
                </TableCell>
                <TableCell>
                  <Chip size="small" label={p.is_active ? 'Active' : 'Inactive'}
                    color={p.is_active ? 'success' : 'default'} />
                  {p.must_change_password && (
                    <Chip size="small" label="Default pwd" color="warning" sx={{ ml: 0.5 }} />
                  )}
                </TableCell>
                <TableCell>{p.last_login_at ? new Date(p.last_login_at).toLocaleString() : '—'}</TableCell>
                <TableCell>
                  <Box sx={{ display: 'flex', gap: 0.5 }}>
                    <Button size="small" onClick={() => setEditTarget(p)}>Edit</Button>
                    <Button size="small" color={p.is_active ? 'warning' : 'success'}
                      onClick={() => toggleActiveMutation.mutate(p)}>
                      {p.is_active ? 'Deactivate' : 'Activate'}
                    </Button>
                    <Button size="small" color="error"
                      onClick={() => {
                        if (window.confirm(`Reset ${p.mobile_number}'s password to their mobile number?`)) {
                          resetMutation.mutate(p.parent_id)
                        }
                      }}>
                      Reset Password
                    </Button>
                  </Box>
                </TableCell>
              </TableRow>
            ))}
            {parents?.length === 0 && (
              <TableRow>
                <TableCell colSpan={7}>
                  <Typography color="text.secondary" sx={{ py: 2 }}>
                    No parent accounts yet. Use “Sync from Students” to create them from existing student contacts.
                  </Typography>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </Box>

      <EditParentDialog parent={editTarget} open={!!editTarget} onClose={() => setEditTarget(null)} />
      <DevicesDialog parent={devicesTarget} open={!!devicesTarget} onClose={() => setDevicesTarget(null)} />
    </Box>
  )
}

function EditParentDialog({ parent, open, onClose }: { parent: ParentAccount | null; open: boolean; onClose: () => void }) {
  const queryClient = useQueryClient()
  const [fullName, setFullName] = useState('')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (parent) {
      setFullName(parent.full_name ?? '')
      setError(null)
    }
  }, [parent])

  const saveMutation = useMutation({
    mutationFn: () => updateParent(parent!.parent_id, { full_name: fullName.trim() || null }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['parents'] })
      onClose()
    },
    onError: (e) => setError(apiErrorMessage(e)),
  })

  if (!parent) return null
  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Edit Parent — {parent.mobile_number}</DialogTitle>
      <DialogContent>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
          {error && <Typography color="error">{error}</Typography>}
          <TextField label="Parent Name" value={fullName} onChange={(e) => setFullName(e.target.value)} />
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button variant="contained" onClick={() => saveMutation.mutate()}>Save Changes</Button>
      </DialogActions>
    </Dialog>
  )
}

function DevicesDialog({ parent, open, onClose }: { parent: ParentAccount | null; open: boolean; onClose: () => void }) {
  const { data: devices } = useQuery({
    queryKey: ['parent-devices', parent?.parent_id],
    queryFn: () => listParentDevices(parent!.parent_id),
    enabled: !!parent,
  })
  if (!parent) return null
  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Devices — {parent.mobile_number}</DialogTitle>
      <DialogContent>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Platform</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Registered</TableCell>
              <TableCell>Last Seen</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {devices?.map((d) => (
              <TableRow key={d.device_id}>
                <TableCell>{d.platform}</TableCell>
                <TableCell>
                  <Chip size="small" label={d.is_active ? 'Active' : 'Inactive'}
                    color={d.is_active ? 'success' : 'default'} />
                </TableCell>
                <TableCell>{new Date(d.created_at).toLocaleDateString()}</TableCell>
                <TableCell>{new Date(d.last_seen_at).toLocaleString()}</TableCell>
              </TableRow>
            ))}
            {devices?.length === 0 && (
              <TableRow><TableCell colSpan={4}>No registered devices.</TableCell></TableRow>
            )}
          </TableBody>
        </Table>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Close</Button>
      </DialogActions>
    </Dialog>
  )
}
