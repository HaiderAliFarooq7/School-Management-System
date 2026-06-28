import { useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { DataGrid, type GridColDef } from '@mui/x-data-grid'
import {
  Alert, Box, Button, Card, CardContent, Checkbox, Chip, FormControlLabel, Grid, MenuItem, Select, Tab, Table,
  TableBody, TableCell, TableHead, TableRow, Tabs, Typography,
} from '@mui/material'
import {
  PENDING_REPORT_COLUMNS, downloadPendingReportExcel, downloadPendingReportPdf, getFeeAnalytics, getPendingReport,
  type PendingReportRow,
} from '../api/feeReports'
import { listGrades } from '../api/grades'
import { useAuth } from '../context/AuthContext'

export function FeeReportsPage() {
  const { role } = useAuth()
  const isAdmin = role === 'Admin'
  const [tab, setTab] = useState(0)

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        Fee Reports
      </Typography>
      <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 2 }}>
        <Tab label="Pending Fee Report" />
        {isAdmin && <Tab label="Analytics" />}
      </Tabs>
      {tab === 0 && <PendingReportTab />}
      {tab === 1 && isAdmin && <AnalyticsTab />}
    </Box>
  )
}

const STATUS_COLOR: Record<string, 'success' | 'warning' | 'error' | 'default'> = {
  Paid: 'success', Partial: 'warning', Unpaid: 'error', 'No Vouchers': 'default',
}

function PendingReportTab() {
  const { data: grades } = useQuery({ queryKey: ['grades'], queryFn: listGrades })
  const [selectedClasses, setSelectedClasses] = useState<string[]>([])
  const [statusFilter, setStatusFilter] = useState('')
  const [selectedColumns, setSelectedColumns] = useState<string[]>(
    ['registration_no', 'name', 'father_name', 'class_name', 'total_pending', 'fee_status'],
  )

  const mutation = useMutation({ mutationFn: () => getPendingReport({ class_names: selectedClasses, status_filter: statusFilter }) })

  const columns: GridColDef<PendingReportRow>[] = [
    { field: 'registration_no', headerName: 'Reg No', width: 100 },
    { field: 'name', headerName: 'Name', flex: 1 },
    { field: 'father_name', headerName: "Father's Name", flex: 1 },
    { field: 'class_name', headerName: 'Class', width: 90 },
    { field: 'phone', headerName: 'Phone', width: 110 },
    { field: 'vouchers_pending', headerName: 'Fee Pending', width: 110, type: 'number' },
    { field: 'charges_pending', headerName: 'Charges Pending', width: 130, type: 'number' },
    { field: 'total_pending', headerName: 'Total Pending', width: 120, type: 'number' },
    {
      field: 'fee_status', headerName: 'Status', width: 110,
      renderCell: (p) => <Chip size="small" label={p.value} color={STATUS_COLOR[p.value as string] ?? 'default'} />,
    },
    {
      field: 'is_overdue', headerName: 'Overdue', width: 90,
      renderCell: (p) => (p.value ? <Chip size="small" label="Overdue" color="error" /> : null),
    },
  ]

  const toggleColumn = (key: string) =>
    setSelectedColumns((prev) => (prev.includes(key) ? prev.filter((k) => k !== key) : [...prev, key]))

  return (
    <Box>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Every active student's pending fee — current month plus every unpaid/partial prior month,
        plus open extra charges — sorted by class then name. Filter by class, by Due/Partial/Unpaid/
        Overdue, and choose which columns appear on the printed PDF.
      </Typography>

      <Box sx={{ display: 'flex', gap: 2, mb: 2, flexWrap: 'wrap', alignItems: 'center' }}>
        <Select
          multiple
          size="small"
          value={selectedClasses}
          onChange={(e) => setSelectedClasses(e.target.value as unknown as string[])}
          displayEmpty
          sx={{ minWidth: 200 }}
          renderValue={(selected) => (selected as string[]).length ? (selected as string[]).join(', ') : 'All Classes'}
        >
          {grades?.map((g) => <MenuItem key={g.grade_id} value={g.class_name}>{g.class_name}</MenuItem>)}
        </Select>
        <Button size="small" onClick={() => setSelectedClasses(grades?.map((g) => g.class_name) ?? [])}>
          Select All Classes
        </Button>
        <Select size="small" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} displayEmpty sx={{ width: 160 }}>
          <MenuItem value="">Any Status</MenuItem>
          <MenuItem value="Unpaid">Unpaid</MenuItem>
          <MenuItem value="Partial">Partial</MenuItem>
          <MenuItem value="Overdue">Overdue</MenuItem>
          <MenuItem value="Paid">Paid</MenuItem>
          <MenuItem value="No Vouchers">No Vouchers</MenuItem>
        </Select>
        <Button variant="contained" onClick={() => mutation.mutate()}>Run Report</Button>
      </Box>

      {mutation.isError && <Alert severity="error" sx={{ mb: 2 }}>Could not run the report. Please try again.</Alert>}

      <Typography variant="body2" sx={{ mb: 1 }}>PDF Columns:</Typography>
      <Box sx={{ display: 'flex', flexWrap: 'wrap', mb: 2 }}>
        {PENDING_REPORT_COLUMNS.map((c) => (
          <FormControlLabel
            key={c.key}
            control={<Checkbox size="small" checked={selectedColumns.includes(c.key)} onChange={() => toggleColumn(c.key)} />}
            label={c.label}
          />
        ))}
      </Box>
      <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
        <Button
          variant="outlined"
          onClick={() => downloadPendingReportPdf({ class_names: selectedClasses, status_filter: statusFilter, columns: selectedColumns })}
        >
          Download PDF
        </Button>
        <Button
          variant="outlined"
          onClick={() => downloadPendingReportExcel({ class_names: selectedClasses, status_filter: statusFilter, columns: selectedColumns })}
        >
          Download Excel
        </Button>
      </Box>

      <Box sx={{ height: 600 }}>
        <DataGrid
          rows={mutation.data ?? []}
          columns={columns}
          getRowId={(row) => row.registration_no}
          loading={mutation.isPending}
          density="compact"
        />
      </Box>
    </Box>
  )
}

function AnalyticsTab() {
  const { data: grades } = useQuery({ queryKey: ['grades'], queryFn: listGrades })
  const [classFilter, setClassFilter] = useState('')
  const [months, setMonths] = useState(6)
  const { data, isLoading, isError } = useQuery({
    queryKey: ['fee-analytics', classFilter, months],
    queryFn: () => getFeeAnalytics(months, classFilter),
  })

  if (isError) return <Alert severity="error">Could not load analytics. Please try again.</Alert>
  if (isLoading || !data) return <Typography color="text.secondary">Loading…</Typography>

  const cards = [
    { label: 'Total Billed', value: data.total_billed },
    { label: 'Total Collected', value: data.total_collected },
    { label: 'Total Discounted', value: data.total_discounted },
    { label: 'Total Outstanding', value: data.total_outstanding },
    { label: 'Extra Charges Total', value: data.charges_total },
    { label: 'Extra Charges Pending', value: data.charges_pending },
  ]

  return (
    <Box>
      <Box sx={{ display: 'flex', gap: 2, mb: 3, flexWrap: 'wrap' }}>
        <Select size="small" value={classFilter} onChange={(e) => setClassFilter(e.target.value)} displayEmpty sx={{ width: 180 }}>
          <MenuItem value="">All Classes</MenuItem>
          {grades?.map((g) => <MenuItem key={g.grade_id} value={g.class_name}>{g.class_name}</MenuItem>)}
        </Select>
        <Select size="small" value={months} onChange={(e) => setMonths(Number(e.target.value))} sx={{ width: 160 }}>
          <MenuItem value={3}>Last 3 months</MenuItem>
          <MenuItem value={6}>Last 6 months</MenuItem>
          <MenuItem value={12}>Last 12 months</MenuItem>
        </Select>
      </Box>

      <Grid container spacing={2} sx={{ mb: 3 }}>
        {cards.map((c) => (
          <Grid key={c.label} size={{ xs: 12, sm: 6, md: 4 }}>
            <Card>
              <CardContent>
                <Typography color="text.secondary">{c.label}</Typography>
                <Typography variant="h5">Rs. {c.value.toFixed(0)}</Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
        <Grid size={{ xs: 12, sm: 6, md: 4 }}>
          <Card>
            <CardContent>
              <Typography color="text.secondary">Voucher Status</Typography>
              <Box sx={{ display: 'flex', gap: 1, mt: 1, flexWrap: 'wrap' }}>
                {Object.entries(data.voucher_status_counts).map(([status, count]) => (
                  <Chip key={status} label={`${status}: ${count}`} color={STATUS_COLOR[status] ?? 'default'} />
                ))}
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Typography variant="h6" gutterBottom>Per-Class Breakdown</Typography>
      <Table size="small" sx={{ maxWidth: 800, mb: 4 }}>
        <TableHead>
          <TableRow>
            <TableCell>Class</TableCell>
            <TableCell>Students</TableCell>
            <TableCell>Total Billed</TableCell>
            <TableCell>Collected</TableCell>
            <TableCell>Discounted</TableCell>
            <TableCell>Pending</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {data.by_class.map((row) => (
            <TableRow key={row.class_name}>
              <TableCell>{row.class_name}</TableCell>
              <TableCell>{row.student_count}</TableCell>
              <TableCell>{row.total.toFixed(0)}</TableCell>
              <TableCell>{row.collected.toFixed(0)}</TableCell>
              <TableCell>{row.discounted.toFixed(0)}</TableCell>
              <TableCell>{row.pending.toFixed(0)}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      <Typography variant="h6" gutterBottom>Monthly Collection Trend</Typography>
      <Table size="small" sx={{ maxWidth: 800 }}>
        <TableHead>
          <TableRow>
            <TableCell>Month</TableCell>
            <TableCell>Billed</TableCell>
            <TableCell>Collected</TableCell>
            <TableCell>Discounted</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {data.monthly_trend.map((row) => (
            <TableRow key={row.month}>
              <TableCell>{row.month}</TableCell>
              <TableCell>{row.billed.toFixed(0)}</TableCell>
              <TableCell>{row.collected.toFixed(0)}</TableCell>
              <TableCell>{row.discounted.toFixed(0)}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </Box>
  )
}
