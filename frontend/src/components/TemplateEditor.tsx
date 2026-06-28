import { useEffect, useState } from 'react'
import {
  Alert, Button, Dialog, DialogActions, DialogContent, DialogTitle, FormControlLabel, Switch, TextField, Typography,
} from '@mui/material'
import { renderTemplate, type Template } from '../api/communication'

const SAMPLE_VALUES: Record<string, string> = {
  student_name: 'Ali Khan', parent_name: 'Khan Sahab', class: 'Grade 5', date: new Date().toLocaleDateString(),
  fee_amount: '5000', remaining_fee: '2500', school_name: 'Greenwood School', voucher_no: 'VC-1024',
}

interface Props {
  open: boolean
  onClose: () => void
  template: Template | null
  onSave: (values: { message: string; enabled: boolean; whatsapp_template_name: string | null }) => void
  error?: string | null
}

export function TemplateEditor({ open, onClose, template, onSave, error }: Props) {
  const [message, setMessage] = useState('')
  const [enabled, setEnabled] = useState(true)
  const [whatsappTemplateName, setWhatsappTemplateName] = useState('')

  useEffect(() => {
    if (open && template) {
      setMessage(template.message)
      setEnabled(template.enabled)
      setWhatsappTemplateName(template.whatsapp_template_name ?? '')
    }
  }, [open, template])

  if (!template) return null

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>{template.name}</DialogTitle>
      <DialogContent>
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
          Variables: {template.variables.map((v) => `{{${v}}}`).join(', ') || 'none'}
        </Typography>
        <TextField
          fullWidth
          multiline
          minRows={3}
          label="Message"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          sx={{ mb: 2 }}
        />
        <TextField
          fullWidth
          label="WhatsApp Approved Template Name (optional)"
          placeholder="e.g. pending_fee"
          value={whatsappTemplateName}
          onChange={(e) => setWhatsappTemplateName(e.target.value)}
          helperText="Only used when sending via WhatsApp with templates enabled. Leave blank to use the provider's built-in default for this message type."
          sx={{ mb: 2 }}
        />
        <FormControlLabel
          control={<Switch checked={enabled} onChange={(e) => setEnabled(e.target.checked)} />}
          label="Enabled"
          sx={{ mb: 2, display: 'block' }}
        />
        <Typography variant="subtitle2" gutterBottom>Preview (sample values)</Typography>
        <Typography variant="body2" sx={{ p: 1.5, bgcolor: 'action.hover', borderRadius: 1 }}>
          {renderTemplate(message, SAMPLE_VALUES) || '—'}
        </Typography>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          variant="contained"
          onClick={() => onSave({ message, enabled, whatsapp_template_name: whatsappTemplateName.trim() || null })}
        >
          Save
        </Button>
      </DialogActions>
    </Dialog>
  )
}
