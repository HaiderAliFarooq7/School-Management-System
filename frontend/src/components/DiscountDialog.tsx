import { useEffect, useState } from 'react'
import {
  Alert, Button, Dialog, DialogActions, DialogContent, DialogTitle, TextField, Typography,
} from '@mui/material'

interface Props {
  open: boolean
  onClose: () => void
  title: string
  maxDiscount: number
  onApply: (amount: number, reason: string) => void
  error?: string | null
}

export function DiscountDialog({ open, onClose, title, maxDiscount, onApply, error }: Props) {
  const [amount, setAmount] = useState('')
  const [reason, setReason] = useState('')

  useEffect(() => {
    if (open) {
      setAmount('')
      setReason('')
    }
  }, [open])

  const numericAmount = Number(amount)
  const isValidAmount = amount !== '' && Number.isFinite(numericAmount) && numericAmount > 0 && numericAmount <= maxDiscount

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>{title}</DialogTitle>
      <DialogContent>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Give a fee relaxation/concession — e.g. a parent asks for Rs. 500 off. The discount
          counts toward settling the balance, even if it wasn't paid in cash. Maximum discount
          right now is Rs. {maxDiscount.toFixed(0)} (the unpaid balance).
        </Typography>
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        <TextField
          fullWidth
          label="Discount Amount"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          sx={{ mb: 2 }}
          autoFocus
        />
        <TextField
          fullWidth
          label="Reason (optional)"
          placeholder="e.g. Sibling discount, hardship relief"
          value={reason}
          onChange={(e) => setReason(e.target.value)}
        />
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          variant="contained"
          disabled={!isValidAmount}
          onClick={() => onApply(numericAmount, reason)}
        >
          Apply Discount
        </Button>
      </DialogActions>
    </Dialog>
  )
}
