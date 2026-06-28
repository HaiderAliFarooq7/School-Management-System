import { useEffect, useState } from 'react'
import {
  Alert, Button, Dialog, DialogActions, DialogContent, DialogTitle, MenuItem, Select, TextField, Typography,
} from '@mui/material'
import type { ProviderType } from '../api/communication'

interface Props {
  open: boolean
  onClose: () => void
  title: string
  recipient: string
  message: string
  /** When false (e.g. a fixed template like Attendance/Fee Reminder), the message is read-only — only the channel can be changed. */
  editableMessage?: boolean
  channel: ProviderType
  onChannelChange?: (channel: ProviderType) => void
  onQueue: (message: string) => void
  error?: string | null
  isQueuing?: boolean
}

export function MessagePreviewDialog({
  open, onClose, title, recipient, message, editableMessage = true, channel, onChannelChange, onQueue, error, isQueuing,
}: Props) {
  const [draft, setDraft] = useState(message)

  useEffect(() => {
    if (open) setDraft(message)
  }, [open, message])

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>{title}</DialogTitle>
      <DialogContent>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Recipient: {recipient || '—'}
        </Typography>
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        <Select
          fullWidth
          size="small"
          value={channel}
          onChange={(e) => onChannelChange?.(e.target.value as ProviderType)}
          sx={{ mb: 2 }}
          disabled={!onChannelChange}
        >
          <MenuItem value="sms">SMS</MenuItem>
          <MenuItem value="whatsapp">WhatsApp</MenuItem>
        </Select>
        <TextField
          fullWidth
          multiline
          minRows={4}
          label="Message Preview"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          disabled={!editableMessage}
        />
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button variant="contained" disabled={!draft.trim() || !recipient || isQueuing} onClick={() => onQueue(draft)}>
          Queue Message
        </Button>
      </DialogActions>
    </Dialog>
  )
}
