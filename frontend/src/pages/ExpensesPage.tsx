import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Alert, Box, Button, Card, CardContent, Chip, Dialog, DialogActions, DialogContent, DialogTitle,
  Grid, IconButton, MenuItem, Select, Skeleton, Table, TableBody, TableCell, TableContainer,
  TableHead, TableRow, TextField, Tooltip, Typography,
} from '@mui/material'
import { BarChart } from '@mui/x-charts/BarChart'
import EditIcon from '@mui/icons-material/Edit'
import DeleteIcon from '@mui/icons-material/Delete'
import AddIcon from '@mui/icons-material/Add'
import {
  PAYMENT_METHODS, createExpense, deleteExpense, getExpenseSummary, listExpenseCategories,
  listExpenses, updateExpense, type Expense, type ExpensePayload,
} from '../api/expenses'
import { useConfirm, useToast } from '../components/feedback'

function apiErrorMessage(e: unknown): string {
  return String((e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? e)
}

function fmtRs(n: number) {
  return `Rs. ${Math.round(n).toLocaleString()}`
}

/** YYYY-MM-DD in the *local* timezone. toISOString() would convert to UTC,
 * which in Pakistan (UTC+5) shifts any local midnight back to the previous
 * day — the default date range would silently start a day early. */
function isoDate(d: Date) {
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

const EMPTY_FORM: ExpensePayload = {
  expense_date: isoDate(new Date()),
  category: 'Salary',
  description: '',
  paid_to: '',
  for_month: '',
  amount: 0,
  payment_method: 'Cash',
  note: '',
}

export function ExpensesPage() {
  const queryClient = useQueryClient()
  const toast = useToast()
  const confirmAction = useConfirm()

  const today = new Date()
  const [dateFrom, setDateFrom] = useState(isoDate(new Date(today.getFullYear(), today.getMonth(), 1)))
  const [dateTo, setDateTo] = useState(isoDate(today))
  const [category, setCategory] = useState('')

  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [form, setForm] = useState<ExpensePayload>(EMPTY_FORM)
  const [amountText, setAmountText] = useState('')

  const { data: categories } = useQuery({ queryKey: ['expense-categories'], queryFn: listExpenseCategories })
  const filters = { date_from: dateFrom, date_to: dateTo, category }
  const { data: expenses, isLoading, isError } = useQuery({
    queryKey: ['expenses', dateFrom, dateTo, category],
    queryFn: () => listExpenses(filters),
  })
  const { data: summary } = useQuery({
    queryKey: ['expense-summary', dateFrom, dateTo],
    queryFn: () => getExpenseSummary({ date_from: dateFrom, date_to: dateTo }),
  })

  const refresh = () => {
    queryClient.invalidateQueries({ queryKey: ['expenses'] })
    queryClient.invalidateQueries({ queryKey: ['expense-summary'] })
  }

  const saveMutation = useMutation({
    mutationFn: () => {
      const payload: ExpensePayload = {
        ...form,
        amount: Number(amountText) || 0,
        for_month: form.category === 'Salary' ? form.for_month || null : null,
      }
      return editingId ? updateExpense(editingId, payload) : createExpense(payload)
    },
    onSuccess: () => {
      toast(editingId ? 'Expense updated.' : 'Expense recorded.')
      setDialogOpen(false)
      refresh()
    },
    onError: (e) => toast(apiErrorMessage(e), 'error'),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => deleteExpense(id),
    onSuccess: () => { toast('Expense deleted.'); refresh() },
    onError: (e) => toast(apiErrorMessage(e), 'error'),
  })

  function openAdd() {
    setEditingId(null)
    setForm(EMPTY_FORM)
    setAmountText('')
    setDialogOpen(true)
  }

  function openEdit(e: Expense) {
    setEditingId(e.expense_id)
    setForm({
      expense_date: e.expense_date,
      category: e.category,
      description: e.description,
      paid_to: e.paid_to,
      for_month: e.for_month ?? '',
      amount: e.amount,
      payment_method: e.payment_method,
      note: e.note ?? '',
    })
    setAmountText(String(e.amount))
    setDialogOpen(true)
  }

  const amountValid = Number(amountText) > 0
  const net = summary?.net ?? 0

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1, flexWrap: 'wrap', gap: 1 }}>
        <Typography variant="h5">Expenses &amp; Salaries</Typography>
        <Button variant="contained" startIcon={<AddIcon />} onClick={openAdd}>Add Expense</Button>
      </Box>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Money paid out by the school. Income below is fee payments actually collected in the same
        date range, so Net Profit/Loss reconciles with the Collections page.
      </Typography>

      <Box sx={{ display: 'flex', gap: 2, mb: 3, flexWrap: 'wrap', alignItems: 'center' }}>
        <TextField
          label="From" type="date" size="small" value={dateFrom}
          onChange={(e) => setDateFrom(e.target.value)} InputLabelProps={{ shrink: true }}
        />
        <TextField
          label="To" type="date" size="small" value={dateTo}
          onChange={(e) => setDateTo(e.target.value)} InputLabelProps={{ shrink: true }}
        />
        <Select size="small" value={category} onChange={(e) => setCategory(e.target.value)} displayEmpty sx={{ width: 170 }}>
          <MenuItem value="">All Categories</MenuItem>
          {categories?.map((c) => <MenuItem key={c} value={c}>{c}</MenuItem>)}
        </Select>
      </Box>

      {!summary ? (
        <Grid container spacing={2} sx={{ mb: 3 }}>
          {[0, 1, 2, 3].map((i) => (
            <Grid key={i} size={{ xs: 12, sm: 6, md: 3 }}><Skeleton variant="rounded" height={92} /></Grid>
          ))}
        </Grid>
      ) : (
        <Grid container spacing={2} sx={{ mb: 3 }}>
          {[
            { label: 'Fees Collected', value: summary.income, color: '#2e7d32' },
            { label: 'Total Expenses', value: summary.expenses, color: '#c62828' },
            { label: 'Salaries Paid', value: summary.salary_total, color: '#ed6c02' },
          ].map((c) => (
            <Grid key={c.label} size={{ xs: 12, sm: 6, md: 3 }}>
              <Card sx={{ height: '100%' }}>
                <CardContent>
                  <Typography variant="body2" color="text.secondary">{c.label}</Typography>
                  <Typography variant="h6" sx={{ color: c.color }}>{fmtRs(c.value)}</Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Card sx={{ height: '100%' }}>
              <CardContent>
                <Typography variant="body2" color="text.secondary">
                  Net {net >= 0 ? 'Profit' : 'Loss'}
                </Typography>
                <Typography variant="h6" color={net >= 0 ? 'success.main' : 'error'}>
                  {fmtRs(Math.abs(net))}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {summary && summary.monthly.length > 0 && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="subtitle1" gutterBottom>Income vs Expenses by Month</Typography>
            <BarChart
              height={280}
              dataset={summary.monthly}
              xAxis={[{ dataKey: 'month', scaleType: 'band' }]}
              series={[
                { dataKey: 'income', label: 'Collected', color: '#2e7d32' },
                { dataKey: 'expenses', label: 'Expenses', color: '#c62828' },
              ]}
            />
          </CardContent>
        </Card>
      )}

      {summary && summary.by_category.length > 0 && (
        <Box sx={{ display: 'flex', gap: 1, mb: 3, flexWrap: 'wrap' }}>
          {summary.by_category.map((c) => (
            <Chip key={c.category} label={`${c.category}: ${fmtRs(c.total)} (${c.count})`} size="small" />
          ))}
        </Box>
      )}

      {isError && <Alert severity="error" sx={{ mb: 2 }}>Could not load expenses. Please try again.</Alert>}

      <TableContainer sx={{ mb: 2 }}>
        <Table size="small" sx={{ minWidth: 820 }}>
          <TableHead>
            <TableRow>
              <TableCell>Date</TableCell>
              <TableCell>Category</TableCell>
              <TableCell>Description</TableCell>
              <TableCell>Paid To</TableCell>
              <TableCell>For Month</TableCell>
              <TableCell align="right">Amount (Rs.)</TableCell>
              <TableCell>Method</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {expenses?.map((e) => (
              <TableRow key={e.expense_id}>
                <TableCell>{e.expense_date}</TableCell>
                <TableCell><Chip size="small" label={e.category} /></TableCell>
                <TableCell>{e.description || '—'}</TableCell>
                <TableCell>{e.paid_to || '—'}</TableCell>
                <TableCell>{e.for_month || '—'}</TableCell>
                <TableCell align="right">{Math.round(e.amount).toLocaleString()}</TableCell>
                <TableCell>{e.payment_method}</TableCell>
                <TableCell>
                  <Tooltip title="Edit">
                    <IconButton size="small" onClick={() => openEdit(e)}><EditIcon fontSize="small" /></IconButton>
                  </Tooltip>
                  <Tooltip title="Delete">
                    <IconButton
                      size="small" color="error"
                      onClick={async () => {
                        const ok = await confirmAction({
                          title: `Delete this ${e.category.toLowerCase()} expense?`,
                          message: `${fmtRs(e.amount)} on ${e.expense_date} will be permanently removed.`,
                          confirmLabel: 'Delete',
                          destructive: true,
                        })
                        if (ok) deleteMutation.mutate(e.expense_id)
                      }}
                    >
                      <DeleteIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </TableCell>
              </TableRow>
            ))}
            {!isLoading && expenses?.length === 0 && (
              <TableRow>
                <TableCell colSpan={8}>
                  <Typography color="text.secondary" sx={{ py: 1 }}>
                    No expenses recorded in this range.
                  </Typography>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>

      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} fullWidth maxWidth="sm">
        <DialogTitle>{editingId ? 'Edit Expense' : 'Add Expense'}</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
            <TextField
              label="Date" type="date" size="small" value={form.expense_date}
              onChange={(e) => setForm({ ...form, expense_date: e.target.value })}
              InputLabelProps={{ shrink: true }}
            />
            <Select
              size="small" value={form.category}
              onChange={(e) => setForm({ ...form, category: e.target.value })}
            >
              {categories?.map((c) => <MenuItem key={c} value={c}>{c}</MenuItem>)}
            </Select>
            <TextField
              label={form.category === 'Salary' ? 'Staff Name' : 'Paid To (vendor)'}
              size="small" value={form.paid_to}
              onChange={(e) => setForm({ ...form, paid_to: e.target.value })}
            />
            {form.category === 'Salary' && (
              <TextField
                label="Salary For Month (YYYY-MM)" size="small" placeholder="2026-09"
                value={form.for_month ?? ''}
                onChange={(e) => setForm({ ...form, for_month: e.target.value })}
              />
            )}
            <TextField
              label="Description" size="small" value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
            />
            <TextField
              label="Amount (Rs.)" size="small" value={amountText}
              onChange={(e) => setAmountText(e.target.value)}
              error={amountText !== '' && !amountValid}
              helperText={amountText !== '' && !amountValid ? 'Enter an amount greater than zero.' : ' '}
            />
            <Select
              size="small" value={form.payment_method}
              onChange={(e) => setForm({ ...form, payment_method: e.target.value })}
            >
              {PAYMENT_METHODS.map((m) => <MenuItem key={m} value={m}>{m}</MenuItem>)}
            </Select>
            <TextField
              label="Note (optional)" size="small" multiline rows={2} value={form.note ?? ''}
              onChange={(e) => setForm({ ...form, note: e.target.value })}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            disabled={!amountValid || saveMutation.isPending}
            onClick={() => saveMutation.mutate()}
          >
            {editingId ? 'Save Changes' : 'Add Expense'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
