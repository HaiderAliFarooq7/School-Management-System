import { useEffect, useState } from 'react'
import {
  Alert, Button, Dialog, DialogActions, DialogContent, DialogTitle, TextField, Box, Typography,
} from '@mui/material'

interface Initial {
  description?: string
  total_amount: number
  paid_amount: number
  discount_amount: number
  discount_reason: string | null
}

interface Props {
  open: boolean
  onClose: () => void
  title: string
  initial: Initial | null
  showDescription?: boolean
  error?: string | null
  onSave: (values: { description?: string; total_amount: number; paid_amount: number; discount_amount: number; discount_reason: string | null }) => void
}

export function EditFigureDialog({ open, onClose, title, initial, showDescription, error, onSave }: Props) {
  const [description, setDescription] = useState('')
  const [totalAmount, setTotalAmount] = useState('')
  const [paidAmount, setPaidAmount] = useState('')
  const [discountAmount, setDiscountAmount] = useState('')
  const [discountReason, setDiscountReason] = useState('')

  useEffect(() => {
    if (initial) {
      setDescription(initial.description ?? '')
      setTotalAmount(String(initial.total_amount))
      setPaidAmount(String(initial.paid_amount))
      setDiscountAmount(String(initial.discount_amount))
      setDiscountReason(initial.discount_reason ?? '')
    }
  }, [initial])

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>{title}</DialogTitle>
      <DialogContent>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Admin-only: directly overwrite these figures, even if a payment or discount is already recorded.
        </Typography>
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          {showDescription && (
            <TextField label="Description" value={description} onChange={(e) => setDescription(e.target.value)} fullWidth />
          )}
          <TextField label="Total Amount" value={totalAmount} onChange={(e) => setTotalAmount(e.target.value)} fullWidth />
          <TextField label="Paid Amount" value={paidAmount} onChange={(e) => setPaidAmount(e.target.value)} fullWidth />
          <TextField label="Discount Amount" value={discountAmount} onChange={(e) => setDiscountAmount(e.target.value)} fullWidth />
          <TextField label="Discount Reason (optional)" value={discountReason} onChange={(e) => setDiscountReason(e.target.value)} fullWidth />
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          variant="contained"
          onClick={() =>
            onSave({
              description: showDescription ? description : undefined,
              total_amount: Number(totalAmount) || 0,
              paid_amount: Number(paidAmount) || 0,
              discount_amount: Number(discountAmount) || 0,
              discount_reason: discountReason || null,
            })
          }
        >
          Save Changes
        </Button>
      </DialogActions>
    </Dialog>
  )
}
