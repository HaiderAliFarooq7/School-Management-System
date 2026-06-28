import { useEffect, useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import {
  Alert, Box, Button, Card, CardContent, Chip, Dialog, DialogActions, DialogContent, DialogTitle,
  FormControlLabel, Grid, Switch, TextField, Typography,
} from '@mui/material'
import { testWhatsAppAccountDraft, type WhatsAppAccount } from '../api/whatsappAccounts'

export interface WhatsAppAccountFormValues {
  name: string
  business_account_id: string
  phone_number_id: string
  access_token: string
  graph_version: string
  use_templates: boolean
  webhook_verify_token: string
  webhook_secret: string
  enabled: boolean
}

interface Props {
  open: boolean
  onClose: () => void
  account: WhatsAppAccount | null // null = create mode
  onSave: (values: WhatsAppAccountFormValues) => void
  error?: string | null
}

const EMPTY_FORM: WhatsAppAccountFormValues = {
  name: '', business_account_id: '', phone_number_id: '', access_token: '',
  graph_version: 'v25.0', use_templates: false, webhook_verify_token: '', webhook_secret: '', enabled: true,
}

const STATUS_COLOR: Record<string, 'success' | 'error' | 'default'> = { connected: 'success', disconnected: 'error' }

export function WhatsAppAccountDialog({ open, onClose, account, onSave, error }: Props) {
  const [form, setForm] = useState<WhatsAppAccountFormValues>(EMPTY_FORM)
  const testMutation = useMutation({ mutationFn: testWhatsAppAccountDraft })

  useEffect(() => {
    if (!open) return
    testMutation.reset()
    if (account) {
      setForm({
        name: account.name,
        business_account_id: account.business_account_id ?? '',
        phone_number_id: account.phone_number_id ?? '',
        access_token: '',
        graph_version: account.graph_version ?? 'v25.0',
        use_templates: account.use_templates,
        webhook_verify_token: '',
        webhook_secret: '',
        enabled: account.enabled,
      })
    } else {
      setForm(EMPTY_FORM)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, account])

  const canTest = !!form.phone_number_id && (!!form.access_token || (account?.has_access_token ?? false))
  const canSave = !!form.name && !!form.phone_number_id && (!!form.access_token || !!account)

  function handleTest() {
    const tokenForTest = form.access_token
    if (!tokenForTest) return // editing without a new token — nothing new to test against Meta
    testMutation.mutate({
      access_token: tokenForTest,
      phone_number_id: form.phone_number_id,
      business_account_id: form.business_account_id || undefined,
      graph_version: form.graph_version,
    })
  }

  const result = testMutation.data

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>{account ? 'Edit WhatsApp Account' : 'Add WhatsApp Account'}</DialogTitle>
      <DialogContent>
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        <Grid container spacing={2}>
          <Grid size={12}>
            <TextField
              fullWidth label="Account Name" value={form.name} autoFocus
              onChange={(e) => setForm({ ...form, name: e.target.value })}
            />
          </Grid>
          <Grid size={{ xs: 12, sm: 6 }}>
            <TextField
              fullWidth label="Phone Number ID" value={form.phone_number_id}
              onChange={(e) => setForm({ ...form, phone_number_id: e.target.value })}
            />
          </Grid>
          <Grid size={{ xs: 12, sm: 6 }}>
            <TextField
              fullWidth label="Business Account ID" value={form.business_account_id}
              onChange={(e) => setForm({ ...form, business_account_id: e.target.value })}
            />
          </Grid>
          <Grid size={12}>
            <TextField
              fullWidth label="Permanent Access Token" type="password" value={form.access_token}
              placeholder={account ? 'Leave blank to keep the existing token' : ''}
              onChange={(e) => setForm({ ...form, access_token: e.target.value })}
            />
          </Grid>
          <Grid size={{ xs: 12, sm: 6 }}>
            <TextField
              fullWidth label="Graph API Version" value={form.graph_version}
              onChange={(e) => setForm({ ...form, graph_version: e.target.value })}
            />
          </Grid>
          <Grid size={{ xs: 12, sm: 6 }}>
            <FormControlLabel
              sx={{ mt: 1 }}
              control={<Switch checked={form.use_templates} onChange={(e) => setForm({ ...form, use_templates: e.target.checked })} />}
              label="Use approved templates"
            />
          </Grid>
          <Grid size={{ xs: 12, sm: 6 }}>
            <TextField
              fullWidth label="Webhook Verify Token (optional)" type="password" value={form.webhook_verify_token}
              placeholder={account?.has_webhook_verify_token ? 'Leave blank to keep existing' : ''}
              onChange={(e) => setForm({ ...form, webhook_verify_token: e.target.value })}
            />
          </Grid>
          <Grid size={{ xs: 12, sm: 6 }}>
            <TextField
              fullWidth label="Webhook Secret (optional)" type="password" value={form.webhook_secret}
              placeholder={account?.has_webhook_secret ? 'Leave blank to keep existing' : ''}
              onChange={(e) => setForm({ ...form, webhook_secret: e.target.value })}
            />
          </Grid>
          <Grid size={12}>
            <FormControlLabel
              control={<Switch checked={form.enabled} onChange={(e) => setForm({ ...form, enabled: e.target.checked })} />}
              label="Active"
            />
          </Grid>
        </Grid>

        {!form.access_token && account && (
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
            Enter a new token above to test it before saving — testing isn't possible against a token that's
            already saved from here (it's never sent back to the browser).
          </Typography>
        )}

        {result && (
          <Box sx={{ mt: 2 }}>
            <Card variant="outlined">
              <CardContent sx={{ py: 1.5 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                  <Chip
                    size="small"
                    label={result.status === 'connected' ? 'Connected' : 'Disconnected'}
                    color={STATUS_COLOR[result.status] ?? 'default'}
                  />
                  {result.business_name && <Typography variant="body2">{result.business_name}</Typography>}
                </Box>
                {result.phone_number && (
                  <Typography variant="body2" color="text.secondary">Number: {result.phone_number}</Typography>
                )}
                {result.error && <Alert severity="warning" sx={{ mt: 1 }}>{result.error}</Alert>}
              </CardContent>
            </Card>
          </Box>
        )}
        {testMutation.isError && <Alert severity="error" sx={{ mt: 2 }}>Could not reach the server to test this connection.</Alert>}
      </DialogContent>
      <DialogActions>
        <Button onClick={handleTest} disabled={!canTest || testMutation.isPending}>Test Connection</Button>
        <Box sx={{ flexGrow: 1 }} />
        <Button onClick={onClose}>Cancel</Button>
        <Button variant="contained" disabled={!canSave} onClick={() => onSave(form)}>Save</Button>
      </DialogActions>
    </Dialog>
  )
}
