import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Box, Button, Checkbox, Chip, Divider, FormControlLabel, MenuItem, Select, Tab, Tabs, TextField, Typography,
} from '@mui/material'
import { DataGrid, type GridColDef, type GridRowSelectionModel } from '@mui/x-data-grid'
import { useNavigate } from 'react-router-dom'
import { listGrades } from '../api/grades'
import {
  applyVoucherDiscount, bulkDeleteVouchers, bulkGenerate, deleteVoucher, downloadAllChallans, downloadSelectedVouchersPdf,
  downloadStudentChallan, downloadVoucherPdf, filterVouchers, generateVoucher, payVoucher, searchVouchers,
  type Voucher, type VoucherFilterRow, type VoucherSearchResult,
} from '../api/feeVouchers'
import { getSchool, updateSchool } from '../api/school'
import { listStudents, type Student } from '../api/students'
import QrCodeScannerIcon from '@mui/icons-material/QrCodeScanner'
import { DiscountDialog } from '../components/DiscountDialog'
import { QrScannerDialog } from '../components/QrScannerDialog'
import { useConfirm, useToast } from '../components/feedback'
import { useAuth } from '../context/AuthContext'
import { usePhoneColumns } from '../hooks/usePhoneColumns'

const STATUS_COLOR: Record<string, 'success' | 'warning' | 'error'> = {
  Paid: 'success',
  Partial: 'warning',
  Unpaid: 'error',
}

function apiErrorMessage(e: unknown): string {
  return String((e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? e)
}

export function FeeVouchersPage() {
  const [tab, setTab] = useState(0)

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        Fee Vouchers
      </Typography>
      <Tabs
        value={tab}
        onChange={(_, v) => setTab(v)}
        sx={{ mb: 2 }}
        variant="scrollable"
        scrollButtons="auto"
        allowScrollButtonsMobile
      >
        <Tab label="Find & Pay" />
        <Tab label="Generate Vouchers" />
        <Tab label="Print Challans" />
      </Tabs>
      {tab === 0 && <FindAndPayTab />}
      {tab === 1 && <GenerateTab />}
      {tab === 2 && <PrintChallansTab />}
    </Box>
  )
}

function FindAndPayTab() {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const { role } = useAuth()
  const isAdmin = role === 'Admin'
  const phoneColumns = usePhoneColumns([
    'registration_no', 'total_amount', 'paid_amount', 'discount_amount', 'status', 'is_overdue', 'charges_pending',
  ])
  const toast = useToast()
  const confirmAction = useConfirm()
  const { data: grades } = useQuery({ queryKey: ['grades'], queryFn: listGrades })

  const [discountError, setDiscountError] = useState<string | null>(null)
  const [discountTarget, setDiscountTarget] = useState<{ id: number; max: number } | null>(null)
  const [payAmounts, setPayAmounts] = useState<Record<number, string>>({})

  // Advanced filter state
  const [selectedClasses, setSelectedClasses] = useState<string[]>([])
  const [selectedStatuses, setSelectedStatuses] = useState<string[]>([])
  const [filterByMonth, setFilterByMonth] = useState(false)
  const [filterYear, setFilterYear] = useState(new Date().getFullYear())
  const [filterMonth, setFilterMonth] = useState(new Date().getMonth() + 1)
  const [overdueOnly, setOverdueOnly] = useState(false)
  const [chargesPendingOnly, setChargesPendingOnly] = useState(false)
  const [selectionModel, setSelectionModel] = useState<GridRowSelectionModel>([])
  const [hasFiltered, setHasFiltered] = useState(false)

  const filterMutation = useMutation({
    mutationFn: () =>
      filterVouchers({
        class_names: selectedClasses,
        status_filter: selectedStatuses,
        year: filterByMonth ? filterYear : null,
        month: filterByMonth ? filterMonth : null,
        overdue_only: overdueOnly,
        charges_pending_only: chargesPendingOnly,
      }),
    onSuccess: () => { setHasFiltered(true); setSelectionModel([]) },
  })

  const payMutation = useMutation({
    mutationFn: ({ voucherId, amount }: { voucherId: number; amount: number }) => payVoucher(voucherId, amount),
    onSuccess: () => {
      toast('Payment recorded.')
      filterMutation.mutate()
      queryClient.invalidateQueries({ queryKey: ['students'] })
    },
    onError: (e) => toast(apiErrorMessage(e), 'error'),
  })

  const discountMutation = useMutation({
    mutationFn: ({ voucherId, amount, reason }: { voucherId: number; amount: number; reason: string }) =>
      applyVoucherDiscount(voucherId, amount, reason),
    onSuccess: () => {
      filterMutation.mutate()
      queryClient.invalidateQueries({ queryKey: ['students'] })
      setDiscountTarget(null)
      setDiscountError(null)
    },
    onError: (e) => setDiscountError(apiErrorMessage(e)),
  })

  const deleteMutation = useMutation({
    mutationFn: (voucherId: number) => deleteVoucher(voucherId),
    onSuccess: () => {
      toast('Voucher deleted.')
      filterMutation.mutate()
    },
    onError: (e) => toast(apiErrorMessage(e), 'error'),
  })

  const bulkDeleteMutation = useMutation({
    mutationFn: (voucherIds: number[]) => bulkDeleteVouchers(voucherIds),
    onSuccess: (result) => {
      filterMutation.mutate()
      setSelectionModel([])
      const skippedMsg = result.skipped.length
        ? ` ${result.skipped.length} voucher(s) skipped (already have a payment or discount).`
        : ''
      toast(`Deleted ${result.deleted} voucher(s).${skippedMsg}`, result.skipped.length ? 'warning' : 'success')
    },
    onError: (e) => toast(apiErrorMessage(e), 'error'),
  })

  const selectedIds = Array.from(selectionModel as Iterable<number>)

  const renderActions = (row: Voucher) => (
    <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
      {row.remaining > 0 && (
        <>
          <TextField
            size="small"
            placeholder="Pay"
            sx={{ width: 70 }}
            value={payAmounts[row.voucher_id] ?? ''}
            onChange={(e) => setPayAmounts((prev) => ({ ...prev, [row.voucher_id]: e.target.value }))}
          />
          <Button
            size="small"
            variant="contained"
            onClick={() => payMutation.mutate({ voucherId: row.voucher_id, amount: Number(payAmounts[row.voucher_id]) || 0 })}
          >
            Pay
          </Button>
          {isAdmin && (
            <Button size="small" color="secondary" onClick={() => setDiscountTarget({ id: row.voucher_id, max: row.remaining })}>
              Discount
            </Button>
          )}
        </>
      )}
      <Button size="small" onClick={() => downloadVoucherPdf(row.voucher_id)}>PDF</Button>
      <Button size="small" onClick={() => navigate(`/fees/student/${row.student_id}`)}>Profile</Button>
      {isAdmin && (
        <Button
          size="small"
          color="error"
          onClick={async () => {
            const ok = await confirmAction({
              title: 'Delete this voucher?',
              message: 'The voucher and its recorded figures will be permanently removed.',
              confirmLabel: 'Delete',
              destructive: true,
            })
            if (ok) deleteMutation.mutate(row.voucher_id)
          }}
        >
          Delete
        </Button>
      )}
    </Box>
  )

  const filterColumns: GridColDef<VoucherFilterRow>[] = [
    { field: 'registration_no', headerName: 'Reg No', width: 100 },
    { field: 'student_name', headerName: 'Student', flex: 1 },
    { field: 'fee_month', headerName: 'Month', width: 110 },
    { field: 'total_amount', headerName: 'Total', width: 80, type: 'number' },
    { field: 'paid_amount', headerName: 'Paid', width: 80, type: 'number' },
    { field: 'discount_amount', headerName: 'Discount', width: 90, type: 'number' },
    { field: 'remaining', headerName: 'Remaining', width: 100, type: 'number' },
    {
      field: 'status', headerName: 'Status', width: 100,
      renderCell: (p) => <Chip size="small" label={p.value} color={STATUS_COLOR[p.value] ?? 'default'} />,
    },
    {
      field: 'is_overdue', headerName: 'Overdue', width: 90,
      renderCell: (p) => (p.value ? <Chip size="small" label="Overdue" color="error" /> : null),
    },
    { field: 'charges_pending', headerName: 'Charges Pending', width: 130, type: 'number' },
    { field: 'actions', headerName: 'Actions', width: 320, sortable: false, renderCell: (p) => renderActions(p.row) },
  ]

  return (
    <Box>
      <VoucherLookup
        payMutation={payMutation}
        discountTarget={discountTarget}
        setDiscountTarget={setDiscountTarget}
        discountMutation={discountMutation}
        discountError={discountError}
        setDiscountError={setDiscountError}
        isAdmin={isAdmin}
      />

      <Divider sx={{ my: 3 }} />

      <Typography variant="h6" gutterBottom>
        Advanced Filter
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Filter vouchers any way you need — by class (or all classes), payment status, a specific
        month, overdue only, or students who still have extra charges pending. Then select rows to
        print or delete in bulk.
      </Typography>

      <Box sx={{ display: 'flex', gap: 2, mb: 2, flexWrap: 'wrap', alignItems: 'center' }}>
        <Select
          multiple
          size="small"
          value={selectedClasses}
          onChange={(e) => setSelectedClasses(e.target.value as unknown as string[])}
          displayEmpty
          sx={{ minWidth: 200, width: { xs: '100%', sm: 'auto' } }}
          renderValue={(selected) => (selected as string[]).length ? (selected as string[]).join(', ') : 'All Classes'}
        >
          {grades?.map((g) => <MenuItem key={g.grade_id} value={g.class_name}>{g.class_name}</MenuItem>)}
        </Select>
        <Button size="small" onClick={() => setSelectedClasses(grades?.map((g) => g.class_name) ?? [])}>
          Select All Classes
        </Button>
        {selectedClasses.length > 0 && (
          <Button size="small" onClick={() => setSelectedClasses([])}>Clear Classes</Button>
        )}

        <Select
          multiple
          size="small"
          value={selectedStatuses}
          onChange={(e) => setSelectedStatuses(e.target.value as unknown as string[])}
          displayEmpty
          sx={{ minWidth: 180, width: { xs: '100%', sm: 'auto' } }}
          renderValue={(selected) => (selected as string[]).length ? (selected as string[]).join(', ') : 'All Statuses'}
        >
          <MenuItem value="Unpaid">Unpaid</MenuItem>
          <MenuItem value="Partial">Partial</MenuItem>
          <MenuItem value="Paid">Paid</MenuItem>
        </Select>

        <FormControlLabel
          control={<Checkbox checked={overdueOnly} onChange={(e) => setOverdueOnly(e.target.checked)} />}
          label="Overdue only"
        />
        <FormControlLabel
          control={<Checkbox checked={chargesPendingOnly} onChange={(e) => setChargesPendingOnly(e.target.checked)} />}
          label="Has extra charges pending"
        />
      </Box>

      <Box sx={{ display: 'flex', gap: 2, mb: 2, flexWrap: 'wrap', alignItems: 'center' }}>
        <FormControlLabel
          control={<Checkbox checked={filterByMonth} onChange={(e) => setFilterByMonth(e.target.checked)} />}
          label="Limit to a specific month"
        />
        {filterByMonth && (
          <>
            <TextField label="Year" size="small" type="number" value={filterYear} onChange={(e) => setFilterYear(Number(e.target.value))} sx={{ width: 90 }} />
            <TextField label="Month" size="small" type="number" value={filterMonth} onChange={(e) => setFilterMonth(Number(e.target.value))} sx={{ width: 90 }} />
          </>
        )}
        <Button variant="contained" onClick={() => filterMutation.mutate()}>
          Apply Filter
        </Button>
      </Box>

      {hasFiltered && (
        <>
          <Box sx={{ display: 'flex', gap: 2, mb: 1, alignItems: 'center', flexWrap: 'wrap' }}>
            <Typography variant="body2" color="text.secondary">
              {selectedIds.length > 0 ? `${selectedIds.length} selected` : `${filterMutation.data?.length ?? 0} voucher(s) match`}
            </Typography>
            {selectedIds.length > 0 && (
              <>
                <Button size="small" onClick={() => downloadSelectedVouchersPdf(selectedIds, '4up')}>
                  Print Selected (4-per-sheet)
                </Button>
                <Button size="small" onClick={() => downloadSelectedVouchersPdf(selectedIds, 'individual')}>
                  Print Selected (1-per-page)
                </Button>
                {isAdmin && (
                  <Button
                    size="small"
                    color="error"
                    onClick={async () => {
                      const ok = await confirmAction({
                        title: `Delete ${selectedIds.length} selected voucher(s)?`,
                        message: 'This permanently removes the selected vouchers, including any with payments or discounts recorded.',
                        confirmLabel: 'Delete',
                        destructive: true,
                      })
                      if (ok) bulkDeleteMutation.mutate(selectedIds)
                    }}
                  >
                    Delete Selected
                  </Button>
                )}
              </>
            )}
            {isAdmin && selectedIds.length === 0 && (filterMutation.data?.length ?? 0) > 0 && (
              <Button
                size="small"
                color="error"
                variant="outlined"
                onClick={async () => {
                  const ids = (filterMutation.data ?? []).map((v) => v.voucher_id)
                  const ok = await confirmAction({
                    title: `Delete ALL ${ids.length} matching voucher(s)?`,
                    message: 'Every voucher matching the current filter will be permanently removed. This cannot be undone.',
                    confirmLabel: 'Delete All',
                    destructive: true,
                  })
                  if (ok) bulkDeleteMutation.mutate(ids)
                }}
              >
                Delete All Matching ({filterMutation.data?.length ?? 0})
              </Button>
            )}
          </Box>
          <Box sx={{ height: 600 }}>
            <DataGrid
              {...phoneColumns}
              rows={filterMutation.data ?? []}
              columns={filterColumns}
              getRowId={(row) => row.voucher_id}
              loading={filterMutation.isPending}
              density="compact"
              checkboxSelection
              rowSelectionModel={selectionModel}
              onRowSelectionModelChange={setSelectionModel}
            />
          </Box>
        </>
      )}

      <DiscountDialog
        open={!!discountTarget}
        onClose={() => { setDiscountTarget(null); setDiscountError(null) }}
        title="Apply Fee Discount"
        maxDiscount={discountTarget?.max ?? 0}
        error={discountError}
        onApply={(amount, reason) => {
          if (discountTarget) discountMutation.mutate({ voucherId: discountTarget.id, amount, reason })
        }}
      />
    </Box>
  )
}

interface MutateFn<T> {
  mutate: (vars: T) => void
}

function VoucherLookup({
  discountTarget, setDiscountTarget, discountMutation, discountError, setDiscountError, payMutation, isAdmin,
}: {
  discountTarget: { id: number; max: number } | null
  setDiscountTarget: (t: { id: number; max: number } | null) => void
  discountMutation: MutateFn<{ voucherId: number; amount: number; reason: string }>
  discountError: string | null
  setDiscountError: (s: string | null) => void
  payMutation: MutateFn<{ voucherId: number; amount: number }>
  isAdmin: boolean
}) {
  const navigate = useNavigate()
  const phoneColumns = usePhoneColumns(['voucher_id', 'registration_no', 'class_name', 'phone', 'other_pending'])
  const [query, setQuery] = useState('')
  const [scannerOpen, setScannerOpen] = useState(false)
  const [payAmounts, setPayAmounts] = useState<Record<number, string>>({})
  const mutation = useMutation({ mutationFn: (q: string) => searchVouchers(q) })

  const columns: GridColDef<VoucherSearchResult>[] = [
    { field: 'voucher_id', headerName: 'Voucher No', width: 100 },
    { field: 'registration_no', headerName: 'Reg No', width: 100 },
    { field: 'name', headerName: 'Name', flex: 1 },
    { field: 'class_name', headerName: 'Class', width: 90 },
    { field: 'phone', headerName: 'Phone', width: 110 },
    { field: 'fee_month', headerName: 'Month', width: 110 },
    {
      field: 'status', headerName: 'This Voucher', width: 100,
      renderCell: (p) => <Chip size="small" label={p.value} color={STATUS_COLOR[p.value] ?? 'default'} />,
    },
    { field: 'other_pending', headerName: 'Other Pending', width: 120, type: 'number' },
    {
      field: 'actions', headerName: '', width: 320, sortable: false,
      renderCell: (p) => {
        const remaining = p.row.total_amount - p.row.paid_amount - p.row.discount_amount
        return (
          <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
            {remaining > 0 && (
              <>
                <TextField
                  size="small"
                  placeholder="Pay"
                  sx={{ width: 65 }}
                  value={payAmounts[p.row.voucher_id] ?? ''}
                  onChange={(e) => setPayAmounts((prev) => ({ ...prev, [p.row.voucher_id]: e.target.value }))}
                />
                <Button
                  size="small"
                  variant="contained"
                  onClick={() => payMutation.mutate({ voucherId: p.row.voucher_id, amount: Number(payAmounts[p.row.voucher_id]) || 0 })}
                >
                  Pay
                </Button>
                {isAdmin && (
                  <Button size="small" color="secondary" onClick={() => setDiscountTarget({ id: p.row.voucher_id, max: remaining })}>
                    Discount
                  </Button>
                )}
              </>
            )}
            <Button size="small" onClick={() => downloadVoucherPdf(p.row.voucher_id)}>PDF</Button>
            <Button size="small" onClick={() => navigate(`/fees/student/${p.row.student_id}`)}>All Dues</Button>
          </Box>
        )
      },
    },
  ]

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Find a Voucher — by voucher no, name, phone, or CNIC
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Same as the fee counter at school: a student hands over their printed voucher, and you look
        them up here to record a payment, give a discount, or see what else they owe.
      </Typography>
      <Box sx={{ display: 'flex', gap: 2, mb: 2, flexWrap: 'wrap', alignItems: 'center' }}>
        <TextField
          label="Voucher no / Name / Phone / CNIC"
          size="small"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          sx={{ width: { xs: '100%', sm: 320 } }}
          onKeyDown={(e) => e.key === 'Enter' && mutation.mutate(query)}
        />
        <Button variant="contained" disabled={!query} onClick={() => mutation.mutate(query)}>
          Search
        </Button>
        <Button variant="outlined" startIcon={<QrCodeScannerIcon />} onClick={() => setScannerOpen(true)}>
          Scan QR
        </Button>
      </Box>
      <QrScannerDialog open={scannerOpen} onClose={() => setScannerOpen(false)} />
      {mutation.data && (
        <Box sx={{ height: 350 }}>
          <DataGrid {...phoneColumns} rows={mutation.data} columns={columns} getRowId={(row) => row.voucher_id} density="compact" />
        </Box>
      )}

      <DiscountDialog
        open={!!discountTarget}
        onClose={() => { setDiscountTarget(null); setDiscountError(null) }}
        title="Apply Fee Discount"
        maxDiscount={discountTarget?.max ?? 0}
        error={discountError}
        onApply={(amount, reason) => {
          if (discountTarget) discountMutation.mutate({ voucherId: discountTarget.id, amount, reason })
        }}
      />
    </Box>
  )
}

function GenerateTab() {
  const { role } = useAuth()
  const isAdmin = role === 'Admin'
  const confirmAction = useConfirm()
  const queryClient = useQueryClient()
  const { data: grades } = useQuery({ queryKey: ['grades'], queryFn: listGrades })
  const [studentId, setStudentId] = useState('')
  const [classNameForGen, setClassNameForGen] = useState('')
  const [year, setYear] = useState(new Date().getFullYear())
  const [month, setMonth] = useState(new Date().getMonth() + 1)
  const [amount, setAmount] = useState('')
  const [result, setResult] = useState<string | null>(null)

  const grade = grades?.find((g) => g.class_name === classNameForGen)

  const generateMutation = useMutation({
    mutationFn: () => generateVoucher(Number(studentId), year, month, Number(amount) || grade?.fee_amount || 0),
    onSuccess: (v) => {
      setResult(`Voucher #${v.voucher_id} for ${v.fee_month}: total Rs. ${v.total_amount}, status ${v.status}`)
      queryClient.invalidateQueries({ queryKey: ['balance-sheet'] })
      queryClient.invalidateQueries({ queryKey: ['students'] })
    },
    onError: () => setResult('Failed to generate voucher — check the student ID.'),
  })

  const [selectedClasses, setSelectedClasses] = useState<string[]>([])
  const [bulkYear, setBulkYear] = useState(new Date().getFullYear())
  const [bulkMonth, setBulkMonth] = useState(new Date().getMonth() + 1)
  const [bulkResult, setBulkResult] = useState<string | null>(null)

  const bulkMutation = useMutation({
    mutationFn: () => bulkGenerate(selectedClasses, bulkYear, bulkMonth),
    onSuccess: (vouchers) => {
      setBulkResult(`Generated/updated ${vouchers.length} voucher(s) for ${selectedClasses.join(', ')}.`)
      queryClient.invalidateQueries({ queryKey: ['balance-sheet'] })
      queryClient.invalidateQueries({ queryKey: ['students'] })
    },
    onError: () => setBulkResult('Bulk generation failed.'),
  })

  const [deleting, setDeleting] = useState(false)

  async function handleDeleteGenerated() {
    setDeleting(true)
    try {
      const matches = await filterVouchers({
        class_names: selectedClasses, status_filter: [], year: bulkYear, month: bulkMonth,
        overdue_only: false, charges_pending_only: false,
      })
      if (matches.length === 0) {
        setBulkResult(`No vouchers found for ${selectedClasses.join(', ')} — ${bulkMonth}/${bulkYear}. Make sure the class and month above match what you used to generate them.`)
        return
      }
      const ok = await confirmAction({
        title: `Delete ${matches.length} voucher(s)?`,
        message: `All vouchers for ${selectedClasses.join(', ')} — ${bulkMonth}/${bulkYear} will be permanently removed, including any with payments or discounts. This cannot be undone.`,
        confirmLabel: 'Delete',
        destructive: true,
      })
      if (!ok) {
        return
      }
      const result = await bulkDeleteVouchers(matches.map((m) => m.voucher_id))
      const skippedMsg = result.skipped.length ? ` ${result.skipped.length} skipped (already have a payment or discount).` : ''
      setBulkResult(`Deleted ${result.deleted} voucher(s).${skippedMsg}`)
      queryClient.invalidateQueries({ queryKey: ['balance-sheet'] })
      queryClient.invalidateQueries({ queryKey: ['students'] })
    } catch (e) {
      setBulkResult(apiErrorMessage(e))
    } finally {
      setDeleting(false)
    }
  }

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Single Voucher
      </Typography>
      <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', maxWidth: 700, mb: 2 }}>
        <TextField label="Student ID" size="small" value={studentId} onChange={(e) => setStudentId(e.target.value)} />
        <Select size="small" value={classNameForGen} onChange={(e) => setClassNameForGen(e.target.value)} displayEmpty sx={{ width: 160 }}>
          <MenuItem value="">Class (for default fee)</MenuItem>
          {grades?.map((g) => <MenuItem key={g.grade_id} value={g.class_name}>{g.class_name}</MenuItem>)}
        </Select>
        <TextField label="Year" size="small" type="number" value={year} onChange={(e) => setYear(Number(e.target.value))} sx={{ width: 100 }} />
        <TextField label="Month (1-12)" size="small" type="number" value={month} onChange={(e) => setMonth(Number(e.target.value))} sx={{ width: 120 }} />
        <TextField label={`Amount (default ${grade?.fee_amount ?? 0})`} size="small" value={amount} onChange={(e) => setAmount(e.target.value)} />
        <Button variant="contained" onClick={() => generateMutation.mutate()} disabled={!studentId}>
          Generate Voucher
        </Button>
      </Box>
      {result && <Typography sx={{ mb: 3 }}>{result}</Typography>}

      <Divider sx={{ mb: 3 }} />

      <Typography variant="h6" gutterBottom>
        Bulk Generate (class-wise)
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Generates one voucher per active student in the selected classes. Each student's own fee
        (set at admission) is used automatically; students without one use the class's default fee.
      </Typography>
      <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'center' }}>
        <Select
          multiple
          size="small"
          value={selectedClasses}
          onChange={(e) => setSelectedClasses(e.target.value as unknown as string[])}
          displayEmpty
          sx={{ minWidth: 220, width: { xs: '100%', sm: 'auto' } }}
          renderValue={(selected) => (selected as string[]).join(', ') || 'Select classes'}
        >
          {grades?.map((g) => <MenuItem key={g.grade_id} value={g.class_name}>{g.class_name}</MenuItem>)}
        </Select>
        <Button size="small" onClick={() => setSelectedClasses(grades?.map((g) => g.class_name) ?? [])}>
          Select All Classes
        </Button>
        <TextField label="Year" size="small" type="number" value={bulkYear} onChange={(e) => setBulkYear(Number(e.target.value))} sx={{ width: 100 }} />
        <TextField label="Month (1-12)" size="small" type="number" value={bulkMonth} onChange={(e) => setBulkMonth(Number(e.target.value))} sx={{ width: 130 }} />
        <Button variant="contained" disabled={selectedClasses.length === 0} onClick={() => bulkMutation.mutate()}>
          Generate for Selected Classes
        </Button>
        {isAdmin && (
          <Button
            variant="outlined"
            color="error"
            disabled={selectedClasses.length === 0 || deleting}
            onClick={handleDeleteGenerated}
          >
            {deleting ? 'Checking…' : 'Delete Vouchers for Selected Classes/Month'}
          </Button>
        )}
      </Box>
      <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
        Generated the wrong vouchers? Use the <strong>same class/year/month</strong> selected above and
        click delete to remove them in bulk. This deletes outright, including any voucher that already
        has a payment or discount recorded against it — double-check the confirmation count before continuing.
      </Typography>
      {bulkResult && <Typography sx={{ mt: 2 }}>{bulkResult}</Typography>}
    </Box>
  )
}

function PrintChallansTab() {
  const queryClient = useQueryClient()
  const { data: grades } = useQuery({ queryKey: ['grades'], queryFn: listGrades })
  const { data: school } = useQuery({ queryKey: ['school'], queryFn: getSchool })
  const [selectedClasses, setSelectedClasses] = useState<string[]>([])
  const [mode, setMode] = useState<'4up' | 'individual'>('4up')
  const [note, setNote] = useState('')
  const [noteLoaded, setNoteLoaded] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [noteSaved, setNoteSaved] = useState(false)

  useEffect(() => {
    if (school && !noteLoaded) {
      setNote(school.challan_note ?? '')
      setNoteLoaded(true)
    }
  }, [school, noteLoaded])

  const saveNoteMutation = useMutation({
    mutationFn: () => updateSchool({ ...school, challan_note: note }),
    onSuccess: () => {
      setNoteSaved(true)
      queryClient.invalidateQueries({ queryKey: ['school'] })
    },
  })

  const printMutation = useMutation({
    mutationFn: () => downloadAllChallans({ class_names: selectedClasses, mode, note }),
    onError: (e) => setError(apiErrorMessage(e)),
    onSuccess: () => setError(null),
  })

  // Single-student print
  const [singleSearch, setSingleSearch] = useState('')
  const singleSearchMutation = useMutation({
    mutationFn: () => listStudents({ search: singleSearch, status_filter: 'Active' }),
  })
  const printOneMutation = useMutation({
    mutationFn: (student: Student) => downloadStudentChallan(student.student_id, note),
    onError: (e) => setError(apiErrorMessage(e)),
    onSuccess: () => setError(null),
  })

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Print All Challans
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Generates one combined PDF with every active student's complete pending dues — every
        unpaid/partial month plus every open extra charge, rolled into a single challan per student
        ending in a Grand Total row. Students with nothing outstanding are skipped. 4 challans per A4
        sheet by default. Leave classes empty to include every class.
      </Typography>

      <TextField
        label="Note (printed on every challan)"
        size="small"
        multiline
        minRows={2}
        fullWidth
        sx={{ maxWidth: 500, mb: 1 }}
        value={note}
        onChange={(e) => { setNote(e.target.value); setNoteSaved(false) }}
        placeholder="e.g. Late fee may apply for overdue payments."
      />
      <Box sx={{ mb: 2 }}>
        <Button size="small" variant="outlined" onClick={() => saveNoteMutation.mutate()} disabled={saveNoteMutation.isPending}>
          Save Note
        </Button>
        {noteSaved && <Typography component="span" color="success.main" sx={{ ml: 1 }}>Saved.</Typography>}
      </Box>

      <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'center', mb: 2 }}>
        <Select
          multiple
          size="small"
          value={selectedClasses}
          onChange={(e) => setSelectedClasses(e.target.value as unknown as string[])}
          displayEmpty
          sx={{ minWidth: 220, width: { xs: '100%', sm: 'auto' } }}
          renderValue={(selected) => (selected as string[]).length ? (selected as string[]).join(', ') : 'All Classes'}
        >
          {grades?.map((g) => <MenuItem key={g.grade_id} value={g.class_name}>{g.class_name}</MenuItem>)}
        </Select>
        <Select size="small" value={mode} onChange={(e) => setMode(e.target.value as '4up' | 'individual')} sx={{ width: { xs: '100%', sm: 220 } }}>
          <MenuItem value="4up">4 Challans per A4 Sheet</MenuItem>
          <MenuItem value="individual">1 Challan per Page</MenuItem>
        </Select>
        <Button variant="contained" onClick={() => printMutation.mutate()} disabled={printMutation.isPending}>
          Print All Challans
        </Button>
      </Box>
      {error && <Typography color="error" sx={{ mb: 2 }}>{error}</Typography>}

      <Divider sx={{ mb: 3 }} />

      <Typography variant="h6" gutterBottom>
        Print One Student's Challan
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Search for a student and print just their challan, using the same note above.
      </Typography>
      <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', mb: 2, flexWrap: 'wrap' }}>
        <TextField
          label="Search student (name or reg no)"
          size="small"
          value={singleSearch}
          onChange={(e) => setSingleSearch(e.target.value)}
          sx={{ width: { xs: '100%', sm: 260 } }}
        />
        <Button variant="outlined" onClick={() => singleSearchMutation.mutate()} disabled={!singleSearch}>
          Search
        </Button>
      </Box>
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, maxWidth: 600 }}>
        {singleSearchMutation.data?.map((s) => (
          <Box key={s.student_id} sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 1, flexWrap: 'wrap', border: '1px solid', borderColor: 'divider', borderRadius: 1, px: 2, py: 1 }}>
            <Typography variant="body2">
              {s.registration_no} — {s.name} ({s.class_name})
            </Typography>
            <Button size="small" variant="contained" onClick={() => printOneMutation.mutate(s)} disabled={printOneMutation.isPending}>
              Print Challan
            </Button>
          </Box>
        ))}
        {singleSearchMutation.data && singleSearchMutation.data.length === 0 && (
          <Typography color="text.secondary">No matching active students.</Typography>
        )}
      </Box>
    </Box>
  )
}
