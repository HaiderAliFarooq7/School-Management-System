import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Alert, Box, Button, Card, CardContent, Chip, Grid, MenuItem, Select, Tab, Tabs, TextField, Typography,
} from '@mui/material'
import {
  getHistory, listProviders, listQueue, listTemplates, testProvider, updateProvider, updateTemplate,
  type Provider, type Template,
} from '../api/communication'
import { ProviderDialog } from '../components/ProviderDialog'
import { TemplateEditor } from '../components/TemplateEditor'
import { QueueTable } from '../components/QueueTable'
import { HistoryTable } from '../components/HistoryTable'
import { BulkSendPanel } from '../components/BulkSendPanel'
import { useAuth } from '../context/AuthContext'

export function CommunicationPage() {
  const { role } = useAuth()
  const isAdmin = role === 'Admin'
  const [tab, setTab] = useState(0)

  const { data: queue, isFetching: queueLoading } = useQuery({
    queryKey: ['communication-queue'],
    queryFn: () => listQueue(),
    refetchInterval: 15000,
  })

  const pending = queue?.filter((q) => q.status === 'pending').length ?? 0
  const processing = queue?.filter((q) => q.status === 'processing').length ?? 0
  const sentToday = queue?.filter((q) => q.status === 'sent' && q.sent_at && new Date(q.sent_at).toDateString() === new Date().toDateString()).length ?? 0
  const failed = queue?.filter((q) => q.status === 'failed').length ?? 0

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        Communication
      </Typography>

      <Grid container spacing={2} sx={{ mb: 2 }}>
        {[
          { label: 'Pending', value: pending },
          { label: 'Processing', value: processing },
          { label: 'Sent Today', value: sentToday },
          { label: 'Failed', value: failed },
        ].map((card) => (
          <Grid key={card.label} size={{ xs: 6, sm: 3 }}>
            <Card>
              <CardContent>
                <Typography color="text.secondary">{card.label}</Typography>
                <Typography variant="h5">{card.value}</Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Tabs value={tab} onChange={(_e, v) => setTab(v)} sx={{ mb: 2 }}>
        <Tab label="Bulk Send" />
        <Tab label="Queue" />
        <Tab label="History" />
        <Tab label="Templates" />
        {isAdmin && <Tab label="Providers" />}
      </Tabs>

      {tab === 0 && <BulkSendPanel />}
      {tab === 1 && <QueueTable rows={queue ?? []} loading={queueLoading} />}
      {tab === 2 && <HistoryTab />}
      {tab === 3 && <TemplatesTab isAdmin={isAdmin} />}
      {tab === 4 && isAdmin && <ProvidersTab />}
    </Box>
  )
}

function HistoryTab() {
  const [studentId, setStudentId] = useState('')
  const [phone, setPhone] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')

  const filterMutation = useMutation({
    mutationFn: () => getHistory({
      student_id: studentId ? Number(studentId) : undefined,
      phone: phone || undefined,
      status_filter: statusFilter || undefined,
      date_from: dateFrom || undefined,
      date_to: dateTo || undefined,
    }),
  })

  const { data: initial, isFetching } = useQuery({ queryKey: ['communication-history'], queryFn: () => getHistory({}) })
  const rows = filterMutation.data ?? initial ?? []

  return (
    <Box>
      <Box sx={{ display: 'flex', gap: 2, mb: 2, flexWrap: 'wrap' }}>
        <TextField label="Student ID" size="small" value={studentId} onChange={(e) => setStudentId(e.target.value)} sx={{ width: 120 }} />
        <TextField label="Phone" size="small" value={phone} onChange={(e) => setPhone(e.target.value)} sx={{ width: 150 }} />
        <Select size="small" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} displayEmpty sx={{ width: 130 }}>
          <MenuItem value="">Any Status</MenuItem>
          <MenuItem value="sent">Sent</MenuItem>
          <MenuItem value="failed">Failed</MenuItem>
        </Select>
        <TextField label="From" type="date" size="small" InputLabelProps={{ shrink: true }} value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />
        <TextField label="To" type="date" size="small" InputLabelProps={{ shrink: true }} value={dateTo} onChange={(e) => setDateTo(e.target.value)} />
        <Button variant="contained" onClick={() => filterMutation.mutate()}>Search</Button>
      </Box>
      <HistoryTable rows={rows} loading={isFetching || filterMutation.isPending} />
    </Box>
  )
}

function TemplatesTab({ isAdmin }: { isAdmin: boolean }) {
  const queryClient = useQueryClient()
  const { data, isFetching } = useQuery({ queryKey: ['communication-templates'], queryFn: listTemplates })
  const [editing, setEditing] = useState<Template | null>(null)
  const [saveError, setSaveError] = useState<string | null>(null)

  const saveMutation = useMutation({
    mutationFn: (values: { message: string; enabled: boolean; whatsapp_template_name: string | null }) =>
      updateTemplate(editing!.id, values),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['communication-templates'] }); setEditing(null); setSaveError(null) },
    onError: (e) => setSaveError(String((e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? 'Could not save template.')),
  })

  return (
    <Box>
      {isFetching && <Typography color="text.secondary">Loading…</Typography>}
      <Grid container spacing={2}>
        {data?.map((t) => (
          <Grid key={t.id} size={{ xs: 12, md: 6 }}>
            <Card>
              <CardContent>
                <Typography variant="h6">{t.name}</Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>{t.type} · {t.enabled ? 'Enabled' : 'Disabled'}</Typography>
                <Typography variant="body2" sx={{ mb: 1 }}>{t.message || '(blank — composed per message)'}</Typography>
                {isAdmin && <Button size="small" onClick={() => setEditing(t)}>Edit</Button>}
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
      <TemplateEditor
        open={!!editing}
        onClose={() => { setEditing(null); setSaveError(null) }}
        template={editing}
        onSave={(v) => saveMutation.mutate(v)}
        error={saveError}
      />
    </Box>
  )
}

function ProvidersTab() {
  const queryClient = useQueryClient()
  const { data, isFetching } = useQuery({ queryKey: ['communication-providers'], queryFn: listProviders })
  const [editing, setEditing] = useState<Provider | null>(null)
  const [testResult, setTestResult] = useState<string | null>(null)
  const [saveError, setSaveError] = useState<string | null>(null)

  const saveMutation = useMutation({
    mutationFn: (values: { enabled: boolean; configuration_json: Record<string, string> }) => updateProvider(editing!.id, values),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['communication-providers'] }); setEditing(null); setSaveError(null) },
    onError: (e) => setSaveError(String((e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? e)),
  })

  const testMutation = useMutation({
    mutationFn: (providerId: number) => testProvider(providerId),
    onSuccess: (res) => setTestResult(res.status === 'sent' ? 'Test message sent (mock).' : `Test failed: ${res.error}`),
    onError: () => setTestResult('Could not reach the server to run this test.'),
  })

  return (
    <Box>
      {isFetching && <Typography color="text.secondary">Loading…</Typography>}
      <Grid container spacing={2}>
        {data?.map((p) => (
          <Grid key={p.id} size={{ xs: 12, md: 6 }}>
            <Card sx={{ bgcolor: p.enabled ? 'success.50' : undefined }}>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <Typography variant="h6">{p.name}</Typography>
                  <Chip
                    size="small"
                    label={p.enabled ? 'Active' : 'Inactive'}
                    color={p.enabled ? 'success' : 'default'}
                  />
                </Box>
                {p.type === 'whatsapp_cloud' ? (
                  <>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                      <Chip
                        size="small"
                        label={p.last_test_status === 'connected' ? 'Connected' : p.last_test_status === 'disconnected' ? 'Disconnected' : 'Not tested'}
                        color={p.last_test_status === 'connected' ? 'success' : p.last_test_status === 'disconnected' ? 'error' : 'default'}
                      />
                      {p.business_name && <Typography variant="body2" color="text.secondary">{p.business_name}</Typography>}
                    </Box>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      {p.phone_number_display ?? 'No number registered yet'} · Sent today: {p.messages_sent_today}
                    </Typography>
                  </>
                ) : (
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>{p.type}</Typography>
                )}
                <Button size="small" onClick={() => { setEditing(p); setTestResult(null) }}>Configure</Button>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
      {saveError && <Alert severity="error" sx={{ mt: 2 }}>{saveError}</Alert>}
      <ProviderDialog
        open={!!editing}
        onClose={() => setEditing(null)}
        provider={editing}
        onSave={(v) => saveMutation.mutate(v)}
        onTest={() => editing && testMutation.mutate(editing.id)}
        testResult={testResult}
        error={saveError}
      />
    </Box>
  )
}
