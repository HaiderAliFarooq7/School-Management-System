import { Component, useState, type ReactNode } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Box, Button, Card, CardContent, Chip, Grid, MenuItem, Select, Skeleton, Table, TableBody, TableCell, TableContainer,
  TableHead, TableRow, Typography,
} from '@mui/material'
import { BarChart } from '@mui/x-charts/BarChart'
import { LineChart } from '@mui/x-charts/LineChart'
import { PieChart } from '@mui/x-charts/PieChart'
import PersonAddIcon from '@mui/icons-material/PersonAdd'
import PaidIcon from '@mui/icons-material/Paid'
import QrCodeScannerIcon from '@mui/icons-material/QrCodeScanner'
import EventAvailableIcon from '@mui/icons-material/EventAvailable'
import { useNavigate } from 'react-router-dom'
import { getAttendanceDailyStatus } from '../api/attendance'
import { getDashboardStats } from '../api/dashboard'
import { getFeeAnalytics } from '../api/feeReports'
import { listGrades } from '../api/grades'
import { QrScannerDialog } from '../components/QrScannerDialog'
import { useAuth } from '../context/AuthContext'

const STATUS_COLOR: Record<string, 'success' | 'warning' | 'error' | 'default'> = {
  Paid: 'success', Partial: 'warning', Unpaid: 'error',
}

export function DashboardPage() {
  const navigate = useNavigate()
  const { role } = useAuth()
  const isAdmin = role === 'Admin'
  const canSeeAttendanceStatus = role === 'Admin' || role === 'Accountant'
  const [scannerOpen, setScannerOpen] = useState(false)
  const { data, isLoading } = useQuery({ queryKey: ['dashboard-stats'], queryFn: getDashboardStats, enabled: canSeeAttendanceStatus })
  const { data: attendanceStatus } = useQuery({
    queryKey: ['attendance-daily-status'],
    queryFn: () => getAttendanceDailyStatus(),
    enabled: canSeeAttendanceStatus,
  })

  const cards = isAdmin
    ? [
      { label: 'Active Students', value: data?.total_students ?? 0 },
      { label: 'Classes', value: data?.total_classes ?? 0 },
      { label: 'Fees Collected (Rs.)', value: (data?.total_collected ?? 0).toFixed(0) },
      { label: 'Discounts Given (Rs.)', value: (data?.total_discounted ?? 0).toFixed(0) },
      { label: 'Fees Outstanding (Rs.)', value: (data?.total_outstanding ?? 0).toFixed(0) },
      { label: 'Extra Charges Outstanding (Rs.)', value: (data?.outstanding_charges ?? 0).toFixed(0) },
    ]
    : [
      { label: 'Active Students', value: data?.total_students ?? 0 },
      { label: 'Classes', value: data?.total_classes ?? 0 },
    ]

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        Dashboard
      </Typography>

      <Box sx={{ display: 'flex', gap: 2, mb: 3, flexWrap: 'wrap' }}>
        {/* Attendance is a quick action for every role. */}
        <Button
          variant="contained"
          size="large"
          color="success"
          startIcon={<EventAvailableIcon />}
          onClick={() => navigate('/attendance')}
          sx={{ py: 2, px: 4, fontSize: '1.1rem' }}
        >
          Attendance
        </Button>
        {(role === 'Admin' || role === 'Accountant') && (
          <>
            <Button
              variant="contained"
              size="large"
              startIcon={<PersonAddIcon />}
              onClick={() => navigate('/students/new')}
              sx={{ py: 2, px: 4, fontSize: '1.1rem' }}
            >
              New Admission
            </Button>
            <Button
              variant="outlined"
              size="large"
              startIcon={<PaidIcon />}
              onClick={() => navigate('/fees/student')}
              sx={{ py: 2, px: 4, fontSize: '1.1rem' }}
            >
              Student Fee
            </Button>
            <Button
              variant="outlined"
              size="large"
              color="secondary"
              startIcon={<QrCodeScannerIcon />}
              onClick={() => setScannerOpen(true)}
              sx={{ py: 2, px: 4, fontSize: '1.1rem' }}
            >
              Fee QR Scanner
            </Button>
            <QrScannerDialog open={scannerOpen} onClose={() => setScannerOpen(false)} />
          </>
        )}
      </Box>

      {canSeeAttendanceStatus ? (
        <Grid container spacing={2}>
          {cards.map((c) => (
            <Grid key={c.label} size={{ xs: 12, sm: 6, md: 3 }}>
              <Card>
                <CardContent>
                  <Typography color="text.secondary">{c.label}</Typography>
                  <Typography variant="h4">
                    {isLoading ? <Skeleton width={90} /> : c.value}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      ) : (
        <Typography color="text.secondary">
          {role === 'Teacher'
            ? 'Use Attendance to mark a class, or Fee Status to see which students have pending fees.'
            : "School-wide fee totals are visible to Admin only. Use Student Fee to manage an individual student's fees."}
        </Typography>
      )}

      {canSeeAttendanceStatus && (
        <Box sx={{ mt: 4 }}>
          <Typography variant="h6" gutterBottom>
            Today's Attendance Status
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Classes that haven't fully marked attendance yet today — worth a nudge to the teacher, or a heads-up to parents.
          </Typography>
          <TableContainer sx={{ maxWidth: 600 }}>
            <Table size="small" sx={{ minWidth: 360 }}>
            <TableHead>
              <TableRow>
                <TableCell>Class</TableCell>
                <TableCell>Marked / Total</TableCell>
                <TableCell>Status</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {attendanceStatus?.map((row) => (
                <TableRow key={row.class_name}>
                  <TableCell>{row.class_name}</TableCell>
                  <TableCell>{row.marked_count} / {row.total_active_students}</TableCell>
                  <TableCell>
                    {row.fully_marked ? (
                      <Chip size="small" label="Marked" color="success" />
                    ) : row.any_marked ? (
                      <Chip size="small" label="Partial" color="warning" />
                    ) : (
                      <Chip size="small" label="Not Marked" color="error" />
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
            </Table>
          </TableContainer>
        </Box>
      )}

      {isAdmin && <ChartErrorBoundary><AnalyticsSection /></ChartErrorBoundary>}
    </Box>
  )
}

function AnalyticsSection() {
  const { data: grades } = useQuery({ queryKey: ['grades'], queryFn: listGrades })
  const [classFilter, setClassFilter] = useState('')
  const [months, setMonths] = useState(6)
  const { data, isLoading } = useQuery({
    queryKey: ['dashboard-fee-analytics', classFilter, months],
    queryFn: () => getFeeAnalytics(months, classFilter),
  })

  return (
    <Box sx={{ mt: 5 }}>
      <Typography variant="h6" gutterBottom>
        Analytics
      </Typography>
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

      {isLoading || !data ? (
        <Grid container spacing={3}>
          <Grid size={{ xs: 12, md: 7 }}><Skeleton variant="rounded" height={340} /></Grid>
          <Grid size={{ xs: 12, md: 5 }}><Skeleton variant="rounded" height={340} /></Grid>
          <Grid size={{ xs: 12 }}><Skeleton variant="rounded" height={340} /></Grid>
        </Grid>
      ) : (
        <Grid container spacing={3}>
          <Grid size={{ xs: 12, md: 7 }}>
            <Card>
              <CardContent>
                <Typography variant="subtitle1" gutterBottom>Collected vs. Pending by Class</Typography>
                {data.by_class.length > 0 ? (
                  <BarChart
                    height={300}
                    dataset={data.by_class}
                    xAxis={[{ dataKey: 'class_name', scaleType: 'band' }]}
                    series={[
                      { dataKey: 'collected', label: 'Collected', color: '#2e7d32' },
                      { dataKey: 'pending', label: 'Pending', color: '#c62828' },
                    ]}
                  />
                ) : (
                  <Typography color="text.secondary">No data yet.</Typography>
                )}
              </CardContent>
            </Card>
          </Grid>

          <Grid size={{ xs: 12, md: 5 }}>
            <Card>
              <CardContent>
                <Typography variant="subtitle1" gutterBottom>Voucher Status</Typography>
                {Object.values(data.voucher_status_counts).some((v) => v > 0) ? (
                  <PieChart
                    height={300}
                    series={[{
                      data: Object.entries(data.voucher_status_counts).map(([status, count]) => ({
                        id: status, value: count, label: status,
                        color: status === 'Paid' ? '#2e7d32' : status === 'Partial' ? '#ed6c02' : '#c62828',
                      })),
                      innerRadius: 50,
                    }]}
                  />
                ) : (
                  <Typography color="text.secondary">No vouchers yet.</Typography>
                )}
                <Box sx={{ display: 'flex', gap: 1, mt: 1, flexWrap: 'wrap', justifyContent: 'center' }}>
                  {Object.entries(data.voucher_status_counts).map(([status, count]) => (
                    <Chip key={status} label={`${status}: ${count}`} color={STATUS_COLOR[status] ?? 'default'} size="small" />
                  ))}
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid size={{ xs: 12 }}>
            <Card>
              <CardContent>
                <Typography variant="subtitle1" gutterBottom>Monthly Collection Trend</Typography>
                {data.monthly_trend.length > 0 ? (
                  <LineChart
                    height={300}
                    dataset={data.monthly_trend}
                    xAxis={[{ dataKey: 'month', scaleType: 'point' }]}
                    series={[
                      { dataKey: 'billed', label: 'Billed', color: '#1565c0' },
                      { dataKey: 'collected', label: 'Collected', color: '#2e7d32' },
                      { dataKey: 'discounted', label: 'Discounted', color: '#ed6c02' },
                    ]}
                  />
                ) : (
                  <Typography color="text.secondary">No data yet.</Typography>
                )}
              </CardContent>
            </Card>
          </Grid>

          <Grid size={{ xs: 12 }}>
            <Card>
              <CardContent>
                <Typography variant="subtitle1" gutterBottom>Per-Class Breakdown</Typography>
                <TableContainer>
                  <Table size="small" sx={{ minWidth: 560 }}>
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
                </TableContainer>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}
    </Box>
  )
}

// Keeps a chart-rendering bug from taking down the whole Dashboard for Admin.
class ChartErrorBoundary extends Component<{ children: ReactNode }, { hasError: boolean }> {
  state = { hasError: false }
  static getDerivedStateFromError() {
    return { hasError: true }
  }
  render() {
    if (this.state.hasError) {
      return <Typography color="text.secondary">Analytics charts couldn't be displayed right now.</Typography>
    }
    return this.props.children
  }
}
