import { useEffect, useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Alert, Avatar, Box, Button, TextField, Typography } from '@mui/material'
import { getSchool, updateSchool, uploadLogo, type School } from '../api/school'

export function SchoolSettingsPage() {
  const queryClient = useQueryClient()
  const { data } = useQuery({ queryKey: ['school'], queryFn: getSchool })
  const [form, setForm] = useState<Partial<School>>({})
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (data) setForm(data)
  }, [data])

  function apiErrorMessage(e: unknown, fallback: string): string {
    return String((e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? fallback)
  }

  const mutation = useMutation({
    mutationFn: () =>
      updateSchool({
        name: form.name ?? '',
        address: form.address ?? '',
        phone: form.phone ?? '',
        bank_name: form.bank_name ?? '',
        account_title: form.account_title ?? '',
        account_number: form.account_number ?? '',
        iban: form.iban ?? '',
        fee_due_day: form.fee_due_day ?? 10,
      }),
    onSuccess: () => { setSaved(true); setError(null) },
    onError: (e) => setError(apiErrorMessage(e, 'Could not save settings.')),
  })

  const logoMutation = useMutation({
    mutationFn: (file: File) => uploadLogo(file),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['school'] }); setError(null) },
    onError: (e) => setError(apiErrorMessage(e, 'Logo upload failed.')),
  })

  const set = (field: keyof School) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((f) => ({ ...f, [field]: e.target.value }))

  return (
    <Box sx={{ maxWidth: 600 }}>
      <Typography variant="h5" gutterBottom>
        School Settings
      </Typography>
      {saved && <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSaved(false)}>Saved.</Alert>}
      {error && <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>{error}</Alert>}

      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
        <Avatar src={data?.logo_path ? '/api/school/logo' : undefined} sx={{ width: 64, height: 64 }} variant="rounded" />
        <Button variant="outlined" onClick={() => fileInputRef.current?.click()}>
          Upload School Logo
        </Button>
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          hidden
          onChange={(e) => {
            const file = e.target.files?.[0]
            if (file) logoMutation.mutate(file)
          }}
        />
        <Typography variant="body2" color="text.secondary">
          Appears on every printed fee voucher.
        </Typography>
      </Box>

      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        <TextField label="School Name" value={form.name ?? ''} onChange={set('name')} />
        <TextField label="Address" value={form.address ?? ''} onChange={set('address')} />
        <TextField label="Phone" value={form.phone ?? ''} onChange={set('phone')} />
        <TextField label="Bank Name" value={form.bank_name ?? ''} onChange={set('bank_name')} />
        <TextField label="Account Title" value={form.account_title ?? ''} onChange={set('account_title')} />
        <TextField label="Account Number" value={form.account_number ?? ''} onChange={set('account_number')} />
        <TextField label="IBAN" value={form.iban ?? ''} onChange={set('iban')} />
        <TextField
          label="Fee Due Day (of month)"
          type="number"
          value={form.fee_due_day ?? 10}
          onChange={(e) => setForm((f) => ({ ...f, fee_due_day: Number(e.target.value) }))}
          inputProps={{ min: 1, max: 31 }}
        />
        <Button variant="contained" onClick={() => mutation.mutate()}>
          Save
        </Button>
      </Box>
    </Box>
  )
}
