import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Box, Button, Checkbox, Chip, MenuItem, Select, Table, TableBody, TableCell, TableHead, TableRow, TextField, Typography,
} from '@mui/material'
import {
  addCharge, applyChargeDiscount, bulkAddCharge, bulkDeleteCharges, deleteCharge, getStudentCharges, payCharge,
} from '../api/extraCharges'
import { listGrades } from '../api/grades'
import { DiscountDialog } from '../components/DiscountDialog'
import { useAuth } from '../context/AuthContext'

export function ExtraChargesPage() {
  const queryClient = useQueryClient()
  const { role } = useAuth()
  const isAdmin = role === 'Admin'
  const [studentId, setStudentId] = useState('')
  const [description, setDescription] = useState('')
  const [amount, setAmount] = useState('')
  const [payAmounts, setPayAmounts] = useState<Record<number, string>>({})
  const [discountTarget, setDiscountTarget] = useState<{ id: number; max: number } | null>(null)
  const [discountError, setDiscountError] = useState<string | null>(null)
  const [selected, setSelected] = useState<number[]>([])

  const sid = Number(studentId) || 0
  const { data: charges } = useQuery({
    queryKey: ['charges', sid],
    queryFn: () => getStudentCharges(sid),
    enabled: sid > 0,
  })

  const addMutation = useMutation({
    mutationFn: () => addCharge(sid, description, Number(amount) || 0),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['charges', sid] })
      setDescription('')
      setAmount('')
    },
    onError: (e) => alert(String((e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? 'Could not add charge.')),
  })

  const payMutation = useMutation({
    mutationFn: ({ chargeId, amt }: { chargeId: number; amt: number }) => payCharge(chargeId, amt),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['charges', sid] }),
    onError: (e) => alert(String((e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? 'Payment failed.')),
  })

  const discountMutation = useMutation({
    mutationFn: ({ chargeId, amt, reason }: { chargeId: number; amt: number; reason: string }) =>
      applyChargeDiscount(chargeId, amt, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['charges', sid] })
      setDiscountTarget(null)
      setDiscountError(null)
    },
    onError: (e) => setDiscountError(String((e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? e)),
  })

  const deleteMutation = useMutation({
    mutationFn: (chargeId: number) => deleteCharge(chargeId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['charges', sid] }),
    onError: () => alert('Cannot delete — this charge already has a payment or discount recorded against it.'),
  })

  const bulkDeleteMutation = useMutation({
    mutationFn: (chargeIds: number[]) => bulkDeleteCharges(chargeIds),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ['charges', sid] })
      setSelected([])
      const skippedMsg = result.skipped.length ? ` ${result.skipped.length} skipped (already have a payment or discount).` : ''
      alert(`Deleted ${result.deleted} charge(s).${skippedMsg}`)
    },
  })

  const toggleSelected = (chargeId: number) =>
    setSelected((prev) => (prev.includes(chargeId) ? prev.filter((id) => id !== chargeId) : [...prev, chargeId]))

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        Extra Charges
      </Typography>
      <TextField
        label="Student ID"
        size="small"
        value={studentId}
        onChange={(e) => { setStudentId(e.target.value); setSelected([]) }}
        sx={{ mb: 2 }}
      />

      {sid > 0 && (
        <>
          <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
            <TextField label="Description" size="small" value={description} onChange={(e) => setDescription(e.target.value)} />
            <TextField label="Amount" size="small" value={amount} onChange={(e) => setAmount(e.target.value)} />
            <Button variant="contained" onClick={() => addMutation.mutate()} disabled={!description || !amount || Number(amount) <= 0}>
              Add Charge
            </Button>
            {isAdmin && selected.length > 0 && (
              <Button
                color="error"
                onClick={() => {
                  if (confirm(`Delete ${selected.length} selected charge(s)?`)) {
                    bulkDeleteMutation.mutate(selected)
                  }
                }}
              >
                Delete Selected ({selected.length})
              </Button>
            )}
          </Box>

          <Table size="small">
            <TableHead>
              <TableRow>
                {isAdmin && <TableCell></TableCell>}
                <TableCell>Description</TableCell>
                <TableCell>Amount</TableCell>
                <TableCell>Paid</TableCell>
                <TableCell>Discount</TableCell>
                <TableCell>Remaining</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {charges?.map((c) => (
                <TableRow key={c.charge_id}>
                  {isAdmin && (
                    <TableCell padding="checkbox">
                      <Checkbox checked={selected.includes(c.charge_id)} onChange={() => toggleSelected(c.charge_id)} />
                    </TableCell>
                  )}
                  <TableCell>{c.description}</TableCell>
                  <TableCell>{c.amount}</TableCell>
                  <TableCell>{c.paid_amount}</TableCell>
                  <TableCell>{c.discount_amount}</TableCell>
                  <TableCell>{c.remaining_amount}</TableCell>
                  <TableCell>
                    <Chip size="small" label={c.status} color={c.status === 'Paid' ? 'success' : 'warning'} />
                  </TableCell>
                  <TableCell>
                    <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                      {c.status !== 'Paid' && (
                        <>
                          <TextField
                            size="small"
                            sx={{ width: 80 }}
                            value={payAmounts[c.charge_id] ?? ''}
                            onChange={(e) => setPayAmounts((prev) => ({ ...prev, [c.charge_id]: e.target.value }))}
                          />
                          <Button
                            size="small"
                            disabled={!(Number(payAmounts[c.charge_id]) > 0)}
                            onClick={() => payMutation.mutate({ chargeId: c.charge_id, amt: Number(payAmounts[c.charge_id]) || 0 })}
                          >
                            Pay
                          </Button>
                          {isAdmin && (
                            <Button
                              size="small"
                              color="secondary"
                              onClick={() => setDiscountTarget({ id: c.charge_id, max: c.remaining_amount })}
                            >
                              Discount
                            </Button>
                          )}
                        </>
                      )}
                      {isAdmin && (
                        <Button
                          size="small"
                          color="error"
                          onClick={() => { if (confirm('Delete this charge?')) deleteMutation.mutate(c.charge_id) }}
                        >
                          Delete
                        </Button>
                      )}
                    </Box>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </>
      )}

      <DiscountDialog
        open={!!discountTarget}
        onClose={() => { setDiscountTarget(null); setDiscountError(null) }}
        title="Apply Charge Discount"
        maxDiscount={discountTarget?.max ?? 0}
        error={discountError}
        onApply={(amount, reason) => {
          if (discountTarget) discountMutation.mutate({ chargeId: discountTarget.id, amt: amount, reason })
        }}
      />

      <BulkChargeSection />
    </Box>
  )
}

function BulkChargeSection() {
  const { data: grades } = useQuery({ queryKey: ['grades'], queryFn: listGrades })
  const [selectedClasses, setSelectedClasses] = useState<string[]>([])
  const [description, setDescription] = useState('')
  const [amount, setAmount] = useState('')
  const [result, setResult] = useState<string | null>(null)

  const mutation = useMutation({
    mutationFn: () => bulkAddCharge(selectedClasses, description, Number(amount) || 0),
    onSuccess: (charges) => {
      setResult(`Added "${description}" (Rs. ${amount}) to ${charges.length} student(s) in ${selectedClasses.join(', ')}.`)
      setDescription('')
      setAmount('')
    },
    onError: () => setResult('Bulk charge failed.'),
  })

  return (
    <Box sx={{ mt: 4, p: 2, border: '1px solid', borderColor: 'divider', borderRadius: 1, maxWidth: 700 }}>
      <Typography variant="h6" gutterBottom>
        Bulk Add Charge (class-wise)
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Adds the same charge to every active student in the selected classes in one go — e.g. exam
        fee, annual fund, uniform charge.
      </Typography>
      <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
        <Select
          multiple
          size="small"
          value={selectedClasses}
          onChange={(e) => setSelectedClasses(e.target.value as unknown as string[])}
          displayEmpty
          sx={{ minWidth: 220 }}
          renderValue={(selected) => (selected as string[]).join(', ') || 'Select classes'}
        >
          {grades?.map((g) => (
            <MenuItem key={g.grade_id} value={g.class_name}>{g.class_name}</MenuItem>
          ))}
        </Select>
        <Button size="small" onClick={() => setSelectedClasses(grades?.map((g) => g.class_name) ?? [])}>
          Select All Classes
        </Button>
        <TextField label="Description" size="small" value={description} onChange={(e) => setDescription(e.target.value)} />
        <TextField label="Amount" size="small" value={amount} onChange={(e) => setAmount(e.target.value)} />
        <Button
          variant="contained"
          disabled={selectedClasses.length === 0 || !description || !amount}
          onClick={() => mutation.mutate()}
        >
          Add to Selected Classes
        </Button>
      </Box>
      {result && <Typography sx={{ mt: 2 }}>{result}</Typography>}
    </Box>
  )
}
