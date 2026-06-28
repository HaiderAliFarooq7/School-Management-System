import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Alert, Box, Button, Card, CardContent, Chip, Grid, Typography,
} from '@mui/material'
import AddIcon from '@mui/icons-material/Add'
import {
  createWhatsAppAccount, deleteWhatsAppAccount, listWhatsAppAccounts, setDefaultWhatsAppAccount,
  testWhatsAppAccount, updateWhatsAppAccount, type WhatsAppAccount,
} from '../api/whatsappAccounts'
import { WhatsAppAccountDialog, type WhatsAppAccountFormValues } from '../components/WhatsAppAccountDialog'
import { WhatsAppTestMessageDialog } from '../components/WhatsAppTestMessageDialog'

const STATUS_COLOR: Record<string, 'success' | 'error' | 'default'> = { connected: 'success', disconnected: 'error' }

export function WhatsAppAccountsPage() {
  const queryClient = useQueryClient()
  const { data, isFetching } = useQuery({ queryKey: ['whatsapp-accounts'], queryFn: listWhatsAppAccounts })

  const [editing, setEditing] = useState<WhatsAppAccount | null>(null)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [testMessageAccountId, setTestMessageAccountId] = useState<number | null>(null)
  const [saveError, setSaveError] = useState<string | null>(null)
  const [testStatus, setTestStatus] = useState<Record<number, string>>({})

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['whatsapp-accounts'] })

  const createMutation = useMutation({
    mutationFn: createWhatsAppAccount,
    onSuccess: () => { invalidate(); setDialogOpen(false); setSaveError(null) },
    onError: (e) => setSaveError(extractError(e)),
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, values }: { id: number; values: Partial<WhatsAppAccountFormValues> }) =>
      updateWhatsAppAccount(id, values),
    onSuccess: () => { invalidate(); setDialogOpen(false); setSaveError(null) },
    onError: (e) => setSaveError(extractError(e)),
  })

  const deleteMutation = useMutation({
    mutationFn: deleteWhatsAppAccount,
    onSuccess: () => { invalidate(); setSaveError(null) },
    onError: (e) => setSaveError(extractError(e)),
  })

  const setDefaultMutation = useMutation({
    mutationFn: setDefaultWhatsAppAccount,
    onSuccess: () => { invalidate(); setSaveError(null) },
    onError: (e) => setSaveError(extractError(e)),
  })

  const testMutation = useMutation({
    mutationFn: testWhatsAppAccount,
    onSuccess: (result, id) => {
      setTestStatus((prev) => ({ ...prev, [id]: result.status }))
      invalidate()
    },
    onError: (e) => setSaveError(extractError(e)),
  })

  function openCreate() {
    setEditing(null)
    setSaveError(null)
    setDialogOpen(true)
  }

  function openEdit(account: WhatsAppAccount) {
    setEditing(account)
    setSaveError(null)
    setDialogOpen(true)
  }

  function handleSave(values: WhatsAppAccountFormValues) {
    if (editing) {
      const payload: Partial<WhatsAppAccountFormValues> = { ...values }
      if (!payload.access_token) delete payload.access_token
      if (!payload.webhook_verify_token) delete payload.webhook_verify_token
      if (!payload.webhook_secret) delete payload.webhook_secret
      updateMutation.mutate({ id: editing.id, values: payload })
    } else {
      createMutation.mutate(values)
    }
  }

  function handleToggleEnabled(account: WhatsAppAccount) {
    updateMutation.mutate({ id: account.id, values: { enabled: !account.enabled } })
  }

  function handleDelete(account: WhatsAppAccount) {
    if (window.confirm(`Delete WhatsApp account "${account.name}"?`)) deleteMutation.mutate(account.id)
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h5">WhatsApp Business Accounts</Typography>
        <Button variant="contained" startIcon={<AddIcon />} onClick={openCreate}>Add Account</Button>
      </Box>

      {saveError && !dialogOpen && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setSaveError(null)}>{saveError}</Alert>
      )}
      {isFetching && <Typography color="text.secondary">Loading…</Typography>}
      {!isFetching && data?.length === 0 && (
        <Alert severity="info">No WhatsApp accounts configured yet. Add one to start sending notifications.</Alert>
      )}

      <Grid container spacing={2}>
        {data?.map((account) => {
          const status = testStatus[account.id] ?? account.last_test_status
          return (
            <Grid key={account.id} size={{ xs: 12, md: 6 }}>
              <Card sx={{ bgcolor: account.is_default ? 'success.50' : undefined }}>
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                    <Typography variant="h6">{account.name}</Typography>
                    <Box sx={{ display: 'flex', gap: 0.5 }}>
                      {account.is_default && <Chip size="small" label="Default" color="primary" />}
                      <Chip size="small" label={account.enabled ? 'Active' : 'Inactive'} color={account.enabled ? 'success' : 'default'} />
                    </Box>
                  </Box>

                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                    <Chip
                      size="small"
                      label={status === 'connected' ? 'Connected' : status === 'disconnected' ? 'Disconnected' : 'Not tested'}
                      color={STATUS_COLOR[status ?? ''] ?? 'default'}
                    />
                    {account.business_name && <Typography variant="body2" color="text.secondary">{account.business_name}</Typography>}
                  </Box>

                  <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                    {account.phone_number_display ?? account.phone_number_id ?? 'No phone number set'} · Sent today: {account.messages_sent_today}
                  </Typography>

                  {account.last_error && (
                    <Alert severity="warning" sx={{ mb: 1 }}>{account.last_error}</Alert>
                  )}

                  <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                    <Button size="small" onClick={() => openEdit(account)}>Configure</Button>
                    <Button size="small" onClick={() => testMutation.mutate(account.id)} disabled={testMutation.isPending}>
                      Test Connection
                    </Button>
                    <Button size="small" onClick={() => setTestMessageAccountId(account.id)}>Send Test Message</Button>
                    {!account.is_default && (
                      <Button size="small" onClick={() => setDefaultMutation.mutate(account.id)}>Set Default</Button>
                    )}
                    <Button size="small" onClick={() => handleToggleEnabled(account)}>
                      {account.enabled ? 'Disable' : 'Enable'}
                    </Button>
                    <Button size="small" color="error" onClick={() => handleDelete(account)}>Delete</Button>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          )
        })}
      </Grid>

      <WhatsAppAccountDialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        account={editing}
        onSave={handleSave}
        error={saveError}
      />
      {testMessageAccountId !== null && (
        <WhatsAppTestMessageDialog
          open
          accountId={testMessageAccountId}
          onClose={() => setTestMessageAccountId(null)}
        />
      )}
    </Box>
  )
}

function extractError(e: unknown): string {
  return String((e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? e)
}
