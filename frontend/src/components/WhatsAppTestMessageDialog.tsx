import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import {
  Alert, Button, Dialog, DialogActions, DialogContent, DialogTitle, TextField, Typography,
} from '@mui/material'
import { sendWhatsAppAccountTestMessage } from '../api/whatsappAccounts'

interface Props {
  open: boolean
  onClose: () => void
  accountId: number
}

export function WhatsAppTestMessageDialog({ open, onClose, accountId }: Props) {
  const [recipient, setRecipient] = useState('')
  const [templateName, setTemplateName] = useState('hello_world')

  const mutation = useMutation({
    mutationFn: () => sendWhatsAppAccountTestMessage(accountId, recipient, templateName),
  })

  const handleClose = () => {
    mutation.reset()
    setRecipient('')
    onClose()
  }

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>Send WhatsApp Test Message</DialogTitle>
      <DialogContent>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Sends one approved Meta template message directly — bypasses the queue. Use a number that's
          added as a test recipient in your Meta app, in international format (e.g. 923001234567).
        </Typography>
        <TextField
          fullWidth label="Recipient Number" placeholder="923001234567" value={recipient}
          onChange={(e) => setRecipient(e.target.value)} sx={{ mb: 2 }} autoFocus
        />
        <TextField
          fullWidth label="Approved Template Name" value={templateName}
          onChange={(e) => setTemplateName(e.target.value)} helperText="Default hello_world is pre-approved on every WhatsApp Business app."
          sx={{ mb: 2 }}
        />
        {mutation.data && (
          <Alert severity={mutation.data.status === 'sent' ? 'success' : 'error'} sx={{ mb: 1 }}>
            {mutation.data.status === 'sent'
              ? `Sent — Meta message id: ${mutation.data.message_id}`
              : mutation.data.error}
          </Alert>
        )}
        {mutation.data && (
          <Typography variant="caption" component="pre" sx={{ whiteSpace: 'pre-wrap', color: 'text.secondary' }}>
            {JSON.stringify(mutation.data.provider_response ?? { http_status: mutation.data.http_status }, null, 2)}
          </Typography>
        )}
        {mutation.isError && <Alert severity="error" sx={{ mb: 1 }}>Could not reach the server to send this message.</Alert>}
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose}>Close</Button>
        <Button variant="contained" disabled={!recipient || !templateName || mutation.isPending} onClick={() => mutation.mutate()}>
          Send
        </Button>
      </DialogActions>
    </Dialog>
  )
}
