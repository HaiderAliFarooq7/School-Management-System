import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import {
  Alert, Button, Dialog, DialogActions, DialogContent, DialogTitle, TextField,
} from '@mui/material'
import { changePassword } from '../api/auth'

interface Props {
  open: boolean
  onClose: () => void
}

export function ChangePasswordDialog({ open, onClose }: Props) {
  const [current, setCurrent] = useState('')
  const [next, setNext] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  const reset = () => { setCurrent(''); setNext(''); setConfirm(''); setError(null); setSuccess(false) }

  const mutation = useMutation({
    mutationFn: () => changePassword(current, next),
    onSuccess: () => { setSuccess(true); setError(null); setCurrent(''); setNext(''); setConfirm('') },
    onError: (e) => setError(String((e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? e)),
  })

  const handleSubmit = () => {
    setError(null)
    if (next.length < 6) { setError('New password must be at least 6 characters.'); return }
    if (next !== confirm) { setError('New password and confirmation do not match.'); return }
    mutation.mutate()
  }

  return (
    <Dialog open={open} onClose={() => { reset(); onClose() }} maxWidth="xs" fullWidth>
      <DialogTitle>Change Password</DialogTitle>
      <DialogContent>
        {success && <Alert severity="success" sx={{ mb: 2 }}>Password changed successfully.</Alert>}
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        <TextField
          fullWidth type="password" label="Current Password" value={current}
          onChange={(e) => setCurrent(e.target.value)} sx={{ mb: 2, mt: 1 }} autoFocus
        />
        <TextField
          fullWidth type="password" label="New Password" value={next}
          onChange={(e) => setNext(e.target.value)} sx={{ mb: 2 }}
          helperText="At least 6 characters"
        />
        <TextField
          fullWidth type="password" label="Confirm New Password" value={confirm}
          onChange={(e) => setConfirm(e.target.value)}
        />
      </DialogContent>
      <DialogActions>
        <Button onClick={() => { reset(); onClose() }}>Close</Button>
        <Button
          variant="contained"
          disabled={!current || !next || !confirm || mutation.isPending}
          onClick={handleSubmit}
        >
          Update Password
        </Button>
      </DialogActions>
    </Dialog>
  )
}
