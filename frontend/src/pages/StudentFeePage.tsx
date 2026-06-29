import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate, useParams } from 'react-router-dom'
import {
  Box, Button, Card, CardContent, Chip, Divider, Grid, MenuItem, Select, Table, TableBody,
  TableCell, TableHead, TableRow, TextField, Typography,
} from '@mui/material'
import { getBalanceSheet } from '../api/feeReports'
import { getStudent, listStudents } from '../api/students'
import { downloadFile } from '../api/client'
import { applyVoucherDiscount, deleteVoucher, editVoucher, generateVoucher, payVoucher } from '../api/feeVouchers'
import { addCharge, applyChargeDiscount, deleteCharge, editCharge, payCharge } from '../api/extraCharges'
import { listGrades } from '../api/grades'
import { DiscountDialog } from '../components/DiscountDialog'
import { EditFigureDialog } from '../components/EditFigureDialog'
import { useAuth } from '../context/AuthContext'

const STATUS_COLOR: Record<string, 'success' | 'warning' | 'error'> = {
  Paid: 'success', Partial: 'warning', Unpaid: 'error', Open: 'warning',
}

function apiErrorMessage(e: unknown): string {
  return String((e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? e)
}

export function StudentFeePage() {
  const { studentId } = useParams()
  const id = Number(studentId) || 0

  if (!id) return <StudentSearchPicker />
  return <StudentLedger studentId={id} />
}

function StudentSearchPicker() {
  const navigate = useNavigate()
  const [query, setQuery] = useState('')
  const { data: results, isFetching } = useQuery({
    queryKey: ['student-fee-search', query],
    queryFn: () => listStudents({ search: query }),
    enabled: query.length > 0,
  })

  return (
    <Box sx={{ maxWidth: 600 }}>
      <Typography variant="h5" gutterBottom>
        Student Fee
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Search for a student to view and manage their fee — vouchers, payments, discounts, and
        extra charges, all in one place.
      </Typography>
      <TextField
        fullWidth
        autoFocus
        label="Search by name, registration no, or CNIC"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        sx={{ mb: 2 }}
      />
      {isFetching && <Typography color="text.secondary">Searching…</Typography>}
      {results?.map((s) => (
        <Box
          key={s.student_id}
          onClick={() => navigate(`/fees/student/${s.student_id}`)}
          sx={{
            p: 1.5, mb: 1, border: '1px solid', borderColor: 'divider', borderRadius: 1,
            cursor: 'pointer', '&:hover': { bgcolor: 'action.hover' },
          }}
        >
          <Typography fontWeight="bold">{s.name} <Typography component="span" color="text.secondary">({s.registration_no})</Typography></Typography>
          <Typography variant="body2" color="text.secondary">Class: {s.class_name} · Father: {s.father_name}</Typography>
        </Box>
      ))}
      {query && results?.length === 0 && !isFetching && (
        <Typography color="text.secondary">No students found.</Typography>
      )}
    </Box>
  )
}

function StudentLedger({ studentId }: { studentId: number }) {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { role } = useAuth()
  const isAdmin = role === 'Admin'
  const { data: student } = useQuery({ queryKey: ['student', studentId], queryFn: () => getStudent(studentId) })
  const { data: sheet } = useQuery({ queryKey: ['balance-sheet', studentId], queryFn: () => getBalanceSheet(studentId) })
  const { data: grades } = useQuery({ queryKey: ['grades'], queryFn: listGrades })

  const [payAmounts, setPayAmounts] = useState<Record<string, string>>({})
  const [discountTarget, setDiscountTarget] = useState<{ type: 'voucher' | 'charge'; id: number; max: number } | null>(null)
  const [discountError, setDiscountError] = useState<string | null>(null)
  const [editTarget, setEditTarget] = useState<{ type: 'voucher' | 'charge'; id: number } | null>(null)
  const [editError, setEditError] = useState<string | null>(null)

  const refresh = () => {
    queryClient.invalidateQueries({ queryKey: ['balance-sheet', studentId] })
    queryClient.invalidateQueries({ queryKey: ['student', studentId] })
  }

  const payVoucherMutation = useMutation({
    mutationFn: ({ voucherId, amount }: { voucherId: number; amount: number }) => payVoucher(voucherId, amount),
    onSuccess: refresh,
    onError: (e) => alert(apiErrorMessage(e)),
  })
  const payChargeMutation = useMutation({
    mutationFn: ({ chargeId, amount }: { chargeId: number; amount: number }) => payCharge(chargeId, amount),
    onSuccess: refresh,
    onError: (e) => alert(apiErrorMessage(e)),
  })
  const voucherDiscountMutation = useMutation({
    mutationFn: ({ voucherId, amount, reason }: { voucherId: number; amount: number; reason: string }) =>
      applyVoucherDiscount(voucherId, amount, reason),
    onSuccess: () => { refresh(); setDiscountTarget(null); setDiscountError(null) },
    onError: (e) => setDiscountError(apiErrorMessage(e)),
  })
  const chargeDiscountMutation = useMutation({
    mutationFn: ({ chargeId, amount, reason }: { chargeId: number; amount: number; reason: string }) =>
      applyChargeDiscount(chargeId, amount, reason),
    onSuccess: () => { refresh(); setDiscountTarget(null); setDiscountError(null) },
    onError: (e) => setDiscountError(apiErrorMessage(e)),
  })
  const deleteVoucherMutation = useMutation({
    mutationFn: (voucherId: number) => deleteVoucher(voucherId),
    onSuccess: refresh,
    onError: (e) => alert(apiErrorMessage(e)),
  })
  const deleteChargeMutation = useMutation({
    mutationFn: (chargeId: number) => deleteCharge(chargeId),
    onSuccess: refresh,
    onError: (e) => alert(apiErrorMessage(e)),
  })
  const editVoucherMutation = useMutation({
    mutationFn: ({ voucherId, values }: { voucherId: number; values: { total_amount: number; paid_amount: number; discount_amount: number; discount_reason: string | null } }) =>
      editVoucher(voucherId, values),
    onSuccess: () => { refresh(); setEditTarget(null); setEditError(null) },
    onError: (e) => setEditError(apiErrorMessage(e)),
  })
  const editChargeMutation = useMutation({
    mutationFn: ({ chargeId, values }: { chargeId: number; values: { description: string; total_amount: number; paid_amount: number; discount_amount: number; discount_reason: string | null } }) =>
      editCharge(chargeId, {
        description: values.description, amount: values.total_amount, paid_amount: values.paid_amount,
        discount_amount: values.discount_amount, discount_reason: values.discount_reason,
      }),
    onSuccess: () => { refresh(); setEditTarget(null); setEditError(null) },
    onError: (e) => setEditError(apiErrorMessage(e)),
  })

  const [genYear, setGenYear] = useState(new Date().getFullYear())
  const [genMonth, setGenMonth] = useState(new Date().getMonth() + 1)
  const [genAmount, setGenAmount] = useState('')
  const generateMutation = useMutation({
    mutationFn: () => generateVoucher(studentId, genYear, genMonth, Number(genAmount) || student?.default_fee || 0),
    onSuccess: () => { refresh(); setGenAmount('') },
    onError: (e) => alert(apiErrorMessage(e)),
  })

  const [chargeDesc, setChargeDesc] = useState('')
  const [chargeAmount, setChargeAmount] = useState('')
  const addChargeMutation = useMutation({
    mutationFn: () => addCharge(studentId, chargeDesc, Number(chargeAmount) || 0),
    onSuccess: () => { refresh(); setChargeDesc(''); setChargeAmount('') },
    onError: (e) => alert(apiErrorMessage(e)),
  })

  if (!student || !sheet) return <Typography>Loading...</Typography>

  const defaultGenAmount = grades?.find((g) => g.class_name === student.class_name)?.fee_amount ?? 0

  return (
    <Box>
      <Button sx={{ mb: 1 }} onClick={() => navigate('/fees/student')}>← Search Another Student</Button>
      <Typography variant="h5" gutterBottom>
        {student.name} <Typography component="span" color="text.secondary">({student.registration_no})</Typography>
      </Typography>
      <Typography color="text.secondary" gutterBottom>
        Class: {student.class_name} · Father: {student.father_name} · Phone: {student.phone || '—'} · CNIC: {student.cnic || '—'}
      </Typography>

      <Grid container spacing={2} sx={{ mb: 1, mt: 1 }}>
        <Grid size={{ xs: 12, sm: 4 }}>
          <Card>
            <CardContent>
              <Typography color="text.secondary">Total Fees Due</Typography>
              <Typography variant="h5">Rs. {sheet.total_fees_due.toFixed(0)}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 4 }}>
          <Card>
            <CardContent>
              <Typography color="text.secondary">Total Paid</Typography>
              <Typography variant="h5">Rs. {sheet.total_paid.toFixed(0)}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 4 }}>
          <Card sx={{ bgcolor: sheet.total_pending > 0 ? 'error.50' : undefined }}>
            <CardContent>
              <Typography color="text.secondary">Total Pending</Typography>
              <Typography variant="h5" color={sheet.total_pending > 0 ? 'error' : 'success.main'}>
                Rs. {sheet.total_pending.toFixed(0)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
      {sheet.total_discounted > 0 && (
        <Typography color="text.secondary" sx={{ mb: 2 }}>
          Total discount/concession given so far: Rs. {sheet.total_discounted.toFixed(0)}
        </Typography>
      )}

      <Divider sx={{ my: 2 }} />

      <Typography variant="h6" gutterBottom>
        Fee Vouchers
      </Typography>
      <Table size="small" sx={{ maxWidth: 950, mb: 2 }}>
        <TableHead>
          <TableRow>
            <TableCell>Month</TableCell>
            <TableCell>Total</TableCell>
            <TableCell>Paid</TableCell>
            <TableCell>Discount</TableCell>
            <TableCell>Pending</TableCell>
            <TableCell>Status</TableCell>
            <TableCell>Actions</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {sheet.vouchers.map((v) => {
            const remaining = Math.max(v.total_amount - v.paid_amount - v.discount_amount, 0)
            const key = `v-${v.voucher_id}`
            return (
              <TableRow key={v.voucher_id}>
                <TableCell>{v.fee_month}</TableCell>
                <TableCell>{v.total_amount}</TableCell>
                <TableCell>{v.paid_amount}</TableCell>
                <TableCell>{v.discount_amount > 0 ? `${v.discount_amount}${v.discount_reason ? ` (${v.discount_reason})` : ''}` : '—'}</TableCell>
                <TableCell>{remaining.toFixed(0)}</TableCell>
                <TableCell>
                  <Chip size="small" label={v.status} color={STATUS_COLOR[v.status] ?? 'default'} />
                </TableCell>
                <TableCell>
                  <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                    {remaining > 0 && (
                      <>
                        <TextField
                          size="small" placeholder="Amount" sx={{ width: 70 }}
                          value={payAmounts[key] ?? ''}
                          onChange={(e) => setPayAmounts((p) => ({ ...p, [key]: e.target.value }))}
                        />
                        <Button size="small" variant="contained" onClick={() => payVoucherMutation.mutate({ voucherId: v.voucher_id, amount: Number(payAmounts[key]) || 0 })}>
                          Pay
                        </Button>
                        {isAdmin && (
                          <Button size="small" color="secondary" onClick={() => setDiscountTarget({ type: 'voucher', id: v.voucher_id, max: remaining })}>
                            Discount
                          </Button>
                        )}
                      </>
                    )}
                    <Button size="small" onClick={() => downloadFile(`/fee-vouchers/${v.voucher_id}/pdf`, {}, `voucher_${v.voucher_id}.pdf`)}>
                      PDF
                    </Button>
                    {isAdmin && (
                      <>
                        <Button size="small" onClick={() => setEditTarget({ type: 'voucher', id: v.voucher_id })}>
                          Edit
                        </Button>
                        <Button
                          size="small"
                          color="error"
                          onClick={() => { if (confirm(`Delete the ${v.fee_month} voucher?`)) deleteVoucherMutation.mutate(v.voucher_id) }}
                        >
                          Delete
                        </Button>
                      </>
                    )}
                  </Box>
                </TableCell>
              </TableRow>
            )
          })}
        </TableBody>
      </Table>

      <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'center', mb: 4 }}>
        <Typography variant="body2" color="text.secondary">Generate voucher:</Typography>
        <TextField label="Year" size="small" type="number" value={genYear} onChange={(e) => setGenYear(Number(e.target.value))} sx={{ width: 90 }} />
        <Select size="small" value={genMonth} onChange={(e) => setGenMonth(Number(e.target.value))} sx={{ width: 130 }}>
          {Array.from({ length: 12 }, (_, i) => i + 1).map((m) => (
            <MenuItem key={m} value={m}>{new Date(2000, m - 1).toLocaleString('en', { month: 'long' })}</MenuItem>
          ))}
        </Select>
        <TextField
          label={`Amount (default Rs. ${student.default_fee ?? defaultGenAmount})`}
          size="small" value={genAmount} onChange={(e) => setGenAmount(e.target.value)} sx={{ width: 220 }}
        />
        <Button variant="contained" onClick={() => generateMutation.mutate()}>Generate</Button>
      </Box>

      <Divider sx={{ my: 2 }} />

      <Typography variant="h6" gutterBottom>
        Extra Charges
      </Typography>
      <Table size="small" sx={{ maxWidth: 950, mb: 2 }}>
        <TableHead>
          <TableRow>
            <TableCell>Description</TableCell>
            <TableCell>Amount</TableCell>
            <TableCell>Paid</TableCell>
            <TableCell>Discount</TableCell>
            <TableCell>Status</TableCell>
            <TableCell>Actions</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {sheet.charges.map((c) => {
            const remaining = Math.max(c.amount - c.paid_amount - c.discount_amount, 0)
            const key = `c-${c.charge_id}`
            return (
              <TableRow key={c.charge_id}>
                <TableCell>{c.description}</TableCell>
                <TableCell>{c.amount}</TableCell>
                <TableCell>{c.paid_amount}</TableCell>
                <TableCell>{c.discount_amount > 0 ? `${c.discount_amount}${c.discount_reason ? ` (${c.discount_reason})` : ''}` : '—'}</TableCell>
                <TableCell>
                  <Chip size="small" label={c.status} color={STATUS_COLOR[c.status] ?? 'default'} />
                </TableCell>
                <TableCell>
                  <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                    {remaining > 0 && (
                      <>
                        <TextField
                          size="small" placeholder="Amount" sx={{ width: 70 }}
                          value={payAmounts[key] ?? ''}
                          onChange={(e) => setPayAmounts((p) => ({ ...p, [key]: e.target.value }))}
                        />
                        <Button size="small" variant="contained" onClick={() => payChargeMutation.mutate({ chargeId: c.charge_id, amount: Number(payAmounts[key]) || 0 })}>
                          Pay
                        </Button>
                        {isAdmin && (
                          <Button size="small" color="secondary" onClick={() => setDiscountTarget({ type: 'charge', id: c.charge_id, max: remaining })}>
                            Discount
                          </Button>
                        )}
                      </>
                    )}
                    {isAdmin && (
                      <>
                        <Button size="small" onClick={() => setEditTarget({ type: 'charge', id: c.charge_id })}>
                          Edit
                        </Button>
                        <Button
                          size="small"
                          color="error"
                          onClick={() => { if (confirm(`Delete "${c.description}"?`)) deleteChargeMutation.mutate(c.charge_id) }}
                        >
                          Delete
                        </Button>
                      </>
                    )}
                  </Box>
                </TableCell>
              </TableRow>
            )
          })}
        </TableBody>
      </Table>

      <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'center' }}>
        <Typography variant="body2" color="text.secondary">Add charge:</Typography>
        <TextField label="Description" size="small" value={chargeDesc} onChange={(e) => setChargeDesc(e.target.value)} />
        <TextField label="Amount" size="small" value={chargeAmount} onChange={(e) => setChargeAmount(e.target.value)} sx={{ width: 120 }} />
        <Button variant="contained" disabled={!chargeDesc || !chargeAmount} onClick={() => addChargeMutation.mutate()}>
          Add Charge
        </Button>
      </Box>

      <DiscountDialog
        open={!!discountTarget}
        onClose={() => { setDiscountTarget(null); setDiscountError(null) }}
        title={discountTarget?.type === 'charge' ? 'Apply Charge Discount' : 'Apply Fee Discount'}
        maxDiscount={discountTarget?.max ?? 0}
        error={discountError}
        onApply={(amount, reason) => {
          if (!discountTarget) return
          if (discountTarget.type === 'voucher') {
            voucherDiscountMutation.mutate({ voucherId: discountTarget.id, amount, reason })
          } else {
            chargeDiscountMutation.mutate({ chargeId: discountTarget.id, amount, reason })
          }
        }}
      />

      <EditFigureDialog
        open={!!editTarget}
        onClose={() => { setEditTarget(null); setEditError(null) }}
        title={editTarget?.type === 'charge' ? 'Edit Extra Charge' : 'Edit Fee Voucher'}
        showDescription={editTarget?.type === 'charge'}
        error={editError}
        initial={(() => {
          if (!editTarget) return null
          if (editTarget.type === 'voucher') {
            const v = sheet.vouchers.find((x) => x.voucher_id === editTarget.id)
            if (!v) return null
            return { total_amount: v.total_amount, paid_amount: v.paid_amount, discount_amount: v.discount_amount, discount_reason: v.discount_reason }
          }
          const c = sheet.charges.find((x) => x.charge_id === editTarget.id)
          if (!c) return null
          return { description: c.description, total_amount: c.amount, paid_amount: c.paid_amount, discount_amount: c.discount_amount, discount_reason: c.discount_reason }
        })()}
        onSave={(values) => {
          if (!editTarget) return
          if (editTarget.type === 'voucher') {
            editVoucherMutation.mutate({ voucherId: editTarget.id, values })
          } else {
            editChargeMutation.mutate({ chargeId: editTarget.id, values: { ...values, description: values.description ?? '' } })
          }
        }}
      />

    </Box>
  )
}
