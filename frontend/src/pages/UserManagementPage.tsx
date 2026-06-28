import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Box, Button, Chip, Dialog, DialogActions, DialogContent, DialogTitle, MenuItem, Select, Table, TableBody,
  TableCell, TableHead, TableRow, TextField, Typography,
} from '@mui/material'
import {
  activateUser, createUser, deactivateUser, deleteUser, listUsers, updateUser, type User,
} from '../api/users'
import { listGrades } from '../api/grades'

const ROLES = ['Admin', 'Accountant', 'Teacher']

function apiErrorMessage(e: unknown): string {
  return String((e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? e)
}

export function UserManagementPage() {
  const queryClient = useQueryClient()
  const { data: users } = useQuery({ queryKey: ['users'], queryFn: listUsers })
  const { data: grades } = useQuery({ queryKey: ['grades'], queryFn: listGrades })
  const [editTarget, setEditTarget] = useState<User | null>(null)

  const [form, setForm] = useState({ username: '', full_name: '', password: '', role_name: 'Teacher', assigned_class_name: '' })
  const [createError, setCreateError] = useState<string | null>(null)

  const createMutation = useMutation({
    mutationFn: () =>
      createUser({
        ...form,
        assigned_class_name: form.role_name === 'Teacher' ? form.assigned_class_name || null : null,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] })
      setForm({ username: '', full_name: '', password: '', role_name: 'Teacher', assigned_class_name: '' })
      setCreateError(null)
    },
    onError: (e) => setCreateError(apiErrorMessage(e)),
  })

  const deactivateMutation = useMutation({
    mutationFn: (userId: number) => deactivateUser(userId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['users'] }),
    onError: (e) => alert(apiErrorMessage(e)),
  })

  const activateMutation = useMutation({
    mutationFn: (userId: number) => activateUser(userId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['users'] }),
    onError: (e) => alert(apiErrorMessage(e)),
  })

  const deleteMutation = useMutation({
    mutationFn: (userId: number) => deleteUser(userId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['users'] }),
    onError: (e) => alert(apiErrorMessage(e)),
  })

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        Users
      </Typography>

      {createError && <Typography color="error" sx={{ mb: 1 }}>{createError}</Typography>}
      <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mb: 3, maxWidth: 900 }}>
        <TextField label="Username" size="small" value={form.username} onChange={(e) => setForm((f) => ({ ...f, username: e.target.value }))} />
        <TextField label="Full Name" size="small" value={form.full_name} onChange={(e) => setForm((f) => ({ ...f, full_name: e.target.value }))} />
        <TextField
          label="Password"
          size="small"
          type="password"
          value={form.password}
          onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))}
          helperText="At least 6 characters"
        />
        <Select size="small" value={form.role_name} onChange={(e) => setForm((f) => ({ ...f, role_name: e.target.value }))} sx={{ width: 140 }}>
          {ROLES.map((r) => <MenuItem key={r} value={r}>{r}</MenuItem>)}
        </Select>
        {form.role_name === 'Teacher' && (
          <Select
            size="small"
            value={form.assigned_class_name}
            onChange={(e) => setForm((f) => ({ ...f, assigned_class_name: e.target.value }))}
            displayEmpty
            sx={{ width: 160 }}
          >
            <MenuItem value="">Assigned Class</MenuItem>
            {grades?.map((g) => <MenuItem key={g.grade_id} value={g.class_name}>{g.class_name}</MenuItem>)}
          </Select>
        )}
        <Button
          variant="contained"
          disabled={!form.username || !form.full_name || form.password.length < 6}
          onClick={() => createMutation.mutate()}
        >
          Create User
        </Button>
      </Box>

      <Table size="small" sx={{ maxWidth: 950 }}>
        <TableHead>
          <TableRow>
            <TableCell>Username</TableCell>
            <TableCell>Full Name</TableCell>
            <TableCell>Role</TableCell>
            <TableCell>Class</TableCell>
            <TableCell>Status</TableCell>
            <TableCell></TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {users?.map((u) => (
            <TableRow key={u.user_id}>
              <TableCell>{u.username}</TableCell>
              <TableCell>{u.full_name}</TableCell>
              <TableCell>{u.role_name}</TableCell>
              <TableCell>{u.assigned_class_name ?? '—'}</TableCell>
              <TableCell>
                <Chip size="small" label={u.is_active ? 'Active' : 'Inactive'} color={u.is_active ? 'success' : 'default'} />
              </TableCell>
              <TableCell>
                <Box sx={{ display: 'flex', gap: 0.5 }}>
                  <Button size="small" onClick={() => setEditTarget(u)}>
                    Edit
                  </Button>
                  {u.is_active ? (
                    <Button size="small" color="warning" onClick={() => deactivateMutation.mutate(u.user_id)}>
                      Deactivate
                    </Button>
                  ) : (
                    <Button size="small" color="success" onClick={() => activateMutation.mutate(u.user_id)}>
                      Activate
                    </Button>
                  )}
                  <Button
                    size="small"
                    color="error"
                    onClick={() => {
                      if (window.confirm(`Permanently delete user "${u.username}"? This cannot be undone.`)) {
                        deleteMutation.mutate(u.user_id)
                      }
                    }}
                  >
                    Delete
                  </Button>
                </Box>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      <EditUserDialog
        user={editTarget}
        grades={grades ?? []}
        open={!!editTarget}
        onClose={() => setEditTarget(null)}
      />
    </Box>
  )
}

function EditUserDialog({
  user, grades, open, onClose,
}: { user: User | null; grades: { grade_id: number; class_name: string }[]; open: boolean; onClose: () => void }) {
  const queryClient = useQueryClient()
  const [username, setUsername] = useState('')
  const [fullName, setFullName] = useState('')
  const [roleName, setRoleName] = useState('Teacher')
  const [assignedClassName, setAssignedClassName] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (user) {
      setUsername(user.username)
      setFullName(user.full_name)
      setRoleName(user.role_name)
      setAssignedClassName(user.assigned_class_name ?? '')
      setNewPassword('')
      setError(null)
    }
  }, [user])

  const saveMutation = useMutation({
    mutationFn: () =>
      updateUser(user!.user_id, {
        username,
        full_name: fullName,
        role_name: roleName,
        assigned_class_name: roleName === 'Teacher' ? assignedClassName || null : null,
        ...(newPassword ? { password: newPassword } : {}),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] })
      onClose()
    },
    onError: (e) => setError(String((e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? e)),
  })

  if (!user) return null

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Edit User — {user.username}</DialogTitle>
      <DialogContent>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
          {error && <Typography color="error">{error}</Typography>}
          <TextField label="Username" value={username} onChange={(e) => setUsername(e.target.value)} />
          <TextField label="Full Name" value={fullName} onChange={(e) => setFullName(e.target.value)} />
          <Select value={roleName} onChange={(e) => setRoleName(e.target.value)}>
            {ROLES.map((r) => <MenuItem key={r} value={r}>{r}</MenuItem>)}
          </Select>
          {roleName === 'Teacher' && (
            <Select value={assignedClassName} onChange={(e) => setAssignedClassName(e.target.value)} displayEmpty>
              <MenuItem value="">Assigned Class</MenuItem>
              {grades.map((g) => <MenuItem key={g.grade_id} value={g.class_name}>{g.class_name}</MenuItem>)}
            </Select>
          )}
          <TextField
            label="New Password (leave blank to keep current)"
            type="password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
          />
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button variant="contained" onClick={() => saveMutation.mutate()}>Save Changes</Button>
      </DialogActions>
    </Dialog>
  )
}
