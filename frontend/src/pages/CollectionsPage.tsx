import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Box, Button, ButtonGroup, Card, CardContent, Chip, Divider, Grid, IconButton, MenuItem, Paper,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow, TextField, Typography,
} from '@mui/material'
import DeleteIcon from '@mui/icons-material/Delete'
import ReceiptLongIcon from '@mui/icons-material/ReceiptLong'
import {
  createHandover, deleteHandover, getCollectionsDetail, getCollectionsSummary, getReconciliation,
  listHandovers,
} from '../api/collections'
import { listUsers } from '../api/users'
import { useConfirm, useToast } from '../components/feedback'

type Preset = 'today' | 'week' | 'month' | 'custom'

function fmt(d: Date): string {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

/** Local-time range for a preset. "Week" = Monday→today, "Month" = 1st→today. */
function presetRange(preset: Preset): { from: string; to: string } {
  const now = new Date()
  if (preset === 'today') return { from: fmt(now), to: fmt(now) }
  if (preset === 'week') {
    const diffToMon = (now.getDay() + 6) % 7
    const mon = new Date(now)
    mon.setDate(now.getDate() - diffToMon)
    return { from: fmt(mon), to: fmt(now) }
  }
  if (preset === 'month') {
    const first = new Date(now.getFullYear(), now.getMonth(), 1)
    return { from: fmt(first), to: fmt(now) }
  }
  return { from: '', to: '' }
}

const rupees = (n: number) => `Rs. ${Math.round(n).toLocaleString()}`

function apiErrorMessage(e: unknown): string {
  return String((e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? e)
}

export function CollectionsPage() {
  const [preset, setPreset] = useState<Preset>('today')
  const [customFrom, setCustomFrom] = useState(fmt(new Date()))
  const [customTo, setCustomTo] = useState(fmt(new Date()))

  const range = preset === 'custom' ? { from: customFrom, to: customTo } : presetRange(preset)
  const [drillActor, setDrillActor] = useState<{ id: number | null; name: string } | null>(null)

  const { data: summary, isFetching } = useQuery({
    queryKey: ['collections-summary', range.from, range.to],
    queryFn: () => getCollectionsSummary({ date_from: range.from, date_to: range.to }),
  })

  const presetLabel: Record<Preset, string> = {
    today: 'Today', week: 'This Week', month: 'This Month', custom: 'Custom Range',
  }

  return (
    <Box>
      <Typography variant="h5" gutterBottom>Collections by Accountant</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Who collected how much — fees and extra charges — over any period, drill down to see whose
        fee each accountant took, and reconcile it against the cash they've handed in.
      </Typography>

      <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'center', mb: 2 }}>
        <ButtonGroup variant="outlined" size="small">
          {(['today', 'week', 'month', 'custom'] as const).map((p) => (
            <Button
              key={p}
              variant={preset === p ? 'contained' : 'outlined'}
              onClick={() => setPreset(p)}
            >
              {presetLabel[p]}
            </Button>
          ))}
        </ButtonGroup>
        {preset === 'custom' && (
          <>
            <TextField
              label="From" type="date" size="small" value={customFrom}
              onChange={(e) => setCustomFrom(e.target.value)} InputLabelProps={{ shrink: true }}
            />
            <TextField
              label="To" type="date" size="small" value={customTo}
              onChange={(e) => setCustomTo(e.target.value)} InputLabelProps={{ shrink: true }}
            />
          </>
        )}
        {range.from && (
          <Typography variant="body2" color="text.secondary">
            {range.from === range.to ? range.from : `${range.from} → ${range.to}`}
          </Typography>
        )}
      </Box>

      <Grid container spacing={2} sx={{ mb: 2 }}>
        <SummaryCard label="Total Collected" value={rupees(summary?.total_collected ?? 0)} highlight />
        <SummaryCard label="Fees" value={rupees(summary?.fee_collected ?? 0)} />
        <SummaryCard label="Extra Charges" value={rupees(summary?.charge_collected ?? 0)} />
        <SummaryCard label="# Payments" value={String(summary?.payment_count ?? 0)} />
      </Grid>

      <TableContainer component={Paper} variant="outlined" sx={{ mb: 2 }}>
        <Table size="small" sx={{ minWidth: 720 }}>
          <TableHead>
            <TableRow>
              <TableCell>Accountant</TableCell>
              <TableCell>Role</TableCell>
              <TableCell align="right">Fees</TableCell>
              <TableCell align="right">Charges</TableCell>
              <TableCell align="right">Total</TableCell>
              <TableCell align="right"># Payments</TableCell>
              <TableCell align="center">Details</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {summary?.rows.map((r) => (
              <TableRow key={r.actor_user_id ?? r.actor_username} hover>
                <TableCell>{r.actor_username || '—'}</TableCell>
                <TableCell>{r.actor_role || '—'}</TableCell>
                <TableCell align="right">{rupees(r.fee_collected)}</TableCell>
                <TableCell align="right">{rupees(r.charge_collected)}</TableCell>
                <TableCell align="right"><strong>{rupees(r.total_collected)}</strong></TableCell>
                <TableCell align="right">{r.payment_count}</TableCell>
                <TableCell align="center">
                  <Button
                    size="small" startIcon={<ReceiptLongIcon fontSize="small" />}
                    onClick={() => setDrillActor({ id: r.actor_user_id, name: r.actor_username })}
                  >
                    View
                  </Button>
                </TableCell>
              </TableRow>
            ))}
            {summary && summary.rows.length === 0 && (
              <TableRow>
                <TableCell colSpan={7}>
                  <Typography color="text.secondary" sx={{ py: 2 }}>
                    {isFetching ? 'Loading…' : 'No collections recorded in this period.'}
                  </Typography>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {drillActor && (
        <PaymentDetailPanel
          actor={drillActor}
          range={range}
          onClose={() => setDrillActor(null)}
        />
      )}

      <Divider sx={{ my: 3 }} />

      <ReconciliationSection />
    </Box>
  )
}

function SummaryCard({ label, value, highlight }: { label: string; value: string; highlight?: boolean }) {
  return (
    <Grid size={{ xs: 6, sm: 3 }}>
      <Card variant="outlined" sx={{ bgcolor: highlight ? 'primary.50' : undefined }}>
        <CardContent>
          <Typography color="text.secondary" variant="body2">{label}</Typography>
          <Typography variant="h6">{value}</Typography>
        </CardContent>
      </Card>
    </Grid>
  )
}

function PaymentDetailPanel({
  actor, range, onClose,
}: {
  actor: { id: number | null; name: string }
  range: { from: string; to: string }
  onClose: () => void
}) {
  const { data: rows, isFetching } = useQuery({
    queryKey: ['collections-detail', actor.id, range.from, range.to],
    queryFn: () => getCollectionsDetail({ actor_user_id: actor.id, date_from: range.from, date_to: range.to }),
  })

  return (
    <Paper variant="outlined" sx={{ p: 2, mb: 1 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
        <Typography variant="subtitle1" fontWeight={600}>
          Payments collected by {actor.name || '—'}
        </Typography>
        <Button size="small" onClick={onClose}>Close</Button>
      </Box>
      <TableContainer sx={{ maxHeight: 420 }}>
        <Table size="small" stickyHeader sx={{ minWidth: 640 }}>
          <TableHead>
            <TableRow>
              <TableCell>When</TableCell>
              <TableCell>Student</TableCell>
              <TableCell>Item</TableCell>
              <TableCell align="right">Amount</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {rows?.map((p) => (
              <TableRow key={p.id}>
                <TableCell>{new Date(p.created_at).toLocaleString()}</TableCell>
                <TableCell>{p.student_name || '—'}</TableCell>
                <TableCell>
                  <Chip
                    size="small"
                    label={p.target_type === 'extra_charge' ? 'Charge' : 'Fee'}
                    color={p.target_type === 'extra_charge' ? 'warning' : 'success'}
                    variant="outlined"
                    sx={{ mr: 1 }}
                  />
                  {p.label}
                </TableCell>
                <TableCell align="right">{p.amount != null ? rupees(p.amount) : '—'}</TableCell>
              </TableRow>
            ))}
            {rows && rows.length === 0 && (
              <TableRow>
                <TableCell colSpan={4}>
                  <Typography color="text.secondary" sx={{ py: 1 }}>
                    {isFetching ? 'Loading…' : 'No payments in this period.'}
                  </Typography>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </Paper>
  )
}

function ReconciliationSection() {
  const queryClient = useQueryClient()
  const toast = useToast()
  const confirmAction = useConfirm()

  const { data: recon } = useQuery({ queryKey: ['collections-reconciliation'], queryFn: getReconciliation })
  const { data: handovers } = useQuery({ queryKey: ['collections-handovers'], queryFn: () => listHandovers() })
  const { data: users } = useQuery({ queryKey: ['users'], queryFn: listUsers })
  const accountants = useMemo(
    () => (users ?? []).filter((u) => u.role_name === 'Accountant' && u.is_active),
    [users],
  )

  const [accountantId, setAccountantId] = useState('')
  const [amount, setAmount] = useState('')
  const [handoverDate, setHandoverDate] = useState(fmt(new Date()))
  const [note, setNote] = useState('')

  const refresh = () => {
    queryClient.invalidateQueries({ queryKey: ['collections-reconciliation'] })
    queryClient.invalidateQueries({ queryKey: ['collections-handovers'] })
  }

  const createMutation = useMutation({
    mutationFn: () => createHandover({
      accountant_user_id: Number(accountantId),
      amount: Number(amount),
      handover_date: handoverDate || undefined,
      note: note || null,
    }),
    onSuccess: () => {
      toast('Handover recorded.')
      setAmount(''); setNote('')
      refresh()
    },
    onError: (e) => toast(apiErrorMessage(e), 'error'),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => deleteHandover(id),
    onSuccess: () => { toast('Handover removed.'); refresh() },
    onError: (e) => toast(apiErrorMessage(e), 'error'),
  })

  const canSubmit = !!accountantId && Number(amount) > 0

  return (
    <Box>
      <Typography variant="h6" gutterBottom>Cash Reconciliation (all-time)</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Everything each accountant has ever collected minus the cash they've handed in. The
        <strong> balance</strong> is what they're still holding.
      </Typography>

      <TableContainer component={Paper} variant="outlined" sx={{ mb: 3 }}>
        <Table size="small" sx={{ minWidth: 620 }}>
          <TableHead>
            <TableRow>
              <TableCell>Accountant</TableCell>
              <TableCell align="right">Total Collected</TableCell>
              <TableCell align="right">Handed Over</TableCell>
              <TableCell align="right">Balance Held</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {recon?.map((r) => (
              <TableRow key={r.actor_user_id ?? r.actor_username} hover>
                <TableCell>{r.actor_username || '—'}{r.actor_role ? ` (${r.actor_role})` : ''}</TableCell>
                <TableCell align="right">{rupees(r.total_collected)}</TableCell>
                <TableCell align="right">{rupees(r.total_handed_over)}</TableCell>
                <TableCell align="right">
                  <Typography
                    component="span"
                    fontWeight={700}
                    color={r.balance > 0 ? 'error.main' : r.balance < 0 ? 'warning.main' : 'success.main'}
                  >
                    {rupees(r.balance)}
                  </Typography>
                </TableCell>
              </TableRow>
            ))}
            {recon && recon.length === 0 && (
              <TableRow>
                <TableCell colSpan={4}>
                  <Typography color="text.secondary" sx={{ py: 2 }}>No accountants yet.</Typography>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>

      <Typography variant="subtitle1" fontWeight={600} gutterBottom>Record a Cash Handover</Typography>
      <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'center', mb: 3 }}>
        <TextField
          select label="Accountant" size="small" value={accountantId}
          onChange={(e) => setAccountantId(e.target.value)} sx={{ minWidth: 200 }}
        >
          {accountants.length === 0 && <MenuItem value="" disabled>No active accountants</MenuItem>}
          {accountants.map((u) => (
            <MenuItem key={u.user_id} value={String(u.user_id)}>
              {u.full_name} ({u.username})
            </MenuItem>
          ))}
        </TextField>
        <TextField
          label="Amount received" size="small" type="number" value={amount}
          onChange={(e) => setAmount(e.target.value)} sx={{ width: 160 }}
        />
        <TextField
          label="Date" type="date" size="small" value={handoverDate}
          onChange={(e) => setHandoverDate(e.target.value)} InputLabelProps={{ shrink: true }}
        />
        <TextField
          label="Note (optional)" size="small" value={note}
          onChange={(e) => setNote(e.target.value)} sx={{ minWidth: 200 }}
        />
        <Button
          variant="contained" disabled={!canSubmit || createMutation.isPending}
          onClick={() => createMutation.mutate()}
        >
          Record Handover
        </Button>
      </Box>

      <Typography variant="subtitle1" fontWeight={600} gutterBottom>Recent Handovers</Typography>
      <TableContainer component={Paper} variant="outlined">
        <Table size="small" sx={{ minWidth: 680 }}>
          <TableHead>
            <TableRow>
              <TableCell>Date</TableCell>
              <TableCell>Accountant</TableCell>
              <TableCell align="right">Amount</TableCell>
              <TableCell>Note</TableCell>
              <TableCell>Recorded By</TableCell>
              <TableCell align="center">Remove</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {handovers?.map((h) => (
              <TableRow key={h.id}>
                <TableCell>{h.handover_date}</TableCell>
                <TableCell>{h.accountant_username || '—'}</TableCell>
                <TableCell align="right">{rupees(h.amount)}</TableCell>
                <TableCell>{h.note || '—'}</TableCell>
                <TableCell>{h.recorded_by_username || '—'}</TableCell>
                <TableCell align="center">
                  <IconButton
                    size="small" color="error" aria-label="Remove handover"
                    onClick={async () => {
                      const ok = await confirmAction({
                        title: 'Remove this handover?',
                        message: `${rupees(h.amount)} from ${h.accountant_username} on ${h.handover_date} will be removed from the reconciliation.`,
                        confirmLabel: 'Remove',
                        destructive: true,
                      })
                      if (ok) deleteMutation.mutate(h.id)
                    }}
                  >
                    <DeleteIcon fontSize="small" />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
            {handovers && handovers.length === 0 && (
              <TableRow>
                <TableCell colSpan={6}>
                  <Typography color="text.secondary" sx={{ py: 2 }}>No handovers recorded yet.</Typography>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  )
}
